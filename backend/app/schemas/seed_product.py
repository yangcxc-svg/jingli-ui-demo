"""Seed product schema and normalization.

定义 storage/sample_docs/seed_products.json 的统一商品 schema。
- 既兼容现有字段（use_cases / target_users / not_recommended_for / comparison_tags）
- 也支持任务 5 建议字段（scenarios / target_people / avoid_for / tags / budget_level）
- price 必须为非负数；price_level 自动按价格区间推导（可被 JSON 覆盖）
- image_url / purchase_url 必须看起来像合法 URL 或本地资源路径
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


BudgetLevel = Literal["low", "mid", "high", "luxury"]


def _infer_budget_level(price: Decimal | None) -> BudgetLevel | None:
    if price is None:
        return None
    if price < Decimal("500"):
        return "low"
    if price < Decimal("3000"):
        return "mid"
    if price < Decimal("10000"):
        return "high"
    return "luxury"


def _looks_like_url_or_path(value: str) -> bool:
    if not value:
        return False
    return (
        value.startswith("http://")
        or value.startswith("https://")
        or value.startswith("/")
        or value.startswith("./")
    )


class SeedProduct(BaseModel):
    """Seed JSON 中单个商品的统一 schema。"""

    model_config = ConfigDict(extra="allow")

    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    price: Decimal | None = None
    currency: str = "CNY"
    brand: str | None = None
    image_url: str | None = None
    purchase_url: str | None = None

    # 任务 5 建议字段（统一对外字段名）
    scenarios: list[str] = Field(default_factory=list)
    target_people: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel | None = None
    tags: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    avoid_for: list[str] = Field(default_factory=list)
    description: str | None = None

    # 现有字段保留（不强制必填）
    use_cases: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(default_factory=list)
    not_recommended_for: list[str] = Field(default_factory=list)
    comparison_tags: list[str] = Field(default_factory=list)
    specs: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"

    @field_validator("price")
    @classmethod
    def _price_non_negative(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("price must be non-negative")
        return value

    @field_validator("image_url", "purchase_url")
    @classmethod
    def _url_looks_valid(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if not _looks_like_url_or_path(value):
            raise ValueError(f"invalid url-like value: {value!r}")
        return value

    @model_validator(mode="after")
    def _normalize_aliases(self) -> "SeedProduct":
        # 老字段 -> 新字段的回填，确保推荐过滤可用
        if not self.scenarios and self.use_cases:
            self.scenarios = list(self.use_cases)
        if not self.target_people and self.target_users:
            self.target_people = list(self.target_users)
        if not self.avoid_for and self.not_recommended_for:
            self.avoid_for = list(self.not_recommended_for)
        if not self.tags and self.comparison_tags:
            self.tags = list(self.comparison_tags)

        # budget_level 自动推导（允许 JSON 显式覆盖）
        if self.budget_level is None:
            self.budget_level = _infer_budget_level(self.price)

        return self


class SeedProductCatalogFile(BaseModel):
    """seed_products.json 顶层结构。"""

    products: list[SeedProduct]


def validate_products_payload(raw: Any) -> tuple[list[SeedProduct], list[str]]:
    """对外校验入口。

    返回 (有效商品列表, 错误信息列表)。
    错误信息按商品 product_id 或下标定位，方便启动期或 CLI 报错时定位。
    """
    errors: list[str] = []
    if not isinstance(raw, dict) or "products" not in raw:
        return [], ["seed json 顶层缺少 'products' 字段"]

    items = raw.get("products")
    if not isinstance(items, list):
        return [], ["seed json 'products' 字段必须为数组"]

    validated: list[SeedProduct] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        locator = (
            f"products[{index}] (product_id={item.get('product_id')!r})"
            if isinstance(item, dict)
            else f"products[{index}]"
        )
        try:
            product = SeedProduct.model_validate(item)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{locator}: {exc}")
            continue
        if product.product_id in seen_ids:
            errors.append(f"{locator}: duplicate product_id {product.product_id!r}")
            continue
        seen_ids.add(product.product_id)
        validated.append(product)

    return validated, errors