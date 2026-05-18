from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class EvalCase(UUIDTimestampMixin, Base):
    __tablename__ = "eval_cases"

    question: Mapped[str] = mapped_column(Text)
    scenario: Mapped[str] = mapped_column(String(100))
    expected_products: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_facts: Mapped[list[str]] = mapped_column(JSON, default=list)
    forbidden_facts: Mapped[list[str]] = mapped_column(JSON, default=list)


class EvalResult(UUIDTimestampMixin, Base):
    __tablename__ = "eval_results"

    eval_case_id: Mapped[str] = mapped_column(ForeignKey("eval_cases.id"), index=True)
    metrics: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")

