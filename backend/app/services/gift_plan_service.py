from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.agent.prompts import (
    GIFT_PLAN_PROMPT_VERSION,
    GUIDE_SYSTEM_PROMPT,
    build_gift_plan_prompt,
)
from app.llm.client import LLMClient
from app.schemas.gift_plan import (
    GiftPlanGenerateRequest,
    GiftPlanResponse,
    GiftPlanValuePoint,
)
from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class GiftPlanService:
    def __init__(self) -> None:
        self.llm = LLMClient()
        self.recommendations = RecommendationService()

    async def generate(self, request: GiftPlanGenerateRequest) -> GiftPlanResponse:
        budget = request.budget or self._extract_budget(request.message)
        recommendation = await self.recommendations.recommend_products(
            RecommendationRequest(
                message=request.message,
                budget=budget,
                preference=request.preference,
                max_products=4,
                include_fallback=True,
            )
        )
        products = recommendation.products
        scores_by_product_id = {score.product_id: score for score in recommendation.scores}

        title = self._build_title(request)
        total_amount = sum((item.price or Decimal("0")) for item in products)
        remaining = budget - total_amount if budget is not None else None
        usage_percent = None
        if budget and budget > 0:
            usage_percent = min(100.0, float((total_amount / budget) * Decimal("100")))

        prompt = build_gift_plan_prompt(
            message=request.message,
            candidate_products=[
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "price": p.price,
                    "reason": p.reason,
                    "highlights": p.highlights,
                    "evidence": scores_by_product_id.get(p.product_id).reasons
                    if scores_by_product_id.get(p.product_id)
                    else [p.reason],
                    "penalties": scores_by_product_id.get(p.product_id).penalties
                    if scores_by_product_id.get(p.product_id)
                    else [],
                }
                for p in products
            ],
            budget=budget,
            preference=request.preference,
            total_amount=total_amount,
        )
        llm_result = await self.llm.generate(
            prompt,
            system=GUIDE_SYSTEM_PROMPT,
            prompt_name="gift_plan",
            prompt_version=GIFT_PLAN_PROMPT_VERSION,
        )
        structured = self._parse_structured(llm_result.text)
        if structured:
            answer = (
                str(structured.get("answer") or "").strip()
                or self._fallback_answer(request, products)
            )
            selected_ids = structured.get("selected_product_ids") or []
            if isinstance(selected_ids, list) and selected_ids:
                products = self._reorder_products(products, [str(x) for x in selected_ids])
                total_amount = sum((item.price or Decimal("0")) for item in products)
                remaining = budget - total_amount if budget is not None else None
                if budget and budget > 0:
                    usage_percent = min(
                        100.0, float((total_amount / budget) * Decimal("100"))
                    )
        else:
            answer = llm_result.text.strip() or self._fallback_answer(request, products)

        return GiftPlanResponse(
            plan_id=str(uuid4()),
            title=title,
            requirement=request.message,
            strategy=self._build_strategy(request),
            budget=budget,
            total_amount=total_amount,
            remaining_amount=remaining,
            usage_percent=round(usage_percent, 1) if usage_percent is not None else None,
            answer=answer,
            products=products,
            value_points=self._build_value_points(request),
            replacement_chips=self._build_replacement_chips(request),
        )

    # ---- structured output helpers ----

    @staticmethod
    def _parse_structured(text: str) -> dict[str, Any] | None:
        """宽松 JSON 解析：容忍 ```json ... ``` 包裹与前后多余文本。

        解析失败返回 None，由调用方走自然语言兜底。
        """
        if not text:
            return None
        candidate = text.strip()
        # 去掉 ```json ... ``` 围栏
        fence = re.match(r"```(?:json)?\s*(.+?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if fence:
            candidate = fence.group(1).strip()
        # 直接 JSON
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        # 退一步：抓取第一段 { ... }
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            logger.warning("gift_plan_json_parse_failed err=%s", exc)
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _reorder_products(
        products: list[ProductCard], selected_ids: list[str]
    ) -> list[ProductCard]:
        """按模型给出的 selected_product_ids 重排候选商品。

        - 只采用候选商品中存在的 id（防止幻觉）。
        - 模型未列出的候选商品保留在末尾，避免接口商品突然变少。
        """
        by_id = {p.product_id: p for p in products}
        ordered: list[ProductCard] = []
        seen: set[str] = set()
        for pid in selected_ids:
            if pid in by_id and pid not in seen:
                ordered.append(by_id[pid])
                seen.add(pid)
        for product in products:
            if product.product_id not in seen:
                ordered.append(product)
        return ordered

    @staticmethod
    def _extract_budget(message: str) -> Decimal | None:
        matches = re.findall(r"(\d{2,6})\s*元?", message)
        if not matches:
            return None
        return Decimal(matches[-1])

    @staticmethod
    def _build_title(request: GiftPlanGenerateRequest) -> str:
        if request.preference:
            return f"AI 组合礼单 · {request.preference}"
        if "老丈人" in request.message:
            return "老丈人见面礼组合"
        if "女朋友" in request.message or "女生" in request.message:
            return "生日礼物组合"
        return "AI 送礼组合方案"

    @staticmethod
    def _build_strategy(request: GiftPlanGenerateRequest) -> str:
        if request.preference:
            return f"根据“{request.preference}”偏好重新生成组合方案"
        return "推荐策略：组合礼单，而不是单一商品"

    @staticmethod
    def _build_value_points(request: GiftPlanGenerateRequest) -> list[GiftPlanValuePoint]:
        if request.preference and "高端" in request.preference:
            return [
                GiftPlanValuePoint(title="品质升级", desc="优先选择更有分量和品质感的主礼。", icon="🎁"),
                GiftPlanValuePoint(title="体面表达", desc="适合正式关系和重要场景，不显随意。", icon="🎩"),
                GiftPlanValuePoint(title="兼顾实用", desc="在预算内保留真实使用价值。", icon="✨"),
            ]
        return [
            GiftPlanValuePoint(title="体面感", desc="组合方案比单件礼物更有分量。", icon="🎩"),
            GiftPlanValuePoint(title="实用性", desc="覆盖日常使用、健康关怀或兴趣偏好。", icon="✨"),
            GiftPlanValuePoint(title="自然度", desc="多件搭配降低送礼压力，更容易被接受。", icon="🎁"),
        ]

    @staticmethod
    def _build_replacement_chips(request: GiftPlanGenerateRequest) -> list[str]:
        if request.preference and "高端" in request.preference:
            return ["控制在 4000 内", "更健康", "更商务", "增加科技感", "更适合第一次见面"]
        return ["更高端", "更健康", "更稳妥", "控制在 2500 内", "增加科技感"]

    @staticmethod
    def _fallback_answer(
        request: GiftPlanGenerateRequest, products: list[ProductCard]
    ) -> str:
        names = "、".join(item.name for item in products)
        return f"我建议用组合礼单来满足这个场景：{names}。这样可以兼顾体面感、实用性和预算控制。"
