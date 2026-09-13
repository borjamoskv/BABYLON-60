#!/usr/bin/env python3
import sys
import uuid
from pathlib import Path

# Add the parent directory to the python path so we can import babylon60
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "01_ORCHESTRATOR"))

from babylon60.verification.verification_gate import VerificationGate

def main() -> None:
    print("============================================================")
    print(" 🛡️  C5-REAL: PRUEBA DE CONCEPTO DE CAUSAL SIGN-OFF (TOUCHID) ")
    print("============================================================")
    print("\nInicializando KERNEL VerificationGate...")
    
    # We use a temporary local sqlite db for the demo
    gate = VerificationGate(db_path="/tmp/babylon60_audit_demo.sqlite")
    
    execution_id = str(uuid.uuid4())
    action_name = "PURGE_LEGACY_MODULE"
    description = "Eliminación irreversible del directorio apps/babylon60-ide (Migración a LSP Paracortex)"
    
    print("\n[!] El agente autónomo propone la siguiente acción destructiva:")
    print(f"    - Acción: {action_name}")
    print(f"    - Descripción: {description}")
    print("    - Riesgo: CRITICAL")
    print("\nInvocando Secure Enclave (TouchID / Password) para atestación de firma...\n")
    
    success = gate.enforce_biometric_sign_off(execution_id, action_name, description)
    
    if success:
        print("\n[✓] EXITO: El humano ha firmado la transacción de estado.")
        print("    Verificando SQLite WAL...")
        
        # Check that it was inserted
        cur = gate._conn.cursor()
        cur.execute("SELECT cryptographic_digest, decision FROM audit_ledger ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            print(f"    -> [LEDGER ENTRY] Hash: {row[0]}")
            print(f"    -> [LEDGER ENTRY] Decisión: {row[1]}")
    else:
        print("\n[X] FALLO: El humano ha rechazado la firma o se ha agotado el tiempo.")
        print("    El agente tiene el paso denegado por el Ring-0.")

if __name__ == "__main__":
    main()
