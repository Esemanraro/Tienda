#!/usr/bin/env python3
"""
Script de Diagnóstico Detallado para Problemas de Checkout
==========================================================
Este script diagnostica paso a paso el proceso de checkout
"""

import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "http://127.0.0.1:5003"

def diagnose_checkout():
    session = requests.Session()
    
    print("🔍 DIAGNÓSTICO DE CHECKOUT\n")
    
    # 1. Login
    print("1. Intentando login...")
    login_page = session.get(f"{BASE_URL}/auth/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if csrf_token:
        csrf_value = csrf_token.get('value')
        print(f"   ✅ CSRF token encontrado en login: {csrf_value[:20]}...")
    else:
        print("   ❌ No se encontró CSRF token en login")
        return
    
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_value
    }
    
    login_response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
    print(f"   Status code: {login_response.status_code}")
    if login_response.status_code == 302:
        print("   ✅ Login exitoso (redirección)")
    
    # 2. Agregar item al carrito
    print("\n2. Agregando item al carrito...")
    # Primero obtener la página principal para el CSRF
    index_page = session.get(f"{BASE_URL}/")
    soup = BeautifulSoup(index_page.text, 'html.parser')
    
    # Buscar el meta tag con CSRF
    meta_csrf = soup.find('meta', {'name': 'csrf-token'})
    if meta_csrf:
        csrf_value = meta_csrf.get('content')
        print(f"   ✅ CSRF token encontrado en meta tag: {csrf_value[:20]}...")
    
    # Agregar al carrito con AJAX
    add_to_cart_data = {
        'toy_id': '7',
        'quantity': '2',
        'csrf_token': csrf_value
    }
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    
    add_response = session.post(f"{BASE_URL}/add_to_cart", data=add_to_cart_data, headers=headers)
    print(f"   Status code: {add_response.status_code}")
    if add_response.status_code == 200:
        print("   ✅ Item agregado al carrito")
        try:
            response_json = add_response.json()
            print(f"   Respuesta: {response_json}")
        except:
            pass
    
    # 3. Verificar página de checkout
    print("\n3. Accediendo a página de checkout...")
    checkout_page = session.get(f"{BASE_URL}/checkout")
    print(f"   Status code: {checkout_page.status_code}")
    
    if checkout_page.status_code == 200:
        soup = BeautifulSoup(checkout_page.text, 'html.parser')
        
        # Buscar el formulario de checkout
        checkout_form = soup.find('form', {'action': lambda x: x and 'checkout' in x})
        if checkout_form:
            print("   ✅ Formulario de checkout encontrado")
            
            # Buscar CSRF en el formulario
            csrf_input = checkout_form.find('input', {'name': 'csrf_token'})
            if csrf_input:
                csrf_checkout = csrf_input.get('value')
                print(f"   ✅ CSRF token en formulario: {csrf_checkout[:20]}...")
            else:
                print("   ❌ No se encontró CSRF token en el formulario de checkout")
            
            # Verificar el botón de submit
            submit_button = checkout_form.find('button', {'type': 'submit'})
            if submit_button:
                print(f"   ✅ Botón de submit encontrado: '{submit_button.text.strip()}'")
            else:
                print("   ❌ No se encontró botón de submit")
        else:
            print("   ❌ No se encontró formulario de checkout")
    
    # 4. Intentar procesar checkout
    print("\n4. Intentando procesar checkout...")
    
    # Obtener el CSRF token más reciente
    checkout_page = session.get(f"{BASE_URL}/checkout")
    soup = BeautifulSoup(checkout_page.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    
    if csrf_input:
        csrf_value = csrf_input.get('value')
        print(f"   CSRF token para POST: {csrf_value[:20]}...")
        
        # Intentar checkout con diferentes configuraciones
        checkout_data = {
            'csrf_token': csrf_value
        }
        
        # Intento 1: POST normal
        print("\n   Intento 1: POST normal")
        checkout_response = session.post(f"{BASE_URL}/checkout", data=checkout_data, allow_redirects=False)
        print(f"   Status code: {checkout_response.status_code}")
        print(f"   Headers: {dict(checkout_response.headers)}")
        if checkout_response.status_code in [400, 500]:
            print(f"   Contenido de error: {checkout_response.text[:500]}")
        
        # Intento 2: Con headers adicionales
        print("\n   Intento 2: Con headers adicionales")
        headers = {
            'Referer': f"{BASE_URL}/checkout",
            'Origin': BASE_URL
        }
        checkout_response2 = session.post(f"{BASE_URL}/checkout", data=checkout_data, headers=headers, allow_redirects=False)
        print(f"   Status code: {checkout_response2.status_code}")
        
        # Verificar cookies de sesión
        print("\n5. Información de sesión:")
        print(f"   Cookies: {session.cookies.get_dict()}")

if __name__ == "__main__":
    diagnose_checkout()
