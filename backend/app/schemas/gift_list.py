from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.product import ProductCard


class GiftListAddRequest(BaseModel):
    list_id: str = "default"
    product: ProductCard
    quantity: int = Field(default=1, ge=1, le=99)


class GiftListUpdateRequest(BaseModel):
    list_id: str = "default"
    quantity: int = Field(ge=0, le=99)


class GiftListItem(BaseModel):
    product: ProductCard
    quantity: int = 1
    added_at: datetime


class GiftListResponse(BaseModel):
    list_id: str
    items: list[GiftListItem]
    total_count: int
    total_amount: Decimal | None = None


class GiftListCheckoutItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=99)


class GiftListCheckoutPreviewRequest(BaseModel):
    list_id: str = "default"
    items: list[GiftListCheckoutItemRequest]


class GiftListCheckoutItem(BaseModel):
    product: ProductCard
    quantity: int
    subtotal: Decimal | None = None


class GiftListCheckoutPreviewResponse(BaseModel):
    list_id: str
    items: list[GiftListCheckoutItem]
    total_count: int
    total_amount: Decimal | None = None
    unavailable_product_ids: list[str] = []
