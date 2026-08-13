import json
from pathlib import Path

def fix_imports():
    with open('imports.json', 'r') as f:
        data = json.load(f)
        
    for finding in data.get('findings', []):
        if finding['clase'] in ('FANTASMA_INTERNO', 'FANTASMA', 'SIMBOLO_FANTASMA'):
            for pt in finding['puntos']:
                filepath = Path(pt['fichero'])
                line_idx = pt['linea'] - 1
                
                if filepath.exists():
                    lines = filepath.read_text().splitlines()
                    if 0 <= line_idx < len(lines):
                        # Comment out the ghost import
                        original = lines[line_idx]
                        if not original.strip().startswith('#'):
                            lines[line_idx] = f"# {original}  # purgado por anergía"
                            filepath.write_text('\n'.join(lines) + '\n')
                            print(f"Fixed {filepath}:{pt['linea']}")

if __name__ == '__main__':
    fix_imports()
