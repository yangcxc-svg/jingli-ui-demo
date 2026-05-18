"""Knowledge ingestion service.

将上传文档解析、切片并存入进程内 KnowledgeStore，使其立刻可被 Chat 检索引用。
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException, UploadFile

from app.core.config import settings
from app.rag.loader import DocumentLoader
from app.rag.splitter import TextSplitter
from app.rag.store import KnowledgeStore
from app.schemas.document import DocumentResponse, DocumentUploadResponse

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".csv", ".log", ".pdf", ".docx"}


class KnowledgeService:
    def __init__(self) -> None:
        self.store = KnowledgeStore()
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()

    async def upload(
        self, file: UploadFile, background_tasks: BackgroundTasks
    ) -> DocumentUploadResponse:
        filename = file.filename or "untitled"
        suffix = Path(filename).suffix.lower()
        if suffix not in _SUPPORTED_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {suffix or '未知'}（仅支持 {sorted(_SUPPORTED_SUFFIXES)}）",
            )

        max_bytes = settings.max_upload_mb * 1024 * 1024
        content = await file.read()
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"文件超过 {settings.max_upload_mb} MB 上限",
            )

        doc = self.store.register_document(filename=filename, file_type=suffix.lstrip("."))
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        target = upload_dir / f"{doc.document_id}_{filename}"
        target.write_bytes(content)

        try:
            text = await self.loader.load(str(target))
            chunks = self.splitter.split(text)
            added = self.store.add_chunks(doc.document_id, chunks)
            if added == 0:
                self.store.mark_status(
                    doc.document_id, "failed", chunk_count=0, error_message="未能解析出任何文本片段"
                )
            else:
                self.store.mark_status(doc.document_id, "ready", chunk_count=added)
        except Exception as exc:  # noqa: BLE001
            logger.exception("document_processing_failed id=%s", doc.document_id)
            self.store.mark_status(doc.document_id, "failed", error_message=str(exc))

        latest = self.store._documents[doc.document_id]  # noqa: SLF001
        return DocumentUploadResponse(document_id=doc.document_id, status=latest.status)

    async def list_documents(self) -> list[DocumentResponse]:
        return [
            DocumentResponse(
                document_id=d.document_id,
                filename=d.filename,
                status=d.status,
                chunk_count=d.chunk_count,
                error_message=d.error_message,
            )
            for d in self.store.list_documents()
        ]