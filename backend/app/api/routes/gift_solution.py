from fastapi import APIRouter

from app.schemas.gift_solution import GiftSolutionGenerateRequest, GiftSolutionResponse
from app.services.gift_solution_service import GiftSolutionService

router = APIRouter()


@router.post("/generate", response_model=GiftSolutionResponse)
async def generate_gift_solution(payload: GiftSolutionGenerateRequest) -> GiftSolutionResponse:
    return await GiftSolutionService().generate(payload)
