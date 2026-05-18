from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.product import ProductCard


class GiftListAddRequest(BaseModel):
    list_id: str = "default"
    product: ProductCard
    quantity: int = Field(default=1, ge=1, le=99)


class GiftListItem(BaseModel):
    product: ProductCard
    quantity: int = 1
    added_at: datetime


class GiftListResponse(BaseModel):
    list_id: str
    items: list[GiftListItem]
    total_count: int
    total_amount: Decimal | None = None

