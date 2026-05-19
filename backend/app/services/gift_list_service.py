from __future__ import annotations

import threading
from datetime import datetime
from decimal import Decimal

from app.schemas.gift_list import GiftListAddRequest, GiftListItem, GiftListResponse


class GiftListService:
    """Small in-memory gift list store for the UI integration demo."""

    _instance: "GiftListService | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "GiftListService":
        with cls._instance_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._lists = {}  # type: ignore[attr-defined]
                inst._lock = threading.Lock()  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    _lists: dict[str, dict[str, GiftListItem]]
    _lock: threading.Lock

    def add_item(self, payload: GiftListAddRequest) -> GiftListResponse:
        with self._lock:
            items = self._lists.setdefault(payload.list_id, {})
            existing = items.get(payload.product.product_id)
            if existing:
                items[payload.product.product_id] = GiftListItem(
                    product=payload.product,
                    quantity=existing.quantity + payload.quantity,
                    added_at=existing.added_at,
                )
            else:
                items[payload.product.product_id] = GiftListItem(
                    product=payload.product,
                    quantity=payload.quantity,
                    added_at=datetime.utcnow(),
                )
            return self._build_response(payload.list_id, items)

    def get_list(self, list_id: str = "default") -> GiftListResponse:
        with self._lock:
            return self._build_response(list_id, self._lists.setdefault(list_id, {}))

    def remove_item(self, product_id: str, list_id: str = "default") -> GiftListResponse:
        with self._lock:
            items = self._lists.setdefault(list_id, {})
            items.pop(product_id, None)
            return self._build_response(list_id, items)

    def update_quantity(
        self, product_id: str, quantity: int, list_id: str = "default"
    ) -> GiftListResponse:
        with self._lock:
            items = self._lists.setdefault(list_id, {})
            existing = items.get(product_id)
            if not existing:
                return self._build_response(list_id, items)

            if quantity <= 0:
                items.pop(product_id, None)
            else:
                items[product_id] = GiftListItem(
                    product=existing.product,
                    quantity=quantity,
                    added_at=existing.added_at,
                )
            return self._build_response(list_id, items)

    def _build_response(
        self, list_id: str, items_by_product_id: dict[str, GiftListItem]
    ) -> GiftListResponse:
        items = list(items_by_product_id.values())
        total_amount: Decimal | None = Decimal("0")
        for item in items:
            if item.product.price is None:
                total_amount = None
                break
            total_amount += item.product.price * item.quantity

        return GiftListResponse(
            list_id=list_id,
            items=items,
            total_count=sum(item.quantity for item in items),
            total_amount=total_amount,
        )
