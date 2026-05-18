import asyncio
import time
from collections.abc import AsyncIterator
from uuid import uuid4

from app.agent.graph import GuideAgent
from app.llm.client import ChatMessage
from app.metrics.collector import MetricsCollector
from app.schemas.chat import ChatRequest, ChatResponse, StreamEvent
from app.schemas.product import ProductCard
from app.services.conversation_memory import ConversationMemory
from app.services.seed_product_loader import seed_product_catalog


class ChatService:
    def __init__(self) -> None:
        self.agent = GuideAgent()
        self.metrics = MetricsCollector()
        self.memory = ConversationMemory()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        conversation_id = request.conversation_id or str(uuid4())
        history = self._get_history(conversation_id)
        started = time.perf_counter()
        result = await self.agent.run(
            request.message,
            conversation_id=conversation_id,
            image_ids=request.image_ids,
            history=history,
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
            products=result.products,
            citations=result.citations,
        )

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        conversation_id = request.conversation_id or str(uuid4())
        message_id = str(uuid4())
        history = self._get_history(conversation_id)
        # 为了能在 stream 结束时记录指标，我们累计 delta 并预取 citations
        # 简化做法：仍调用 agent.astream 输出 token，但同时复用 graph 的检索逻辑统计 citations
        chunks = await self.agent.tools.search_knowledge(request.message)
        citations_n = len([c for c in chunks if c.get("text")])
        product_cards = self._build_product_cards(chunks)
        started = time.perf_counter()
        buffer: list[str] = []
        async for delta in self.agent.astream(
            request.message,
            conversation_id=conversation_id,
            image_ids=request.image_ids,
            history=history,
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

    def _build_product_cards(self, chunks: list[dict[str, object]]) -> list[ProductCard]:
        cards: list[ProductCard] = []
        seen: set[str] = set()
        for chunk in chunks:
            product_id = str(chunk.get("document_id") or "")
            if not product_id or product_id in seen:
                continue
            product = seed_product_catalog.get_by_id(product_id)
            if not product:
                continue
            seen.add(product_id)
            tags = product.get("comparison_tags")
            if not isinstance(tags, list):
                tags = product.get("use_cases")
            if not isinstance(tags, list):
                tags = []
            highlights = product.get("highlights")
            if not isinstance(highlights, list):
                highlights = []
            cards.append(
                ProductCard(
                    product_id=product_id,
                    name=str(product.get("name") or ""),
                    image_url=str(product.get("image_url") or "") or None,
                    price=product.get("price"),
                    tags=[str(tag) for tag in tags[:4]],
                    highlights=[str(item) for item in highlights[:3]],
                    reason=str(highlights[0]) if highlights else "匹配当前咨询需求",
                    detail_url=str(product.get("purchase_url") or "") or None,
                )
            )
            if len(cards) >= 3:
                break
        return cards

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

        for card in product_cards:
            if card.product_id not in emitted_product_ids:
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
