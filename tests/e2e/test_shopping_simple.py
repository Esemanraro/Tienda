#!/usr/bin/env python3
"""
Script de pruebas simplificado para el flujo de compras
Basado en el script de diagnóstico que funciona correctamente
"""

import requests
import sqlite3
from urllib.parse import urljoin
import re
from datetime import datetime

class SimpleShoppingTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5001"
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Registra el resultado de una prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"{status} - {test_name} ({timestamp})"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': timestamp
        })
        
    def login_user(self, username, password):
        """Login simplificado basado en el script que funciona"""
        try:
            login_url = urljoin(self.base_url, "/auth/login")
            
            # Obtener página de login
            login_page = self.session.get(login_url)
            if login_page.status_code != 200:
                self.log_result(f"Login {username}", False, f"No se pudo acceder a login: {login_page.status_code}")
                return False
            
            # Extraer CSRF token
            meta_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', login_page.text)
            if not meta_match:
                self.log_result(f"Login {username}", False, "No se pudo obtener token CSRF")
                return False
            
            csrf_token = meta_match.group(1)
            
            # Hacer login
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token
            }
            
            login_response = self.session.post(login_url, data=login_data)
            if login_response.status_code in [200, 302]:
                self.log_result(f"Login {username}", True, "Autenticación exitosa")
                return True
            else:
                self.log_result(f"Login {username}", False, f"Error en login: {login_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result(f"Login {username}", False, f"Excepción: {e}")
            return False
    
    def test_add_to_cart(self):
        """Prueba agregar producto al carrito"""
        try:
            # Obtener un producto de la base de datos
            conn = sqlite3.connect('tiendita.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM toy WHERE is_active = 1 AND stock > 0 LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                self.log_result("Agregar al carrito", False, "No hay productos disponibles")
                return False
            
            toy_id, toy_name = result
            
            # Obtener token CSRF
            home_page = self.session.get(self.base_url)
            csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', home_page.text)
            if not csrf_match:
                self.log_result("Agregar al carrito", False, "No se pudo obtener token CSRF")
                return False
            
            csrf_token = csrf_match.group(1)
            
            # Agregar al carrito
            add_cart_url = urljoin(self.base_url, "/add_to_cart")
            cart_data = {
                'toy_id': str(toy_id),
                'quantity': '1',
                'csrf_token': csrf_token
            }
            
            response = self.session.post(add_cart_url, data=cart_data)
            if response.status_code in [200, 302]:
                self.log_result("Agregar al carrito", True, f"Producto '{toy_name}' agregado")
                return True
            else:
                self.log_result("Agregar al carrito", False, f"Error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Agregar al carrito", False, f"Excepción: {e}")
            return False
    
    def test_view_cart(self):
        """Prueba visualizar el carrito"""
        try:
            cart_url = urljoin(self.base_url, "/cart")
            response = self.session.get(cart_url)
            
            if response.status_code == 200:
                if len(response.text) > 1000:  # Página tiene contenido sustancial
                    self.log_result("Visualizar carrito", True, "Carrito accesible")
                    return True
                else:
                    self.log_result("Visualizar carrito", False, "Página muy pequeña")
                    return False
            else:
                self.log_result("Visualizar carrito", False, f"Error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Visualizar carrito", False, f"Excepción: {e}")
            return False
    
    def test_checkout(self):
        """Prueba el proceso de checkout"""
        try:
            # Obtener token CSRF del carrito
            cart_url = urljoin(self.base_url, "/cart")
            cart_page = self.session.get(cart_url)
            
            if cart_page.status_code != 200:
                self.log_result("Checkout", False, "No se pudo acceder al carrito")
                return False
            
            csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', cart_page.text)
            if not csrf_match:
                self.log_result("Checkout", False, "No se pudo obtener token CSRF")
                return False
            
            csrf_token = csrf_match.group(1)
            
            # Realizar checkout
            checkout_url = urljoin(self.base_url, "/checkout")
            checkout_data = {
                'csrf_token': csrf_token
            }
            
            response = self.session.post(checkout_url, data=checkout_data)
            if response.status_code in [200, 302]:
                self.log_result("Checkout", True, "Proceso completado")
                return True
            else:
                self.log_result("Checkout", False, f"Error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Checkout", False, f"Excepción: {e}")
            return False
    
    def run_complete_test(self):
        """Ejecuta una prueba completa del flujo de compras"""
        print("🛒 PRUEBA SIMPLIFICADA DEL FLUJO DE COMPRAS")
        print("=" * 60)
        
        # Verificar servidor
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                self.log_result("Servidor disponible", True)
            else:
                self.log_result("Servidor disponible", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_result("Servidor disponible", False, f"Error: {e}")
            return
        
        # Login
        if not self.login_user('user_ana1', 'password123'):
            print("❌ No se pudo hacer login, abortando pruebas")
            return
        
        # Pruebas del carrito
        self.test_add_to_cart()
        self.test_view_cart()
        self.test_checkout()
        
        # Resumen
        print(f"\n📊 RESUMEN DE PRUEBAS")
        print("=" * 30)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"🎯 Total: {total_tests}")
        print(f"✅ Exitosas: {passed_tests}")
        print(f"❌ Fallidas: {failed_tests}")
        print(f"📈 Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ PRUEBAS FALLIDAS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")

if __name__ == "__main__":
    tester = SimpleShoppingTest()
    tester.run_complete_test()
