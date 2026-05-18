from fastapi import APIRouter

from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter()


@router.post("", response_model=FeedbackResponse)
async def create_feedback(payload: FeedbackCreate) -> FeedbackResponse:
    return await FeedbackService().create_feedback(payload)

