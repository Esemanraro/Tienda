#!/usr/bin/env python3
"""
Script para actualizar las referencias de rutas en los templates
de 'main.' a los nuevos blueprints
"""

import os
import re

# Mapeo de rutas viejas a nuevas
route_mapping = {
    # Auth routes
    'main.login': 'auth.login',
    'main.logout': 'auth.logout',
    'main.register': 'auth.register',
    
    # Shop routes
    'main.index': 'shop.index',
    'main.search': 'shop.search',
    'main.add_to_cart': 'shop.add_to_cart',
    'main.view_cart': 'shop.view_cart',
    'main.update_cart': 'shop.update_cart',
    'main.checkout': 'shop.checkout',
    'main.order_summary': 'shop.order_summary',
    
    # Admin routes
    'main.admin_dashboard': 'admin.dashboard',
    'main.add_toy': 'admin.add_toy',
    'main.edit_toy': 'admin.edit_toy',
    'main.delete_toy': 'admin.delete_toy',
    
    # User routes
    'main.profile': 'user.profile',
    'main.add_balance': 'user.add_balance',
    'main.change_password': 'user.change_password',
    'main.update_center': 'user.update_center',
}

def update_template_file(file_path):
    """Actualizar un archivo de template"""
    print(f"Actualizando: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Actualizar cada ruta
    for old_route, new_route in route_mapping.items():
        # Buscar patrones como url_for('main.route')
        pattern = f"url_for\\('{old_route}'"
        replacement = f"url_for('{new_route}'"
        content = re.sub(pattern, replacement, content)
    
    # Solo escribir si hubo cambios
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Actualizado")
        return True
    else:
        print(f"  - Sin cambios")
        return False

def main():
    """Función principal"""
    templates_dir = 'templates'
    updated_files = 0
    total_files = 0
    
    print("Actualizando referencias de rutas en templates...")
    print("=" * 50)
    
    # Recorrer todos los archivos HTML en templates
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                total_files += 1
                
                if update_template_file(file_path):
                    updated_files += 1
    
    print("=" * 50)
    print(f"Resumen:")
    print(f"  Archivos procesados: {total_files}")
    print(f"  Archivos actualizados: {updated_files}")
    print(f"  Archivos sin cambios: {total_files - updated_files}")

if __name__ == '__main__':
    main()
