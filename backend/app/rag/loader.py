"""Multi-format document loader (txt / md / pdf / docx)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoader:
    SUPPORTED_TEXT = {".txt", ".md", ".markdown", ".csv", ".log"}
    SUPPORTED_PDF = {".pdf"}
    SUPPORTED_DOCX = {".docx"}

    async def load(self, path: str) -> str:
        p = Path(path)
        suffix = p.suffix.lower()
        try:
            if suffix in self.SUPPORTED_TEXT:
                return self._load_text(p)
            if suffix in self.SUPPORTED_PDF:
                return self._load_pdf(p)
            if suffix in self.SUPPORTED_DOCX:
                return self._load_docx(p)
        except Exception:  # noqa: BLE001
            logger.exception("document_load_failed path=%s", path)
            return ""
        logger.warning("unsupported_document_format suffix=%s", suffix)
        return ""

    @staticmethod
    def _load_text(p: Path) -> str:
        return p.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _load_pdf(p: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        pieces: list[str] = []
        for page in reader.pages:
            try:
                pieces.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001
                continue
        return "\n".join(pieces)

    @staticmethod
    def _load_docx(p: Path) -> str:
        from docx import Document  # python-docx

        doc = Document(str(p))
        return "\n".join(para.text for para in doc.paragraphs if para.text)