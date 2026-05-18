from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import UUIDTimestampMixin


class Document(UUIDTimestampMixin, Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="processing")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)


class KnowledgeChunk(UUIDTimestampMixin, Base):
    __tablename__ = "knowledge_chunks"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    chunk_text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict)
    vector_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

