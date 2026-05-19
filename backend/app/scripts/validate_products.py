"""校验 seed_products.json 的 CLI 脚本。

用法：
    cd backend
    python -m app.scripts.validate_products
    python -m app.scripts.validate_products ../storage/sample_docs/seed_products.json

任一字段不符合 SeedProduct schema 时，进程以非零状态码退出，并打印明确错误信息。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.services.seed_product_loader import _resolve_seed_path
from app.schemas.seed_product import validate_products_payload


def _resolve(path: str | None) -> Path:
    if path:
        return Path(path).expanduser()
    from app.core.config import settings

    return _resolve_seed_path(settings.seed_products_path)


def main(argv: list[str]) -> int:
    target = _resolve(argv[1] if len(argv) > 1 else None)
    if not target.exists():
        print(f"[error] seed file not found: {target}", file=sys.stderr)
        return 2

    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[error] invalid json in {target}: {exc}", file=sys.stderr)
        return 2

    products, errors = validate_products_payload(raw)
    if errors:
        print(f"[error] {len(errors)} validation error(s) in {target}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"[ok] {target}")
    print(f"  products: {len(products)}")
    by_level: dict[str, int] = {}
    for product in products:
        key = product.budget_level or "unknown"
        by_level[key] = by_level.get(key, 0) + 1
    print(f"  budget_level distribution: {by_level}")
    missing_image = [p.product_id for p in products if not p.image_url]
    missing_purchase = [p.product_id for p in products if not p.purchase_url]
    if missing_image:
        print(f"  [warn] missing image_url: {missing_image}")
    if missing_purchase:
        print(f"  [warn] missing purchase_url: {missing_purchase}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))