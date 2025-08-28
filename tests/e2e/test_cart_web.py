#!/usr/bin/env python3
"""
Test del carrito usando el cliente de prueba de Flask
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Toy

def test_cart_web():
    """Prueba del carrito usando Flask test client"""
    
    print("🛒 PRUEBA WEB DEL CARRITO")
    print("=" * 40)
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Deshabilitar CSRF para pruebas
    
    with app.test_client() as client:
        with app.app_context():
            # Obtener datos de prueba
            user = User.query.filter_by(username='admin').first()
            toys = Toy.query.filter(Toy.is_active == True, Toy.stock > 0).all()
            
            if not user or not toys:
                print("❌ No hay datos suficientes para la prueba")
                return False
                
            toy = toys[0]
            print(f"👤 Usuario: {user.username}")
            print(f"📦 Juguete: {toy.name}")
            print(f"💰 Precio: A$ {toy.price:.2f}")
            print(f"📊 Stock: {toy.stock}")
            
            # 1. Login
            print("\n1. 🔑 Iniciando sesión...")
            response = client.post('/auth/login', data={
                'username': user.username,
                'password': 'admin123'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✅ Login exitoso")
            else:
                print(f"   ❌ Error en login: {response.status_code}")
                return False
            
            # 2. Agregar al carrito
            print("\n2. ➕ Agregando al carrito...")
            response = client.post('/add_to_cart', data={
                'toy_id': toy.id,
                'quantity': 2
            })
            
            print(f"   📊 Respuesta: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.get_json()
                    if data and data.get('success'):
                        print(f"   ✅ Éxito: {data.get('message', 'Producto agregado')}")
                    else:
                        print(f"   ❌ Error: {data.get('message', 'Error desconocido') if data else 'Sin respuesta JSON'}")
                except:
                    print("   ⚠️ Respuesta no es JSON, probablemente redirección")
            elif response.status_code == 302:
                print("   ✅ Redirección exitosa (comportamiento normal)")
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                print(f"   📄 Contenido: {response.get_data(as_text=True)[:200]}...")
            
            # 3. Ver carrito
            print("\n3. 👁️ Verificando carrito...")
            response = client.get('/cart')
            
            if response.status_code == 200:
                print("   ✅ Página del carrito carga correctamente")
                
                content = response.get_data(as_text=True)
                
                if toy.name in content:
                    print(f"   ✅ Juguete '{toy.name}' encontrado en carrito")
                else:
                    print(f"   ❌ Juguete '{toy.name}' NO encontrado en carrito")
                    
                if str(toy.price) in content:
                    print("   ✅ Precio encontrado en carrito")
                else:
                    print("   ⚠️ Precio no encontrado claramente")
                    
                # Buscar indicadores de cantidad
                if "cantidad" in content.lower() or "quantity" in content.lower():
                    print("   ✅ Información de cantidad presente")
                else:
                    print("   ⚠️ Información de cantidad no clara")
                    
            else:
                print(f"   ❌ Error al cargar carrito: {response.status_code}")
                print(f"   📄 Contenido: {response.get_data(as_text=True)[:200]}...")
            
            # 4. Agregar más cantidad
            print("\n4. ➕ Agregando más cantidad...")
            response = client.post('/add_to_cart', data={
                'toy_id': toy.id,
                'quantity': 1
            })
            
            if response.status_code in [200, 302]:
                print("   ✅ Segunda adición exitosa")
            else:
                print(f"   ❌ Error en segunda adición: {response.status_code}")
            
            # 5. Verificar carrito final
            print("\n5. 🔍 Verificación final del carrito...")
            response = client.get('/cart')
            
            if response.status_code == 200:
                content = response.get_data(as_text=True)
                print("   ✅ Carrito final cargado")
                
                # Buscar total
                import re
                total_match = re.search(r'Total.*?A\$\s*([\d,]+\.?\d*)', content)
                if total_match:
                    total = total_match.group(1)
                    print(f"   💰 Total encontrado: A$ {total}")
                else:
                    print("   ⚠️ Total no encontrado claramente")
            
            print("\n" + "=" * 40)
            print("✅ PRUEBA WEB COMPLETADA")
            
            return True

if __name__ == "__main__":
    try:
        test_cart_web()
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
