#!/usr/bin/env python3
"""
Directly create database tables without loading the full Flask app.
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'tiendita.db')
db_uri = f'sqlite:///{db_path}'

def create_tables():
    """Create all database tables."""
    print(f"🔧 Connecting to database: {db_uri}")
    
    # Create engine and metadata
    engine = create_engine(db_uri)
    metadata = MetaData()
    
    print("🛠️  Creating tables...")
    
    # Define tables
    user_table = Table('user', metadata,
        Column('id', Integer, primary_key=True),
        Column('username', String(64), unique=True, nullable=False),
        Column('email', String(120), unique=True, nullable=True),
        Column('password_hash', String(128), nullable=False),
        Column('is_admin', Boolean, default=False),
        Column('balance', Float, default=0.0),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('last_login', DateTime),
        Column('is_active', Boolean, default=True),
        Column('center', String(64)),
        Column('profile_pic', String(120), default='default.jpg')
    )
    
    toy_table = Table('toy', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(100), nullable=False),
        Column('description', Text),
        Column('price', Float, nullable=False),
        Column('image_url', String(200)),
        Column('category', String(50)),
        Column('stock', Integer, default=0),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('updated_at', DateTime, onupdate=datetime.utcnow),
        Column('deleted_at', DateTime, nullable=True),
        Column('is_active', Boolean, default=True)
    )
    
    order_table = Table('order', metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('created_at', DateTime, default=datetime.utcnow),
        Column('total_price', Float, nullable=False),
        Column('status', String(20), default='pending'),
        Column('shipping_address', Text),
        Column('payment_method', String(50))
    )
    
    order_item_table = Table('order_item', metadata,
        Column('id', Integer, primary_key=True),
        Column('order_id', Integer, ForeignKey('order.id'), nullable=False),
        Column('toy_id', Integer, ForeignKey('toy.id'), nullable=False),
        Column('quantity', Integer, nullable=False),
        Column('price_at_purchase', Float, nullable=False)
    )
    
    # Create all tables
    try:
        metadata.create_all(engine)
        print("✅ Tables created successfully!")
        
        # Verify tables were created
        inspector = MetaData()
        inspector.reflect(engine)
        
        print("\n📋 Tables in database:")
        for table_name in inspector.tables:
            print(f"- {table_name}")
            
            # Print columns for each table
            table = Table(table_name, inspector, autoload_with=engine)
            print(f"  Columns: {', '.join([col.name for col in table.columns])}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Starting database table creation...")
    print(f"📁 Database will be created at: {db_path}")
    
    # Create the database file if it doesn't exist
    if not os.path.exists(db_path):
        print("📄 Creating new database file...")
        open(db_path, 'a').close()
    
    if create_tables():
        print("\n✨ Database initialization complete!")
        print("\nYou can now start the Flask application with:")
        print("  FLASK_APP=app:create_app flask run --port 5001")
    else:
        print("\n❌ Database initialization failed! Please check the error messages above.")
