"""Database maintenance utilities for legacy deployments.

These helpers make sure that production databases created before
certain migrations still receive the columns that the current models
expect.  They run lightweight, idempotent `ALTER TABLE` statements so
we avoid forcing a full Alembic migration workflow in constrained
setups.
"""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db


def _existing_columns(table: str) -> set[str]:
    """Return the set of existing columns for a table."""
    inspector = inspect(db.engine)
    try:
        existing = {col["name"] for col in inspector.get_columns(table)}
    except SQLAlchemyError:
        return set()
    return existing


def ensure_order_table_columns() -> None:
    """Ensure legacy ``order`` tables have the newest bookkeeping columns.

    SQLite deployments that pre-date the Alembic migrations lack several
    pricing and status fields that the ORM layer now expects. When Flask
    loads the dashboard we perform a quick schema upgrade so the ORM can
    safely select ``Order`` rows without hitting ``no such column`` errors.
    """

    required_columns: dict[str, str] = {
        "order_date": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "subtotal_price": "REAL NOT NULL DEFAULT 0",
        "discount_percentage": "REAL NOT NULL DEFAULT 0",
        "discount_amount": "REAL NOT NULL DEFAULT 0",
        "discounted_total": "REAL NOT NULL DEFAULT 0",
        "discount_center": "VARCHAR(64)",
        "updated_at": "DATETIME",
        "deleted_at": "DATETIME",
        "is_active": "INTEGER NOT NULL DEFAULT 1",
    }

    existing = _existing_columns("order")
    if not existing:
        # Table doesn't exist or inspection failed; nothing to do.
        return

    statements: list[str] = []
    for column, ddl in required_columns.items():
        if column not in existing:
            statements.append(
                f"ALTER TABLE \"order\" ADD COLUMN {column} {ddl}"
            )

    if not statements:
        return

    connection = db.engine.connect()
    trans = connection.begin()
    try:
        for statement in statements:
            connection.execute(text(statement))

        # Backfill pricing data so dashboard statistics remain accurate.
        if "subtotal_price" not in existing or "discounted_total" not in existing:
            connection.execute(
                text(
                    """
                    UPDATE "order"
                    SET
                        subtotal_price = COALESCE(subtotal_price, total_price),
                        discounted_total = COALESCE(discounted_total, total_price)
                    """
                )
            )

        if "order_date" not in existing:
            connection.execute(
                text(
                    """
                    UPDATE "order"
                    SET order_date = COALESCE(order_date, created_at, CURRENT_TIMESTAMP)
                    """
                )
            )

        if "discount_percentage" not in existing or "discount_amount" not in existing:
            connection.execute(
                text(
                    """
                    UPDATE "order"
                    SET
                        discount_percentage = COALESCE(discount_percentage, 0),
                        discount_amount = COALESCE(discount_amount, 0)
                    """
                )
            )

        if "is_active" not in existing:
            connection.execute(
                text(
                    """
                    UPDATE "order"
                    SET is_active = COALESCE(is_active, 1)
                    """
                )
            )

        trans.commit()
    except SQLAlchemyError:
        trans.rollback()
        raise
    finally:
        connection.close()

