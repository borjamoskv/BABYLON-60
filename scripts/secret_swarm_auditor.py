#!/usr/bin/env python3
# C5-REAL: Swarm Thread Dispatcher for TOP SECRET Auditing
# Vector: BFT_STATE_LOOP, Bypass estocástico (O(N^2) friction) mediante concurrencia atómica.
import os
import re
import math
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any

# Exclusión de Anergía (Directorios ruidosos o binarios)
EXCLUDE_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'dist', 'build', '.cortex', '.babylon60', '.mypy_cache', '.pytest_cache', '.ruff_cache', 'c5_remotion_video', 'scratch', 'anvil_yung', 'BABYLON-60-fixes'}
EXCLUDE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.db', '.sqlite', '.sqlite3', '.npz', '.pyc', '.so', '.dylib', '.zip', '.tar', '.gz', '.db-shm', '.db-wal', '.lock', '.ipynb', '.patch', '.json'}

# Patrones Top Secret
PATTERNS = {
    'AWS_ACCESS_KEY': r'AKIA[0-9A-Z]{16}',
    'RSA_PRIVATE_KEY': r'-----BEGIN RSA PRIVATE KEY-----',
    'GENERIC_PRIVATE_KEY': r'-----BEGIN PRIVATE KEY-----',
    'JWT_TOKEN': r'eyJ[a-zA-Z0-9_-]{5,}\.eyJ[a-zA-Z0-9_-]{5,}\.[a-zA-Z0-9_-]{5,}',
    'GITHUB_TOKEN': r'ghp_[a-zA-Z0-9]{36}',
    'GOOGLE_API': r'AIza[0-9A-Za-z-_]{35}',
    'SLACK_TOKEN': r'xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}',
    'GENERIC_SECRET': r'(?i)(password|secret|api_key|access_token)[\s:=]+[\'"]([^\'"]{8,})[\'"]'
}

def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy

def scan_file(filepath: str) -> List[Dict[str, Any]]:
    findings = []
    # Auto-evasión: No auditarse a sí mismo
    if "secret_swarm_auditor.py" in filepath:
        return findings

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            # Check Patterns
            for p_name, p_regex in PATTERNS.items():
                for match in re.finditer(p_regex, line):
                    secret_val = match.group(0)
                    if p_name == 'GENERIC_SECRET':
                        secret_val = match.group(2)
                    
                    # C5-REAL Enmascaramiento estructural (Hash criptográfico)
                    secret_hash = hashlib.sha3_256(secret_val.encode()).hexdigest()[:16]
                    masked = secret_val[:4] + "..." + secret_val[-4:] if len(secret_val) > 8 else "***"
                    
                    findings.append({
                        'file': filepath,
                        'line': i + 1,
                        'type': p_name,
                        'masked_value': masked,
                        'hash': secret_hash
                    })

            # Check Entropy en palabras largas (Base64/Hex)
            words = re.findall(r'\b[a-zA-Z0-9+/=]{20,}\b', line)
            for w in words:
                ent = shannon_entropy(w)
                if ent > 4.8: # Alta entropía = Posible secreto
                    secret_hash = hashlib.sha3_256(w.encode()).hexdigest()[:16]
                    masked = w[:4] + "..." + w[-4:]
                    findings.append({
                        'file': filepath,
                        'line': i + 1,
                        'type': 'HIGH_ENTROPY_STRING',
                        'entropy': round(ent, 2),
                        'masked_value': masked,
                        'hash': secret_hash
                    })
    except (UnicodeDecodeError, OSError):
        # Failsafe silencioso limitado a IO/Encoding
        pass
        
    return findings

def get_target_files(root_dir: str) -> List[str]:
    targets = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Poda de directorios de anergía
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext not in EXCLUDE_EXTS:
                targets.append(os.path.join(dirpath, f))
    return targets

def main():
    root = "/Users/borjafernandezangulo/30_BABYLON-60"
    files = get_target_files(root)
    
    print(f"[C5-REAL] Swarm Audit Initialized (ITERATION 2). Targets: {len(files)} files.")
    
    all_findings = []
    # Despliegue de Enjambre Físico (max_workers)
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(scan_file, f): f for f in files}
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_findings.extend(res)
    
    # Consolidación del Ledger
    report_path = os.path.join(root, "AUDITORIA_TOP_SECRET.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# C5-REAL: AUDITORÍA TOP SECRET (MASTER LEDGER - ITERATION 2)\n\n")
        rf.write("> **MOSKV-1 APEX SINGULARITY**\n")
        rf.write(f"> Total Archivos Escaneados: {len(files)}\n")
        rf.write(f"> Anomalías Detectadas: {len(all_findings)}\n\n")
        
        if not all_findings:
            rf.write("## ESTADO BFT: LIMPIO\nNo se detectó entropía TOP SECRET en el repositorio tras la poda de Anergía.\n")
        else:
            rf.write("## VULNERABILIDADES DETECTADAS\n\n")
            rf.write("| Archivo | Línea | Tipo | Valor Enmascarado | Hash (SHA3-256) | Entropía |\n")
            rf.write("|---|---|---|---|---|---|\n")
            for f in all_findings:
                ent_str = str(f.get('entropy', '-'))
                rf.write(f"| `{os.path.relpath(f['file'], root)}` | {f['line']} | {f['type']} | `{f['masked_value']}` | `{f['hash']}` | {ent_str} |\n")
                
    print(f"[C5-REAL] Auditoría Completada. Resultados consolidados en: {report_path}")

if __name__ == "__main__":
    main()
