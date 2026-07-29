#!/usr/bin/env python3
# C5-REAL: Swarm Thread Dispatcher for TOP SECRET Auditing (ULTRATHINK P0 - ITERATION 3)
# Vector: BFT_STATE_LOOP, SARIF Integration, Delta Scanning, Zero-Anergy Whitelisting
import os
import re
import math
import hashlib
import json
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any

# Exclusión de Anergía (Directorios ruidosos o binarios)
EXCLUDE_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'dist', 'build', '.cortex', '.babylon60', '.mypy_cache', '.pytest_cache', '.ruff_cache', 'c5_remotion_video', 'scratch', 'anvil_yung', 'BABYLON-60-fixes', 'target', 'claude_code_local_logs'}
EXCLUDE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.db', '.sqlite', '.sqlite3', '.npz', '.pyc', '.so', '.dylib', '.zip', '.tar', '.gz', '.db-shm', '.db-wal', '.lock', '.ipynb', '.patch', '.json', '.jsonl', '.rlib', '.rmeta'}

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

# Whitelist de Anergía para Cadenas de Alta Entropía
WHITELIST_ENTROPY = [
    r'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx',
    r'0123456789abcdefghijklmnopqrstuvwxyz',
    r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    r'docs\.google\.com/[^\s]+',
    r'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv',
    r'0123456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ',  # BASE60_ALPHABET (constante pública de diseño, utils/base60.py)
]

# Valores literales conocidos como NO-secretos (ejemplos oficiales de documentación
# o dummies de test auto-descritos). C5-REAL: cada entrada justificada inline.
WHITELIST_VALUES = {
    'AKIAIOSFODNN7EXAMPLE',      # Clave de ejemplo oficial de la documentación de AWS (no es real)
    'dummy_key_for_stress',      # Dummy auto-descrito: stress test (extensions/llm/fable_stress_test.py)
    'dummy_key_for_steerability',  # Dummy auto-descrito: PoC steerability (extensions/llm/fable_steerability_poc.py)
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

def is_whitelisted(line: str) -> bool:
    for w in WHITELIST_ENTROPY:
        if re.search(w, line):
            return True
    return False

def scan_file(filepath: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    # Auto-evasión
    if "secret_swarm_auditor.py" in filepath or not os.path.isfile(filepath):
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
                    if secret_val in WHITELIST_VALUES:
                        continue
                    
                    secret_hash = hashlib.sha3_256(secret_val.encode()).hexdigest()[:16]
                    masked = secret_val[:4] + "..." + secret_val[-4:] if len(secret_val) > 8 else "***"
                    
                    findings.append({
                        'file': filepath,
                        'line': i + 1,
                        'type': p_name,
                        'masked_value': masked,
                        'hash': secret_hash,
                        'entropy': None
                    })

            # Check Entropy
            if not is_whitelisted(line):
                words = re.findall(r'\b[a-zA-Z0-9+/=]{20,}\b', line)
                for w in words:
                    ent = shannon_entropy(w)
                    if ent > 4.8:
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
        _ = None
        
    return findings

def get_target_files(root_dir: str, explicit_files: List[str] | None = None) -> List[str]:
    targets = []
    if explicit_files:
        for f in explicit_files:
            if os.path.exists(f):
                ext = os.path.splitext(f)[1].lower()
                if ext not in EXCLUDE_EXTS:
                    targets.append(os.path.abspath(f))
        return targets

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext not in EXCLUDE_EXTS:
                targets.append(os.path.join(dirpath, f))
    return targets

def export_sarif(findings: List[Dict[str, Any]], root: str, output_path: str):
    sarif: Dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "MOSKV-1 Swarm Auditor",
                    "informationUri": "https://github.com/borjamoskv",
                    "rules": [
                        {
                            "id": "SECRET-01",
                            "name": "HardcodedSecret",
                            "shortDescription": {"text": "Hardcoded top secret string detected."},
                            "helpUri": "https://github.com/borjamoskv"
                        }
                    ]
                }
            },
            "results": []
        }]
    }

    for f in findings:
        rel_path = os.path.relpath(f['file'], root)
        msg = f"Detectado secreto tipo {f['type']} con hash {f['hash']}"
        sarif["runs"][0]["results"].append({
            "ruleId": "SECRET-01",
            "message": {"text": msg},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": rel_path},
                    "region": {
                        "startLine": f['line'],
                        "startColumn": 1
                    }
                }
            }]
        })

    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(sarif, out_file, indent=2)

def main():
    parser = argparse.ArgumentParser(description="C5-REAL Swarm Secret Auditor")
    parser.add_argument("--files", nargs='*', help="Delta mode: specific files to scan")
    parser.add_argument("--sarif", action="store_true", help="Generate SARIF report")
    args = parser.parse_args()

    root = os.getcwd()
    files = get_target_files(root, explicit_files=args.files)
    
    print(f"[*] C5-REAL Swarm (ULTRATHINK P0 - IT3). Escaneando {len(files)} deltas/archivos...")
    
    all_findings = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(scan_file, f): f for f in files}
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_findings.extend(res)
    
    # CI PR Annotations
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if all_findings:
        for f in all_findings:
            rel_path = os.path.relpath(f['file'], root)
            if in_ci:
                print(f"::error file={rel_path},line={f['line']}::[C5-REAL] Secret Detected: {f['type']} ({f['hash']})")
    
    # SARIF Output
    if args.sarif:
        export_sarif(all_findings, root, os.path.join(root, "secret_audit.sarif"))
        print("[*] Reporte SARIF generado: secret_audit.sarif")

    # BFT State
    if all_findings:
        print("[!] ANERGÍA DETECTADA. Fricción estructural encontrada.")
        exit(1)
    else:
        print("[*] ESTADO BFT: LIMPIO.")
        exit(0)

if __name__ == "__main__":
    main()
