from decimal import Decimal

from pydantic import BaseModel

from app.schemas.product import ProductCard


class GiftPlanGenerateRequest(BaseModel):
    message: str
    budget: Decimal | None = None
    preference: str | None = None


class GiftPlanValuePoint(BaseModel):
    title: str
    desc: str
    icon: str = "✨"


class GiftPlanResponse(BaseModel):
    plan_id: str
    title: str
    requirement: str
    strategy: str
    budget: Decimal | None = None
    total_amount: Decimal
    remaining_amount: Decimal | None = None
    usage_percent: float | None = None
    answer: str
    products: list[ProductCard]
    value_points: list[GiftPlanValuePoint]
    replacement_chips: list[str]

