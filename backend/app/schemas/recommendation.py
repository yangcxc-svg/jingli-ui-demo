from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.gift_intent import GiftIntent
from app.schemas.product import ProductCard
from app.schemas.recommendation_score import ProductScore, RecommendationEvidence


BudgetLevel = Literal["low", "mid", "high", "luxury"]
RecommendationStrategy = Literal["llm_direct", "hybrid_algorithm", "llm_rerank"]
RecommendationPlanType = Literal["ranked_topn", "budget_optimized"]


class RecommendationRequest(BaseModel):
    message: str
    user_id: str | None = None
    scenario: str | None = None
    budget: Decimal | None = None
    preference: str | None = None
    conversation_id: str | None = None
    max_products: int = 3
    max_candidates: int = 20
    include_fallback: bool = False
    strategy: RecommendationStrategy | None = None
    allow_generic_recommendation: bool = False
    use_profile: bool = True

    # 任务 5：新增过滤维度
    scenarios: list[str] = Field(default_factory=list)
    target_people: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel | None = None
    gift_intent: GiftIntent | None = None


class RelaxationOption(BaseModel):
    option_id: str
    label: str
    description: str
    patch: dict[str, object] = Field(default_factory=dict)


class RecommendationPlan(BaseModel):
    plan_id: str
    plan_type: RecommendationPlanType
    products: list[ProductCard]
    product_ids: list[str] = Field(default_factory=list)
    total_price: Decimal = Decimal("0")
    original_budget: Decimal | None = None
    budget_upper_bound: Decimal | None = None
    budget_constraint_type: str = "unknown"
    budget_usage: float | None = None
    upper_bound_usage: float | None = None
    budget_overage: Decimal = Decimal("0")
    budget_overage_ratio: float = 0.0
    gift_roles: dict[str, str] = Field(default_factory=dict)
    relevance_score: float = 0.0
    diversity_score: float = 0.0
    complement_score: float = 0.0
    objective_score: float = 0.0
    judge_reason: str = ""


class RecommendationResult(BaseModel):
    products: list[ProductCard]
    citations: list[dict[str, object]] = []
    intent: GiftIntent | None = None
    needs_clarification: bool = False
    clarification_question: str | None = None
    missing_slots: list[str] = Field(default_factory=list)
    scores: list[ProductScore] = Field(default_factory=list)
    evidence: list[RecommendationEvidence] = Field(default_factory=list)
    needs_relaxation: bool = False
    relaxation_reason: str | None = None
    relaxation_options: list[RelaxationOption] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    plans: list[RecommendationPlan] = Field(default_factory=list)
    selected_plan_id: str | None = None
    selected_plan_type: RecommendationPlanType | None = None
    plan_judge_reason: str | None = None
    strategy: RecommendationStrategy = "llm_direct"
    pipeline: dict[str, int | float | str | bool | None] = Field(default_factory=dict)
