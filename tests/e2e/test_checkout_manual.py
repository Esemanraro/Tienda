#!/usr/bin/env python3
"""
Test manual del checkout con debug detallado
"""

import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "http://127.0.0.1:5003"

def test_checkout_flow():
    session = requests.Session()
    
    print("🔍 TEST MANUAL DE CHECKOUT CON DEBUG\n")
    
    # 1. Login
    print("1. Login...")
    login_page = session.get(f"{BASE_URL}/auth/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token.get('value') if csrf_token else ''
    }
    
    login_response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)
    print(f"   Status: {login_response.status_code}")
    
    # 2. Verificar sesión inicial
    print("\n2. Verificando sesión inicial...")
    session_check = session.get(f"{BASE_URL}/api/debug/session")
    if session_check.status_code == 200:
        data = session_check.json()
        print(f"   Usuario: {data.get('username')}")
        print(f"   Carrito: {data.get('cart')}")
        print(f"   Items en carrito: {data.get('cart_count')}")
    
    # 3. Agregar item al carrito
    print("\n3. Agregando item al carrito...")
    index_page = session.get(f"{BASE_URL}/")
    soup = BeautifulSoup(index_page.text, 'html.parser')
    
    meta_csrf = soup.find('meta', {'name': 'csrf-token'})
    csrf_value = meta_csrf.get('content') if meta_csrf else ''
    
    add_to_cart_data = {
        'toy_id': '7',
        'quantity': '2',
        'csrf_token': csrf_value
    }
    
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    
    add_response = session.post(f"{BASE_URL}/add_to_cart", data=add_to_cart_data, headers=headers)
    print(f"   Status: {add_response.status_code}")
    if add_response.status_code == 200:
        print(f"   Response: {add_response.json()}")
    
    # 4. Verificar sesión después de agregar
    print("\n4. Verificando sesión después de agregar...")
    session_check = session.get(f"{BASE_URL}/api/debug/session")
    if session_check.status_code == 200:
        data = session_check.json()
        print(f"   Carrito: {data.get('cart')}")
        print(f"   Items en carrito: {data.get('cart_count')}")
    
    # 5. Ir directamente a checkout
    print("\n5. Navegando a checkout...")
    checkout_response = session.get(f"{BASE_URL}/checkout", allow_redirects=False)
    print(f"   Status: {checkout_response.status_code}")
    
    if checkout_response.status_code == 302:
        print(f"   ❌ Redirigido a: {checkout_response.headers.get('Location')}")
        # Seguir la redirección
        checkout_response = session.get(checkout_response.headers.get('Location'))
    
    # 6. Si llegamos a checkout, intentar hacer el POST
    if '/checkout' in checkout_response.url:
        print("\n6. Intentando confirmar compra...")
        soup = BeautifulSoup(checkout_response.text, 'html.parser')
        
        # Buscar CSRF en el formulario
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_value = csrf_input.get('value')
            
            checkout_data = {
                'csrf_token': csrf_value
            }
            
            confirm_response = session.post(f"{BASE_URL}/checkout", data=checkout_data, allow_redirects=True)
            print(f"   Status: {confirm_response.status_code}")
            print(f"   URL final: {confirm_response.url}")
            
            # Buscar mensajes
            soup = BeautifulSoup(confirm_response.text, 'html.parser')
            messages = soup.find_all(class_=['flash-message', 'alert'])
            if messages:
                print("   Mensajes:")
                for msg in messages:
                    print(f"      - {msg.text.strip()}")
    else:
        print("   ❌ No se pudo acceder a checkout")
        # Verificar mensajes de error
        soup = BeautifulSoup(checkout_response.text, 'html.parser')
        messages = soup.find_all(class_=['flash-message', 'alert'])
        if messages:
            print("   Mensajes de error:")
            for msg in messages:
                print(f"      - {msg.text.strip()}")

if __name__ == "__main__":
    test_checkout_flow()
