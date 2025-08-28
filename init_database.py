#!/usr/bin/env python3
"""
Initialize the database with all required tables.
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Now import the app factory and models
from app import create_app, db
from app.models import User, Toy, Order, OrderItem

def init_db():
    """Initialize the database."""
    print("Creating database tables...")
    
    # Create the application
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nTables in database:")
        for table in tables:
            print(f"- {table}")
        
        # Check if the toy table exists and has columns
        if 'toy' in tables:
            print("\n✅ 'toy' table created successfully!")
            print("Columns in 'toy' table:")
            columns = inspector.get_columns('toy')
            for column in columns:
                print(f"- {column['name']} ({column['type']})")
        else:
            print("\n❌ Error: 'toy' table not found in database!")
            return False
            
        return True

if __name__ == '__main__':
    print("🚀 Starting database initialization...")
    print(f"📁 Current working directory: {os.getcwd()}")
    
    # Create the database file if it doesn't exist
    db_path = os.path.join(os.path.dirname(__file__), 'tiendita.db')
    if not os.path.exists(db_path):
        print(f"📄 Creating new database file at: {db_path}")
        open(db_path, 'a').close()
    
    if init_db():
        print("✅ Database initialization complete!")
        print("\nYou can now start the Flask application with:")
        print("  FLASK_APP=app:create_app flask run --port 5001")
    else:
        print("❌ Database initialization failed!")
