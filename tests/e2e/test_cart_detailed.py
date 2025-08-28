#!/usr/bin/env python3
"""
Test detallado del carrito con manejo de CSRF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Toy
from flask import session
import re

def test_cart_with_csrf():
    """Prueba del carrito con manejo correcto de CSRF"""
    
    print(" PRUEBA DETALLADA DEL CARRITO CON CSRF")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # Obtener datos de prueba
        users = User.query.filter_by(is_active=True).all()
        toys = Toy.query.filter(Toy.is_active == True, Toy.stock > 0).all()
        
        if not users or not toys:
            print(" No hay datos suficientes para la prueba")
            return False
            
        user = users[0]
        toy = toys[0]
        
        print(f" Usuario: {user.username}")
        print(f" Juguete: {toy.name} (Stock: {toy.stock})")
        
    with app.test_client() as client:
        # 1. Login del usuario
        print("\n1.  Iniciando sesin...")
        
        # Obtener pgina de login para CSRF token
        response = client.get('/auth/login')
        csrf_token = None
        
        if response.status_code == 200:
            # Extraer CSRF token del HTML
            content = response.get_data(as_text=True)
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', content)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   CSRF token obtenido: {csrf_token[:20]}...")
            else:
                print("   CSRF token no encontrado en login")
        
        # Login con credenciales
        login_data = {
            'username': user.username,
            'password': 'password123',  # Contraseña por defecto
        }
        if csrf_token:
            login_data['csrf_token'] = csrf_token
            
        response = client.post('/auth/login', data=login_data, follow_redirects=True)
        
        if response.status_code == 200:
            print("   Login exitoso")
        else:
            print(f"   Error en login: {response.status_code}")
            
        # 2. Obtener pgina principal para nuevo CSRF
        print("\n2.  Obteniendo pgina principal...")
        response = client.get('/')
        
        if response.status_code == 200:
            content = response.get_data(as_text=True)
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', content)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   Nuevo CSRF token: {csrf_token[:20]}...")
            else:
                print("   CSRF token no encontrado en pgina principal")
        
        # 3. Agregar al carrito con CSRF
        print("\n3.  Agregando al carrito...")
        
        cart_data = {
            'toy_id': toy.id,
            'quantity': 2
        }
        if csrf_token:
            cart_data['csrf_token'] = csrf_token
            
        response = client.post('/add_to_cart', data=cart_data, follow_redirects=False)
        
        print(f"   Respuesta: {response.status_code}")
        if response.status_code == 302:
            print("   Redireccin correcta")
            print(f"   Redireccin a: {response.headers.get('Location', 'No especificado')}")
        elif response.status_code == 400:
            print("   Error 400 - Posible problema con datos del formulario")
            # Intentar obtener ms informacin del error
            try:
                error_content = response.get_data(as_text=True)
                if error_content:
                    print(f"   Contenido del error: {error_content[:200]}...")
            except:
                pass
        else:
            print(f"   Respuesta inesperada: {response.status_code}")
            
        # 4. Verificar carrito
        print("\n4.  Verificando carrito...")
        response = client.get('/cart')
        
        if response.status_code == 200:
            content = response.get_data(as_text=True)
            print("   Pgina del carrito carga correctamente")
            
            if toy.name in content:
                print(f"   Juguete '{toy.name}' encontrado en carrito")
            else:
                print(f"   Juguete '{toy.name}' NO encontrado en carrito")
                
            # Buscar informacin de cantidad y precio
            if "quantity" in content.lower() or str(toy.price) in content:
                print("   Informacin de cantidad/precio encontrada")
            else:
                print("   Informacin de cantidad/precio no clara")
        else:
            print(f"   Error al cargar carrito: {response.status_code}")
            
        # 5. Verificar sesin directamente
        print("\n5.  Verificando sesin...")
        with client.session_transaction() as sess:
            cart = sess.get('cart', {})
            print(f"   Items en sesin: {len(cart)}")
            
            if cart:
                for toy_id, item in cart.items():
                    if isinstance(item, dict):
                        print(f"   Juguete {toy_id}: {item.get('quantity', 0)} unidades @ A$ {item.get('price', 0):.2f}")
                    else:
                        print(f"   Juguete {toy_id}: {item} (formato simple)")
            else:
                print("   Carrito vaco en sesin")
                
        print("\n" + "=" * 50)
        print(" DIAGNSTICO COMPLETADO")
        
        return True

if __name__ == "__main__":
    try:
        test_cart_with_csrf()
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
