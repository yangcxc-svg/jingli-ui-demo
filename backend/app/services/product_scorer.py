from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.schemas.gift_intent import GiftIntent
from app.schemas.recommendation_score import ProductScore


@dataclass(frozen=True)
class ProductScoringWeights:
    scenario_match: float = 30.0
    target_people_match: float = 25.0
    budget_fit: float = 20.0
    preference_match: float = 8.0
    style_match: float = 8.0
    rating: float = 6.0
    highlight_baseline: float = 3.0
    avoid_penalty: float = 35.0
    over_budget_penalty: float = 28.0
    unknown_price_penalty: float = 6.0


class ProductScorer:
    def __init__(self, weights: ProductScoringWeights | None = None) -> None:
        self.weights = weights or ProductScoringWeights()

    def score(self, product: dict[str, Any], intent: GiftIntent) -> ProductScore:
        product_id = str(product.get("product_id") or "")
        score = 0.0
        reasons: list[str] = []
        penalties: list[str] = []

        product_scenarios = self._as_text_set(product.get("scenarios") or product.get("use_cases"))
        product_people = self._as_text_set(product.get("target_people") or product.get("target_users"))
        product_tags = self._as_text_set(product.get("tags") or product.get("comparison_tags"))
        product_highlights = self._as_text_set(product.get("highlights"))
        product_avoid = self._as_text_set(product.get("avoid_for") or product.get("not_recommended_for"))
        product_text = " ".join(
            [
                str(product.get("name") or ""),
                str(product.get("category") or ""),
                " ".join(product_scenarios),
                " ".join(product_people),
                " ".join(product_tags),
                " ".join(product_highlights),
            ]
        )

        scenario_matches = self._intersection(intent.scenarios, product_scenarios)
        if scenario_matches:
            score += self.weights.scenario_match
            reasons.append(f"匹配送礼场景：{'、'.join(scenario_matches)}")

        people_matches = self._intersection(intent.target_people, product_people)
        if people_matches:
            score += self.weights.target_people_match
            reasons.append(f"适合送礼对象：{'、'.join(people_matches)}")

        budget_score, budget_reason, budget_penalty = self._score_budget(product, intent)
        score += budget_score
        if budget_reason:
            reasons.append(budget_reason)
        if budget_penalty:
            penalties.append(budget_penalty)

        preference_matches = self._keyword_matches(intent.preferences, product_text)
        if preference_matches:
            score += self.weights.preference_match * len(preference_matches)
            reasons.append(f"偏好命中：{'、'.join(preference_matches)}")

        style_matches = self._keyword_matches(intent.gift_style, product_text)
        if style_matches:
            score += self.weights.style_match * len(style_matches)
            reasons.append(f"风格命中：{'、'.join(style_matches)}")

        avoid_matches = self._avoid_matches(intent, product_avoid, product_text)
        if avoid_matches:
            score -= self.weights.avoid_penalty * len(avoid_matches)
            penalties.append(f"禁忌命中：{'、'.join(avoid_matches)}")

        rating_score = self._score_rating(product)
        if rating_score > 0:
            score += rating_score
            reasons.append("评价表现较好")

        if product_highlights:
            score += self.weights.highlight_baseline
            if not reasons:
                reasons.append("商品卖点完整，适合作为候选礼物")

        if not reasons:
            reasons.append("作为通用候选商品保留")

        return ProductScore(
            product_id=product_id,
            score=round(max(score, 0.0), 2),
            reasons=reasons,
            penalties=penalties,
        )

    def _score_budget(
        self,
        product: dict[str, Any],
        intent: GiftIntent,
    ) -> tuple[float, str | None, str | None]:
        price = self._to_decimal(product.get("price"))
        if price is None:
            return -self.weights.unknown_price_penalty, None, "价格未知，预算匹配不确定"

        if intent.budget is not None:
            if price <= intent.budget:
                ratio = price / intent.budget if intent.budget > 0 else Decimal("1")
                if ratio >= Decimal("0.55"):
                    return self.weights.budget_fit, "价格在预算内且礼物分量较合适", None
                return self.weights.budget_fit * 0.65, "价格在预算内，适合作为高性价比选择", None
            if price <= intent.budget * Decimal("1.15"):
                return self.weights.budget_fit * 0.25, None, "略超预算，需要用户确认"
            return -self.weights.over_budget_penalty, None, "明显超出预算"

        if intent.budget_level:
            product_budget_level = product.get("budget_level")
            if product_budget_level == intent.budget_level:
                return self.weights.budget_fit * 0.75, f"符合{intent.budget_level}预算档位", None

        return 0.0, None, None

    def _score_rating(self, product: dict[str, Any]) -> float:
        rating = product.get("rating")
        if not isinstance(rating, dict):
            return 0.0
        raw_score = self._to_decimal(rating.get("score"))
        if raw_score is None:
            return 0.0
        if raw_score >= Decimal("4.6"):
            return self.weights.rating
        if raw_score >= Decimal("4.3"):
            return self.weights.rating * 0.65
        if raw_score >= Decimal("4.0"):
            return self.weights.rating * 0.35
        return 0.0

    @staticmethod
    def _to_decimal(value: object) -> Decimal | None:
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _as_text_set(value: object) -> set[str]:
        if not isinstance(value, list):
            return set()
        return {str(item) for item in value if str(item).strip()}

    @staticmethod
    def _intersection(left: list[str], right: set[str]) -> list[str]:
        return [item for item in left if item in right]

    @staticmethod
    def _keyword_matches(keywords: list[str], product_text: str) -> list[str]:
        return [keyword for keyword in keywords if keyword and keyword in product_text]

    @staticmethod
    def _avoid_matches(
        intent: GiftIntent,
        product_avoid: set[str],
        product_text: str,
    ) -> list[str]:
        matches: list[str] = []
        for item in intent.avoid:
            if item and (item in product_text or item in product_avoid):
                matches.append(item)
        for item in product_avoid:
            if item and (
                item in intent.scenarios
                or item in intent.target_people
                or item in intent.gift_style
                or item in intent.preferences
            ):
                matches.append(item)
        return list(dict.fromkeys(matches))

