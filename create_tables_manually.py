"""
Script para crear tablas manualmente.
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, CheckConstraint, inspect
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Configuración de la base de datos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'tiendita-dev.db')
DB_URI = f'sqlite:///{DB_PATH}'

# Crear motor y metadatos
engine = create_engine(DB_URI)
metadata = MetaData()

# Definir tablas manualmente
users = Table(
    'user', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(64), unique=True, nullable=False, index=True),
    Column('email', String(120), unique=True, nullable=True, index=True),
    Column('password_hash', String(128), nullable=False),
    Column('is_admin', Boolean, default=False),
    Column('balance', Float, default=0.0),
    Column('created_at', DateTime, nullable=False, default=datetime.now),
    Column('last_login', DateTime, nullable=True),
    Column('center', String(64), index=True),
    Column('profile_pic', String(120), nullable=True),
    Column('is_active', Boolean, default=True),
    CheckConstraint('balance >= 0', name='check_balance_positive')
)

toys = Table(
    'toy', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False, index=True),
    Column('description', Text, nullable=True),
    Column('price', Float, nullable=False),
    Column('image_url', String(200), nullable=True),
    Column('category', String(50), index=True),
    Column('stock', Integer, default=0),
    Column('created_at', DateTime, nullable=False, default=datetime.now),
    Column('updated_at', DateTime, onupdate=datetime.now, nullable=True),
    Column('deleted_at', DateTime, nullable=True),
    Column('is_active', Boolean, default=True)
)

orders = Table(
    'order', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('order_date', DateTime, nullable=False, default=datetime.now, index=True),
    Column('total_price', Float, nullable=False),
    Column('created_at', DateTime, nullable=False, default=datetime.now),
    Column('updated_at', DateTime, onupdate=datetime.now, nullable=True),
    Column('deleted_at', DateTime, nullable=True),
    Column('is_active', Boolean, default=True)
)

order_items = Table(
    'order_item', metadata,
    Column('id', Integer, primary_key=True),
    Column('order_id', Integer, ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('toy_id', Integer, ForeignKey('toy.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('quantity', Integer, nullable=False),
    Column('price', Float, nullable=False),
    Column('created_at', DateTime, nullable=False, default=datetime.now),
    Column('updated_at', DateTime, onupdate=datetime.now, nullable=True),
    Column('is_active', Boolean, default=True),
    CheckConstraint('quantity > 0', name='check_quantity_positive')
)

def create_tables():
    """Crea todas las tablas en la base de datos."""
    print("🔨 Creando tablas manualmente...")
    
    # Eliminar la base de datos existente si existe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ Base de datos existente eliminada: {DB_PATH}")
    
    # Crear el directorio instance si no existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Crear todas las tablas
    metadata.create_all(engine)
    
    # Verificar que las tablas se crearon
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊 Tablas creadas: {tables}")
    
    if tables:
        print("✅ Tablas creadas exitosamente.")
    else:
        print("❌ No se crearon tablas.")

if __name__ == "__main__":
    create_tables()
