#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de agregar ALOHA Dólares
"""

import requests
import sys
from bs4 import BeautifulSoup

def test_add_balance_functionality():
    """Prueba la funcionalidad completa de agregar balance"""
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("🧪 Iniciando pruebas de ALOHA Dólares...")
    
    try:
        # 1. Obtener página de login
        print("\n1️⃣ Obteniendo página de login...")
        login_response = session.get(f"{base_url}/auth/login")
        
        if login_response.status_code != 200:
            print(f"❌ Error al acceder a login: {login_response.status_code}")
            return False
            
        # Extraer CSRF token
        soup = BeautifulSoup(login_response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        
        if not csrf_token:
            print("❌ No se encontró token CSRF en login")
            return False
            
        csrf_value = csrf_token.get('value')
        print(f"✅ Token CSRF obtenido: {csrf_value[:20]}...")
        
        # 2. Hacer login
        print("\n2️⃣ Realizando login...")
        login_data = {
            'username': 'user_ana1',
            'password': 'password123',
            'csrf_token': csrf_value
        }
        
        login_post = session.post(f"{base_url}/auth/login", data=login_data)
        
        if login_post.status_code not in [200, 302]:
            print(f"❌ Error en login: {login_post.status_code}")
            return False
            
        print("✅ Login exitoso")
        
        # 3. Acceder al perfil
        print("\n3️⃣ Accediendo al perfil...")
        profile_response = session.get(f"{base_url}/user/profile")
        
        if profile_response.status_code != 200:
            print(f"❌ Error al acceder al perfil: {profile_response.status_code}")
            return False
            
        # Extraer balance actual
        profile_soup = BeautifulSoup(profile_response.text, 'html.parser')
        balance_element = profile_soup.find('span', class_='balance-amount')
        
        if balance_element:
            current_balance = balance_element.text.strip()
            print(f"✅ Balance actual: {current_balance}")
        else:
            print("⚠️ No se pudo obtener el balance actual")
            current_balance = "No disponible"
        
        # 4. Obtener nuevo CSRF token para agregar balance
        print("\n4️⃣ Obteniendo token CSRF del perfil...")
        csrf_token_profile = profile_soup.find('input', {'name': 'csrf_token'})
        
        if not csrf_token_profile:
            print("❌ No se encontró token CSRF en perfil")
            return False
            
        csrf_value_profile = csrf_token_profile.get('value')
        print(f"✅ Token CSRF del perfil: {csrf_value_profile[:20]}...")
        
        # 5. Agregar balance
        print("\n5️⃣ Agregando A$ 50.00 al balance...")
        balance_data = {
            'amount': '50.00',
            'csrf_token': csrf_value_profile
        }
        
        add_balance_response = session.post(f"{base_url}/user/add_balance", data=balance_data)
        
        print(f"📊 Respuesta del servidor:")
        print(f"   - Status Code: {add_balance_response.status_code}")
        print(f"   - Headers: {dict(add_balance_response.headers)}")
        
        if add_balance_response.status_code == 200:
            # Respuesta JSON
            try:
                response_json = add_balance_response.json()
                print(f"   - JSON Response: {response_json}")
                
                if response_json.get('success'):
                    print("✅ Balance agregado exitosamente!")
                    print(f"   - Mensaje: {response_json.get('message')}")
                    print(f"   - Nuevo balance: {response_json.get('new_balance')}")
                else:
                    print(f"❌ Error en la respuesta: {response_json.get('message')}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error al parsear JSON: {e}")
                print(f"   - Contenido: {add_balance_response.text[:200]}...")
                return False
                
        elif add_balance_response.status_code == 302:
            # Redirección
            print("✅ Redirección exitosa (probablemente éxito)")
            location = add_balance_response.headers.get('Location', 'No especificada')
            print(f"   - Redirigiendo a: {location}")
            
        else:
            print(f"❌ Error al agregar balance: {add_balance_response.status_code}")
            print(f"   - Contenido: {add_balance_response.text[:200]}...")
            return False
        
        # 6. Verificar nuevo balance
        print("\n6️⃣ Verificando nuevo balance...")
        new_profile_response = session.get(f"{base_url}/user/profile")
        
        if new_profile_response.status_code == 200:
            new_profile_soup = BeautifulSoup(new_profile_response.text, 'html.parser')
            new_balance_element = new_profile_soup.find('span', class_='balance-amount')
            
            if new_balance_element:
                new_balance = new_balance_element.text.strip()
                print(f"✅ Nuevo balance: {new_balance}")
                print(f"📈 Cambio: {current_balance} → {new_balance}")
            else:
                print("⚠️ No se pudo obtener el nuevo balance")
        
        print("\n🎉 Prueba completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_add_balance_functionality()
    sys.exit(0 if success else 1)
