import asyncio
import time
from collections.abc import AsyncIterator
from uuid import uuid4

from app.agent.graph import GuideAgent
from app.llm.client import ChatMessage
from app.metrics.collector import MetricsCollector
from app.schemas.chat import ChatRequest, ChatResponse, IntentState, StreamEvent
from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationRequest
from app.services.conversation_memory import ConversationMemory
from app.services.recommendation_service import RecommendationService


class ChatService:
    def __init__(self) -> None:
        self.agent = GuideAgent()
        self.metrics = MetricsCollector()
        self.memory = ConversationMemory()
        self.recommendations = RecommendationService()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        conversation_id = request.conversation_id or str(uuid4())
        history = self._get_history(conversation_id)
        recommendation_message = self._build_recommendation_message(
            request.message,
            conversation_id=conversation_id,
        )
        recommendation = await self.recommendations.recommend_products(
            RecommendationRequest(
                message=recommendation_message,
                user_id=request.user_id,
                conversation_id=conversation_id,
                max_products=3,
                include_fallback=False,
                strategy=request.recommendation_strategy,
                allow_generic_recommendation=request.allow_generic_recommendation,
                use_profile=request.use_profile,
            )
        )
        if recommendation.needs_clarification:
            answer = recommendation.clarification_question or "我还需要补充一个关键信息，才能更准确推荐。"
            message_id = str(uuid4())
            self.memory.append_pair(
                conversation_id,
                user_message=request.message,
                assistant_message=answer,
            )
            return ChatResponse(
                conversation_id=conversation_id,
                message_id=message_id,
                answer=answer,
                intent=IntentState(intent="clarification"),
                products=[],
                citations=[],
                needs_clarification=True,
                clarification_question=answer,
            )
        relaxation = self._build_relaxation_payload(recommendation)
        use_algorithm_context = recommendation.strategy in {"hybrid_algorithm", "llm_rerank"}
        started = time.perf_counter()
        result = await self.agent.run(
            request.message,
            conversation_id=conversation_id,
            image_ids=request.image_ids,
            history=history,
            candidate_products=self._build_candidate_payload(recommendation)
            if use_algorithm_context
            else None,
            relaxation=relaxation,
            selected_plan=self._build_selected_plan_payload(recommendation)
            if use_algorithm_context
            else None,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        message_id = str(uuid4())

        self.metrics.record_chat(
            query=request.message,
            answer_chars=len(result.answer or ""),
            citation_count=len(result.citations or []),
            latency_ms=latency_ms,
            has_images=bool(request.image_ids),
        )
        self.memory.append_pair(
            conversation_id,
            user_message=request.message,
            assistant_message=result.answer,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            answer=result.answer,
            intent=result.intent,
            products=recommendation.products if use_algorithm_context else result.products,
            citations=result.citations,
            needs_relaxation=recommendation.needs_relaxation,
            relaxation_reason=recommendation.relaxation_reason,
            relaxation_options=recommendation.relaxation_options,
            suggested_questions=recommendation.suggested_questions,
        )

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        conversation_id = request.conversation_id or str(uuid4())
        message_id = str(uuid4())
        history = self._get_history(conversation_id)
        recommendation_message = self._build_recommendation_message(
            request.message,
            conversation_id=conversation_id,
        )
        # 为了能在 stream 结束时记录指标，我们累计 delta 并预取推荐商品。
        recommendation = await self.recommendations.recommend_products(
            RecommendationRequest(
                message=recommendation_message,
                user_id=request.user_id,
                conversation_id=conversation_id,
                max_products=3,
                include_fallback=False,
                strategy=request.recommendation_strategy,
                allow_generic_recommendation=request.allow_generic_recommendation,
                use_profile=request.use_profile,
            )
        )
        if recommendation.needs_clarification:
            answer = recommendation.clarification_question or "我还需要补充一个关键信息，才能更准确推荐。"
            async for event in self._stream_text(answer):
                yield event
            self.memory.append_pair(
                conversation_id,
                user_message=request.message,
                assistant_message=answer,
            )
            yield StreamEvent(
                event="done",
                conversation_id=conversation_id,
                message_id=message_id,
            )
            return
        citations_n = len(recommendation.citations)
        use_algorithm_context = recommendation.strategy in {"hybrid_algorithm", "llm_rerank"}
        product_cards = recommendation.products if use_algorithm_context else []
        if recommendation.needs_relaxation:
            yield StreamEvent(
                event="relaxation_options",
                relaxation_options=recommendation.relaxation_options,
                relaxation_reason=recommendation.relaxation_reason,
                suggested_questions=recommendation.suggested_questions,
            )
        # 任务 6 续：将预取的候选商品作为白名单注入 prompt，避免模型编造不存在的商品。
        candidate_dicts = (
            self._build_candidate_payload(recommendation) if use_algorithm_context else None
        )
        started = time.perf_counter()
        buffer: list[str] = []
        async for delta in self.agent.astream(
            request.message,
            conversation_id=conversation_id,
            image_ids=request.image_ids,
            history=history,
            candidate_products=candidate_dicts,
            relaxation=self._build_relaxation_payload(recommendation),
            selected_plan=self._build_selected_plan_payload(recommendation)
            if use_algorithm_context
            else None,
        ):
            if delta:
                buffer.append(delta)
        answer = "".join(buffer)
        async for event in self._replay_answer_with_product_cards(answer, product_cards):
            yield event
        latency_ms = int((time.perf_counter() - started) * 1000)
        self.metrics.record_chat(
            query=request.message,
            answer_chars=len(answer),
            citation_count=citations_n,
            latency_ms=latency_ms,
            has_images=bool(request.image_ids),
        )
        self.memory.append_pair(
            conversation_id,
            user_message=request.message,
            assistant_message=answer,
        )
        yield StreamEvent(
            event="done",
            conversation_id=conversation_id,
            message_id=message_id,
        )

    def _get_history(self, conversation_id: str) -> list[ChatMessage]:
        return [
            ChatMessage(role=item.role, content=item.content)
            for item in self.memory.get_recent(conversation_id)
        ]

    @staticmethod
    def _build_relaxation_payload(recommendation) -> dict[str, object] | None:
        if not recommendation.needs_relaxation:
            return None
        return {
            "needs_relaxation": True,
            "reason": recommendation.relaxation_reason,
            "options": [item.model_dump(mode="json") for item in recommendation.relaxation_options],
            "suggested_questions": recommendation.suggested_questions,
        }

    @staticmethod
    def _build_candidate_payload(recommendation) -> list[dict[str, object]]:
        scores_by_product_id = {score.product_id: score for score in recommendation.scores}
        return [
            {
                "product_id": p.product_id,
                "name": p.name,
                "price": p.price,
                "reason": p.reason,
                "gift_role": p.gift_role,
                "evidence": scores_by_product_id.get(p.product_id).reasons
                if scores_by_product_id.get(p.product_id)
                else [p.reason],
                "penalties": scores_by_product_id.get(p.product_id).penalties
                if scores_by_product_id.get(p.product_id)
                else [],
            }
            for p in recommendation.products
        ]

    @staticmethod
    def _build_selected_plan_payload(recommendation) -> dict[str, object] | None:
        selected_plan = next(
            (plan for plan in recommendation.plans if plan.plan_id == recommendation.selected_plan_id),
            None,
        )
        if selected_plan is None:
            return None
        return {
            "selected_plan_type": recommendation.selected_plan_type,
            "plan_judge_reason": recommendation.plan_judge_reason,
            "total_price": str(selected_plan.total_price),
            "original_budget": (
                str(selected_plan.original_budget)
                if selected_plan.original_budget is not None
                else None
            ),
            "budget_upper_bound": (
                str(selected_plan.budget_upper_bound)
                if selected_plan.budget_upper_bound is not None
                else None
            ),
            "budget_constraint_type": selected_plan.budget_constraint_type,
            "budget_overage_ratio": selected_plan.budget_overage_ratio,
            "gift_roles": selected_plan.gift_roles,
        }

    def _build_recommendation_message(self, message: str, *, conversation_id: str) -> str:
        recent = self.memory.get_recent(conversation_id, max_messages=4)
        if not recent or not self._last_assistant_asked_clarification(recent):
            return message
        user_messages = [item.content for item in recent if item.role == "user"]
        if not user_messages:
            return message
        return "。".join([user_messages[-1], message])

    @staticmethod
    def _last_assistant_asked_clarification(history: list[object]) -> bool:
        assistant_messages = [
            getattr(item, "content", "")
            for item in history
            if getattr(item, "role", "") == "assistant"
        ]
        if not assistant_messages:
            return False
        last = assistant_messages[-1]
        markers = ("送给谁", "什么场景", "预算", "关键信息", "主要想送给")
        return any(marker in last for marker in markers)

    async def _replay_answer_with_product_cards(
        self, answer: str, product_cards: list[ProductCard]
    ) -> AsyncIterator[StreamEvent]:
        if not product_cards:
            async for event in self._stream_text(answer):
                yield event
            return

        sections = self._split_answer_by_products(answer, product_cards)
        emitted_product_ids: set[str] = set()
        for text, card in sections:
            if text:
                async for event in self._stream_text(text):
                    yield event
            if card and card.product_id not in emitted_product_ids:
                await asyncio.sleep(1)
                emitted_product_ids.add(card.product_id)
                yield StreamEvent(event="product_cards", products=[card])

        # 修复：只推送文本中真正被提及的商品卡片；
        # 若一个商品都没匹配上（如模型没听话编了别的名称），才退回候选池兜底，
        # 避免出现"AI 推荐 2 个、卡片区却出 3 个"的不一致体验。
        if not emitted_product_ids:
            for card in product_cards:
                await asyncio.sleep(1)
                emitted_product_ids.add(card.product_id)
                yield StreamEvent(event="product_cards", products=[card])

    async def _stream_text(self, text: str) -> AsyncIterator[StreamEvent]:
        chunk_size = 28
        for start in range(0, len(text), chunk_size):
            chunk = text[start : start + chunk_size]
            if chunk:
                yield StreamEvent(event="message_delta", text=chunk)
                await asyncio.sleep(0.015)

    def _split_answer_by_products(
        self, answer: str, product_cards: list[ProductCard]
    ) -> list[tuple[str, ProductCard | None]]:
        mentions: list[tuple[int, ProductCard]] = []
        for card in product_cards:
            candidates = [
                card.name,
                card.name.replace(" 真无线降噪耳机", ""),
                card.name.replace(" 开放式运动耳机", ""),
                " ".join(card.name.split()[1:]) if len(card.name.split()) > 1 else card.name,
            ]
            positions = [answer.find(alias) for alias in candidates if alias and answer.find(alias) != -1]
            if positions:
                mentions.append((min(positions), card))

        mentions.sort(key=lambda item: item[0])
        if not mentions:
            return [(answer, None)]

        sections: list[tuple[str, ProductCard | None]] = []
        cursor = 0
        for index, (position, card) in enumerate(mentions):
            start = self._line_start(answer, position)
            if start > cursor:
                sections.append((answer[cursor:start], None))
            if index + 1 < len(mentions):
                end = mentions[index + 1][0]
                next_start = self._line_start(answer, end)
            else:
                next_start = self._tail_start(answer, position)
            sections.append((answer[start:next_start], card))
            cursor = next_start

        if cursor < len(answer):
            sections.append((answer[cursor:], None))
        return sections

    @staticmethod
    def _line_start(text: str, position: int) -> int:
        index = text.rfind("\n", 0, position)
        return 0 if index == -1 else index + 1

    @staticmethod
    def _tail_start(text: str, from_position: int) -> int:
        tail_markers = ("补充建议", "选择建议", "总结", "小结", "最终建议", "您更", "你更")
        best = len(text)
        for marker in tail_markers:
            index = text.find(marker, from_position)
            if index != -1:
                best = min(best, index)
        return best
