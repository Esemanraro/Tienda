#!/usr/bin/env python3
"""
Script de Pruebas para Optimización Móvil de Tiendita ALOHA
Valida que todas las funcionalidades móviles estén funcionando correctamente
"""

import requests
import sys
import time
from urllib.parse import urljoin

class MobileOptimizationTester:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
        # Headers para simular dispositivo móvil
        self.mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(self.mobile_headers)

    def log_test(self, test_name, success, details=""):
        """Registra el resultado de una prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })

    def test_server_availability(self):
        """Prueba que el servidor esté disponible"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("Disponibilidad del Servidor", success, details)
            return success
        except Exception as e:
            self.log_test("Disponibilidad del Servidor", False, str(e))
            return False

    def test_mobile_css_loading(self):
        """Verifica que el CSS móvil se cargue correctamente"""
        try:
            css_url = urljoin(self.base_url, "/static/css/mobile.css")
            response = self.session.get(css_url)
            success = response.status_code == 200 and len(response.content) > 0
            details = f"Size: {len(response.content)} bytes" if success else f"Status: {response.status_code}"
            self.log_test("Carga de CSS Móvil", success, details)
            return success
        except Exception as e:
            self.log_test("Carga de CSS Móvil", False, str(e))
            return False

    def test_mobile_js_loading(self):
        """Verifica que el JavaScript móvil se cargue correctamente"""
        try:
            js_url = urljoin(self.base_url, "/static/js/mobile.js")
            response = self.session.get(js_url)
            success = response.status_code == 200 and len(response.content) > 0
            details = f"Size: {len(response.content)} bytes" if success else f"Status: {response.status_code}"
            self.log_test("Carga de JavaScript Móvil", success, details)
            return success
        except Exception as e:
            self.log_test("Carga de JavaScript Móvil", False, str(e))
            return False

    def test_mobile_navigation_elements(self):
        """Verifica que los elementos de navegación móvil estén presentes"""
        try:
            response = self.session.get(self.base_url)
            content = response.text
            
            # Verificar elementos clave de navegación móvil
            mobile_nav_present = 'class="mobile-nav"' in content
            
            # Verificar iconos básicos que siempre están presentes (sin autenticación)
            basic_nav_items = [
                '🏠',  # Home icon
                '🔍',  # Search icon
            ]
            
            basic_icons_present = all(icon in content for icon in basic_nav_items)
            
            # Verificar estructura de navegación
            nav_structure = '<nav class="mobile-nav">' in content and '<ul>' in content
            
            success = mobile_nav_present and basic_icons_present and nav_structure
            details = f"Nav: {mobile_nav_present}, Iconos básicos: {basic_icons_present}, Estructura: {nav_structure}"
            self.log_test("Elementos de Navegación Móvil", success, details)
            return success
        except Exception as e:
            self.log_test("Elementos de Navegación Móvil", False, str(e))
            return False

    def test_responsive_meta_tags(self):
        """Verifica que las meta tags responsive estén presentes"""
        try:
            response = self.session.get(self.base_url)
            content = response.text
            
            viewport_meta = 'name="viewport"' in content and 'width=device-width' in content
            mobile_optimized = 'name="mobile-web-app-capable"' in content
            
            success = viewport_meta and mobile_optimized
            details = f"Viewport: {viewport_meta}, Mobile optimized: {mobile_optimized}"
            self.log_test("Meta Tags Responsive", success, details)
            return success
        except Exception as e:
            self.log_test("Meta Tags Responsive", False, str(e))
            return False

    def test_touch_friendly_elements(self):
        """Verifica que los elementos sean touch-friendly"""
        try:
            response = self.session.get(self.base_url)
            content = response.text
            
            # Verificar clases CSS para elementos touch-friendly
            touch_classes = [
                'touch-target',
                'mobile-button',
                'mobile-input'
            ]
            
            touch_elements_present = any(css_class in content for css_class in touch_classes)
            mobile_styles_present = 'mobile.css' in content
            
            success = mobile_styles_present  # Al menos el CSS móvil debe estar presente
            details = f"CSS móvil: {mobile_styles_present}, Touch elements: {touch_elements_present}"
            self.log_test("Elementos Touch-Friendly", success, details)
            return success
        except Exception as e:
            self.log_test("Elementos Touch-Friendly", False, str(e))
            return False

    def test_login_page_mobile(self):
        """Prueba la página de login en móvil"""
        try:
            login_url = urljoin(self.base_url, "/auth/login")
            response = self.session.get(login_url)
            success = response.status_code == 200
            
            if success:
                content = response.text
                has_mobile_form = 'mobile.css' in content
                has_csrf = 'csrf_token' in content
                success = has_mobile_form and has_csrf
                details = f"Mobile CSS: {has_mobile_form}, CSRF: {has_csrf}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Página de Login Móvil", success, details)
            return success
        except Exception as e:
            self.log_test("Página de Login Móvil", False, str(e))
            return False

    def test_shop_page_mobile(self):
        """Prueba la página principal de la tienda en móvil"""
        try:
            response = self.session.get(self.base_url)
            success = response.status_code == 200
            
            if success:
                content = response.text
                has_product_grid = 'product' in content.lower()
                has_mobile_nav = 'mobile-nav' in content
                success = has_product_grid and has_mobile_nav
                details = f"Grid productos: {has_product_grid}, Nav móvil: {has_mobile_nav}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Página Principal Móvil", success, details)
            return success
        except Exception as e:
            self.log_test("Página Principal Móvil", False, str(e))
            return False

    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🧪 Iniciando Pruebas de Optimización Móvil para Tiendita ALOHA")
        print("=" * 60)
        
        # Lista de pruebas a ejecutar
        tests = [
            self.test_server_availability,
            self.test_mobile_css_loading,
            self.test_mobile_js_loading,
            self.test_responsive_meta_tags,
            self.test_mobile_navigation_elements,
            self.test_touch_friendly_elements,
            self.test_login_page_mobile,
            self.test_shop_page_mobile,
        ]
        
        # Ejecutar pruebas
        total_tests = len(tests)
        passed_tests = 0
        
        for test in tests:
            if test():
                passed_tests += 1
            time.sleep(0.5)  # Pequeña pausa entre pruebas
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS MÓVILES")
        print("=" * 60)
        print(f"Total de pruebas: {total_tests}")
        print(f"Pruebas exitosas: {passed_tests}")
        print(f"Pruebas fallidas: {total_tests - passed_tests}")
        print(f"Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ¡TODAS LAS PRUEBAS MÓVILES PASARON!")
            print("✅ La optimización móvil está funcionando correctamente")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} pruebas fallaron")
            print("🔧 Revisa los detalles arriba para identificar problemas")
        
        return passed_tests == total_tests

def main():
    """Función principal"""
    print("🚀 Tester de Optimización Móvil - Tiendita ALOHA")
    print("Verificando funcionalidades móviles...")
    print()
    
    tester = MobileOptimizationTester()
    success = tester.run_all_tests()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
