from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationStrategy


GiftShape = Literal["single_gift", "gift_combo", "either"]


class GiftShapeDecision(BaseModel):
    shape: GiftShape
    confidence: float = 0.0
    reason: str
    signals: list[str] = Field(default_factory=list)
    recommended_product_count: int = 1
    use_combo_optimizer: bool = False


class GiftSolutionGenerateRequest(BaseModel):
    message: str
    user_id: str | None = None
    conversation_id: str | None = None
    recommendation_strategy: RecommendationStrategy | None = "hybrid_algorithm"
    allow_generic_recommendation: bool = True
    use_profile: bool = True


class GiftSolutionResponse(BaseModel):
    solution_id: str
    shape_decision: GiftShapeDecision
    title: str
    summary: str
    products: list[ProductCard]
    total_amount: Decimal | None = None
    recommendation_reason: str
    giving_timing: str
    giving_place: str
    gift_talk: str
    recipient_reaction_reply: str
    packaging_advice: str
    avoid_tips: list[str] = Field(default_factory=list)
    follow_up_question: str | None = None
    selected_plan_type: str | None = None
    plan_judge_reason: str | None = None
    pipeline: dict[str, object] = Field(default_factory=dict)
