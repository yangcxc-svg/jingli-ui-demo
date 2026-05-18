from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "trace_id": getattr(request.state, "trace_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "trace_id": getattr(request.state, "trace_id", None),
            },
        )

