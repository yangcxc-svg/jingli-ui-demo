from fastapi import APIRouter, Query

from app.schemas.eval import EvalRunResponse, EvalSummaryResponse, ModelLogListResponse
from app.services.eval_service import EvalService
from app.services.model_log_service import model_log_service

router = APIRouter()


@router.post("/run", response_model=EvalRunResponse)
async def run_eval() -> EvalRunResponse:
    return await EvalService().run()


@router.get("/results", response_model=EvalSummaryResponse)
async def eval_results() -> EvalSummaryResponse:
    return await EvalService().summary()


@router.get("/model-logs", response_model=ModelLogListResponse)
async def model_logs(limit: int = Query(20, ge=1, le=200)) -> ModelLogListResponse:
    return ModelLogListResponse(items=model_log_service.recent(limit=limit))

