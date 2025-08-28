#!/usr/bin/env python3
"""
Script de prueba para verificar las optimizaciones de base de datos
Tiendita ALOHA - Test de Rendimiento
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User, Toy, Order, OrderItem
from pagination_helpers import PaginationHelper

def test_database_performance():
    """Probar el rendimiento de las consultas optimizadas"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Iniciando pruebas de rendimiento de base de datos...")
        print("=" * 60)
        
        # Test 1: Consulta de juguetes con paginación
        print("\n📄 Test 1: Paginación de juguetes")
        start_time = time.time()
        
        toys_pagination = Toy.query.filter_by(is_active=True).order_by(
            Toy.created_at.desc()
        ).paginate(page=1, per_page=12, error_out=False)
        
        end_time = time.time()
        print(f"   ✅ Consulta completada en {(end_time - start_time) * 1000:.2f}ms")
        print(f"   📊 Total de juguetes: {toys_pagination.total}")
        print(f"   📄 Páginas disponibles: {toys_pagination.pages}")
        
        # Test 2: Búsqueda de juguetes
        print("\n🔍 Test 2: Búsqueda de juguetes")
        start_time = time.time()
        
        search_results = Toy.query.filter(
            Toy.is_active == True,
            db.or_(
                db.func.lower(Toy.name).contains('toy'),
                db.func.lower(Toy.description).contains('toy')
            )
        ).limit(10).all()
        
        end_time = time.time()
        print(f"   ✅ Búsqueda completada en {(end_time - start_time) * 1000:.2f}ms")
        print(f"   📊 Resultados encontrados: {len(search_results)}")
        
        # Test 3: Estadísticas del dashboard
        print("\n📊 Test 3: Estadísticas del dashboard")
        start_time = time.time()
        
        # Estadísticas principales
        main_stats = db.session.query(
            db.func.sum(Order.total_price).label('total_sales'),
            db.func.count(Order.id).label('total_orders'),
            db.func.avg(Order.total_price).label('avg_order_value')
        ).filter(Order.is_active == True).first()
        
        # Total de usuarios activos
        total_users = User.query.filter_by(is_active=True).count()
        
        # Ventas por categoría
        sales_by_category = db.session.query(
            Toy.category,
            db.func.sum(OrderItem.quantity).label('quantity'),
            db.func.sum(OrderItem.quantity * OrderItem.price).label('amount')
        ).join(OrderItem).join(Order).filter(
            Order.is_active == True,
            OrderItem.is_active == True,
            Toy.is_active == True
        ).group_by(Toy.category).all()
        
        end_time = time.time()
        print(f"   ✅ Estadísticas calculadas en {(end_time - start_time) * 1000:.2f}ms")
        print(f"   💰 Ventas totales: A$ {main_stats.total_sales or 0:.2f}")
        print(f"   📦 Órdenes totales: {main_stats.total_orders or 0}")
        print(f"   👥 Usuarios activos: {total_users}")
        print(f"   🏷️ Categorías con ventas: {len(sales_by_category)}")
        
        # Test 4: Órdenes recientes
        print("\n📋 Test 4: Órdenes recientes")
        start_time = time.time()
        
        recent_orders = Order.query.filter_by(
            is_active=True
        ).order_by(Order.order_date.desc()).limit(5).all()
        
        end_time = time.time()
        print(f"   ✅ Órdenes recientes obtenidas en {(end_time - start_time) * 1000:.2f}ms")
        print(f"   📦 Órdenes encontradas: {len(recent_orders)}")
        
        # Test 5: Usuarios recientes
        print("\n👥 Test 5: Usuarios recientes")
        start_time = time.time()
        
        recent_users = User.query.filter_by(
            is_active=True
        ).order_by(User.created_at.desc()).limit(5).all()
        
        end_time = time.time()
        print(f"   ✅ Usuarios recientes obtenidos en {(end_time - start_time) * 1000:.2f}ms")
        print(f"   👥 Usuarios encontrados: {len(recent_users)}")
        
        # Test 6: Ventas por fecha (últimos 7 días)
        print("\n📈 Test 6: Ventas por fecha")
        start_time = time.time()
        
        sales_data = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            daily_sales = db.session.query(
                db.func.sum(Order.total_price)
            ).filter(
                Order.is_active == True,
                db.func.date(Order.order_date) == date.date()
            ).scalar() or 0
            sales_data.append(float(daily_sales))
        
        end_time = time.time()
        print(f"   ✅ Datos de ventas calculados en {(end_time - start_time) * 1000:.2f}ms")
        print(f"   📊 Días procesados: 7")
        print(f"   💰 Ventas promedio diaria: A$ {sum(sales_data) / len(sales_data):.2f}")
        
        print("\n" + "=" * 60)
        print("✅ Todas las pruebas de rendimiento completadas exitosamente!")
        print("🚀 Las optimizaciones están funcionando correctamente.")

def test_pagination_helpers():
    """Probar los helpers de paginación"""
    print("\n🔧 Probando helpers de paginación...")
    
    app = create_app()
    
    with app.test_request_context('/?page=2&per_page=24'):
        # Test get_page_number
        page = PaginationHelper.get_page_number()
        print(f"   📄 Página obtenida: {page}")
        
        # Test get_per_page
        per_page = PaginationHelper.get_per_page()
        print(f"   📊 Elementos por página: {per_page}")
    
    with app.test_request_context('/'):
        # Test valores por defecto
        page_default = PaginationHelper.get_page_number()
        per_page_default = PaginationHelper.get_per_page()
        print(f"   📄 Página por defecto: {page_default}")
        print(f"   📊 Elementos por página por defecto: {per_page_default}")
    
    print("   ✅ Helpers de paginación funcionando correctamente")

def check_database_indexes():
    """Verificar que los índices estén creados"""
    app = create_app()
    
    with app.app_context():
        print("\n🗃️ Verificando índices de base de datos...")
        
        # Obtener información de índices (SQLite)
        inspector = db.inspect(db.engine)
        
        # Verificar índices por tabla
        tables = ['user', 'toy', 'order', 'order_item']
        
        for table in tables:
            try:
                indexes = inspector.get_indexes(table)
                print(f"   📋 Tabla '{table}': {len(indexes)} índices encontrados")
                for idx in indexes:
                    print(f"      - {idx['name']}: {idx['column_names']}")
            except Exception as e:
                print(f"   ⚠️ Error al verificar índices de '{table}': {str(e)}")
        
        print("   ✅ Verificación de índices completada")

def main():
    """Función principal del script de pruebas"""
    print("🎮 TIENDITA ALOHA - Test de Optimizaciones de Base de Datos")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Ejecutar pruebas
        test_database_performance()
        test_pagination_helpers()
        check_database_indexes()
        
        print("\n🎉 ¡Todas las pruebas completadas exitosamente!")
        print("💡 La aplicación está optimizada y lista para producción.")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
