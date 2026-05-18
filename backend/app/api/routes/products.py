from fastapi import APIRouter

from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()


@router.get("", response_model=list[ProductResponse])
async def list_products() -> list[ProductResponse]:
    return await ProductService().list_products()


@router.post("", response_model=ProductResponse)
async def create_product(payload: ProductCreate) -> ProductResponse:
    return await ProductService().create_product(payload)

