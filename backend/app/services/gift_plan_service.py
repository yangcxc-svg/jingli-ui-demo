from __future__ import annotations

import re
from decimal import Decimal
from uuid import uuid4

from app.agent.prompts import GUIDE_SYSTEM_PROMPT
from app.agent.tools import AgentTools
from app.llm.client import LLMClient
from app.schemas.gift_plan import (
    GiftPlanGenerateRequest,
    GiftPlanResponse,
    GiftPlanValuePoint,
)
from app.schemas.product import ProductCard
from app.services.seed_product_loader import seed_product_catalog


class GiftPlanService:
    def __init__(self) -> None:
        self.tools = AgentTools()
        self.llm = LLMClient()

    async def generate(self, request: GiftPlanGenerateRequest) -> GiftPlanResponse:
        budget = request.budget or self._extract_budget(request.message)
        query = " ".join(
            item
            for item in [request.message, request.preference, "组合礼单 送礼 礼物 预算 场景"]
            if item
        )
        chunks = await self.tools.search_knowledge(query)
        products = self._build_product_cards(chunks, budget=budget)
        if not products:
            products = self._fallback_products(budget=budget)

        title = self._build_title(request)
        total_amount = sum((item.price or Decimal("0")) for item in products)
        remaining = budget - total_amount if budget is not None else None
        usage_percent = None
        if budget and budget > 0:
            usage_percent = min(100.0, float((total_amount / budget) * Decimal("100")))

        prompt = self._build_prompt(request, products, budget, total_amount)
        llm_result = await self.llm.generate(prompt, system=GUIDE_SYSTEM_PROMPT)
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

    def _build_product_cards(
        self, chunks: list[dict[str, object]], budget: Decimal | None
    ) -> list[ProductCard]:
        cards: list[ProductCard] = []
        seen: set[str] = set()
        running_total = Decimal("0")
        for chunk in chunks:
            product_id = str(chunk.get("document_id") or "")
            if not product_id or product_id in seen:
                continue
            product = seed_product_catalog.get_by_id(product_id)
            if not product:
                continue
            card = self._product_to_card(product_id, product)
            if budget and cards and card.price and running_total + card.price > budget * Decimal("1.15"):
                continue
            seen.add(product_id)
            cards.append(card)
            running_total += card.price or Decimal("0")
            if len(cards) >= 4:
                break
        return cards

    def _fallback_products(self, budget: Decimal | None) -> list[ProductCard]:
        products = seed_product_catalog.list_products()
        cards: list[ProductCard] = []
        running_total = Decimal("0")
        for product in products:
            product_id = str(product.get("product_id") or "")
            if not product_id:
                continue
            card = self._product_to_card(product_id, product)
            if budget and cards and card.price and running_total + card.price > budget * Decimal("1.15"):
                continue
            cards.append(card)
            running_total += card.price or Decimal("0")
            if len(cards) >= 4:
                break
        return cards

    @staticmethod
    def _product_to_card(product_id: str, product: dict[str, object]) -> ProductCard:
        tags = product.get("comparison_tags")
        if not isinstance(tags, list):
            tags = product.get("use_cases")
        if not isinstance(tags, list):
            tags = []

        highlights = product.get("highlights")
        if not isinstance(highlights, list):
            highlights = []

        return ProductCard(
            product_id=product_id,
            name=str(product.get("name") or ""),
            image_url=str(product.get("image_url") or "") or None,
            price=product.get("price"),
            tags=[str(tag) for tag in tags[:4]],
            highlights=[str(item) for item in highlights[:3]],
            reason=str(highlights[0]) if highlights else "匹配当前送礼需求",
            detail_url=str(product.get("purchase_url") or "") or None,
        )

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
    def _build_prompt(
        request: GiftPlanGenerateRequest,
        products: list[ProductCard],
        budget: Decimal | None,
        total_amount: Decimal,
    ) -> str:
        product_lines = "\n".join(
            f"- {item.name}，价格 {item.price} 元，卖点：{item.reason}"
            for item in products
        )
        budget_line = f"用户预算：{budget} 元。" if budget is not None else "用户未明确预算。"
        preference_line = f"用户偏好：{request.preference}。" if request.preference else ""
        return (
            "请为用户生成一套组合礼单说明，要求简洁、可直接展示在移动端页面。\n"
            f"用户需求：{request.message}\n"
            f"{budget_line}\n"
            f"{preference_line}\n"
            f"当前组合总价：{total_amount} 元。\n"
            "候选商品：\n"
            f"{product_lines}\n\n"
            "请说明为什么这样搭配，并给出取舍建议。不要输出内部推理过程。"
        )

    @staticmethod
    def _fallback_answer(
        request: GiftPlanGenerateRequest, products: list[ProductCard]
    ) -> str:
        names = "、".join(item.name for item in products)
        return f"我建议用组合礼单来满足这个场景：{names}。这样可以兼顾体面感、实用性和预算控制。"

