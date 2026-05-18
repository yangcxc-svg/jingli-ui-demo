from decimal import Decimal

from sqlalchemy import JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Product(UUIDTimestampMixin, Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    specs: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="active")

