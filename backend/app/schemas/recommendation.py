from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.gift_intent import GiftIntent
from app.schemas.product import ProductCard
from app.schemas.recommendation_score import ProductScore


BudgetLevel = Literal["low", "mid", "high", "luxury"]


class RecommendationRequest(BaseModel):
    message: str
    scenario: str | None = None
    budget: Decimal | None = None
    preference: str | None = None
    conversation_id: str | None = None
    max_products: int = 3
    max_candidates: int = 20
    include_fallback: bool = False

    # 任务 5：新增过滤维度
    scenarios: list[str] = Field(default_factory=list)
    target_people: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel | None = None
    gift_intent: GiftIntent | None = None


class RecommendationResult(BaseModel):
    products: list[ProductCard]
    citations: list[dict[str, object]] = []
    intent: GiftIntent | None = None
    scores: list[ProductScore] = Field(default_factory=list)
    pipeline: dict[str, int] = Field(default_factory=dict)
