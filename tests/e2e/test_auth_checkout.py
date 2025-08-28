#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import User, Toy
from flask_login import login_user
import re

def test_checkout_with_proper_auth():
    """Probar checkout con autenticación adecuada"""
    print("🔐 PRUEBA DE CHECKOUT CON AUTENTICACIÓN COMPLETA")
    print("="*40)
    
    with app.test_client() as client:
        with app.app_context():
            # Obtener usuario
            admin = User.query.filter_by(username='admin').first()
            print(f"👤 Usuario: {admin.username}")
            print(f"💰 Balance: A$ {admin.balance:.2f}")
            
            # Login con Flask-Login apropiado
            print("\n1. Realizando login completo...")
            
            # Primero hacer login real vía endpoint
            response = client.post('/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✅ Login exitoso vía endpoint")
            else:
                print(f"   ❌ Error en login: {response.status_code}")
            
            # Agregar al carrito
            print("\n2. Agregando items al carrito...")
            toy = Toy.query.filter_by(id=4).first()
            
            # Usar el endpoint add_to_cart
            response = client.post('/add_to_cart', data={
                'toy_id': '4',
                'quantity': '2'
            })
            
            if response.status_code == 200:
                print("   ✅ Item agregado al carrito vía endpoint")
            else:
                print(f"   ❌ Error al agregar: {response.status_code}")
            
            # Verificar carrito
            print("\n3. Verificando carrito...")
            response = client.get('/cart')
            if response.status_code == 200 and b'Robot' in response.data:
                print("   ✅ Carrito contiene el item")
            
            # Obtener página de checkout
            print("\n4. Obteniendo página de checkout...")
            response = client.get('/checkout')
            
            if response.status_code == 200:
                print("   ✅ Página de checkout cargada")
                
                # Extraer token CSRF
                html = response.data.decode('utf-8')
                csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', html)
                
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"   ✅ Token CSRF: {csrf_token[:20]}...")
                    
                    # Intentar checkout
                    print("\n5. Procesando checkout...")
                    response = client.post('/checkout', 
                                         data={'csrf_token': csrf_token},
                                         follow_redirects=False)
                    
                    print(f"   📡 Respuesta: {response.status_code}")
                    
                    if response.status_code == 302:
                        location = response.headers.get('Location', '')
                        print(f"   🔀 Redirección a: {location}")
                        
                        # Seguir la redirección
                        response = client.get(location)
                        html = response.data.decode('utf-8')
                        
                        if 'order_summary' in location:
                            print("   ✅ ¡CHECKOUT EXITOSO! Redirigido a resumen de orden")
                        elif 'Compra realizada' in html:
                            print("   ✅ ¡CHECKOUT EXITOSO! Mensaje de éxito encontrado")
                        else:
                            print("   ℹ️ Redirigido pero estado desconocido")
                    
                    elif response.status_code == 200:
                        html = response.data.decode('utf-8')
                        if 'Compra realizada' in html:
                            print("   ✅ ¡CHECKOUT EXITOSO!")
                        else:
                            print("   ❓ Respuesta 200 pero sin mensaje de éxito")
                    
                    else:
                        print("   ❌ Error en checkout")
                        # Buscar mensajes de error
                        html = response.data.decode('utf-8')
                        if 'alert' in html:
                            start = html.find('alert')
                            end = html.find('</div>', start)
                            if end > start:
                                error_msg = html[start:end]
                                print(f"   ❌ Mensaje: {error_msg[:100]}")
            else:
                print(f"   ❌ Error al cargar checkout: {response.status_code}")
                if response.status_code == 302:
                    print(f"   🔀 Redirigido a: {response.headers.get('Location')}")
    
    print("\n" + "="*40)
    print("📊 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_checkout_with_proper_auth()
