from fastapi import APIRouter

from app.schemas.gift_list import GiftListAddRequest, GiftListResponse
from app.services.gift_list_service import GiftListService

router = APIRouter()


@router.get("", response_model=GiftListResponse)
async def get_gift_list(list_id: str = "default") -> GiftListResponse:
    return GiftListService().get_list(list_id)


@router.post("/items", response_model=GiftListResponse)
async def add_gift_list_item(payload: GiftListAddRequest) -> GiftListResponse:
    return GiftListService().add_item(payload)


@router.delete("/items/{product_id}", response_model=GiftListResponse)
async def remove_gift_list_item(product_id: str, list_id: str = "default") -> GiftListResponse:
    return GiftListService().remove_item(product_id, list_id)
