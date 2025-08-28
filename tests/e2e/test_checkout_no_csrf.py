#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Toy, Order, OrderItem

def test_checkout_without_csrf():
    """Probar checkout desactivando CSRF temporalmente"""
    print("🛒 PRUEBA DE CHECKOUT SIN CSRF")
    print("="*40)
    
    # Desactivar CSRF para esta prueba
    app.config['WTF_CSRF_ENABLED'] = False
    
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
        else:
            print(f"   ❌ Error al cargar checkout: {response.status_code}")
            return
        
        # 4. Procesar pago (POST)
        print("\n4. 💳 Procesando pago (CSRF desactivado)...")
        response = client.post('/checkout', 
                             data={},
                             follow_redirects=True)
        
        print(f"   📡 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            # Verificar mensajes flash
            html = response.data.decode('utf-8')
            if '¡Compra realizada con éxito!' in html:
                print("   ✅ Compra completada exitosamente")
            elif 'No tienes suficientes ALOHA Dollars' in html:
                print("   ❌ Error: Balance insuficiente")
            elif 'Tu carrito está vacío' in html:
                print("   ❌ Error: Carrito vacío")
            elif 'Error al procesar la compra' in html:
                print("   ❌ Error al procesar la compra")
            else:
                # Buscar título de página
                if '<title>' in html:
                    start = html.find('<title>') + 7
                    end = html.find('</title>')
                    title = html[start:end]
                    print(f"   📄 Página resultante: {title}")
                    
                # Buscar mensajes de error
                if 'alert-error' in html or 'alert-danger' in html:
                    print("   ❌ Se encontraron alertas de error en la página")
        
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
            else:
                print("   ❌ No se encontraron órdenes nuevas")
    
    # Reactivar CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    
    print("\n" + "="*40)
    print("📊 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_checkout_without_csrf()
