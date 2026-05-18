from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.rag.splitter import TextSplitter
from app.rag.store import KnowledgeStore

logger = logging.getLogger(__name__)


def _resolve_seed_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path

    backend_dir = Path(__file__).resolve().parents[2]
    repo_root = backend_dir.parent
    candidates = [
        Path.cwd() / path,
        backend_dir / path,
        repo_root / "storage/sample_docs/seed_products.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


class SeedProductCatalog:
    """In-memory product catalog backed by storage/sample_docs/seed_products.json."""

    _instance: "SeedProductCatalog | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "SeedProductCatalog":
        with cls._instance_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._products = []  # type: ignore[attr-defined]
                inst._loaded = False  # type: ignore[attr-defined]
                inst._load_lock = threading.Lock()  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    _products: list[dict[str, Any]]
    _loaded: bool
    _load_lock: threading.Lock

    def load(self, *, force: bool = False) -> int:
        with self._load_lock:
            if self._loaded and not force:
                return len(self._products)

            path = _resolve_seed_path(settings.seed_products_path)
            if not path.exists():
                logger.warning("seed_products_not_found path=%s", path)
                self._products = []
                self._loaded = True
                return 0

            raw = json.loads(path.read_text(encoding="utf-8"))
            products = raw.get("products", [])
            if not isinstance(products, list):
                logger.warning("seed_products_invalid_shape path=%s", path)
                products = []

            self._products = [p for p in products if isinstance(p, dict)]
            self._load_knowledge_texts(self._products)
            self._loaded = True
            logger.info("seed_products_loaded count=%s path=%s", len(self._products), path)
            return len(self._products)

    def list_products(self) -> list[dict[str, Any]]:
        if not self._loaded:
            self.load()
        return list(self._products)

    def get_by_id(self, product_id: str) -> dict[str, Any] | None:
        if not self._loaded:
            self.load()
        for product in self._products:
            if str(product.get("product_id")) == product_id:
                return dict(product)
        return None

    def _load_knowledge_texts(self, products: list[dict[str, Any]]) -> None:
        store = KnowledgeStore()
        splitter = TextSplitter()

        for product in products:
            product_id = str(product.get("product_id") or "").strip()
            if not product_id:
                continue

            knowledge_text = str(product.get("knowledge_text") or "").strip()
            if not knowledge_text:
                continue

            name = str(product.get("name") or product_id)
            category = str(product.get("category") or "")
            price = product.get("price")
            highlights = product.get("highlights") or []
            tags = product.get("comparison_tags") or []

            intro = [
                f"商品ID：{product_id}",
                f"商品名称：{name}",
                f"品类：{category}",
                f"价格：{price} 元" if price is not None else "",
                "核心卖点：" + "；".join(str(item) for item in highlights)
                if isinstance(highlights, list)
                else "",
                "标签：" + "；".join(str(item) for item in tags) if isinstance(tags, list) else "",
            ]
            text = "\n".join(item for item in intro if item) + "\n\n" + knowledge_text

            doc = store.register_document(
                filename=f"{product_id}.txt",
                file_type="seed_product",
                document_id=product_id,
            )
            chunks = splitter.split(text)
            added = store.add_chunks(doc.document_id, chunks)
            store.mark_status(doc.document_id, "ready", chunk_count=added)


seed_product_catalog = SeedProductCatalog()
