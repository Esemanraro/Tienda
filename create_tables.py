import os
from .app import create_app, db

# Set environment variables if necessary, similar to run.py or your usual setup
# This ensures the correct config (DevelopmentConfig) is loaded by create_app
os.environ.setdefault('FLASK_ENV', 'development')

app = create_app()

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Tables created successfully in:", app.config['SQLALCHEMY_DATABASE_URI'])
