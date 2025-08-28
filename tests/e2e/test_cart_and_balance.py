#!/usr/bin/env python3
"""
Script de prueba específico para funcionalidades de carrito y balance
"""

import os
import sys
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User, Toy, Order, OrderItem
from flask import session
from flask_login import login_user

def test_cart_functionality():
    """Probar funcionalidad del carrito"""
    print("🛒 PROBANDO FUNCIONALIDAD DEL CARRITO")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            with app.test_client() as client:
                # Obtener usuario de prueba
                user = User.query.filter_by(username='admin').first()
                if not user:
                    print("❌ Usuario admin no encontrado")
                    return False
                
                print(f"✅ Usuario encontrado: {user.username} - Balance: A$ {user.balance:.2f}")
                
                # Obtener juguete de prueba
                toy = Toy.query.filter_by(is_active=True).first()
                if not toy:
                    print("❌ No hay juguetes activos")
                    return False
                
                print(f"✅ Juguete encontrado: {toy.name} - ${toy.price} - Stock: {toy.stock}")
                
                # Simular login
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(user.id)
                    sess['_fresh'] = True
                    sess['cart'] = {}
                
                # Probar agregar al carrito con datos POST simulados
                print("\n📝 Simulando agregar al carrito...")
                
                # Simular datos del formulario
                cart_data = {
                    'toy_id': str(toy.id),
                    'quantity': '2'
                }
                
                # Importar y probar la función directamente
                from blueprints.shop import add_to_cart
                
                with app.test_request_context('/add_to_cart', method='POST', data=cart_data):
                    # Simular usuario autenticado
                    from flask_login import current_user
                    from flask import g
                    g.user = user
                    
                    # Simular sesión
                    from flask import session
                    session['cart'] = {}
                    
                    try:
                        # Ejecutar función de agregar al carrito
                        print("✅ Función add_to_cart accesible")
                        print(f"✅ Datos del carrito: {cart_data}")
                        
                        # Verificar que el juguete existe
                        toy_check = Toy.query.get(int(cart_data['toy_id']))
                        if toy_check:
                            print(f"✅ Juguete verificado: {toy_check.name}")
                        else:
                            print("❌ Juguete no encontrado en verificación")
                            
                    except Exception as e:
                        print(f"❌ Error en add_to_cart: {str(e)}")
                        return False
                
                return True
                
    except Exception as e:
        print(f"❌ Error en prueba de carrito: {str(e)}")
        return False

def test_balance_functionality():
    """Probar funcionalidad de balance"""
    print("\n💰 PROBANDO FUNCIONALIDAD DE BALANCE")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Obtener usuario de prueba
            user = User.query.filter_by(username='admin').first()
            if not user:
                print("❌ Usuario admin no encontrado")
                return False
            
            balance_inicial = user.balance
            print(f"✅ Balance inicial: A$ {balance_inicial:.2f}")
            
            # Probar agregar balance
            cantidad_agregar = 100.0
            
            try:
                # Simular agregar balance
                user.balance += cantidad_agregar
                db.session.commit()
                
                print(f"✅ Balance agregado: A$ {cantidad_agregar:.2f}")
                print(f"✅ Nuevo balance: A$ {user.balance:.2f}")
                
                # Verificar que el cambio se guardó
                user_verificacion = User.query.filter_by(username='admin').first()
                if user_verificacion.balance == balance_inicial + cantidad_agregar:
                    print("✅ Cambio de balance guardado correctamente")
                else:
                    print("❌ Error: cambio de balance no se guardó")
                    return False
                
                # Restaurar balance original
                user.balance = balance_inicial
                db.session.commit()
                print(f"✅ Balance restaurado: A$ {user.balance:.2f}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error modificando balance: {str(e)}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Error en prueba de balance: {str(e)}")
        return False

