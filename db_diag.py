"""
Script de diagnóstico para la base de datos.
"""
import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Asegurarse de que el directorio raíz esté en el path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar la aplicación después de configurar el path
from app import create_app, db

def check_database():
    """Verifica la conexión y estructura de la base de datos."""
    print("🔍 Iniciando diagnóstico de la base de datos...")
    
    # Crear la aplicación
    app = create_app()
    
    with app.app_context():
        # Obtener la URL de la base de datos
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        print(f"📊 URL de la base de datos: {db_uri}")
        
        # Verificar si el archivo de la base de datos existe
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            print(f"📂 Ruta del archivo de la base de datos: {db_path}")
            if os.path.exists(db_path):
                print("✅ El archivo de la base de datos existe.")
            else:
                print("❌ El archivo de la base de datos NO existe.")
        
        # Crear un motor SQLAlchemy
        engine = db.engine
        print(f"🔌 Motor SQLAlchemy: {engine}")
        
        # Verificar la conexión
        try:
            with engine.connect() as conn:
                print("✅ Conexión a la base de datos exitosa.")
        except Exception as e:
            print(f"❌ Error al conectar a la base de datos: {e}")
            return
        
        # Verificar tablas existentes
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Tablas en la base de datos: {tables}")
        
        # Verificar si las tablas de los modelos existen
        expected_tables = ['user', 'toy', 'order', 'order_item']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Faltan las siguientes tablas: {missing_tables}")
        else:
            print("✅ Todas las tablas esperadas están presentes.")
        
        # Verificar si se pueden crear las tablas
        print("\n🔨 Intentando crear tablas...")
        try:
            db.create_all()
            print("✅ Tablas creadas exitosamente.")
            
            # Verificar tablas nuevamente
            tables_after = inspect(engine).get_table_names()
            print(f"📊 Tablas después de create_all(): {tables_after}")
            
            # Verificar si las tablas se crearon
            still_missing = [t for t in expected_tables if t not in tables_after]
            if still_missing:
                print(f"❌ Aún faltan tablas después de create_all(): {still_missing}")
            else:
                print("✅ Todas las tablas se crearon correctamente.")
                
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")

if __name__ == "__main__":
    check_database()
