from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class User(UUIDTimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")

