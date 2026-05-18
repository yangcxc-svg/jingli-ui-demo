from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class ModelCallLog(UUIDTimestampMixin, Base):
    __tablename__ = "model_call_logs"

    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    prompt_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    request_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)

