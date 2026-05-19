from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    dependencies: dict[str, Any]