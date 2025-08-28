#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test final del checkout con login completo y CSRF
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import User, Toy, Order
import re

def test_checkout_final():
    """Test completo del proceso de checkout"""
    print("🔍 TEST FINAL DE CHECKOUT CON LOGIN Y CSRF")
    print("="*50)
    
    with app.test_client() as client:
        with app.app_context():
            # Estado inicial
            admin = User.query.filter_by(username='admin').first()
            toy = Toy.query.filter_by(id=4).first()
            initial_balance = admin.balance
            initial_stock = toy.stock
            initial_orders = Order.query.count()
            
            print(f"📊 Estado inicial:")
            print(f"   - Balance usuario: A$ {initial_balance:.2f}")
            print(f"   - Stock {toy.name}: {initial_stock}")
            print(f"   - Órdenes totales: {initial_orders}")
            
            # 1. Obtener página de login
            print("\n1. Obteniendo página de login...")
            response = client.get('/auth/login')
            html = response.data.decode('utf-8')
            
            # Extraer CSRF token del login
            csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', html)
            if not csrf_match:
                print("   ❌ No se encontró CSRF token en login")
                return
            
            csrf_token = csrf_match.group(1)
            print(f"   ✅ CSRF token obtenido: {csrf_token[:20]}...")
            
            # 2. Hacer login
            print("\n2. Realizando login...")
            response = client.post('/auth/login', 
                                 data={
                                     'username': 'admin',
                                     'password': 'admin123',
                                     'csrf_token': csrf_token
                                 },
                                 follow_redirects=True)
            
            if b'Bienvenido' in response.data or response.status_code == 200:
                print("   ✅ Login exitoso")
            else:
                print(f"   ❌ Error en login: {response.status_code}")
                return
            
            # 3. Agregar al carrito
            print("\n3. Agregando item al carrito...")
            
            # Primero obtener la página para el CSRF token
            response = client.get('/')
            html = response.data.decode('utf-8')
            csrf_match = re.search(r'<meta[^>]*name="csrf-token"[^>]*content="([^"]+)"', html)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   ✅ CSRF token para carrito: {csrf_token[:20]}...")
            
            # Agregar al carrito
            response = client.post('/add_to_cart',
                                 data={
                                     'toy_id': '4',
                                     'quantity': '2',
                                     'csrf_token': csrf_token
                                 })
            
            if response.status_code in [200, 302]:
                print("   ✅ Item agregado al carrito")
            else:
                print(f"   ❌ Error al agregar: {response.status_code}")
            
            # 4. Verificar carrito
            print("\n4. Verificando carrito...")
            response = client.get('/cart')
            if b'Robot' in response.data:
                print("   ✅ Carrito contiene el item")
            else:
                print("   ❌ Carrito vacío o error")
            
            # 5. Obtener página de checkout
            print("\n5. Obteniendo página de checkout...")
            response = client.get('/checkout')
            
            if response.status_code == 200:
                print("   ✅ Página de checkout cargada")
                html = response.data.decode('utf-8')
                
                # Extraer CSRF token del checkout
                csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', html)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"   ✅ CSRF token de checkout: {csrf_token[:20]}...")
                    
                    # 6. Procesar checkout
                    print("\n6. Procesando checkout...")
                    response = client.post('/checkout',
                                         data={'csrf_token': csrf_token},
                                         follow_redirects=False)
                    
                    print(f"   📡 Respuesta: {response.status_code}")
                    
                    if response.status_code == 302:
                        location = response.headers.get('Location', '')
                        print(f"   🔀 Redirección a: {location}")
                        
                        if 'order' in location:
                            print("   ✅ ¡CHECKOUT EXITOSO!")
                            
                            # Verificar cambios
                            admin = User.query.filter_by(username='admin').first()
                            toy = Toy.query.filter_by(id=4).first()
                            new_orders = Order.query.count()
                            
                            print(f"\n📊 Estado final:")
                            print(f"   - Balance usuario: A$ {admin.balance:.2f} (cambio: A$ {admin.balance - initial_balance:.2f})")
                            print(f"   - Stock {toy.name}: {toy.stock} (cambio: {toy.stock - initial_stock})")
                            print(f"   - Órdenes totales: {new_orders} (nuevas: {new_orders - initial_orders})")
                        else:
                            print("   ❌ Redirección inesperada")
                    else:
                        print("   ❌ Error en checkout")
                        if response.data:
                            html = response.data.decode('utf-8')
                            # Buscar mensajes de error
                            if 'alert' in html:
                                print("   ❌ Mensaje de error encontrado en la respuesta")
                else:
                    print("   ❌ No se encontró CSRF token en checkout")
            else:
                print(f"   ❌ Error al cargar checkout: {response.status_code}")
    
    print("\n" + "="*50)
    print("📊 TEST COMPLETADO")

if __name__ == "__main__":
    test_checkout_final()
