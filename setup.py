import os
import sys
from app import app, db
from models import User, Toy

def setup_app():
    """Initialize the application"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating admin user...")
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create some sample toys
            toys = [
                Toy(
                    name='Sample Toy 1',
                    description='A fun sample toy',
                    price=10.99,
                    image_url='/static/images/toys/default_toy.png'
                ),
                Toy(
                    name='Sample Toy 2',
                    description='Another fun sample toy',
                    price=15.99,
                    image_url='/static/images/toys/default_toy.png'
                )
            ]
            
            for toy in toys:
                db.session.add(toy)
            
            db.session.commit()
            print("Initial data created successfully!")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    setup_app()
