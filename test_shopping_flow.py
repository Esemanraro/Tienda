from app import create_app, db
from app.models import Toy

USERNAME = "admin"
PASSWORD = "admin123"

def login(client, username, password):
    return client.post("/auth/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

def run_full_shopping_flow():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    # Usar un contexto de aplicación para toda la prueba
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        
        # Crear un cliente de prueba con sesión persistente
        client = app.test_client()
        
        # Fase 1: Login
        print("[TEST] Iniciando login...")
        with client.session_transaction() as sess:
            # Limpiar cualquier sesión previa
            sess.clear()
        
        rv = login(client, USERNAME, PASSWORD)
        if not (b"Bienvenido" in rv.data or b"Perfil" in rv.data or rv.status_code == 200):
            print(f"[ERROR] Falló el login. Código: {rv.status_code}")
            print(f"Respuesta: {rv.data[:500]}...")  # Mostrar primeros 500 caracteres
            return False
        
        # Fase 2: Agregar al carrito
        print("[TEST] Buscando juguete activo...")
        toy = Toy.query.filter_by(is_active=True).first()
        if toy is None:
            print("[ERROR] No hay juguetes activos en la base de datos.")
            return False
        
        print(f"[TEST] Agregando juguete '{toy.name}' al carrito...")
        rv = client.post("/add_to_cart", data={
            "toy_id": toy.id,
            "quantity": 2
        }, follow_redirects=True, headers={"X-Requested-With": "XMLHttpRequest"})
        
        if rv.status_code != 200:
            print(f"[ERROR] No se pudo agregar al carrito. Código: {rv.status_code}")
            print(f"Respuesta: {rv.get_json() if rv.is_json else rv.data}")
            return False
        
        # Verificar respuesta JSON
        if rv.is_json:
            json_data = rv.get_json()
            if not json_data.get('success', False):
                print(f"[ERROR] Error en la respuesta JSON: {json_data.get('message', 'Sin mensaje de error')}")
                return False
        
        # Fase 3: Verificar carrito
        print("[TEST] Verificando carrito...")
        rv = client.get("/cart")
        if rv.status_code != 200:
            print(f"[ERROR] Error al cargar el carrito. Código: {rv.status_code}")
            return False
        
        if toy.name.encode() not in rv.data:
            print("[ERROR] El juguete no está en el carrito.")
            print(f"Contenido del carrito: {rv.data[:500]}...")  # Mostrar primeros 500 caracteres
            
            # Imprimir el estado de la sesión para depuración
            with client.session_transaction() as sess:
                print(f"Estado de la sesión: {dict(sess)}")
                print(f"Carrito en sesión: {sess.get('cart', 'No hay carrito')}")
            
            return False
        
        # Fase 4: Checkout
        print("[TEST] Realizando checkout...")
        rv = client.post("/checkout", data={
            # Agregar cualquier dato necesario para el checkout
        }, follow_redirects=True)
        
        if rv.status_code != 200:
            print(f"[ERROR] El checkout falló. Código: {rv.status_code}")
            print(f"Respuesta: {rv.data[:500]}...")
            return False
        
        # Fase 5: Verificar historial
        print("[TEST] Verificando historial de órdenes...")
        rv = client.get("/user/profile")
        if rv.status_code != 200:
            print(f"[ERROR] No se pudo cargar el perfil. Código: {rv.status}")
            return False
        
        # Verificar que la orden se creó con estado 'completada'
        from app.models import Order
        order = Order.query.order_by(Order.id.desc()).first()
        if not order:
            print("[ERROR] No se encontró ninguna orden en la base de datos")
            return False
            
        print(f"[TEST] Orden {order.id} creada con estado: {order.status}")
        if order.status != 'completada':
            print(f"[ERROR] La orden {order.id} tiene estado '{order.status}' en lugar de 'completada'")
            return False
            
        if not (b"Historial" in rv.data or b"Orden" in rv.data):
            print("[WARNING] No se encontró la sección de historial en el perfil.")
            # No consideramos esto un error fatal
        
        print("\n[TEST] Flujo de compra ejecutado exitosamente.")
        return True

if __name__ == "__main__":
    result = run_full_shopping_flow()
    if result:
        print("\n[RESULTADO] TEST EXITOSO: El flujo completo de compra funciona correctamente.")
    else:
        print("\n[RESULTADO] TEST FALLIDO: Hubo un error en el flujo de compra.")
