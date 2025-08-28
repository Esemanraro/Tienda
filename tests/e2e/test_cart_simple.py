#!/usr/bin/env python3
"""
Test simple del carrito usando la funcionalidad interna
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Toy
from blueprints.shop import add_to_session_cart, get_session_cart

def test_cart_simple():
    """Prueba simple del carrito usando funciones internas"""
    
    print("🛒 PRUEBA SIMPLE DEL CARRITO")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        with app.test_request_context():
            # Obtener datos de prueba
            toys = Toy.query.filter(Toy.is_active == True, Toy.stock > 0).all()
            
            if not toys:
                print("❌ No hay juguetes disponibles")
                return False
                
            toy = toys[0]
            print(f"📦 Juguete: {toy.name}")
            print(f"💰 Precio: A$ {toy.price:.2f}")
            print(f"📊 Stock: {toy.stock}")
            
            # Simular sesión vacía
            from flask import session
            session.clear()
            
            print("\n1. 🔍 Verificando carrito vacío...")
            cart = get_session_cart()
            print(f"   📋 Items en carrito: {len(cart)}")
            
            print("\n2. ➕ Agregando juguete al carrito...")
            try:
                result = add_to_session_cart(toy.id, 2)
                if result['success']:
                    print(f"   ✅ Éxito: {result['message']}")
                else:
                    print(f"   ❌ Error: {result['message']}")
                    return False
            except Exception as e:
                print(f"   💥 Excepción: {e}")
                return False
            
            print("\n3. 🔍 Verificando carrito después de agregar...")
            cart = get_session_cart()
            print(f"   📋 Items en carrito: {len(cart)}")
            
            if str(toy.id) in cart:
                item = cart[str(toy.id)]
                print(f"   ✅ Juguete encontrado:")
                print(f"      - ID: {item['toy_id']}")
                print(f"      - Cantidad: {item['quantity']}")
                print(f"      - Precio: A$ {item['price']:.2f}")
                print(f"      - Subtotal: A$ {item['subtotal']:.2f}")
            else:
                print("   ❌ Juguete NO encontrado en carrito")
                return False
            
            print("\n4. ➕ Agregando más cantidad del mismo juguete...")
            try:
                result = add_to_session_cart(toy.id, 1)
                if result['success']:
                    print(f"   ✅ Éxito: {result['message']}")
                else:
                    print(f"   ❌ Error: {result['message']}")
            except Exception as e:
                print(f"   💥 Excepción: {e}")
            
            print("\n5. 🔍 Verificando carrito final...")
            cart = get_session_cart()
            if str(toy.id) in cart:
                item = cart[str(toy.id)]
                print(f"   ✅ Cantidad actualizada: {item['quantity']}")
                print(f"   💰 Subtotal: A$ {item['subtotal']:.2f}")
            
            # Calcular total
            total = sum(item['subtotal'] for item in cart.values())
            print(f"\n💰 TOTAL DEL CARRITO: A$ {total:.2f}")
            
            print("\n" + "=" * 40)
            print("✅ PRUEBA SIMPLE COMPLETADA EXITOSAMENTE")
            
            return True

if __name__ == "__main__":
    try:
        test_cart_simple()
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
