"""
Script para agregar columnas age_range y gender_category a la tabla toy si no existen.
"""
import os
from sqlalchemy import create_engine, text

# Configuración de la base de datos (sqlite dev por defecto)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'tiendita-dev.db')
DB_URI = f'sqlite:///{DB_PATH}'

def column_exists(conn, table, column):
    # SQLite PRAGMA does not accept bound parameters
    res = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    cols = [row[1] for row in res]
    return column in cols

def apply():
    print("--> Verificando columnas en tabla 'toy' ...")
    engine = create_engine(DB_URI)
    with engine.connect() as conn:
        # Verificar existencia de tabla
        t = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='toy'"))
        if not t.fetchone():
            print("[WARN] La tabla 'toy' no existe aún. Se creará automáticamente con db.create_all().")
            return True

        altered = False

        if not column_exists(conn, 'toy', 'age_range'):
            print("--> Agregando columna 'age_range' a 'toy' ...")
            conn.execute(text("ALTER TABLE toy ADD COLUMN age_range VARCHAR(20)"))
            altered = True

        if not column_exists(conn, 'toy', 'gender_category'):
            print("--> Agregando columna 'gender_category' a 'toy' ...")
            conn.execute(text("ALTER TABLE toy ADD COLUMN gender_category VARCHAR(20)"))
            altered = True

        if altered:
            print("[OK] Migración aplicada.")
        else:
            print("[OK] No se requieren cambios, columnas ya existen.")
        return True

if __name__ == '__main__':
    apply()
