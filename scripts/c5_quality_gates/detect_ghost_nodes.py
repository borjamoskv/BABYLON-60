#!/usr/bin/env python3
"""
[AX-2] TOPOLOGY: Ghost Node Detector (Quality Gate)
Escáner de Bisimulación C5-REAL para erradicar Anergía Documental.
Bloquea el pipeline si se detectan símbolos muertos en archivos Markdown.
"""

import os
import re
import sys

# Invariante de Calibración OPSEC: Exclusión de cachés pesados
EXCLUDE_DIRS = {'.git', 'target', '.lake', '.jj', '.hypothesis', '.audit', 'site', 'assets', '.venv', '__pycache__', 'node_modules'}
CODE_EXTS = ('.rs', '.py', '.ts', '.swift', '.lean', '.c', '.h', '.cpp', '.hpp')
DOC_EXTS = ('.md',)

def build_symbol_table(root_dir):
    """Extrae el AST simulado (todos los identificadores) de la base de silicio."""
    symbols = set()
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(CODE_EXTS):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Extraer identificadores tipo C/Python/Rust
                        symbols.update(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]+\b', f.read()))
                except Exception:
                    pass
    return symbols

def audit_ghost_nodes(root_dir, symbol_table):
    """Falsa la documentación buscando símbolos que no existen en el territorio."""
    ghost_report = []
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(DOC_EXTS):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Extraer todo lo que esté entre backticks `simbolo`
                        backticks = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_]+)`', content)
                        for b in backticks:
                            # Filtramos palabras muy comunes o cortas para evitar falsos positivos
                            if b not in symbol_table and len(b) > 4:
                                # Ignoramos si la propia documentación ya lo ha marcado como obsoleto
                                if f"[OBSOLETO: {b}]" not in content:
                                    ghost_report.append((path, b))
                except Exception:
                    pass
    return set(ghost_report)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    print("\033[94m[C5-REAL] Extrayendo base de símbolos del territorio (Silicio)...\033[0m")
    symbols = build_symbol_table(repo_root)
    print(f"\033[92m[C5-REAL] {len(symbols)} símbolos indexados.\033[0m")
    
    print("\033[94m[C5-REAL] Falsando mapas documentales contra el territorio...\033[0m")
    ghosts = audit_ghost_nodes(repo_root, symbols)
    
    if not ghosts:
        print("\033[92m[C5-REAL] Clausura Epistémica validada. Cero Ghost Nodes.\033[0m")
        sys.exit(0)
    else:
        print(f"\033[91m[CORTEX-TAINT] Rotura de Bisimulación Detectada. {len(ghosts)} Ghost Nodes hallados.\033[0m")
        for path, ghost in sorted(ghosts):
            print(f"  - \033[93m{ghost}\033[0m en {os.path.relpath(path, repo_root)}")
        print("\033[91m[C5-REAL] ABORTANDO. La documentación contiene entropía y descalibrará al enjambre.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
