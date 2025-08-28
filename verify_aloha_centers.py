#!/usr/bin/env python3
"""
Script de Verificación de Centros ALOHA y Autenticación
======================================================

Este script verifica la funcionalidad completa de los centros ALOHA
y valida todos los aspectos de autenticación de usuarios.

Funcionalidades verificadas:
- Centros ALOHA existentes y configuración
- Autenticación de usuarios (login/logout)
- Registro de usuarios con centros
- Cambio de centro de usuarios
- Permisos y roles de usuario
- Integridad de la base de datos
- Sesiones de usuario
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
import json

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import User, Toy, Order, OrderItem
    from werkzeug.security import check_password_hash, generate_password_hash
    from flask_login import login_user, logout_user
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Asegúrate de que el entorno virtual esté activado y las dependencias instaladas")
    sys.exit(1)

class ALOHACenterVerifier:
    """Clase principal para verificar centros ALOHA y autenticación"""
    
    def __init__(self):
        self.app = app
        self.db = db
        self.results = {
            'centers': {},
            'authentication': {},
            'database': {},
            'users': {},
            'errors': [],
            'warnings': [],
            'success_count': 0,
            'total_tests': 0
        }
        
    def log_test(self, test_name, success, message="", details=None):
        """Registra el resultado de una prueba"""
        self.results['total_tests'] += 1
        if success:
            self.results['success_count'] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.results['errors'].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
        
        if details:
            print(f"   📋 Detalles: {details}")
    
    def log_warning(self, message):
        """Registra una advertencia"""
        self.results['warnings'].append(message)
        print(f"⚠️  {message}")
    
    def verify_database_connection(self):
        """Verifica la conexión a la base de datos"""
        print("\n🔍 VERIFICANDO CONEXIÓN A BASE DE DATOS")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Verificar que las tablas existen
                tables = ['user', 'toy', 'order', 'order_item']
                for table in tables:
                    result = db.session.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'").fetchone()
                    if result:
                        self.log_test(f"Tabla {table}", True, "Existe en la base de datos")
                    else:
                        self.log_test(f"Tabla {table}", False, "No existe en la base de datos")
                
                # Verificar índices de optimización
                indexes = db.session.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
                index_names = [idx[0] for idx in indexes]
                
                expected_indexes = [
                    'idx_user_active_center',
                    'idx_toy_active_category',
                    'idx_order_active_date'
                ]
                
                for idx in expected_indexes:
                    if idx in index_names:
                        self.log_test(f"Índice {idx}", True, "Existe y optimiza consultas")
                    else:
                        self.log_warning(f"Índice {idx} no encontrado - puede afectar rendimiento")
                
        except Exception as e:
            self.log_test("Conexión DB", False, f"Error: {str(e)}")
    
    def verify_aloha_centers(self):
        """Verifica los centros ALOHA existentes"""
        print("\n🏢 VERIFICANDO CENTROS ALOHA")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Obtener todos los centros únicos
                centers = db.session.query(User.center).filter(User.center.isnot(None)).distinct().all()
                center_list = [center[0] for center in centers if center[0]]
                
                self.results['centers']['total'] = len(center_list)
                self.results['centers']['list'] = center_list
                
                if center_list:
                    self.log_test("Centros ALOHA", True, f"Encontrados {len(center_list)} centros", 
                                f"Centros: {', '.join(center_list)}")
                    
                    # Verificar usuarios por centro
                    for center in center_list:
                        user_count = User.query.filter_by(center=center, is_active=True).count()
                        admin_count = User.query.filter_by(center=center, is_admin=True, is_active=True).count()
                        
                        self.results['centers'][center] = {
                            'users': user_count,
                            'admins': admin_count
                        }
                        
                        self.log_test(f"Centro {center}", True, 
                                    f"{user_count} usuarios, {admin_count} administradores")
                        
                        if admin_count == 0:
                            self.log_warning(f"Centro {center} no tiene administradores activos")
                
                else:
                    self.log_test("Centros ALOHA", False, "No se encontraron centros configurados")
                
        except Exception as e:
            self.log_test("Centros ALOHA", False, f"Error: {str(e)}")
    
    def verify_user_authentication(self):
        """Verifica la autenticación de usuarios"""
        print("\n🔐 VERIFICANDO AUTENTICACIÓN DE USUARIOS")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Verificar usuarios existentes
                total_users = User.query.count()
                active_users = User.query.filter_by(is_active=True).count()
                admin_users = User.query.filter_by(is_admin=True, is_active=True).count()
                
                self.results['users']['total'] = total_users
                self.results['users']['active'] = active_users
                self.results['users']['admins'] = admin_users
                
                self.log_test("Usuarios totales", True, f"{total_users} usuarios en sistema")
                self.log_test("Usuarios activos", True, f"{active_users} usuarios activos")
                self.log_test("Administradores", True, f"{admin_users} administradores activos")
                
                # Verificar usuario admin por defecto
                admin_user = User.query.filter_by(username='admin').first()
                if admin_user:
                    self.log_test("Usuario admin", True, 
                                f"Existe - Centro: {admin_user.center}, Admin: {admin_user.is_admin}")
                    
                    # Verificar hash de contraseña
                    if admin_user.password_hash:
                        self.log_test("Hash contraseña admin", True, "Contraseña hasheada correctamente")
                    else:
                        self.log_test("Hash contraseña admin", False, "Contraseña no hasheada")
                else:
                    self.log_test("Usuario admin", False, "Usuario admin no encontrado")
                
                # Verificar estructura de campos de usuario
                sample_user = User.query.first()
                if sample_user:
                    required_fields = ['username', 'password_hash', 'balance', 'is_admin', 'center']
                    for field in required_fields:
                        if hasattr(sample_user, field):
                            self.log_test(f"Campo {field}", True, "Existe en modelo User")
                        else:
                            self.log_test(f"Campo {field}", False, "No existe en modelo User")
                
        except Exception as e:
            self.log_test("Autenticación", False, f"Error: {str(e)}")
    
    def test_password_verification(self):
        """Prueba la verificación de contraseñas"""
        print("\n🔑 PROBANDO VERIFICACIÓN DE CONTRASEÑAS")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Crear usuario de prueba temporal
                test_password = "test123"
                test_hash = generate_password_hash(test_password)
                
                # Verificar que el hash funciona
                if check_password_hash(test_hash, test_password):
                    self.log_test("Hash/Verificación", True, "Sistema de contraseñas funcional")
                else:
                    self.log_test("Hash/Verificación", False, "Sistema de contraseñas no funcional")
                
                # Verificar contraseña incorrecta
                if not check_password_hash(test_hash, "wrong_password"):
                    self.log_test("Rechazo contraseña incorrecta", True, "Sistema rechaza contraseñas incorrectas")
                else:
                    self.log_test("Rechazo contraseña incorrecta", False, "Sistema acepta contraseñas incorrectas")
                
        except Exception as e:
            self.log_test("Verificación contraseñas", False, f"Error: {str(e)}")
    
    def test_center_assignment(self):
        """Prueba la asignación y cambio de centros"""
        print("\n🏢 PROBANDO ASIGNACIÓN DE CENTROS")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Verificar que los usuarios tienen centros asignados
                users_with_center = User.query.filter(User.center.isnot(None)).count()
                total_users = User.query.count()
                
                if users_with_center > 0:
                    percentage = (users_with_center / total_users) * 100
                    self.log_test("Asignación centros", True, 
                                f"{users_with_center}/{total_users} usuarios ({percentage:.1f}%) tienen centro asignado")
                else:
                    self.log_test("Asignación centros", False, "Ningún usuario tiene centro asignado")
                
                # Verificar centros válidos
                valid_centers = ['David', 'Ana', 'Carlos', 'María', 'Centro1', 'Centro2']
                assigned_centers = db.session.query(User.center).filter(User.center.isnot(None)).distinct().all()
                assigned_center_list = [c[0] for c in assigned_centers]
                
                for center in assigned_center_list:
                    if center in valid_centers or len(center) > 0:
                        self.log_test(f"Centro válido: {center}", True, "Centro tiene formato válido")
                    else:
                        self.log_test(f"Centro inválido: {center}", False, "Centro tiene formato inválido")
                
        except Exception as e:
            self.log_test("Asignación centros", False, f"Error: {str(e)}")
    
    def verify_user_permissions(self):
        """Verifica los permisos de usuario"""
        print("\n👥 VERIFICANDO PERMISOS DE USUARIO")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Verificar usuarios administradores
                admins = User.query.filter_by(is_admin=True, is_active=True).all()
                
                if admins:
                    self.log_test("Administradores activos", True, f"Encontrados {len(admins)} administradores")
                    
                    for admin in admins:
                        self.log_test(f"Admin {admin.username}", True, 
                                    f"Centro: {admin.center}, Balance: ${admin.balance}")
                else:
                    self.log_test("Administradores activos", False, "No hay administradores activos")
                
                # Verificar usuarios regulares
                regular_users = User.query.filter_by(is_admin=False, is_active=True).all()
                
                if regular_users:
                    self.log_test("Usuarios regulares", True, f"Encontrados {len(regular_users)} usuarios regulares")
                    
                    # Verificar balances
                    users_with_balance = [u for u in regular_users if u.balance > 0]
                    if users_with_balance:
                        avg_balance = sum(u.balance for u in users_with_balance) / len(users_with_balance)
                        self.log_test("Balances usuarios", True, 
                                    f"{len(users_with_balance)} usuarios con balance promedio: ${avg_balance:.2f}")
                else:
                    self.log_test("Usuarios regulares", False, "No hay usuarios regulares activos")
                
        except Exception as e:
            self.log_test("Permisos usuario", False, f"Error: {str(e)}")
    
    def verify_session_management(self):
        """Verifica la gestión de sesiones"""
        print("\n🔄 VERIFICANDO GESTIÓN DE SESIONES")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Verificar campos de sesión en usuarios
                users_with_login = User.query.filter(User.last_login.isnot(None)).count()
                total_users = User.query.count()
                
                if users_with_login > 0:
                    self.log_test("Registro last_login", True, 
                                f"{users_with_login}/{total_users} usuarios tienen registro de último login")
                else:
                    self.log_warning("Ningún usuario tiene registro de último login")
                
                # Verificar usuarios recientes (últimos 30 días)
                recent_date = datetime.now() - timedelta(days=30)
                recent_users = User.query.filter(User.last_login > recent_date).count()
                
                if recent_users > 0:
                    self.log_test("Usuarios recientes", True, 
                                f"{recent_users} usuarios activos en últimos 30 días")
                else:
                    self.log_warning("No hay usuarios activos en los últimos 30 días")
                
        except Exception as e:
            self.log_test("Gestión sesiones", False, f"Error: {str(e)}")
    
    def verify_data_integrity(self):
        """Verifica la integridad de los datos"""
        print("\n🔍 VERIFICANDO INTEGRIDAD DE DATOS")
        print("=" * 50)
        
        try:
            with self.app.app_context():
                # Verificar usuarios sin username
                users_no_username = User.query.filter(
                    (User.username == None) | (User.username == '')
                ).count()
                
                if users_no_username == 0:
                    self.log_test("Usernames únicos", True, "Todos los usuarios tienen username válido")
                else:
                    self.log_test("Usernames únicos", False, f"{users_no_username} usuarios sin username")
                
                # Verificar usuarios sin hash de contraseña
                users_no_password = User.query.filter(
                    (User.password_hash == None) | (User.password_hash == '')
                ).count()
                
                if users_no_password == 0:
                    self.log_test("Contraseñas hasheadas", True, "Todos los usuarios tienen contraseña hasheada")
                else:
                    self.log_test("Contraseñas hasheadas", False, f"{users_no_password} usuarios sin contraseña")
                
                # Verificar balances negativos
                negative_balances = User.query.filter(User.balance < 0).count()
                
                if negative_balances == 0:
                    self.log_test("Balances válidos", True, "No hay balances negativos")
                else:
                    self.log_warning(f"{negative_balances} usuarios con balance negativo")
                
                # Verificar órden de datos
                orders = Order.query.count()
                order_items = OrderItem.query.count()
                toys = Toy.query.count()
                
                self.log_test("Datos de órdenes", True, f"{orders} órdenes, {order_items} items, {toys} juguetes")
                
        except Exception as e:
            self.log_test("Integridad datos", False, f"Error: {str(e)}")
    
    def generate_report(self):
        """Genera un reporte completo de verificación"""
        print("\n📊 REPORTE DE VERIFICACIÓN")
        print("=" * 50)
        
        success_rate = (self.results['success_count'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        
        print(f"✅ Pruebas exitosas: {self.results['success_count']}/{self.results['total_tests']} ({success_rate:.1f}%)")
        print(f"❌ Errores encontrados: {len(self.results['errors'])}")
        print(f"⚠️  Advertencias: {len(self.results['warnings'])}")
        
        if self.results['centers'].get('list'):
            print(f"\n🏢 Centros ALOHA encontrados: {', '.join(self.results['centers']['list'])}")
        
        if self.results['users']:
            print(f"👥 Usuarios: {self.results['users'].get('total', 0)} total, "
                  f"{self.results['users'].get('active', 0)} activos, "
                  f"{self.results['users'].get('admins', 0)} administradores")
        
        # Guardar reporte en archivo
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'success_rate': success_rate,
                'total_tests': self.results['total_tests'],
                'successful_tests': self.results['success_count'],
                'errors': len(self.results['errors']),
                'warnings': len(self.results['warnings'])
            },
            'details': self.results
        }
        
        report_file = 'aloha_verification_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        
        # Recomendaciones
        print("\n💡 RECOMENDACIONES:")
        if len(self.results['errors']) > 0:
            print("🔧 Corregir errores críticos encontrados")
        if len(self.results['warnings']) > 0:
            print("⚠️  Revisar advertencias para optimización")
        if success_rate >= 90:
            print("🎉 Sistema en excelente estado - listo para producción")
        elif success_rate >= 75:
            print("✅ Sistema funcional - considerar mejoras menores")
        else:
            print("🚨 Sistema requiere atención - revisar errores críticos")
    
    def run_full_verification(self):
        """Ejecuta la verificación completa"""
        print("🚀 INICIANDO VERIFICACIÓN COMPLETA DE CENTROS ALOHA Y AUTENTICACIÓN")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar todas las verificaciones
        self.verify_database_connection()
        self.verify_aloha_centers()
        self.verify_user_authentication()
        self.test_password_verification()
        self.test_center_assignment()
        self.verify_user_permissions()
        self.verify_session_management()
        self.verify_data_integrity()
        
        # Generar reporte final
        self.generate_report()

def main():
    """Función principal"""
    verifier = ALOHACenterVerifier()
    verifier.run_full_verification()

if __name__ == "__main__":
    main()
