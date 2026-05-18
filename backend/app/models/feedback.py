from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Feedback(UUIDTimestampMixin, Base):
    __tablename__ = "feedbacks"

    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), index=True)
    rating: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

