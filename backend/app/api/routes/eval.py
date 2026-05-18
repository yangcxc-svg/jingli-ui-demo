from fastapi import APIRouter

from app.schemas.eval import EvalRunResponse, EvalSummaryResponse
from app.services.eval_service import EvalService

router = APIRouter()


@router.post("/run", response_model=EvalRunResponse)
async def run_eval() -> EvalRunResponse:
    return await EvalService().run()


@router.get("/results", response_model=EvalSummaryResponse)
async def eval_results() -> EvalSummaryResponse:
    return await EvalService().summary()

