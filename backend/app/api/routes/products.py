from fastapi import APIRouter, Query

from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.recommendation import RecommendationRequest, RecommendationResult
from app.services.product_service import ProductService
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("", response_model=list[ProductResponse])
async def list_products() -> list[ProductResponse]:
    return await ProductService().list_products()


@router.get("/search", response_model=list[ProductResponse])
async def search_products(
    q: str = Query("", description="商品关键词"),
    limit: int = Query(20, ge=1, le=50),
) -> list[ProductResponse]:
    return await ProductService().search_products(query=q, limit=limit)


@router.post("", response_model=ProductResponse)
async def create_product(payload: ProductCreate) -> ProductResponse:
    return await ProductService().create_product(payload)


@router.post("/recommendations", response_model=RecommendationResult)
async def recommend_products(payload: RecommendationRequest) -> RecommendationResult:
    return await RecommendationService().recommend_products(payload)