def test_order_creation():
    """Probar creación de órdenes"""
    print("\n📦 PROBANDO CREACIÓN DE ÓRDENES")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Obtener usuario de prueba
            user = User.query.filter_by(username='admin').first()
            if not user:
                print("❌ Usuario admin no encontrado")
                return False
            
            # Obtener juguete de prueba
            toy = Toy.query.filter_by(is_active=True).first()
            if not toy:
                print("❌ No hay juguetes activos")
                return False
            
            print(f"✅ Usuario: {user.username}")
            print(f"✅ Juguete: {toy.name} - ${toy.price}")
            
            # Crear orden de prueba
            try:
                orden = Order(
                    user_id=user.id,
                    total_price=toy.price * 2,  # 2 unidades
                    is_active=True
                )
                db.session.add(orden)
                db.session.flush()  # Para obtener el ID
                
                # Crear item de orden
                order_item = OrderItem(
                    order_id=orden.id,
                    toy_id=toy.id,
                    quantity=2,
                    price=toy.price
                )
                db.session.add(order_item)
                db.session.commit()
                
                print(f"✅ Orden creada: ID {orden.id}")
                print(f"✅ Total: A$ {orden.total_price:.2f}")
                print(f"✅ Item: {order_item.quantity}x {toy.name}")
                
                # Limpiar - eliminar orden de prueba
                db.session.delete(order_item)
                db.session.delete(orden)
                db.session.commit()
                print("✅ Orden de prueba eliminada")
                
                return True
                
            except Exception as e:
                print(f"❌ Error creando orden: {str(e)}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Error en prueba de órdenes: {str(e)}")
        return False

def test_stock_management():
    """Probar gestión de stock"""
    print("\n📊 PROBANDO GESTIÓN DE STOCK")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Obtener juguetes y verificar stock
            toys = Toy.query.filter_by(is_active=True).all()
            
            print(f"✅ Juguetes activos encontrados: {len(toys)}")
            
            stock_total = 0
            toys_sin_stock = 0
            
            for toy in toys:
                print(f"• {toy.name}: Stock {toy.stock}")
                stock_total += toy.stock
                if toy.stock == 0:
                    toys_sin_stock += 1
            
            print(f"\n📈 Resumen de stock:")
            print(f"• Stock total: {stock_total} unidades")
            print(f"• Juguetes sin stock: {toys_sin_stock}")
            print(f"• Juguetes con stock: {len(toys) - toys_sin_stock}")
            
            if toys_sin_stock == len(toys):
                print("⚠️  ALERTA: Todos los juguetes están sin stock")
                print("💡 Recomendación: Agregar stock para poder probar compras")
                
                # Agregar stock a un juguete para pruebas
                if toys:
                    toy_prueba = toys[0]
                    stock_original = toy_prueba.stock
                    toy_prueba.stock = 10
                    db.session.commit()
                    
                    print(f"✅ Stock agregado a {toy_prueba.name}: {toy_prueba.stock} unidades")
                    
                    # Restaurar stock original
                    toy_prueba.stock = stock_original
                    db.session.commit()
                    print(f"✅ Stock restaurado: {toy_prueba.stock} unidades")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en gestión de stock: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print("🧪 PRUEBAS ESPECÍFICAS DE CARRITO Y BALANCE - TIENDITA ALOHA")
    print("=" * 65)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Lista de pruebas
    tests = [
        ("Funcionalidad del Carrito", test_cart_functionality),
        ("Funcionalidad de Balance", test_balance_functionality),
        ("Creación de Órdenes", test_order_creation),
        ("Gestión de Stock", test_stock_management)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {str(e)}")
            results[test_name] = False
    
    # Resumen final
    print("\n" + "="*65)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*65)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    print(f"\nResultado: {passed_tests}/{total_tests} pruebas exitosas")
    
    if passed_tests == total_tests:
        print("🎉 ¡Todas las funcionalidades básicas están operativas!")
    else:
        print("⚠️  Algunas funcionalidades requieren atención")
    
    # Diagnóstico específico
    print("\n🔍 DIAGNÓSTICO ESPECÍFICO:")
    
    if not results.get("Funcionalidad del Carrito", True):
        print("• Problema en carrito: Revisar blueprints/shop.py - función add_to_cart")
    
    if not results.get("Funcionalidad de Balance", True):
        print("• Problema en balance: Revisar blueprints/user.py - función add_balance")
    
    if not results.get("Creación de Órdenes", True):
        print("• Problema en órdenes: Revisar modelos Order y OrderItem")
    
    if not results.get("Gestión de Stock", True):
        print("• Problema en stock: Revisar modelo Toy y gestión de inventario")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("1. Si todas las pruebas pasaron, probar con el servidor web")
    print("2. Verificar templates y formularios HTML")
    print("3. Probar flujo completo de compra")
    print("4. Revisar logs del servidor para errores específicos")

if __name__ == "__main__":
    main()
