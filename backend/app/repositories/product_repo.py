from decimal import Decimal

from app.schemas.product import ProductCreate, ProductResponse
from app.services.seed_product_loader import seed_product_catalog


def _as_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


class ProductRepository:
    async def list_products(self) -> list[ProductResponse]:
        products = seed_product_catalog.list_products()
        return [self._to_response(product) for product in products]

    async def create_product(self, payload: ProductCreate) -> ProductResponse:
        return ProductResponse(
            product_id="product_placeholder",
            status="active",
            **payload.model_dump(),
        )

    @staticmethod
    def _to_response(product: dict[str, object]) -> ProductResponse:
        # 任务 5：优先 tags 字段，回退到 comparison_tags / use_cases
        tags = product.get("tags")
        if not isinstance(tags, list) or not tags:
            tags = product.get("comparison_tags")
        if not isinstance(tags, list) or not tags:
            tags = product.get("use_cases")
        if not isinstance(tags, list):
            tags = []

        return ProductResponse(
            product_id=str(product.get("product_id") or ""),
            status=str(product.get("status") or "active"),
            name=str(product.get("name") or ""),
            category=str(product.get("category") or ""),
            price=Decimal(str(product["price"])) if product.get("price") is not None else None,
            image_url=str(product.get("image_url") or "") or None,
            brand=str(product.get("brand") or "") or None,
            tags=[str(tag) for tag in tags],
            specs=product.get("specs") if isinstance(product.get("specs"), dict) else {},
            scenarios=_as_str_list(product.get("scenarios")),
            target_people=_as_str_list(product.get("target_people")),
            budget_level=(
                str(product.get("budget_level")) if product.get("budget_level") else None
            ),
            avoid_for=_as_str_list(product.get("avoid_for")),
            highlights=_as_str_list(product.get("highlights")),
            purchase_url=str(product.get("purchase_url") or "") or None,
        )