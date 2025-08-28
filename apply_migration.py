"""
Script para aplicar manualmente la migración que agrega la columna status a la tabla order.
"""
import sys
import os
from sqlalchemy import create_engine, text

# Configuración de la base de datos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'tiendita-dev.db')
DB_URI = f'sqlite:///{DB_PATH}'

def apply_migration():
    print("🔧 Aplicando migración: Agregar columna status a la tabla order...")
    
    try:
        # Crear motor de base de datos
        engine = create_engine(DB_URI)
        
        # Verificar si la columna ya existe
        with engine.connect() as conn:
            # Verificar si la tabla order existe
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='order'
            """))
            if not result.fetchone():
                print("❌ La tabla 'order' no existe en la base de datos.")
                return False
            
            # Verificar si la columna status ya existe
            result = conn.execute(text("""
                PRAGMA table_info('order')
            """))
            columns = [row[1] for row in result.fetchall()]
            
            if 'status' in columns:
                print("ℹ️  La columna 'status' ya existe en la tabla 'order'.")
                return True
            
            # Agregar la columna status
            print("🔄 Agregando columna 'status' a la tabla 'order'...")
            with conn.begin():
                conn.execute(text("""
                    ALTER TABLE `order` 
                    ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'completada'
                """))
            
            print("✅ Migración aplicada exitosamente.")
            return True
            
    except Exception as e:
        print(f"❌ Error al aplicar la migración: {e}")
        return False

if __name__ == "__main__":
    if apply_migration():
        sys.exit(0)
    else:
        sys.exit(1)
