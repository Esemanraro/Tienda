#!/usr/bin/env python3
"""
Script de Pruebas de Autenticación en Vivo
==========================================

Este script prueba la autenticación de usuarios en tiempo real
usando requests para simular un navegador web.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Configuración del servidor
BASE_URL = "http://127.0.0.1:5001"

class AuthenticationTester:
    """Clase para probar autenticación en vivo"""
    
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            'tests': [],
            'success_count': 0,
            'total_tests': 0,
            'errors': []
        }
    
    def log_test(self, test_name, success, message="", details=None):
        """Registra el resultado de una prueba"""
        self.results['total_tests'] += 1
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'].append(result)
        
        if success:
            self.results['success_count'] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.results['errors'].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
        
        if details:
            print(f"   📋 Detalles: {details}")
    
    def check_server_running(self):
        """Verifica si el servidor está ejecutándose"""
        print("\n🌐 VERIFICANDO SERVIDOR")
        print("=" * 40)
        
        try:
            response = self.session.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                self.log_test("Servidor disponible", True, f"Respuesta HTTP {response.status_code}")
                return True
            else:
                self.log_test("Servidor disponible", False, f"HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Servidor disponible", False, "No se puede conectar al servidor")
            print(f"💡 Asegúrate de que el servidor esté ejecutándose en {BASE_URL}")
            return False
        except Exception as e:
            self.log_test("Servidor disponible", False, f"Error: {str(e)}")
            return False
    
    def test_login_page(self):
        """Prueba la página de login"""
        print("\n🔐 PROBANDO PÁGINA DE LOGIN")
        print("=" * 40)
        
        try:
            response = self.session.get(f"{BASE_URL}/auth/login")
            if response.status_code == 200:
                if "login" in response.text.lower() or "usuario" in response.text.lower():
                    self.log_test("Página de login", True, "Página carga correctamente")
                else:
                    self.log_test("Página de login", False, "Página no contiene formulario de login")
            else:
                self.log_test("Página de login", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Página de login", False, f"Error: {str(e)}")
    
    def test_user_login(self, username, password, center):
        """Prueba el login de un usuario específico"""
        print(f"\n🔑 PROBANDO LOGIN: {username}")
        print("=" * 40)
        
        try:
            # Primero obtener la página de login para el CSRF token
            login_page = self.session.get(f"{BASE_URL}/auth/login")
            
            # Intentar extraer CSRF token (simplificado)
            csrf_token = None
            if 'csrf_token' in login_page.text:
                # Buscar el token CSRF en el HTML
                import re
                csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
            
            # Datos de login
            login_data = {
                'username': username,
                'password': password
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # Intentar login
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                data=login_data,
                allow_redirects=False
            )
            
            if response.status_code == 302:  # Redirección exitosa
                self.log_test(f"Login {username}", True, 
                            f"Login exitoso - Centro: {center}")
                
                # Verificar que podemos acceder a una página protegida
                profile_response = self.session.get(f"{BASE_URL}/user/profile")
                if profile_response.status_code == 200:
                    self.log_test(f"Acceso perfil {username}", True, 
                                "Puede acceder a páginas protegidas")
                else:
                    self.log_test(f"Acceso perfil {username}", False, 
                                "No puede acceder a páginas protegidas")
                
                return True
                
            elif response.status_code == 200:  # Página de login con error
                if "error" in response.text.lower() or "incorrecto" in response.text.lower():
                    self.log_test(f"Login {username}", False, "Credenciales incorrectas")
                else:
                    self.log_test(f"Login {username}", False, "Error en formulario")
                return False
            else:
                self.log_test(f"Login {username}", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(f"Login {username}", False, f"Error: {str(e)}")
            return False
    
    def test_logout(self, username):
        """Prueba el logout"""
        print(f"\n🚪 PROBANDO LOGOUT: {username}")
        print("=" * 40)
        
        try:
            response = self.session.get(f"{BASE_URL}/auth/logout", allow_redirects=False)
            
            if response.status_code == 302:  # Redirección exitosa
                self.log_test(f"Logout {username}", True, "Logout exitoso")
                return True
            else:
                self.log_test(f"Logout {username}", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(f"Logout {username}", False, f"Error: {str(e)}")
            return False
    
    def test_admin_access(self, username):
        """Prueba el acceso de administrador"""
        print(f"\n👑 PROBANDO ACCESO ADMIN: {username}")
        print("=" * 40)
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/")
            
            if response.status_code == 200:
                if "dashboard" in response.text.lower() or "administr" in response.text.lower():
                    self.log_test(f"Acceso admin {username}", True, 
                                "Puede acceder al dashboard de administrador")
                else:
                    self.log_test(f"Acceso admin {username}", False, 
                                "Página no parece ser dashboard de admin")
            elif response.status_code == 403:
                self.log_test(f"Acceso admin {username}", False, 
                            "Acceso denegado - no es administrador")
            elif response.status_code == 302:
                # Verificar si la redirección es por falta de permisos o por logout
                location = response.headers.get('Location', '')
                if 'login' in location:
                    self.log_test(f"Acceso admin {username}", False, 
                                "Redirección a login - sesión expirada")
                else:
                    self.log_test(f"Acceso admin {username}", False, 
                                "Redirección - posiblemente no autorizado")
            else:
                self.log_test(f"Acceso admin {username}", False, 
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test(f"Acceso admin {username}", False, f"Error: {str(e)}")
    
    def test_protected_route_access(self, username):
        """Prueba el acceso a rutas protegidas después del logout"""
        print(f"\n🔒 PROBANDO PROTECCIÓN POST-LOGOUT: {username}")
        print("=" * 40)
        
        try:
            # Probar varias rutas protegidas
            protected_routes = [
                '/user/profile',
                '/user/add_balance',
                '/admin/',
                '/shop/cart'
            ]
            
            protected_count = 0
            for route in protected_routes:
                response = self.session.get(f"{BASE_URL}{route}", allow_redirects=False)
                if response.status_code == 302:  # Redirección a login
                    location = response.headers.get('Location', '')
                    if 'login' in location:
                        protected_count += 1
            
            if protected_count >= len(protected_routes) * 0.75:  # Al menos 75% protegidas
                self.log_test(f"Protección post-logout", True, 
                            f"{protected_count}/{len(protected_routes)} rutas protegidas")
            else:
                self.log_test(f"Protección post-logout", False, 
                            f"Solo {protected_count}/{len(protected_routes)} rutas protegidas")
                
        except Exception as e:
            self.log_test(f"Protección post-logout", False, f"Error: {str(e)}")
    
    def test_registration_page(self):
        """Prueba la página de registro"""
        print("\n📝 PROBANDO PÁGINA DE REGISTRO")
        print("=" * 40)
        
        try:
            response = self.session.get(f"{BASE_URL}/auth/register")
            if response.status_code == 200:
                if "registro" in response.text.lower() or "register" in response.text.lower():
                    self.log_test("Página de registro", True, "Página carga correctamente")
                    
                    # Verificar que tiene campo de centro
                    if "centro" in response.text.lower() or "center" in response.text.lower():
                        self.log_test("Campo centro en registro", True, 
                                    "Formulario incluye selección de centro")
                    else:
                        self.log_test("Campo centro en registro", False, 
                                    "Formulario no incluye selección de centro")
                else:
                    self.log_test("Página de registro", False, 
                                "Página no contiene formulario de registro")
            else:
                self.log_test("Página de registro", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Página de registro", False, f"Error: {str(e)}")
    
    def run_full_test(self):
        """Ejecuta todas las pruebas de autenticación"""
        print("🚀 INICIANDO PRUEBAS DE AUTENTICACIÓN EN VIVO")
        print("=" * 60)
        print(f"Servidor: {BASE_URL}")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verificar servidor
        if not self.check_server_running():
            print("\n❌ No se puede continuar sin servidor activo")
            return
        
        # Probar páginas básicas
        self.test_login_page()
        self.test_registration_page()
        
        # Usuarios de prueba por centro
        test_users = [
            {'username': 'admin', 'password': 'admin123', 'center': 'David', 'is_admin': True},
            {'username': 'admin_ana', 'password': 'ana123', 'center': 'Ana', 'is_admin': True},
            {'username': 'admin_carlos', 'password': 'carlos123', 'center': 'Carlos', 'is_admin': True},
            {'username': 'admin_maria', 'password': 'maria123', 'center': 'María', 'is_admin': True},
            {'username': 'user_david1', 'password': 'user123', 'center': 'David', 'is_admin': False},
            {'username': 'user_ana1', 'password': 'user123', 'center': 'Ana', 'is_admin': False}
        ]
        
        # Probar login/logout para cada usuario
        for user in test_users:
            # Nueva sesión para cada usuario
            self.session = requests.Session()
            
            # Probar login
            if self.test_user_login(user['username'], user['password'], user['center']):
                # Si es admin, probar acceso de administrador
                if user['is_admin']:
                    self.test_admin_access(user['username'])
                
                # Probar logout
                self.test_logout(user['username'])
                self.test_protected_route_access(user['username'])
        
        # Generar reporte
        self.generate_report()
    
    def generate_report(self):
        """Genera reporte de pruebas"""
        print("\n📊 REPORTE DE PRUEBAS DE AUTENTICACIÓN")
        print("=" * 50)
        
        success_rate = (self.results['success_count'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        
        print(f"✅ Pruebas exitosas: {self.results['success_count']}/{self.results['total_tests']} ({success_rate:.1f}%)")
        print(f"❌ Errores encontrados: {len(self.results['errors'])}")
        
        # Guardar reporte
        report_file = 'authentication_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        
        if success_rate >= 90:
            print("🎉 Autenticación funcionando excelentemente")
        elif success_rate >= 75:
            print("✅ Autenticación funcional con mejoras menores")
        else:
            print("🚨 Autenticación requiere atención")

def main():
    """Función principal"""
    tester = AuthenticationTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
