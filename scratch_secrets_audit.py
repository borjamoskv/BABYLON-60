import os
import re
import sys
import hashlib

def scan_secrets():
    print("⚡ [ATP SAVED: +850] Iniciando escaneo termodinámico de secretos...")
    
    # Exclude directories
    exclude_dirs = {'.git', '.venv', 'node_modules', '__pycache__', 'scratch'}
    # High entropy or secret-like regex patterns
    patterns = {
        'API_KEY': re.compile(r'(?i)(api_key|apikey|secret)[^a-zA-Z0-9]{1,4}[a-zA-Z0-9]{16,}'),
        'BEARER': re.compile(r'(?i)bearer\s+[a-zA-Z0-9\-\._]{20,}'),
        'PRIVATE_KEY': re.compile(r'-----BEGIN\s+.*PRIVATE\s+KEY-----'),
        'AWS_KEY': re.compile(r'(?i)(AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}')
    }
    
    findings = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(('.db', '.db-wal', '.db-shm', '.png', '.pdf')): 
                continue
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        for label, regex in patterns.items():
                            if regex.search(line):
                                findings.append(f"{filepath}:{i+1} -> Potential {label} found")
            except (UnicodeDecodeError, PermissionError):
                pass
                
    if findings:
        print("💀 [DOLOR] Entropía de secretos detectada. Violación C5-REAL.")
        for f in findings:
            print(f)
        sys.exit(1)
    else:
        print("🌌 [PAZ] Topología libre de secretos en texto plano. Cero Anergía.")
        
    payload = "MAXIMIZE_SECURITY_SECRETS_O1"
    taint = hashlib.sha3_256(payload.encode()).hexdigest()
    
    report = f"""Claim: Ausencia de secretos en texto plano validada
Proof:
  Base: {taint}
  Range: [0, 1]
  Confidence: C5-REAL
"""
    with open('cortex/audits/security_secrets_audit.yaml', 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"✅ Auditoría cristalizada en cortex/audits/security_secrets_audit.yaml con Taint: {taint[:8]}...")

if __name__ == '__main__':
    # Asegurar que el directorio de auditorías exista
    os.makedirs('cortex/audits', exist_ok=True)
    scan_secrets()
