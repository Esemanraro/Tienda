"""
Script simple para inicializar la base de datos.
"""
import os
from app import create_app, db
from app.models import User, Toy

def init_db():
    """Inicializa la base de datos."""
    app = create_app()
    
    with app.app_context():
        # Eliminar la base de datos existente
        db_path = os.path.join('instance', 'tiendita-dev.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Base de datos existente eliminada: {db_path}")
        
        # Crear las tablas
        print("🔨 Creando tablas...")
        db.create_all()
        print("✅ Tablas creadas exitosamente.")
        
        # Verificar que las tablas se crearon
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("📊 Tablas creadas:", tables)
        
        # Crear un usuario administrador
        admin = User(
            username='admin',
            email='admin@aloha.com',
            is_admin=True,
            balance=1000.0,
            center='David',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Crear un juguete de ejemplo
        toy = Toy(
            name='Pulseras Mágicas',
            description='Pulseras con lentejuelas reversibles.',
            price=25.0,
            category='Niña',
            stock=10,
            is_active=True
        )
        db.session.add(toy)
        
        # Guardar los cambios
        db.session.commit()
        print("✅ Usuario administrador y juguete de ejemplo creados exitosamente.")

if __name__ == "__main__":
    init_db()
