#!/usr/bin/env python3
"""
Script para probar la interfaz web de agregar balance usando Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def test_add_balance_web():
    """Prueba la funcionalidad de agregar balance en la interfaz web"""
    
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Iniciando prueba de interfaz web...")
            
            # 1. Navegar a la página de login
            print("\n1️⃣ Navegando a login...")
            await page.goto("http://127.0.0.1:5000/auth/login")
            await page.wait_for_load_state('networkidle')
            
            # 2. Llenar formulario de login
            print("2️⃣ Llenando formulario de login...")
            await page.fill('input[name="username"]', 'test')
            await page.fill('input[name="password"]', 'test123')
            
            # 3. Hacer clic en login
            print("3️⃣ Enviando login...")
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 4. Verificar que estamos logueados
            current_url = page.url
            print(f"URL actual: {current_url}")
            
            if "login" in current_url:
                print("❌ Login falló - aún en página de login")
                # Capturar errores
                error_messages = await page.locator('.flash-message, .error').all_text_contents()
                if error_messages:
                    print(f"Errores: {error_messages}")
                return False
            
            print("✅ Login exitoso!")
            
            # 5. Navegar al perfil
            print("\n4️⃣ Navegando al perfil...")
            await page.goto("http://127.0.0.1:5000/user/profile")
            await page.wait_for_load_state('networkidle')
            
            # 6. Obtener balance actual
            print("5️⃣ Obteniendo balance actual...")
            try:
                balance_element = await page.locator('.balance-amount').first
                current_balance_text = await balance_element.text_content()
                print(f"Balance actual: {current_balance_text}")
                
                # Extraer número del balance
                balance_match = re.search(r'A\$ ([\d,]+\.?\d*)', current_balance_text)
                if balance_match:
                    current_balance = float(balance_match.group(1).replace(',', ''))
                    print(f"Balance numérico: {current_balance}")
                else:
                    print("⚠️ No se pudo extraer balance numérico")
                    current_balance = 0.0
                    
            except Exception as e:
                print(f"⚠️ Error al obtener balance: {e}")
                current_balance = 0.0
            
            # 7. Hacer clic en "Agregar ALOHA Dólares"
            print("\n6️⃣ Abriendo modal de agregar balance...")
            await page.click('a.add-balance-button')
            await page.wait_for_timeout(1000)  # Esperar animación del modal
            
            # 8. Verificar que el modal está visible
            modal = page.locator('#addBalanceModal')
            is_visible = await modal.is_visible()
            
            if not is_visible:
                print("❌ Modal no está visible")
                return False
                
            print("✅ Modal abierto correctamente")
            
            # 9. Llenar cantidad
            amount_to_add = 25.50
            print(f"7️⃣ Agregando A$ {amount_to_add:.2f}...")
            await page.fill('#amount', str(amount_to_add))
            
            # 10. Enviar formulario
            print("8️⃣ Enviando formulario...")
            await page.click('#addBalanceModal button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # 11. Verificar resultado
            print("9️⃣ Verificando resultado...")
            
            # Buscar mensajes de éxito o error
            try:
                # Esperar un poco para que aparezcan los mensajes
                await page.wait_for_timeout(2000)
                
                # Verificar si hay mensajes flash
                flash_messages = await page.locator('.flash-message, .toast, .alert').all_text_contents()
                if flash_messages:
                    print(f"Mensajes: {flash_messages}")
                
                # Obtener nuevo balance
                new_balance_element = await page.locator('.balance-amount').first
                new_balance_text = await new_balance_element.text_content()
                print(f"Nuevo balance: {new_balance_text}")
                
                # Extraer número del nuevo balance
                new_balance_match = re.search(r'A\$ ([\d,]+\.?\d*)', new_balance_text)
                if new_balance_match:
                    new_balance = float(new_balance_match.group(1).replace(',', ''))
                    expected_balance = current_balance + amount_to_add
                    
                    print(f"Balance anterior: A$ {current_balance:.2f}")
                    print(f"Cantidad agregada: A$ {amount_to_add:.2f}")
                    print(f"Balance esperado: A$ {expected_balance:.2f}")
                    print(f"Balance actual: A$ {new_balance:.2f}")
                    
                    if abs(new_balance - expected_balance) < 0.01:  # Tolerancia para decimales
                        print("✅ ¡Balance actualizado correctamente!")
                        return True
                    else:
                        print("❌ El balance no se actualizó correctamente")
                        return False
                else:
                    print("❌ No se pudo extraer el nuevo balance")
                    return False
                    
            except Exception as e:
                print(f"❌ Error al verificar resultado: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Error durante la prueba: {e}")
            return False
            
        finally:
            # Tomar screenshot final
            await page.screenshot(path="test_result.png")
            print("📸 Screenshot guardado como test_result.png")
            
            # Cerrar navegador
            await browser.close()

if __name__ == "__main__":
    print("🚀 Iniciando prueba de interfaz web...")
    result = asyncio.run(test_add_balance_web())
    
    if result:
        print("\n🎉 ¡Prueba exitosa!")
        print("✅ La funcionalidad de agregar ALOHA Dólares funciona correctamente en la web")
    else:
        print("\n❌ Prueba falló")
        print("⚠️ Revisar los logs para más detalles")
