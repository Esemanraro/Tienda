"""Aplicar manualmente las migraciones pendientes de la base de datos."""

from __future__ import annotations

import os
import sys
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


# Configuración de la base de datos (misma ruta que usa la aplicación)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'tiendita-dev.db')
DB_URI = f'sqlite:///{DB_PATH}'


def _ensure_database_file() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()


def _add_status_column(engine: Engine) -> bool:
    print("🔧 Verificando columna 'status' en la tabla 'order'...")
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
            )
            if not result.fetchone():
                print("ℹ️  La tabla 'order' no existe. Se omite esta migración.")
                return True

            result = conn.execute(text("PRAGMA table_info('order')"))
            columns = [row[1] for row in result.fetchall()]

            if 'status' in columns:
                print("✅ La columna 'status' ya existe en la tabla 'order'.")
                return True

            print("🔄 Agregando columna 'status' a la tabla 'order'...")
            with conn.begin():
                conn.execute(
                    text(
                        "ALTER TABLE `order` "
                        "ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'completada'"
                    )
                )

            print("✅ Columna 'status' agregada correctamente.")
            return True
    except SQLAlchemyError as exc:
        print(f"❌ Error al actualizar la tabla 'order': {exc}")
        return False


def _make_email_nullable(database_uri: Optional[str] = None) -> bool:
    from migrations.ensure_user_email_nullable import ensure_user_email_nullable

    return ensure_user_email_nullable(database_uri or DB_URI)


def apply_migrations() -> bool:
    _ensure_database_file()
    engine = create_engine(DB_URI)

    status_ok = _add_status_column(engine)
    email_ok = _make_email_nullable(DB_URI)

    return status_ok and email_ok


if __name__ == "__main__":
    success = apply_migrations()
    sys.exit(0 if success else 1)
