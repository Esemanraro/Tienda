#!/usr/bin/env python3
"""
Normalize front-facing text to plain ASCII in templates and static assets.

Rules:
- Replace accented vowels with plain vowels
- Replace 'ñ'/'Ñ' with 'n'/'N'
- Clean common mojibake sequences seen in repo (e.g., 'GestiA3n' -> 'Gestion')

Usage:
  python tools/normalize_ascii.py [--write]

By default prints a summary of what would change. Use --write to apply.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / 'templates', ROOT / 'static', ROOT / 'blueprints']

ACCENT_MAP = {
    'á':'a','é':'e','í':'i','ó':'o','ú':'u',
    'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U',
    'ñ':'n','Ñ':'N',
}

# Frequent mojibake seen in this repo
MOJIBAKE_MAP = {
    'GestiA3n':'Gestion',
    'DescripciA3n':'Descripcion',
    'categorA-as':'categorias',
    'DA3lares':'Dolares',
    'CategorA-a':'Categoria',
    'GAnero':'Genero',
    'A�':'', # stray replacement char
}

def normalize_text(s: str) -> str:
    # Replace direct mojibake tokens first
    for bad, good in MOJIBAKE_MAP.items():
        s = s.replace(bad, good)
    # Replace known UTF-8 mis-decoded sequences
    s = (
        s.replace('Ã¡','a').replace('Ã©','e').replace('Ã­','i')
         .replace('Ã³','o').replace('Ãº','u').replace('Ã±','n')
         .replace('Â¿','?').replace('Â¡','!').replace('Â°','o')
    )
    # Replace remaining diacritics
    s = ''.join(ACCENT_MAP.get(ch, ch) for ch in s)
    return s

def process_file(path: Path, write: bool) -> bool:
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return False
    new = normalize_text(text)
    if new != text and write:
        path.write_text(new, encoding='utf-8')
        return True
    return new != text

def main():
    write = '--write' in sys.argv
    changed = []
    for base in TARGETS:
        if not base.exists():
            continue
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.html','.js','.css'}:
                if process_file(p, write):
                    changed.append(p.relative_to(ROOT).as_posix())
    if changed:
        print(('Updated' if write else 'Would update') + f' {len(changed)} files:')
        for c in changed:
            print(' -', c)
    else:
        print('No changes needed')

if __name__ == '__main__':
    main()

