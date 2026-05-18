from typing import Literal

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    message_id: str
    rating: Literal["up", "down"]
    reason: str | None = None
    comment: str | None = None


class FeedbackResponse(BaseModel):
    success: bool

