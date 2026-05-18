from pydantic import BaseModel

from app.schemas.chat import Citation, IntentState
from app.schemas.product import ProductCard


class AgentResult(BaseModel):
    answer: str
    intent: IntentState
    products: list[ProductCard] = []
    citations: list[Citation] = []

