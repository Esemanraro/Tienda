"""Ensure the user.email column allows NULL values.

This migration is required because older database snapshots created the
``user.email`` column with a ``NOT NULL`` constraint.  The application now
allows administrators to register accounts without an email address, so the
column must be nullable.  SQLite does not support dropping the constraint in
place, therefore the table is recreated with the desired definition and the
existing data is copied over.
"""
from __future__ import annotations

import os
import sys
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import User


INSTANCE_DIR = os.path.join(PROJECT_ROOT, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)


def _ensure_instance_directory(database_uri: str) -> None:
    """Create the SQLite directory if it does not exist yet."""
    if not database_uri.startswith("sqlite:///"):
        return
    db_path = database_uri.replace("sqlite:///", "", 1)
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    if db_path and not os.path.exists(db_path):
        open(db_path, 'a').close()


def _fetch_indexes(engine: Engine) -> Sequence[str]:
    """Return the list of indexes defined for the ``user`` table."""
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA index_list('user')")).fetchall()
        return [row[1] for row in rows]


def _drop_indexes(connection: Connection, indexes: Sequence[str]) -> None:
    if not indexes:
        return
    drop_sql = "DROP INDEX IF EXISTS \"{}\""
    for index_name in indexes:
        connection.execute(text(drop_sql.format(index_name)))


def ensure_user_email_nullable(database_uri: str | None = None) -> bool:
    """Apply the migration that makes ``user.email`` nullable.

    Parameters
    ----------
    database_uri:
        Optional SQLAlchemy database URI.  When ``None`` the URI configured by
        :func:`create_app` is used.
    """
    app = create_app()

    if database_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

    _ensure_instance_directory(app.config['SQLALCHEMY_DATABASE_URI'])

    try:
        with app.app_context():
            engine = db.engine
            inspector = db.inspect(engine)

            if 'user' not in inspector.get_table_names():
                print("ℹ️  Tabla 'user' no existe. No hay nada que migrar.")
                return True

            email_column = next(
                (column for column in inspector.get_columns('user') if column['name'] == 'email'),
                None,
            )

            if not email_column:
                print("ℹ️  Columna 'email' no encontrada en la tabla 'user'.")
                return True

            if email_column['nullable']:
                print("✅ La columna 'user.email' ya permite valores NULL.")
                return True

            print("🔧 Actualizando la columna 'user.email' para permitir valores NULL...")

            indexes = _fetch_indexes(engine)

            with engine.begin() as conn:
                conn.execute(text('PRAGMA foreign_keys=OFF'))
                _drop_indexes(conn, indexes)
                conn.execute(text('DROP TABLE IF EXISTS user_old'))
                conn.execute(text('ALTER TABLE "user" RENAME TO user_old'))
                conn.execute(text('PRAGMA foreign_keys=ON'))

            # Crear la nueva tabla usando la definición actual del modelo
            User.__table__.create(bind=engine)

            column_names = [column.name for column in User.__table__.columns]
            quoted_names = ', '.join(f'"{name}"' for name in column_names)

            with engine.begin() as conn:
                conn.execute(
                    text(
                        f'INSERT INTO "user" ({quoted_names}) '
                        f'SELECT {quoted_names} FROM user_old'
                    )
                )
                conn.execute(text('DROP TABLE user_old'))

            print("✅ Migración completada: 'user.email' ahora acepta valores NULL.")
            return True
    except SQLAlchemyError as exc:
        print(f"❌ Error durante la migración de 'user.email': {exc}")
    except Exception as exc:  # pragma: no cover - fallback for unexpected issues
        print(f"❌ Error inesperado durante la migración: {exc}")

    return False


if __name__ == '__main__':
    success = ensure_user_email_nullable()
    raise SystemExit(0 if success else 1)
