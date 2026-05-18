from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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


class ProductCard(BaseModel):
    product_id: str
    name: str
    image_url: str | None = None
    price: Decimal | None = None
    tags: list[str] = []
    highlights: list[str] = []
    reason: str
    detail_url: str | None = None

