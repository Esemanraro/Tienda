import os
import re
from pathlib import Path

def check_templates():
    """Verifica y reporta problemas potenciales en los templates"""
    template_dir = Path('templates')
    problems = []
    
    # Patrones a buscar
    patterns = {
        'url_for sin main': r"url_for\('(?!main\.|static)[^']+'\)",
        'referencias a rutas': r"href=\"{{ url_for\('(?!main\.|static)[^']+'\) }}\"",
        'referencias en forms': r"action=\"{{ url_for\('(?!main\.|static)[^']+'\) }}\"",
    }
    
    for template_file in template_dir.glob('**/*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            line_number = 1
            
            for line in content.split('\n'):
                for pattern_name, pattern in patterns.items():
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        route = re.search(r"'([^']+)'", match.group()).group(1)
                        if route != 'static':
                            problems.append({
                                'file': template_file.name,
                                'line': line_number,
                                'pattern': pattern_name,
                                'text': line.strip(),
                                'fix': f"Cambiar '{route}' por 'main.{route}'"
                            })
                line_number += 1
    
    return problems

def print_report(problems):
    """Imprime un reporte de los problemas encontrados"""
    if not problems:
        print("✅ No se encontraron problemas en los templates!")
        return
    
    print("\n🔍 Problemas encontrados en los templates:")
    print("==========================================")
    
    current_file = None
    for problem in problems:
        if current_file != problem['file']:
            current_file = problem['file']
            print(f"\n📄 {current_file}")
        
        print(f"  Línea {problem['line']}: {problem['pattern']}")
        print(f"    {problem['text']}")
        print(f"    ⚠️  {problem['fix']}")

if __name__ == '__main__':
    problems = check_templates()
    print_report(problems)
