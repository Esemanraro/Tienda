#!/usr/bin/env python3
"""
Sistema de Inventario Inteligente para Tiendita ALOHA
Alertas automáticas, predicción de reabastecimiento y dashboard en tiempo real
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import Toy, Order, OrderItem, User

class InventoryManager:
    """Gestor inteligente de inventario"""
    
    def __init__(self):
        self.app = create_app()
        self.low_stock_threshold = 5  # Umbral de stock bajo
        self.critical_stock_threshold = 2  # Umbral crítico
        
    def check_low_stock(self) -> List[Dict]:
        """Verificar juguetes con stock bajo"""
        with self.app.app_context():
            low_stock_toys = Toy.query.filter(
                Toy.is_active == True,
                Toy.stock <= self.low_stock_threshold
            ).all()
            
            alerts = []
            for toy in low_stock_toys:
                alert_level = "CRÍTICO" if toy.stock <= self.critical_stock_threshold else "BAJO"
                alerts.append({
                    'id': toy.id,
                    'name': toy.name,
                    'category': toy.category,
                    'current_stock': toy.stock,
                    'alert_level': alert_level,
                    'price': toy.price,
                    'last_updated': toy.updated_at or toy.created_at
                })
            
            return alerts
    
    def predict_restock_needs(self, days_ahead: int = 30) -> List[Dict]:
        """Predecir necesidades de reabastecimiento basado en ventas históricas"""
        with self.app.app_context():
            # Calcular ventas promedio de los últimos 30 días
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Obtener ventas por juguete
            sales_data = db.session.query(
                OrderItem.toy_id,
                db.func.sum(OrderItem.quantity).label('total_sold'),
                db.func.count(OrderItem.id).label('order_count')
            ).join(Order).filter(
                Order.is_active == True,
                Order.order_date >= thirty_days_ago
            ).group_by(OrderItem.toy_id).all()
            
            predictions = []
            for sale in sales_data:
                toy = Toy.query.get(sale.toy_id)
                if toy and toy.is_active:
                    # Calcular ventas promedio diarias
                    daily_avg = sale.total_sold / 30
                    predicted_demand = daily_avg * days_ahead
                    
                    # Determinar si necesita reabastecimiento
                    needs_restock = toy.stock < predicted_demand
                    
                    if needs_restock:
                        suggested_order = max(
                            int(predicted_demand - toy.stock + 10),  # Buffer de 10
                            20  # Mínimo de 20 unidades
                        )
                        
                        predictions.append({
                            'toy_id': toy.id,
                            'name': toy.name,
                            'category': toy.category,
                            'current_stock': toy.stock,
                            'daily_avg_sales': round(daily_avg, 2),
                            'predicted_demand': int(predicted_demand),
                            'suggested_order_qty': suggested_order,
                            'urgency': 'ALTA' if toy.stock < daily_avg * 7 else 'MEDIA'
                        })
            
            return sorted(predictions, key=lambda x: x['urgency'] == 'ALTA', reverse=True)
    
    def get_inventory_stats(self) -> Dict:
        """Obtener estadísticas generales del inventario"""
        with self.app.app_context():
            total_toys = Toy.query.filter_by(is_active=True).count()
            total_stock = db.session.query(db.func.sum(Toy.stock)).filter(
                Toy.is_active == True
            ).scalar() or 0
            
            low_stock_count = Toy.query.filter(
                Toy.is_active == True,
                Toy.stock <= self.low_stock_threshold
            ).count()
            
            critical_stock_count = Toy.query.filter(
                Toy.is_active == True,
                Toy.stock <= self.critical_stock_threshold
            ).count()
            
            # Valor total del inventario
            total_value = db.session.query(
                db.func.sum(Toy.stock * Toy.price)
            ).filter(Toy.is_active == True).scalar() or 0
            
            # Categorías con stock bajo
            categories_low_stock = db.session.query(
                Toy.category,
                db.func.count(Toy.id)
            ).filter(
                Toy.is_active == True,
                Toy.stock <= self.low_stock_threshold
            ).group_by(Toy.category).all()
            
            return {
                'total_products': total_toys,
                'total_stock_units': int(total_stock),
                'total_inventory_value': float(total_value),
                'low_stock_count': low_stock_count,
                'critical_stock_count': critical_stock_count,
                'categories_with_low_stock': dict(categories_low_stock),
                'stock_health': self._calculate_stock_health(total_toys, low_stock_count)
            }
    
    def _calculate_stock_health(self, total: int, low_stock: int) -> str:
        """Calcular salud general del inventario"""
        if total == 0:
            return "SIN_DATOS"
        
        percentage = (low_stock / total) * 100
        
        if percentage <= 10:
            return "EXCELENTE"
        elif percentage <= 25:
            return "BUENO"
        elif percentage <= 50:
            return "REGULAR"
        else:
            return "CRÍTICO"
    
    def send_alert_email(self, alerts: List[Dict], admin_email: str = None) -> bool:
        """Enviar alertas por email a administradores"""
        if not alerts:
            return True
            
        try:
            # Configuración de email (usar variables de entorno en producción)
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            email_user = os.getenv('EMAIL_USER')
            email_password = os.getenv('EMAIL_PASSWORD')
            
            if not email_user or not email_password:
                print("⚠️ Configuración de email no encontrada")
                return False
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = admin_email or email_user
            msg['Subject'] = f"🚨 Alerta de Inventario - Tiendita ALOHA ({len(alerts)} productos)"
            
            # Crear cuerpo del email
            body = self._create_email_body(alerts)
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            text = msg.as_string()
            server.sendmail(email_user, admin_email or email_user, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            return False
    
    def _create_email_body(self, alerts: List[Dict]) -> str:
        """Crear cuerpo HTML del email de alerta"""
        critical_alerts = [a for a in alerts if a['alert_level'] == 'CRÍTICO']
        low_alerts = [a for a in alerts if a['alert_level'] == 'BAJO']
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f44336; color: white; padding: 10px; }}
                .critical {{ background-color: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 10px 0; }}
                .low {{ background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Alerta de Inventario - Tiendita ALOHA</h2>
                <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        if critical_alerts:
            html += f"""
            <div class="critical">
                <h3>🔴 STOCK CRÍTICO ({len(critical_alerts)} productos)</h3>
                <table>
                    <tr><th>Producto</th><th>Categoría</th><th>Stock</th><th>Precio</th></tr>
            """
            for alert in critical_alerts:
                html += f"""
                    <tr>
                        <td>{alert['name']}</td>
                        <td>{alert['category']}</td>
                        <td>{alert['current_stock']}</td>
                        <td>A${alert['price']:.2f}</td>
                    </tr>
                """
            html += "</table></div>"
        
        if low_alerts:
            html += f"""
            <div class="low">
                <h3>🟡 STOCK BAJO ({len(low_alerts)} productos)</h3>
                <table>
                    <tr><th>Producto</th><th>Categoría</th><th>Stock</th><th>Precio</th></tr>
            """
            for alert in low_alerts:
                html += f"""
                    <tr>
                        <td>{alert['name']}</td>
                        <td>{alert['category']}</td>
                        <td>{alert['current_stock']}</td>
                        <td>A${alert['price']:.2f}</td>
                    </tr>
                """
            html += "</table></div>"
        
        html += """
            <p><strong>Recomendación:</strong> Revisar el inventario y considerar reabastecimiento inmediato.</p>
            <p>Este es un mensaje automático del Sistema de Inventario Inteligente.</p>
        </body>
        </html>
        """
        
        return html
    
    def generate_inventory_report(self) -> Dict:
        """Generar reporte completo de inventario"""
        alerts = self.check_low_stock()
        predictions = self.predict_restock_needs()
        stats = self.get_inventory_stats()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts,
            'predictions': predictions,
            'stats': stats,
            'summary': {
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a['alert_level'] == 'CRÍTICO']),
                'restock_recommendations': len(predictions),
                'inventory_health': stats['stock_health']
            }
        }

def main():
    """Función principal para ejecutar el sistema de inventario"""
    manager = InventoryManager()
    
    print("📦 SISTEMA DE INVENTARIO INTELIGENTE - TIENDITA ALOHA")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Generar reporte completo
    report = manager.generate_inventory_report()
    
    # Mostrar estadísticas generales
    stats = report['stats']
    print("📊 ESTADÍSTICAS GENERALES")
    print("-" * 30)
    print(f"🧸 Total de productos: {stats['total_products']}")
    print(f"📦 Total unidades en stock: {stats['total_stock_units']}")
    print(f"💰 Valor total inventario: A${stats['total_inventory_value']:.2f}")
    print(f"🔴 Productos con stock crítico: {stats['critical_stock_count']}")
    print(f"🟡 Productos con stock bajo: {stats['low_stock_count']}")
    print(f"💚 Salud del inventario: {stats['stock_health']}")
    print()
    
    # Mostrar alertas
    alerts = report['alerts']
    if alerts:
        print("🚨 ALERTAS DE STOCK")
        print("-" * 30)
        for alert in alerts:
            icon = "🔴" if alert['alert_level'] == 'CRÍTICO' else "🟡"
            print(f"{icon} {alert['name']} ({alert['category']})")
            print(f"   Stock actual: {alert['current_stock']} unidades")
            print(f"   Precio: A${alert['price']:.2f}")
            print()
    else:
        print("✅ No hay alertas de stock")
        print()
    
    # Mostrar predicciones
    predictions = report['predictions']
    if predictions:
        print("🔮 PREDICCIONES DE REABASTECIMIENTO")
        print("-" * 30)
        for pred in predictions:
            urgency_icon = "🔥" if pred['urgency'] == 'ALTA' else "⚠️"
            print(f"{urgency_icon} {pred['name']} ({pred['category']})")
            print(f"   Stock actual: {pred['current_stock']}")
            print(f"   Demanda predicha (30 días): {pred['predicted_demand']}")
            print(f"   Cantidad sugerida: {pred['suggested_order_qty']} unidades")
            print(f"   Urgencia: {pred['urgency']}")
            print()
    else:
        print("✅ No se requiere reabastecimiento inmediato")
        print()
    
    # Resumen
    summary = report['summary']
    print("📋 RESUMEN")
    print("-" * 30)
    print(f"🚨 Total alertas: {summary['total_alerts']}")
    print(f"🔴 Alertas críticas: {summary['critical_alerts']}")
    print(f"📈 Recomendaciones de restock: {summary['restock_recommendations']}")
    print(f"💚 Estado general: {summary['inventory_health']}")
    
    return report

if __name__ == "__main__":
    report = main()
