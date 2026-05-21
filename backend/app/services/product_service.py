from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse


class ProductService:
    def __init__(self) -> None:
        self.repo = ProductRepository()

    async def list_products(self) -> list[ProductResponse]:
        return await self.repo.list_products()

    async def search_products(self, query: str, limit: int = 20) -> list[ProductResponse]:
        return await self.repo.search_products(query=query, limit=limit)

    async def create_product(self, payload: ProductCreate) -> ProductResponse:
        return await self.repo.create_product(payload)
