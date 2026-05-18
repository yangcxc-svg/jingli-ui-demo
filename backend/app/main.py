from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.tracing import TraceMiddleware
from app.services.seed_product_loader import seed_product_catalog


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    seed_product_catalog.load()
    yield


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
