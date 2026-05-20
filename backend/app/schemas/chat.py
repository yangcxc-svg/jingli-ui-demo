from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationStrategy, RelaxationOption


class ChatRequest(BaseModel):
    user_id: str | None = None
    conversation_id: str | None = None
    message: str = Field(min_length=1)
    image_ids: list[str] = []
    recommendation_strategy: RecommendationStrategy | None = None
    allow_generic_recommendation: bool = False
    use_profile: bool = True


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    text: str


class IntentState(BaseModel):
    intent: str = "general_question"
    category: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    scenario: str | None = None
    preference: list[str] = []
    constraints: list[str] = []
    compare_targets: list[str] = []


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    intent: IntentState
    products: list[ProductCard] = []
    citations: list[Citation] = []
    needs_clarification: bool = False
    clarification_question: str | None = None
    needs_relaxation: bool = False
    relaxation_reason: str | None = None
    relaxation_options: list[RelaxationOption] = []
    suggested_questions: list[str] = []


class StreamEvent(BaseModel):
    event: Literal["message_delta", "product_cards", "relaxation_options", "citation", "done", "error"]
    text: str | None = None
    products: list[ProductCard] = []
    relaxation_options: list[RelaxationOption] = []
    relaxation_reason: str | None = None
    suggested_questions: list[str] = []
    citations: list[Citation] = []
    conversation_id: str | None = None
    message_id: str | None = None
