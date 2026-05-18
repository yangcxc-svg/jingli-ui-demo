from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDTimestampMixin:
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

