"""
Script para insertar datos de prueba en la base de datos.
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
try:
    # Intentar cargar las tablas existentes
    users = Table('user', metadata, autoload_with=engine)
    toys = Table('toy', metadata, autoload_with=engine)
    orders = Table('order', metadata, autoload_with=engine)
    order_items = Table('order_item', metadata, autoload_with=engine)
    print("✅ Tablas cargadas exitosamente.")
except Exception as e:
    print(f"❌ Error al cargar tablas: {e}")
    print("🔨 Creando tablas manualmente...")
    
    # Si hay un error, crear las tablas manualmente
    metadata = MetaData()
    
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
    
    # Crear todas las tablas
    metadata.create_all(engine)
    print("✅ Tablas creadas exitosamente.")

def insert_test_data():
    """Inserta datos de prueba en la base de datos."""
    print("📝 Insertando datos de prueba...")
    
    # Crear una sesión
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Insertar un usuario administrador
        print("👤 Insertando usuario administrador...")
        admin_data = {
            'username': 'admin',
            'email': 'admin@aloha.com',
            'password_hash': 'pbkdf2:sha256:260000$GDBCIzk11sUAoe9M$d2791040e6665a924fab04f9a5a96a42c1a52dfe002c41a93a1817d2608ae8db',  # admin123
            'is_admin': True,
            'balance': 1000.0,
            'center': 'David',
            'is_active': True,
            'created_at': datetime.now()
        }
        
        # Verificar si el usuario ya existe
        result = session.execute(users.select().where(users.c.username == 'admin')).fetchone()
        if not result:
            session.execute(users.insert().values(**admin_data))
            print("✅ Usuario administrador insertado.")
        else:
            print("ℹ️  El usuario administrador ya existe.")
        
        # Insertar juguetes de ejemplo
        print("🧸 Insertando juguetes de ejemplo...")
        toys_data = [
            {
                'name': 'Pulseras Mágicas',
                'description': 'Pulseras con lentejuelas reversibles.',
                'price': 25.0,
                'category': 'Niña',
                'stock': 10,
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'name': 'Coche de Carreras',
                'description': 'Coche de carreras a control remoto.',
                'price': 50.0,
                'category': 'Niño',
                'stock': 5,
                'is_active': True,
                'created_at': datetime.now()
            },
            {
                'name': 'Rompecabezas 1000 Piezas',
                'description': 'Rompecabezas educativo de 1000 piezas.',
                'price': 35.0,
                'category': 'Familiar',
                'stock': 8,
                'is_active': True,
                'created_at': datetime.now()
            }
        ]
        
        for toy_data in toys_data:
            # Verificar si el juguete ya existe
            result = session.execute(toys.select().where(toys.c.name == toy_data['name'])).fetchone()
            if not result:
                session.execute(toys.insert().values(**toy_data))
                print(f"✅ Juguete insertado: {toy_data['name']}")
            else:
                print(f"ℹ️  El juguete ya existe: {toy_data['name']}")
        
        # Guardar los cambios
        session.commit()
        print("✅ Datos de prueba insertados exitosamente.")
        
    except Exception as e:
        print(f"❌ Error al insertar datos de prueba: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    insert_test_data()
