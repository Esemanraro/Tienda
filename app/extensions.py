from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# Importar LoginManager solo si está instalado
try:
    from flask_login import LoginManager
    login_manager = LoginManager()
except ImportError:
    print("⚠️ flask_login no está instalado")
    login_manager = None

