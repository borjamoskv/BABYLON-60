#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ OPERATIVO LEGIÓN-100 | GLOBAL MONOREPO AUDIT
# ============================================================================
"""
Enjambre concurrente de 100 workers para auditar invariantes C5-REAL a nivel 
estructural en el monorepositorio.
"""

import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------------------------------------------------------
# INVARIANTES Y REGLAS DE SCANNING
# ----------------------------------------------------------------------------

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}", "Slack Token"),
    (r"-----BEGIN RSA PRIVATE KEY-----", "RSA Private Key"),
]

TOPOLOGICAL_VIOLATION_PATTERN = r"from\s+wa_nexus\s+import|import\s+wa_nexus"

def scan_file(filepath: str) -> list:
    """Escanea un archivo contra todas las invariantes."""
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # 1. Escaneo Criptográfico (Zero Trust)
            for pattern, name in SECRET_PATTERNS:
                if re.search(pattern, content):
                    violations.append(f"CRÍTICO [Zero-Trust]: Posible {name} expuesto.")
                    
            # 2. Invariantes Topológicas (Aislamiento babylon60 <-> wa-nexus)
            if "babylon60" in filepath and re.search(TOPOLOGICAL_VIOLATION_PATTERN, content):
                violations.append("CRÍTICO [Topología]: Fractura de aislamiento. Importación cruzada detectada hacia wa-nexus.")
                
    except Exception as e:
        violations.append(f"ERROR: No se pudo leer el archivo: {e}")
        
    return violations

# ----------------------------------------------------------------------------
# ENJAMBRE LEGIÓN-100
# ----------------------------------------------------------------------------

def main():
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    print("================================================================")
    print(" █ OPERATIVO LEGIÓN-100: GLOBAL MONOREPO AUDIT")
    print("================================================================")
    print(f"Target: {target_dir}")
    print("Workers: 100\n")
    
    # Recopilar todos los archivos
    files_to_scan = []
    ignore_dirs = ["/.git", "/target", "__pycache__", "/node_modules", "/.venv", "/.xtts_venv", "/archive", "/tests/fixtures", "/docs", "/experiments"]
    
    for root, _, files in os.walk(target_dir):
        # Ignorar zonas de alta entropía externa o almacenamiento frío
        if any(ignored in root for ignored in ignore_dirs):
            continue
        for file in files:
            filepath = os.path.join(root, file)
            # Ignorar configuraciones que contienen regex intencionales
            if file in [".gitleaks.toml", ".env.canary"]:
                continue
            # Evitar que el escáner se audite a sí mismo y dispare alertas por sus propios patrones Regex
            if "legion_100_agents_full_monorepo.py" in filepath:
                continue
            files_to_scan.append(filepath)
            
    print(f"Archivos indexados para escaneo concurrente: {len(files_to_scan)}\n")
    
    start_time = time.time()
    total_violations = 0
    
    # Lanzar el enjambre de 100 workers
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_to_file = {executor.submit(scan_file, f): f for f in files_to_scan}
        
        for future in as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                violations = future.result()
                if violations:
                    total_violations += len(violations)
                    rel_path = os.path.relpath(filepath, target_dir)
                    print(f"\n[!] INFRACCIÓN EN: {rel_path}")
                    for v in violations:
                        print(f"    -> {v}")
            except Exception as exc:
                print(f"[{filepath}] generó una excepción: {exc}")

    elapsed = time.time() - start_time
    print("\n================================================================")
    print(f" SITREP: REPORTE DE ESTABILIDAD TERMODINÁMICA")
    print("================================================================")
    print(f"Archivos escaneados : {len(files_to_scan)}")
    print(f"Tiempo de ejecución : {elapsed:.3f} segundos")
    print(f"Total Infracciones  : {total_violations}")
    
    if total_violations == 0:
        print("\n✅ DICTAMEN: ESTADO ÓMEGA ALCANZADO. CERO FRACTURAS TOPOLÓGICAS.")
        sys.exit(0)
    else:
        print("\n❌ DICTAMEN: ANERGÍA DETECTADA. REQUIERE PURGA ESTRUCTURAL.")
        sys.exit(1)

if __name__ == "__main__":
    main()
