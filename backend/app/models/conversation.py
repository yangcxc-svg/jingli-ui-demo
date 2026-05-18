from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Conversation(UUIDTimestampMixin, Base):
    __tablename__ = "conversations"

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Message(UUIDTimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    structured_data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

