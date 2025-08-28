#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar el estado de la sesión y el carrito
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import User
import re

def test_session_cart():
    """Verificar el estado de la sesión y el carrito"""
    print("🔍 VERIFICACIÓN DE SESIÓN Y CARRITO")
    print("="*50)
    
    with app.test_client() as client:
        with app.app_context():
            # 1. Login
            print("\n1. Realizando login...")
            response = client.get('/auth/login')
            html = response.data.decode('utf-8')
            csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', html)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
                response = client.post('/auth/login', 
                                     data={
                                         'username': 'admin',
                                         'password': 'admin123',
                                         'csrf_token': csrf_token
                                     },
                                     follow_redirects=True)
                print("   ✅ Login realizado")
            
            # 2. Agregar al carrito
            print("\n2. Agregando item al carrito...")
            response = client.get('/')
            html = response.data.decode('utf-8')
            csrf_match = re.search(r'<meta[^>]*name="csrf-token"[^>]*content="([^"]+)"', html)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
                response = client.post('/add_to_cart',
                                     data={
                                         'toy_id': '4',
                                         'quantity': '2',
                                         'csrf_token': csrf_token
                                     })
                print(f"   Respuesta: {response.status_code}")
            
            # 3. Verificar sesión
            print("\n3. Verificando sesión del carrito...")
            with client.session_transaction() as sess:
                print(f"   Contenido de session['cart']: {sess.get('cart', 'NO EXISTE')}")
                if 'cart' in sess:
                    print(f"   Tipo: {type(sess['cart'])}")
                    print(f"   Vacío?: {not sess['cart']}")
                    print(f"   Contenido: {sess['cart']}")
            
            # 4. Intentar checkout
            print("\n4. Intentando acceder a checkout...")
            response = client.get('/checkout', follow_redirects=False)
            print(f"   Respuesta: {response.status_code}")
            
            if response.status_code == 302:
                print(f"   Redirigido a: {response.headers.get('Location')}")
                
                # Verificar sesión después del intento
                with client.session_transaction() as sess:
                    print(f"\n   Estado del carrito después del intento:")
                    print(f"   - Existe 'cart': {'cart' in sess}")
                    if 'cart' in sess:
                        print(f"   - Contenido: {sess['cart']}")
            else:
                print("   ✅ Página de checkout cargada")
    
    print("\n" + "="*50)
    print("📊 VERIFICACIÓN COMPLETADA")

if __name__ == "__main__":
    test_session_cart()
