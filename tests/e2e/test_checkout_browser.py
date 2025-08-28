#!/usr/bin/env python3
"""
Test de checkout usando un navegador real con Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import time

BASE_URL = "http://127.0.0.1:5003"

async def test_checkout_with_browser():
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔍 TEST DE CHECKOUT CON NAVEGADOR\n")
        
        try:
            # 1. Ir a la página de login
            print("1. Navegando a login...")
            await page.goto(f"{BASE_URL}/auth/login")
            await page.wait_for_load_state('networkidle')
            
            # 2. Hacer login
            print("2. Haciendo login...")
            await page.fill('input[name="username"]', 'admin')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            print(f"   URL después de login: {page.url}")
            
            # 3. Ir a la tienda
            print("\n3. Navegando a la tienda...")
            await page.goto(f"{BASE_URL}/index")
            await page.wait_for_load_state('networkidle')
            
            # 4. Agregar un item al carrito
            print("4. Agregando item al carrito...")
            # Buscar el primer botón de agregar al carrito
            add_buttons = await page.query_selector_all('button:has-text("Agregar al Carrito")')
            if add_buttons:
                await add_buttons[0].click()
                await page.wait_for_timeout(1000)  # Esperar un segundo
                print("   ✅ Item agregado")
            else:
                print("   ❌ No se encontraron botones de agregar al carrito")
            
            # 5. Ir al carrito
            print("\n5. Navegando al carrito...")
            await page.goto(f"{BASE_URL}/cart")
            await page.wait_for_load_state('networkidle')
            
            # Verificar contenido del carrito
            cart_items = await page.query_selector_all('.cart-item')
            print(f"   Items en carrito: {len(cart_items)}")
            
            # 6. Ir a checkout
            print("\n6. Navegando a checkout...")
            await page.goto(f"{BASE_URL}/checkout")
            await page.wait_for_load_state('networkidle')
            
            # Verificar si estamos en checkout o fuimos redirigidos
            current_url = page.url
            print(f"   URL actual: {current_url}")
            
            # Buscar el formulario de checkout
            checkout_form = await page.query_selector('form[action*="checkout"]')
            if checkout_form:
                print("   ✅ Formulario de checkout encontrado")
                
                # Buscar el botón de confirmar
                confirm_button = await page.query_selector('button:has-text("Confirmar Compra")')
                if confirm_button:
                    print("   ✅ Botón de confirmar compra encontrado")
                    
                    # 7. Intentar confirmar la compra
                    print("\n7. Confirmando compra...")
                    await confirm_button.click()
                    await page.wait_for_load_state('networkidle')
                    
                    # Verificar resultado
                    final_url = page.url
                    print(f"   URL final: {final_url}")
                    
                    # Buscar mensajes
                    messages = await page.query_selector_all('.flash-message, .alert')
                    if messages:
                        print("   Mensajes encontrados:")
                        for msg in messages:
                            text = await msg.text_content()
                            print(f"      - {text.strip()}")
                else:
                    print("   ❌ Botón de confirmar compra NO encontrado")
            else:
                print("   ❌ Formulario de checkout NO encontrado")
                
                # Verificar si hay mensaje de error
                error_msgs = await page.query_selector_all('.flash-message.error, .alert-error')
                if error_msgs:
                    print("   ⚠️  Mensajes de error:")
                    for msg in error_msgs:
                        text = await msg.text_content()
                        print(f"      - {text.strip()}")
            
            # Guardar screenshot para debug
            await page.screenshot(path='checkout_screenshot.png')
            print("\n📸 Screenshot guardado en checkout_screenshot.png")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_checkout_with_browser())
