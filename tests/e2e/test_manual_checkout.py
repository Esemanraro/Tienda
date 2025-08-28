#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test manual de checkout - imprime instrucciones para verificar el checkout manualmente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import User, Toy, Order

def manual_checkout_instructions():
    """Imprimir instrucciones para probar el checkout manualmente"""
    print("📋 INSTRUCCIONES PARA PRUEBA MANUAL DE CHECKOUT")
    print("="*50)
    
    with app.app_context():
        # Verificar estado inicial
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"\n✅ Usuario de prueba disponible:")
            print(f"   - Usuario: admin")
            print(f"   - Contraseña: admin123")
            print(f"   - Balance actual: A$ {admin.balance:.2f}")
        
        # Verificar juguetes disponibles
        toys = Toy.query.filter(Toy.stock > 0).limit(3).all()
        if toys:
            print(f"\n✅ Juguetes disponibles para prueba:")
            for toy in toys:
                print(f"   - {toy.name}: A$ {toy.price:.2f} (Stock: {toy.stock})")
        
        # Contar órdenes existentes
        order_count = Order.query.count()
        print(f"\n📊 Órdenes actuales en el sistema: {order_count}")
    
    print("\n" + "="*50)
    print("🔧 PASOS PARA PROBAR EL CHECKOUT:")
    print("="*50)
    
    print("\n1️⃣  Abre el navegador en: http://127.0.0.1:5003")
    print("\n2️⃣  Inicia sesión:")
    print("   - Click en 'Iniciar Sesión'")
    print("   - Usuario: admin")
    print("   - Contraseña: admin123")
    
    print("\n3️⃣  Agrega items al carrito:")
    print("   - Ve a la página principal")
    print("   - Selecciona un juguete")
    print("   - Click en 'Agregar al Carrito'")
    
    print("\n4️⃣  Ve al carrito:")
    print("   - Click en el ícono del carrito")
    print("   - Verifica que aparezcan los items")
    
    print("\n5️⃣  Procede al checkout:")
    print("   - Click en 'Proceder al Pago'")
    print("   - Verifica el resumen de la orden")
    print("   - Click en 'Confirmar Compra'")
    
    print("\n6️⃣  Verifica el resultado:")
    print("   - ✅ Si ves 'Compra realizada con éxito' - ¡ÉXITO!")
    print("   - ❌ Si ves un error - anota el mensaje")
    
    print("\n" + "="*50)
    print("💡 VERIFICACIÓN POST-COMPRA:")
    print("="*50)
    print("\nEjecuta este script nuevamente después de la compra para ver:")
    print("- Si el balance del usuario disminuyó")
    print("- Si se creó una nueva orden")
    print("- Si el stock del juguete se redujo")
    
    print("\n🚀 ¡Listo para probar!")

if __name__ == "__main__":
    manual_checkout_instructions()
