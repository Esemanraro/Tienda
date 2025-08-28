#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del checkout usando Playwright para simular un navegador real
"""
import asyncio
from playwright.async_api import async_playwright

async def test_checkout_with_playwright():
    """Probar el checkout con un navegador real"""
    print("🎭 TEST DE CHECKOUT CON PLAYWRIGHT")
    print("="*50)
    
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. Ir a la página principal
            print("\n1. Navegando a la aplicación...")
            await page.goto('http://127.0.0.1:5003')
            print("   ✅ Página cargada")
            
            # 2. Hacer login
            print("\n2. Realizando login...")
            await page.click('text=Iniciar Sesión')
            await page.wait_for_selector('input[name="username"]')
            
            await page.fill('input[name="username"]', 'admin')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            
            # Esperar a que aparezca el mensaje de bienvenida o el nombre del usuario
            await page.wait_for_timeout(2000)
            
            # Verificar si el login fue exitoso
            if await page.locator('text=admin').count() > 0:
                print("   ✅ Login exitoso")
            else:
                print("   ❌ Login falló")
                return
            
            # 3. Agregar item al carrito
            print("\n3. Agregando item al carrito...")
            # Buscar el primer botón de agregar al carrito
            add_buttons = page.locator('button:has-text("Agregar al Carrito")')
            if await add_buttons.count() > 0:
                await add_buttons.first.click()
                await page.wait_for_timeout(1000)
                print("   ✅ Item agregado al carrito")
            else:
                print("   ❌ No se encontraron botones de agregar al carrito")
                return
            
            # 4. Ir al carrito
            print("\n4. Navegando al carrito...")
            await page.click('a[href="/cart"]')
            await page.wait_for_selector('text=Carrito de Compras')
            print("   ✅ En página del carrito")
            
            # 5. Proceder al checkout
            print("\n5. Procediendo al checkout...")
            checkout_button = page.locator('a:has-text("Proceder al Pago")')
            if await checkout_button.count() > 0:
                await checkout_button.click()
                await page.wait_for_selector('text=Resumen de tu Pedido')
                print("   ✅ En página de checkout")
            else:
                print("   ❌ No se encontró botón de checkout")
                return
            
            # 6. Confirmar compra
            print("\n6. Confirmando compra...")
            confirm_button = page.locator('button:has-text("Confirmar Compra")')
            if await confirm_button.count() > 0:
                # Capturar respuesta
                await confirm_button.click()
                
                # Esperar un poco para ver el resultado
                await page.wait_for_timeout(3000)
                
                # Verificar resultado
                current_url = page.url
                page_content = await page.content()
                
                if 'order' in current_url:
                    print("   ✅ ¡CHECKOUT EXITOSO! Redirigido a resumen de orden")
                elif 'Compra realizada' in page_content:
                    print("   ✅ ¡CHECKOUT EXITOSO! Mensaje de éxito encontrado")
                elif 'Error' in page_content or 'error' in page_content:
                    print("   ❌ Error en checkout")
                    # Buscar mensaje de error específico
                    error_elements = await page.locator('.alert-danger').all_text_contents()
                    if error_elements:
                        print(f"   ❌ Mensaje de error: {error_elements[0]}")
                else:
                    print("   ❓ Estado desconocido")
                    print(f"   URL actual: {current_url}")
            else:
                print("   ❌ No se encontró botón de confirmar compra")
            
        except Exception as e:
            print(f"\n❌ Error durante la prueba: {str(e)}")
        
        finally:
            await browser.close()
    
    print("\n" + "="*50)
    print("📊 TEST COMPLETADO")

if __name__ == "__main__":
    asyncio.run(test_checkout_with_playwright())
