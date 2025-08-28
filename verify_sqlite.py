import sqlite3
import os

def verify_sqlite():
    db_path = 'instance/tiendita.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada en: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nTablas encontradas:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Verificar usuario admin
        cursor.execute("SELECT * FROM user WHERE username='admin';")
        admin = cursor.fetchone()
        print("\nUsuario Admin:")
        if admin:
            print(f"- ID: {admin[0]}")
            print(f"- Username: {admin[1]}")
            print(f"- Is Admin: {admin[4]}")
        
        # Verificar juguetes
        cursor.execute("SELECT * FROM toy;")
        toys = cursor.fetchall()
        print(f"\nJuguetes ({len(toys)}):")
        for toy in toys:
            print(f"- ID: {toy[0]}, Nombre: {toy[1]}, Precio: {toy[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    verify_sqlite() 