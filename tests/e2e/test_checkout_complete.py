#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Toy, Order, OrderItem

def test_complete_checkout():
    """Probar el flujo completo de checkout incluyendo el POST"""
    print("🛒 PRUEBA COMPLETA DE CHECKOUT")
    print("="*40)
    
    with app.app_context():
        # Obtener usuario admin
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"👤 Usuario: {admin.username}")
            print(f"💰 Balance inicial: A$ {admin.balance:.2f}")
        
        # Obtener un juguete
        toy = Toy.query.filter_by(id=4).first()  # Robot Transformador
        if toy:
            print(f"📦 Juguete: {toy.name}")
            print(f"💰 Precio: A$ {toy.price:.2f}")
            print(f"📊 Stock inicial: {toy.stock} unidades")
    
    with app.test_client() as client:
        # 1. Login manual con Flask-Login
        print("\n1. 🔑 Iniciando sesión...")
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
            sess['_id'] = 'test_session'
        
        # 2. Agregar item al carrito
        print("\n2. ➕ Agregando item al carrito...")
        quantity = 2
        with client.session_transaction() as sess:
            sess['cart'] = {
                '4': {
                    'quantity': quantity,
                    'price': float(toy.price)
                }
            }
        print(f"   ✅ {quantity} items agregados al carrito")
        
        # 3. Ver checkout
        print("\n3. 👁️ Verificando página de checkout...")
        response = client.get('/checkout')
        if response.status_code == 200:
            print("   ✅ Página de checkout carga correctamente")
            # Extraer el token CSRF del HTML
            html = response.data.decode('utf-8')
            csrf_token = None
            if '<meta name="csrf-token"' in html:
                start = html.find('content="', html.find('<meta name="csrf-token"')) + 9
                end = html.find('"', start)
                csrf_token = html[start:end]
                print(f"   ✅ Token CSRF encontrado: {csrf_token[:10]}...")
        else:
            print(f"   ❌ Error al cargar checkout: {response.status_code}")
            return
        
        # 4. Procesar pago (POST)
        print("\n4. 💳 Procesando pago...")
        
        # Preparar datos del formulario
        form_data = {'confirm': 'true'}
        if csrf_token:
            form_data['csrf_token'] = csrf_token
        
        response = client.post('/checkout', 
                             data=form_data,
                             follow_redirects=True)
        
        if response.status_code == 200:
            print("   ✅ Respuesta exitosa del servidor")
            
            # Verificar redirección
            if b'Compra realizada exitosamente' in response.data:
                print("   ✅ Compra completada exitosamente")
            elif b'Balance insuficiente' in response.data:
                print("   ❌ Error: Balance insuficiente")
            elif b'carrito' in response.data and b'vac' in response.data:
                print("   ❌ Error: Carrito vacío")
            else:
                # Buscar otros mensajes
                if b'error' in response.data:
                    print("   ❌ Error en la compra")
                else:
                    print("   ℹ️ Respuesta del servidor:")
                    # Buscar título de página
                    if b'<title>' in response.data:
                        start = response.data.find(b'<title>') + 7
                        end = response.data.find(b'</title>')
                        title = response.data[start:end].decode('utf-8')
                        print(f"      Página: {title}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
        
        # 5. Verificar cambios en la base de datos
        print("\n5. 🔍 Verificando cambios en la base de datos...")
        with app.app_context():
            # Verificar usuario
            admin = User.query.filter_by(username='admin').first()
            print(f"   💰 Balance final del usuario: A$ {admin.balance:.2f}")
            
            # Verificar stock
            toy = Toy.query.filter_by(id=4).first()
            print(f"   📊 Stock final del juguete: {toy.stock} unidades")
            
            # Verificar órdenes
            orders = Order.query.filter_by(user_id=admin.id).order_by(Order.created_at.desc()).first()
            if orders:
                print(f"   ✅ Orden creada: #{orders.id}")
                print(f"   💰 Total de la orden: A$ {orders.total_price:.2f}")
                print(f"   📅 Fecha: {orders.created_at}")
                
                # Verificar items de la orden
                items = OrderItem.query.filter_by(order_id=orders.id).all()
                print(f"   📦 Items en la orden: {len(items)}")
                for item in items:
                    print(f"      - {item.toy.name}: {item.quantity} x A$ {item.price:.2f}")
            else:
                print("   ❌ No se encontraron órdenes nuevas")
        
        # 6. Verificar carrito vacío
        print("\n6. 🛒 Verificando estado del carrito...")
        with client.session_transaction() as sess:
            if 'cart' in sess:
                if sess['cart']:
                    print("   ❌ El carrito NO se vació después de la compra")
                else:
                    print("   ✅ El carrito se vació correctamente")
            else:
                print("   ✅ El carrito no existe en la sesión")
    
    print("\n" + "="*40)
    print("📊 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_complete_checkout()
