from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.agent.prompts import GUIDE_SYSTEM_PROMPT
from app.agent.prompts_lib.gift_solution import build_gift_solution_prompt
from app.llm.client import LLMClient
from app.schemas.gift_solution import GiftSolutionGenerateRequest, GiftSolutionResponse
from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationRequest
from app.services.gift_shape_service import GiftShapeService
from app.services.intent_extractor import IntentExtractor
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class GiftSolutionService:
    def __init__(self) -> None:
        self.intent_extractor = IntentExtractor()
        self.shape_service = GiftShapeService()
        self.recommendations = RecommendationService()
        self.llm = LLMClient()

    async def generate(self, request: GiftSolutionGenerateRequest) -> GiftSolutionResponse:
        intent = await self.intent_extractor.extract(request.message)
        shape = self.shape_service.decide(message=request.message, intent=intent)
        max_products = shape.recommended_product_count
        recommendation = await self.recommendations.recommend_products(
            RecommendationRequest(
                message=request.message,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                max_products=max_products,
                include_fallback=shape.use_combo_optimizer,
                strategy=request.recommendation_strategy,
                allow_generic_recommendation=request.allow_generic_recommendation,
                use_profile=request.use_profile,
                gift_intent=intent,
            )
        )
        products = self._normalize_products(recommendation.products, shape.shape)
        selected_plan = self._selected_plan_payload(recommendation)
        prompt = build_gift_solution_prompt(
            message=request.message,
            intent=intent.model_dump(mode="json") if intent else None,
            shape_decision=shape.model_dump(mode="json"),
            products=[self._product_payload(product) for product in products],
            selected_plan=selected_plan,
        )
        try:
            result = await self.llm.generate(
                prompt,
                system=GUIDE_SYSTEM_PROMPT,
                prompt_name="gift_solution",
                prompt_version="gift-solution-v1",
            )
            structured = self._parse_json_object(result.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("gift_solution_llm_failed err=%s", exc)
            structured = None

        total_amount = sum((item.price or Decimal("0")) for item in products)
        fallback = self._fallback_solution(request.message, shape.shape, products)
        data = {**fallback, **(structured or {})}

        return GiftSolutionResponse(
            solution_id=str(uuid4()),
            shape_decision=shape,
            title=str(data.get("title") or fallback["title"]),
            summary=str(data.get("summary") or fallback["summary"]),
            products=products,
            total_amount=total_amount,
            recommendation_reason=str(
                data.get("recommendation_reason") or fallback["recommendation_reason"]
            ),
            giving_timing=str(data.get("giving_timing") or fallback["giving_timing"]),
            giving_place=str(data.get("giving_place") or fallback["giving_place"]),
            gift_talk=str(data.get("gift_talk") or fallback["gift_talk"]),
            recipient_reaction_reply=str(
                data.get("recipient_reaction_reply") or fallback["recipient_reaction_reply"]
            ),
            packaging_advice=str(data.get("packaging_advice") or fallback["packaging_advice"]),
            avoid_tips=self._as_string_list(data.get("avoid_tips")) or fallback["avoid_tips"],
            follow_up_question=str(data.get("follow_up_question") or "") or None,
            selected_plan_type=recommendation.selected_plan_type,
            plan_judge_reason=recommendation.plan_judge_reason,
            pipeline={
                **recommendation.pipeline,
                "gift_shape": shape.shape,
                "gift_shape_confidence": shape.confidence,
                "gift_shape_use_combo_optimizer": shape.use_combo_optimizer,
            },
        )

    @staticmethod
    def _normalize_products(products: list[ProductCard], shape: str) -> list[ProductCard]:
        if shape == "single_gift":
            if not products:
                return []
            normalized: list[ProductCard] = []
            for index, product in enumerate(products[:3]):
                role = "main_gift" if index == 0 else None
                normalized.append(product.model_copy(update={"gift_role": role}))
            return normalized
        if not products:
            return []
        has_main = any(item.gift_role == "main_gift" for item in products)
        normalized: list[ProductCard] = []
        for index, product in enumerate(products):
            role = product.gift_role
            if role is None:
                role = "main_gift" if index == 0 and not has_main else "addon_gift"
            normalized.append(product.model_copy(update={"gift_role": role}))
        return sorted(normalized, key=lambda item: 0 if item.gift_role == "main_gift" else 1)

    @staticmethod
    def _product_payload(product: ProductCard) -> dict[str, object]:
        return {
            "product_id": product.product_id,
            "name": product.name,
            "price": str(product.price) if product.price is not None else None,
            "gift_role": product.gift_role,
            "reason": product.display_reason or product.reason,
        }

    @staticmethod
    def _selected_plan_payload(recommendation) -> dict[str, object] | None:
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
            "gift_roles": selected_plan.gift_roles,
        }

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any] | None:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        candidates = [stripped]
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1])
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    @staticmethod
    def _as_string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    @staticmethod
    def _fallback_solution(
        message: str,
        shape: str,
        products: list[ProductCard],
    ) -> dict[str, object]:
        names = "、".join(item.name for item in products) or "候选礼物"
        is_combo = shape == "gift_combo"
        return {
            "title": "组合送礼方案" if is_combo else "单品送礼方案",
            "summary": f"这次更适合用{'主礼加副礼' if is_combo else '一件清晰的主礼'}来表达心意。",
            "recommendation_reason": f"推荐 {names}，它和当前送礼对象、场景、预算更匹配。",
            "giving_timing": "建议在寒暄后、正式进入正题前送出，显得自然也不突兀。",
            "giving_place": "优先选择玄关、客厅或见面后的私下轻松场景，避免在饭桌上突然递出。",
            "gift_talk": "可以说：这是我根据你平时可能用得上的方向准备的一点心意，希望你喜欢。",
            "recipient_reaction_reply": "如果对方推辞，可以说：不是什么贵重东西，主要是想着你能用得上，收下我也更安心。",
            "packaging_advice": "建议保留简洁体面的包装，必要时附一张短卡片，文字不要太满。",
            "avoid_tips": ["不要强调价格", "不要反复解释自己花了很多心思", "避免让对方当场评价喜不喜欢"],
            "follow_up_question": "",
        }
