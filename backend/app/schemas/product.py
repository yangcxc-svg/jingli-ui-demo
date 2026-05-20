from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


BudgetLevel = str  # "low" | "mid" | "high" | "luxury"
GiftRole = Literal["main_gift", "addon_gift"]


class ProductCreate(BaseModel):
    name: str
    category: str
    price: Decimal | None = None
    image_url: str | None = None
    brand: str | None = None
    tags: list[str] = []
    specs: dict[str, object] = {}


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    status: str = "active"
    scenarios: list[str] = []
    target_people: list[str] = []
    budget_level: BudgetLevel | None = None
    avoid_for: list[str] = []
    highlights: list[str] = []
    purchase_url: str | None = None


class ProductCard(BaseModel):
    product_id: str
    name: str
    image_url: str | None = None
    price: Decimal | None = None
    tags: list[str] = []
    highlights: list[str] = []
    reason: str
    display_reason: str | None = None
    matched_features: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)
    detail_url: str | None = None
    scenarios: list[str] = Field(default_factory=list)
    target_people: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel | None = None
    avoid_for: list[str] = Field(default_factory=list)
    gift_role: GiftRole | None = None
