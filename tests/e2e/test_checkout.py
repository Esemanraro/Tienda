#!/usr/bin/env python
"""Test de la funcionalidad de checkout"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Toy
from flask_login import login_user

def test_checkout_flow():
    """Probar el flujo completo de checkout"""
    print("🛒 PRUEBA DE CHECKOUT")
    print("="*40)
    
    with app.app_context():
        # Obtener usuario admin
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"👤 Usuario: {admin.username}")
            print(f"💰 Balance actual: A$ {admin.balance:.2f}")
        
        # Obtener un juguete
        toy = Toy.query.filter_by(id=4).first()  # Pulseras Mágicas
        if toy:
            print(f"📦 Juguete: {toy.name}")
            print(f"💰 Precio: A$ {toy.price:.2f}")
    
    with app.test_client() as client:
        # 1. Login manual con Flask-Login
        print("\n1. 🔑 Iniciando sesión...")
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
            sess['_id'] = 'test_session'
        
        # 2. Agregar item al carrito
        print("\n2. ➕ Agregando item al carrito...")
        with client.session_transaction() as sess:
            sess['cart'] = {
                '4': {
                    'quantity': 2,
                    'price': float(toy.price)
                }
            }
        print("   ✅ Item agregado al carrito manualmente")
        
        # 3. Ver carrito para verificar
        print("\n3. 👁️ Verificando carrito...")
        response = client.get('/cart')
        if response.status_code == 200:
            print("   ✅ Carrito carga correctamente")
            if b'Pulseras' in response.data or b'Robot' in response.data:
                print("   ✅ Juguete visible en carrito")
        else:
            print(f"   ❌ Error al cargar carrito: {response.status_code}")
        
        # 4. Ir a checkout (GET)
        print("\n4. 🛍️ Accediendo a checkout...")
        try:
            response = client.get('/checkout')
            if response.status_code == 200:
                print("   ✅ Página de checkout carga correctamente")
                
                # Verificar elementos en la página
                if b'Confirmar Compra' in response.data:
                    print("   ✅ Botón de confirmar visible")
                if b'Total' in response.data:
                    print("   ✅ Total visible")
            else:
                print(f"   ❌ Error al cargar checkout: {response.status_code}")
                # Mostrar primeros 500 caracteres del error
                print(f"   ❌ Respuesta: {response.data.decode('utf-8')[:500]}")
        except Exception as e:
            print(f"   ❌ Excepción al acceder a checkout: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 5. Verificar balance antes de comprar
        print(f"\n5. 💰 Verificando balance...")
        with app.app_context():
            admin = User.query.filter_by(username='admin').first()
            toy = Toy.query.filter_by(id=4).first()
            total = 2 * toy.price
            print(f"   💳 Total de la compra: A$ {total:.2f}")
            print(f"   💰 Balance del usuario: A$ {admin.balance:.2f}")
            if admin.balance >= total:
                print("   ✅ Balance suficiente")
            else:
                print("   ❌ Balance insuficiente")
                # Agregar balance para prueba
                admin.balance = total + 100
                db.session.commit()
                print(f"   ✅ Balance actualizado a: A$ {admin.balance:.2f}")
    
    print("\n" + "="*40)
    print("📊 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_checkout_flow()
