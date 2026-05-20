from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from itertools import combinations

from app.schemas.gift_intent import GiftIntent
from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationPlan
from app.schemas.recommendation_score import ProductScore


RankedProduct = tuple[ProductCard, dict[str, object], ProductScore]


class BudgetOptimizerService:
    """Build recommendation plans from already recalled and scored products."""

    def build_plans(
        self,
        *,
        ranked: Sequence[RankedProduct],
        max_products: int,
        intent: GiftIntent,
    ) -> list[RecommendationPlan]:
        if not ranked:
            return []
        budget = intent.budget
        budget_upper_bound = self._budget_upper_bound(intent)

        ranked_plan = self._build_plan(
            plan_id="ranked_topn",
            plan_type="ranked_topn",
            items=list(ranked[:max_products]),
            budget=budget,
            budget_upper_bound=budget_upper_bound,
            budget_constraint_type=intent.budget_constraint_type,
            judge_reason="按商品相关度排序得到的默认推荐方案",
        )
        optimized_plan = self._build_optimized_plan(
            ranked=ranked,
            max_products=max_products,
            budget=budget,
            budget_upper_bound=budget_upper_bound,
            budget_constraint_type=intent.budget_constraint_type,
        )

        plans = [ranked_plan]
        if optimized_plan and optimized_plan.product_ids != ranked_plan.product_ids:
            plans.append(optimized_plan)
        elif optimized_plan:
            plans[0] = ranked_plan.model_copy(
                update={
                    "objective_score": max(
                        ranked_plan.objective_score,
                        optimized_plan.objective_score,
                    )
                }
            )
        return plans

    def _build_optimized_plan(
        self,
        *,
        ranked: Sequence[RankedProduct],
        max_products: int,
        budget: Decimal | None,
        budget_upper_bound: Decimal | None,
        budget_constraint_type: str,
    ) -> RecommendationPlan | None:
        shortlist = list(ranked[: min(len(ranked), 16)])
        best: RecommendationPlan | None = None
        max_size = max(1, min(max_products, len(shortlist)))

        for size in range(1, max_size + 1):
            for combo in combinations(shortlist, size):
                if budget_upper_bound is not None and self._total_price(combo) > budget_upper_bound:
                    continue
                plan = self._build_plan(
                    plan_id="budget_optimized",
                    plan_type="budget_optimized",
                    items=list(combo),
                    budget=budget,
                    budget_upper_bound=budget_upper_bound,
                    budget_constraint_type=budget_constraint_type,
                    judge_reason="在预算约束内综合相关度、预算利用和组合多样性得到的方案",
                )
                if best is None or plan.objective_score > best.objective_score:
                    best = plan

        return best

    def _build_plan(
        self,
        *,
        plan_id: str,
        plan_type: str,
        items: list[RankedProduct],
        budget: Decimal | None,
        budget_upper_bound: Decimal | None,
        budget_constraint_type: str,
        judge_reason: str,
    ) -> RecommendationPlan:
        total_price = self._total_price(items)
        budget_usage = self._budget_usage(total_price, budget)
        upper_bound_usage = self._budget_usage(total_price, budget_upper_bound)
        budget_overage = max(total_price - budget, Decimal("0")) if budget is not None else Decimal("0")
        budget_overage_ratio = (
            round(float(budget_overage / budget), 4) if budget is not None and budget > 0 else 0.0
        )
        gift_roles = self._gift_roles(items)
        cards = [
            card.model_copy(update={"gift_role": gift_roles.get(card.product_id)})
            for card, _product, _score in items
        ]
        product_ids = [card.product_id for card in cards]
        relevance_score = self._relevance_score(items)
        diversity_score = self._diversity_score(items)
        complement_score = self._complement_score(items, total_price, budget, gift_roles)
        budget_score = self._budget_score(upper_bound_usage if budget_upper_bound else budget_usage)
        overage_penalty = self._overage_penalty(
            budget_overage_ratio=budget_overage_ratio,
            budget_constraint_type=budget_constraint_type,
        )
        objective_score = round(
            0.55 * relevance_score
            + 0.20 * budget_score
            + 0.15 * diversity_score
            + 0.10 * complement_score
            - overage_penalty,
            4,
        )

        return RecommendationPlan(
            plan_id=plan_id,
            plan_type=plan_type,  # type: ignore[arg-type]
            products=cards,
            product_ids=product_ids,
            total_price=total_price,
            original_budget=budget,
            budget_upper_bound=budget_upper_bound,
            budget_constraint_type=budget_constraint_type,
            budget_usage=budget_usage,
            upper_bound_usage=upper_bound_usage,
            budget_overage=budget_overage,
            budget_overage_ratio=budget_overage_ratio,
            gift_roles=gift_roles,
            relevance_score=relevance_score,
            diversity_score=diversity_score,
            complement_score=complement_score,
            objective_score=objective_score,
            judge_reason=judge_reason,
        )

    @staticmethod
    def _budget_upper_bound(intent: GiftIntent) -> Decimal | None:
        if intent.budget_upper_bound is not None:
            return intent.budget_upper_bound
        if intent.budget is None:
            return None
        flexibility = intent.budget_flexibility
        if flexibility is None:
            if intent.budget_constraint_type == "hard":
                flexibility = 0.0
            elif intent.budget_constraint_type == "negotiable":
                flexibility = 0.30
            else:
                flexibility = 0.15
        return (intent.budget * (Decimal("1") + Decimal(str(flexibility)))).quantize(Decimal("1"))

    @staticmethod
    def _total_price(items: Sequence[RankedProduct]) -> Decimal:
        total = Decimal("0")
        for card, _product, _score in items:
            total += card.price or Decimal("0")
        return total

    @staticmethod
    def _budget_usage(total_price: Decimal, budget: Decimal | None) -> float | None:
        if budget is None or budget <= 0:
            return None
        return round(float(total_price / budget), 4)

    @staticmethod
    def _relevance_score(items: Sequence[RankedProduct]) -> float:
        if not items:
            return 0.0
        score_sum = sum(max(score.score, 0.0) for _card, _product, score in items)
        max_score = max(len(items) * 100.0, 1.0)
        return round(min(score_sum / max_score, 1.0), 4)

    @staticmethod
    def _budget_score(budget_usage: float | None) -> float:
        if budget_usage is None:
            return 0.5
        if budget_usage <= 0:
            return 0.0
        if budget_usage > 1:
            return 0.0
        if budget_usage >= 0.65:
            return 1.0
        if budget_usage >= 0.35:
            return 0.75
        return 0.45

    @staticmethod
    def _overage_penalty(
        *,
        budget_overage_ratio: float,
        budget_constraint_type: str,
    ) -> float:
        if budget_overage_ratio <= 0:
            return 0.0
        if budget_constraint_type == "hard":
            return 1.0
        if budget_constraint_type == "negotiable":
            return min(budget_overage_ratio * 0.45, 0.18)
        return min(budget_overage_ratio * 0.75, 0.28)

    @staticmethod
    def _gift_roles(items: Sequence[RankedProduct]) -> dict[str, str]:
        if not items:
            return {}
        if len(items) == 1:
            return {items[0][0].product_id: "main_gift"}

        def main_rank(item: RankedProduct) -> tuple[float, Decimal]:
            card, _product, score = item
            return score.score, card.price or Decimal("0")

        main = max(items, key=main_rank)
        roles: dict[str, str] = {}
        for card, _product, _score in items:
            roles[card.product_id] = "main_gift" if card.product_id == main[0].product_id else "addon_gift"
        return roles

    @staticmethod
    def _diversity_score(items: Sequence[RankedProduct]) -> float:
        if len(items) <= 1:
            return 0.35
        categories = {
            str(product.get("category") or "")
            for _card, product, _score in items
            if product.get("category")
        }
        tag_set = {
            tag
            for card, _product, _score in items
            for tag in card.tags
            if tag
        }
        category_score = min(len(categories) / len(items), 1.0)
        tag_score = min(len(tag_set) / max(len(items) * 2, 1), 1.0)
        return round(0.65 * category_score + 0.35 * tag_score, 4)

    @staticmethod
    def _complement_score(
        items: Sequence[RankedProduct],
        total_price: Decimal,
        budget: Decimal | None,
        gift_roles: dict[str, str],
    ) -> float:
        if len(items) <= 1:
            return 0.35
        main_items = [
            (card, product, score)
            for card, product, score in items
            if gift_roles.get(card.product_id) == "main_gift"
        ]
        addon_items = [
            (card, product, score)
            for card, product, score in items
            if gift_roles.get(card.product_id) == "addon_gift"
        ]
        if not main_items or not addon_items:
            return 0.45
        main_card, main_product, _score = main_items[0]
        addon_prices = [card.price or Decimal("0") for card, _product, _score in addon_items]
        main_price = main_card.price or Decimal("0")
        has_main_and_addon = bool(addon_prices) and main_price >= min(addon_prices) * Decimal("1.5")
        main_category = str(main_product.get("category") or "")
        addon_categories = {
            str(product.get("category") or "")
            for _card, product, _score in addon_items
            if product.get("category")
        }
        category_bonus = 0.15 if main_category and any(item != main_category for item in addon_categories) else 0
        usage = float(total_price / budget) if budget and budget > 0 else 0.0
        usage_bonus = 0.25 if 0.55 <= usage <= 1 else 0.0
        return round(min((0.65 if has_main_and_addon else 0.45) + category_bonus + usage_bonus, 1.0), 4)
