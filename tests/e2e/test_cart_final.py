#!/usr/bin/env python3
"""
Test final del carrito después de las correcciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Toy
import requests
import time

def test_cart_final():
    """Prueba final del carrito con servidor en vivo"""
    
    print("🛒 PRUEBA FINAL DEL CARRITO")
    print("=" * 40)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get('http://127.0.0.1:5003', timeout=5)
        print(f"✅ Servidor disponible: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Servidor no disponible: {e}")
        return False
    
    app = create_app()
    
    with app.app_context():
        # Obtener datos de prueba
        users = User.query.filter_by(is_active=True).all()
        toys = Toy.query.filter(Toy.is_active == True, Toy.stock > 0).all()
        
        if not users or not toys:
            print("❌ No hay datos suficientes para la prueba")
            return False
            
        user = users[0]
        toy = toys[0]
        
        print(f"👤 Usuario: {user.username}")
        print(f"📦 Juguete: {toy.name} (Stock: {toy.stock})")
        print(f"💰 Precio: A$ {toy.price:.2f}")
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    # 1. Obtener página de login
    print("\n1. 🔐 Obteniendo página de login...")
    response = session.get('http://127.0.0.1:5003/auth/login')
    
    if response.status_code == 200:
        print("   ✅ Página de login cargada")
        
        # Extraer CSRF token
        import re
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"   ✅ CSRF token obtenido: {csrf_token[:20]}...")
        else:
            print("   ❌ CSRF token no encontrado")
            return False
    else:
        print(f"   ❌ Error al cargar login: {response.status_code}")
        return False
    
    # 2. Login
    print("\n2. 🔑 Iniciando sesión...")
    login_data = {
        'username': user.username,
        'password': 'admin123' if user.username == 'admin' else 'password123',
        'csrf_token': csrf_token
    }
    
    response = session.post('http://127.0.0.1:5003/auth/login', data=login_data)
    
    if response.status_code == 200 and 'login' not in response.url:
        print("   ✅ Login exitoso")
    else:
        print(f"   ❌ Error en login: {response.status_code}")
        print(f"   🔗 URL final: {response.url}")
        return False
    
    # 3. Obtener página principal para nuevo CSRF
    print("\n3. 🏠 Obteniendo página principal...")
    response = session.get('http://127.0.0.1:5003/')
    
    if response.status_code == 200:
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"   ✅ Nuevo CSRF token: {csrf_token[:20]}...")
        else:
            print("   ⚠️ CSRF token no encontrado en página principal")
    
    # 4. Agregar al carrito usando AJAX
    print("\n4. ➕ Agregando al carrito (simulando AJAX)...")
    
    cart_data = {
        'toy_id': toy.id,
        'quantity': 1,
        'csrf_token': csrf_token
    }
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    response = session.post('http://127.0.0.1:5003/add_to_cart', 
                           data=cart_data, 
                           headers=headers)
    
    print(f"   📊 Respuesta: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Éxito: {data.get('message', 'Producto agregado')}")
            else:
                print(f"   ❌ Error: {data.get('message', 'Error desconocido')}")
        except:
            print("   ⚠️ Respuesta no es JSON válido")
    else:
        print(f"   ❌ Error HTTP: {response.status_code}")
        print(f"   📄 Contenido: {response.text[:200]}...")
    
    # 5. Verificar carrito
    print("\n5. 👁️ Verificando carrito...")
    response = session.get('http://127.0.0.1:5003/cart')
    
    if response.status_code == 200:
        print("   ✅ Página del carrito carga correctamente")
        
        if toy.name in response.text:
            print(f"   ✅ Juguete '{toy.name}' encontrado en carrito")
        else:
            print(f"   ❌ Juguete '{toy.name}' NO encontrado en carrito")
            
        if str(toy.price) in response.text:
            print("   ✅ Precio encontrado en carrito")
        else:
            print("   ⚠️ Precio no encontrado claramente")
    else:
        print(f"   ❌ Error al cargar carrito: {response.status_code}")
    
    print("\n" + "=" * 40)
    print("🎯 PRUEBA FINAL COMPLETADA")
    
    return True

if __name__ == "__main__":
    try:
        test_cart_final()
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
