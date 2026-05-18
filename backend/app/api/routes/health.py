from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse(status="ok", dependencies={})


@router.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    return HealthResponse(
        status="ok",
        dependencies={
            "api": "ok",
            "database": "not_checked",
            "redis": "not_checked",
            "vector_db": "not_checked",
            "llm": "not_checked",
        },
    )

