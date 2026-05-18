from app.metrics.collector import MetricsCollector
from app.schemas.feedback import FeedbackCreate, FeedbackResponse


class FeedbackService:
    def __init__(self) -> None:
        self.metrics = MetricsCollector()

    async def create_feedback(self, payload: FeedbackCreate) -> FeedbackResponse:
        self.metrics.record_feedback(payload.message_id, payload.rating)
        return FeedbackResponse(success=True)