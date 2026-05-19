from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.schemas.gift_list import GiftListItem
from app.schemas.product import ProductCard


class GiftListRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_absolute():
            self.db_path = Path.cwd() / self.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS gift_list_items (
                    list_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_snapshot TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    added_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (list_id, product_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_gift_list_items_list_id ON gift_list_items(list_id)"
            )

    def list_items(self, list_id: str) -> list[GiftListItem]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT product_snapshot, quantity, added_at
                FROM gift_list_items
                WHERE list_id = ?
                ORDER BY added_at ASC
                """,
                (list_id,),
            ).fetchall()

        return [
            GiftListItem(
                product=ProductCard.model_validate_json(row["product_snapshot"]),
                quantity=int(row["quantity"]),
                added_at=datetime.fromisoformat(row["added_at"]),
            )
            for row in rows
        ]

    def get_item(self, list_id: str, product_id: str) -> GiftListItem | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT product_snapshot, quantity, added_at
                FROM gift_list_items
                WHERE list_id = ? AND product_id = ?
                """,
                (list_id, product_id),
            ).fetchone()

        if not row:
            return None
        return GiftListItem(
            product=ProductCard.model_validate_json(row["product_snapshot"]),
            quantity=int(row["quantity"]),
            added_at=datetime.fromisoformat(row["added_at"]),
        )

    def upsert_item(
        self,
        list_id: str,
        product: ProductCard,
        quantity: int,
        added_at: datetime | None = None,
    ) -> None:
        now = datetime.utcnow()
        added_at = added_at or now
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO gift_list_items (
                    list_id, product_id, product_snapshot, quantity, added_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(list_id, product_id)
                DO UPDATE SET
                    product_snapshot = excluded.product_snapshot,
                    quantity = excluded.quantity,
                    updated_at = excluded.updated_at
                """,
                (
                    list_id,
                    product.product_id,
                    product.model_dump_json(),
                    quantity,
                    added_at.isoformat(),
                    now.isoformat(),
                ),
            )

    def remove_item(self, list_id: str, product_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM gift_list_items WHERE list_id = ? AND product_id = ?",
                (list_id, product_id),
            )

