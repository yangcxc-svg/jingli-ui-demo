from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.rag.splitter import TextSplitter
from app.rag.store import KnowledgeStore
from app.schemas.seed_product import SeedProduct, validate_products_payload

logger = logging.getLogger(__name__)


class SeedProductValidationError(RuntimeError):
    """seed_products.json 校验失败时抛出，并附带详细错误列表。"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(
            "seed_products.json 校验失败，共 "
            f"{len(errors)} 条错误：\n - "
            + "\n - ".join(errors)
        )


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

    def load(self, *, force: bool = False, strict: bool = True) -> int:
        """加载 seed_products.json 并执行校验。

        Args:
            force: 强制重新加载。
            strict: 任一校验错误都抛出 SeedProductValidationError；
                关闭时仅打印 warning 并丢弃错误条目，便于本地调试。
        """
        with self._load_lock:
            if self._loaded and not force:
                return len(self._products)

            path = _resolve_seed_path(settings.seed_products_path)
            if not path.exists():
                message = f"seed_products.json not found at {path}"
                if strict:
                    raise SeedProductValidationError([message])
                logger.warning("seed_products_not_found path=%s", path)
                self._products = []
                self._loaded = True
                return 0

            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise SeedProductValidationError(
                    [f"{path}: invalid json - {exc}"]
                ) from exc

            validated, errors = validate_products_payload(raw)
            if errors:
                if strict:
                    raise SeedProductValidationError(errors)
                for err in errors:
                    logger.warning("seed_product_invalid %s", err)

            self._products = [self._to_dict(item) for item in validated]
            self._load_knowledge_texts(validated)
            self._loaded = True
            logger.info(
                "seed_products_loaded count=%s path=%s errors=%s",
                len(self._products),
                path,
                len(errors),
            )
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

    @staticmethod
    def _to_dict(product: SeedProduct) -> dict[str, Any]:
        # 保留 extra="allow" 中的额外字段（specs / variants / rating 等）
        data = product.model_dump(mode="python")
        return data

    def _load_knowledge_texts(self, products: list[SeedProduct]) -> None:
        store = KnowledgeStore()
        splitter = TextSplitter()

        for product in products:
            product_id = product.product_id.strip()
            if not product_id:
                continue

            extras = product.model_extra or {}
            knowledge_text = str(extras.get("knowledge_text") or "").strip()
            if not knowledge_text:
                continue

            intro_parts = [
                f"商品ID：{product_id}",
                f"商品名称：{product.name}",
                f"品类：{product.category}",
            ]
            if product.price is not None:
                intro_parts.append(f"价格：{product.price} 元")
            if product.budget_level:
                intro_parts.append(f"预算等级：{product.budget_level}")
            if product.scenarios:
                intro_parts.append("适用场景：" + "；".join(product.scenarios))
            if product.target_people:
                intro_parts.append("目标人群：" + "；".join(product.target_people))
            if product.highlights:
                intro_parts.append("核心卖点：" + "；".join(product.highlights))
            if product.tags:
                intro_parts.append("标签：" + "；".join(product.tags))
            if product.avoid_for:
                intro_parts.append("不建议送给：" + "；".join(product.avoid_for))

            text = "\n".join(intro_parts) + "\n\n" + knowledge_text

            doc = store.register_document(
                filename=f"{product_id}.txt",
                file_type="seed_product",
                document_id=product_id,
            )
            chunks = splitter.split(text)
            added = store.add_chunks(doc.document_id, chunks)
            store.mark_status(doc.document_id, "ready", chunk_count=added)


seed_product_catalog = SeedProductCatalog()