from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.core.config import settings
from app.repositories.gift_list_repo import GiftListRepository
from app.schemas.gift_list import (
    GiftListAddRequest,
    GiftListCheckoutItem,
    GiftListCheckoutPreviewRequest,
    GiftListCheckoutPreviewResponse,
    GiftListItem,
    GiftListResponse,
)


class GiftListService:
    """Persistent gift list service backed by SQLite product snapshots."""

    _instance: "GiftListService | None" = None

    def __new__(cls) -> "GiftListService":
        if cls._instance is None:
            inst = super().__new__(cls)
            inst.repo = GiftListRepository(settings.gift_list_db_path)  # type: ignore[attr-defined]
            cls._instance = inst
        return cls._instance

    repo: GiftListRepository

    def add_item(self, payload: GiftListAddRequest) -> GiftListResponse:
        existing = self.repo.get_item(payload.list_id, payload.product.product_id)
        next_quantity = payload.quantity
        added_at = datetime.utcnow()
        if existing:
            next_quantity = min(99, existing.quantity + payload.quantity)
            added_at = existing.added_at

        self.repo.upsert_item(
            list_id=payload.list_id,
            product=payload.product,
            quantity=next_quantity,
            added_at=added_at,
        )
        return self.get_list(payload.list_id)

    def get_list(self, list_id: str = "default") -> GiftListResponse:
        return self._build_response(list_id, self.repo.list_items(list_id))

    def remove_item(self, product_id: str, list_id: str = "default") -> GiftListResponse:
        self.repo.remove_item(list_id, product_id)
        return self.get_list(list_id)

    def update_quantity(
        self, product_id: str, quantity: int, list_id: str = "default"
    ) -> GiftListResponse:
        existing = self.repo.get_item(list_id, product_id)
        if not existing:
            return self.get_list(list_id)

        if quantity <= 0:
            self.repo.remove_item(list_id, product_id)
        else:
            self.repo.upsert_item(
                list_id=list_id,
                product=existing.product,
                quantity=quantity,
                added_at=existing.added_at,
            )
        return self.get_list(list_id)

    def checkout_preview(
        self, payload: GiftListCheckoutPreviewRequest
    ) -> GiftListCheckoutPreviewResponse:
        stored_items = {
            item.product.product_id: item
            for item in self.repo.list_items(payload.list_id)
        }

        preview_items: list[GiftListCheckoutItem] = []
        unavailable_product_ids: list[str] = []
        for requested in payload.items:
            stored = stored_items.get(requested.product_id)
            if not stored:
                unavailable_product_ids.append(requested.product_id)
                continue
            subtotal = None
            if stored.product.price is not None:
                subtotal = stored.product.price * requested.quantity
            preview_items.append(
                GiftListCheckoutItem(
                    product=stored.product,
                    quantity=requested.quantity,
                    subtotal=subtotal,
                )
            )

        total_amount: Decimal | None = Decimal("0")
        for item in preview_items:
            if item.subtotal is None:
                total_amount = None
                break
            total_amount += item.subtotal

        return GiftListCheckoutPreviewResponse(
            list_id=payload.list_id,
            items=preview_items,
            total_count=sum(item.quantity for item in preview_items),
            total_amount=total_amount,
            unavailable_product_ids=unavailable_product_ids,
        )

    def _build_response(
        self, list_id: str, items: list[GiftListItem]
    ) -> GiftListResponse:
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
