from fastapi import APIRouter

from app.schemas.gift_plan import GiftPlanGenerateRequest, GiftPlanResponse
from app.services.gift_plan_service import GiftPlanService

router = APIRouter()


@router.post("/generate", response_model=GiftPlanResponse)
async def generate_gift_plan(payload: GiftPlanGenerateRequest) -> GiftPlanResponse:
    return await GiftPlanService().generate(payload)

