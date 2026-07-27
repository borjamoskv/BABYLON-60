# [C5-REAL] Exergy-Maximized
"""
cat_id: sweep
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import os
import sys

import yaml

# Agregamos src al PYTHONPATH dinámicamente para importar cortex_kernel
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cortex_kernel.antipattern_forge import audit_file


def sweep_directory(target_dir: str):
    total_violations = 0
    results = {}
    
    for root, dirs, files in os.walk(target_dir):
        # Excluir directorios virtuales y caches
        dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                violations = audit_file(filepath)
                if violations:
                    results[filepath] = violations
                    total_violations += len(violations)
                    
    return results, total_violations

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python sweep.py <directorio_o_archivo_a_analizar>")  # noqa: T201
        sys.exit(1)
        
    target = sys.argv[1]
    target_path = os.path.abspath(target)
    
    print(f"█▄ Iniciando Macrófago Ontológico sobre: {target_path}")  # noqa: T201
    
    if os.path.isfile(target_path):
        violations = audit_file(target_path)
        results = {target_path: violations} if violations else {}
        total_violations = len(violations)
    else:
        results, total_violations = sweep_directory(target_path)
        
    if total_violations > 0:
        print(f"\n[!] Anergía Estocástica Detectada: {total_violations} violaciones.\n")  # noqa: T201
        
        # Reporte Brutalista C5-REAL
        report = {
            "Claim": "El código inspeccionado contiene fallas de topología (Antipatrones).",
            "Violations": results,
            "Resolution": "Reescribir mutaciones o delegar en Git Sentinel."
        }
        
        print(yaml.dump(report, default_flow_style=False, sort_keys=False, allow_unicode=True))  # noqa: T201
        print("\n⚡ [SIGKILL_STATE_PURGE]")  # noqa: T201
        sys.exit(1)
    else:
        print("\n✅ C5-REAL CONFIRMED. Cero Anergía. Exergía pura. ⚡ [ATP SAVED: MAX]")  # noqa: T201
        sys.exit(0)
