from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.product import ProductCard


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1)
    image_ids: list[str] = []


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


class StreamEvent(BaseModel):
    event: Literal["message_delta", "product_cards", "citation", "done", "error"]
    text: str | None = None
    products: list[ProductCard] = []
    citations: list[Citation] = []
    conversation_id: str | None = None
    message_id: str | None = None
