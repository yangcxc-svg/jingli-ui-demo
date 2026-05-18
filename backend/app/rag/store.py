"""In-memory knowledge store for the MVP.

不引入向量库 / 嵌入服务的最小可用实现：
- 进程内单例，按文档保存切片
- 检索使用关键词命中数 + 词频打分（中文按字符 n-gram，英文按单词）

后续阶段可替换为 Qdrant + Embedder，不影响调用方接口。
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """中文按 2-gram，英文/数字按单词，全部小写。"""
    text = text.lower()
    tokens: list[str] = []
    # 英文/数字
    tokens.extend(_WORD_RE.findall(text))
    # 中文 2-gram
    cjk = "".join(_CJK_RE.findall(text))
    for i in range(len(cjk) - 1):
        tokens.append(cjk[i : i + 2])
    return tokens


@dataclass
class StoredChunk:
    chunk_id: str
    document_id: str
    text: str
    token_count: dict[str, int]


@dataclass
class StoredDocument:
    document_id: str
    filename: str
    file_type: str
    status: str = "processing"
    chunk_count: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeStore:
    """Singleton in-memory knowledge store."""

    _instance: "KnowledgeStore | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "KnowledgeStore":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._documents = {}  # type: ignore[attr-defined]
                inst._chunks = []  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    # type-hints for mypy
    _documents: dict[str, StoredDocument]
    _chunks: list[StoredChunk]

    # ---- documents ----

    def register_document(
        self, filename: str, file_type: str, document_id: str | None = None
    ) -> StoredDocument:
        document_id = document_id or str(uuid4())
        if document_id in self._documents:
            return self._documents[document_id]
        doc = StoredDocument(document_id=document_id, filename=filename, file_type=file_type)
        self._documents[document_id] = doc
        return doc

    def mark_status(
        self,
        document_id: str,
        status: str,
        *,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        doc = self._documents.get(document_id)
        if not doc:
            return
        doc.status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message

    def list_documents(self) -> list[StoredDocument]:
        return sorted(self._documents.values(), key=lambda d: d.created_at, reverse=True)

    # ---- chunks ----

    def add_chunks(self, document_id: str, texts: list[str]) -> int:
        added = 0
        for text in texts:
            tokens = _tokenize(text)
            if not tokens:
                continue
            count: dict[str, int] = {}
            for t in tokens:
                count[t] = count.get(t, 0) + 1
            self._chunks.append(
                StoredChunk(
                    chunk_id=str(uuid4()),
                    document_id=document_id,
                    text=text,
                    token_count=count,
                )
            )
            added += 1
        return added

    def search(self, query: str, top_k: int = 5) -> list[tuple[StoredChunk, float]]:
        q_tokens = _tokenize(query)
        if not q_tokens or not self._chunks:
            return []
        results: list[tuple[StoredChunk, float]] = []
        for chunk in self._chunks:
            score = 0.0
            for t in q_tokens:
                if t in chunk.token_count:
                    score += chunk.token_count[t]
            if score > 0:
                # 命中越多越分散加分
                hits = sum(1 for t in q_tokens if t in chunk.token_count)
                score = score * (1.0 + 0.2 * hits)
                results.append((chunk, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
