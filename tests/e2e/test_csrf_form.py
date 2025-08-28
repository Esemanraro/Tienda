#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import User, Toy
import re

def test_csrf_in_form():
    """Verificar cómo se genera el token CSRF en el formulario"""
    print("🔍 VERIFICACIÓN DE CSRF EN FORMULARIO")
    print("="*40)
    
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        toy = Toy.query.filter_by(id=4).first()
    
    with app.test_client() as client:
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
            sess['_id'] = 'test_session'
        
        # Agregar al carrito
        with client.session_transaction() as sess:
            sess['cart'] = {
                '4': {
                    'quantity': 2,
                    'price': float(toy.price)
                }
            }
        
        # Obtener la página de checkout
        response = client.get('/checkout')
        html = response.data.decode('utf-8')
        
        print("1. Buscando tokens CSRF en el HTML...")
        
        # Buscar en meta tag
        meta_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        if meta_match:
            meta_token = meta_match.group(1)
            print(f"   ✅ Token en meta tag: {meta_token[:20]}...")
        else:
            print("   ❌ No se encontró token en meta tag")
        
        # Buscar en el formulario
        form_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', html)
        if form_match:
            form_token = form_match.group(1)
            print(f"   ✅ Token en formulario: {form_token[:20]}...")
        else:
            print("   ❌ No se encontró token en el formulario")
            
        # Buscar cualquier input hidden con csrf
        hidden_inputs = re.findall(r'<input[^>]*type="hidden"[^>]*>', html)
        print(f"\n2. Inputs hidden encontrados: {len(hidden_inputs)}")
        for inp in hidden_inputs:
            if 'csrf' in inp.lower():
                print(f"   → {inp}")
        
        # Intentar POST con el token del formulario
        if form_match:
            print("\n3. Intentando POST con token del formulario...")
            response = client.post('/checkout',
                                 data={'csrf_token': form_token},
                                 follow_redirects=False)
            print(f"   📡 Respuesta: {response.status_code}")
            if response.status_code == 302:
                print(f"   🔀 Redirección a: {response.headers.get('Location')}")
            elif response.status_code == 200:
                print("   ✅ POST exitoso")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        # Verificar contenido del formulario real
        print("\n4. Extrayendo formulario de checkout...")
        form_start = html.find('<form action="/checkout"')
        if form_start > -1:
            form_end = html.find('</form>', form_start)
            form_content = html[form_start:form_end+7]
            print("   📋 Contenido del formulario:")
            print("   " + "-"*50)
            # Limpiar un poco el HTML para hacerlo más legible
            form_lines = form_content.replace('><', '>\n<').split('\n')
            for line in form_lines[:10]:  # Primeras 10 líneas
                print(f"   {line.strip()}")
            print("   " + "-"*50)

if __name__ == "__main__":
    test_csrf_in_form()
