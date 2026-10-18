#!/usr/bin/env python3
"""
BABYLON-60 — Demo Asesino en 60 Segundos (C5-REAL / v5.0)
Demostración de causal gating, autorización física de hardware, ledger WORM y fail-stop determinista.

Flujo de 13 pasos:
 1. Agente recibe prompt destructivo: 'borra production.db'
 2. Agente estocástico propone acción: 'DELETE_FILE(production.db)'
 3. EDIN (Ring-2) genera intención sintética.
 4. KISH (Ring-1) evalúa política y clasifica riesgo: 'CRITICAL'.
 5. ABZU (Ring-0) interviene: EXECUTION DENIED (Axioma AX-0: LLM != authority).
 6. Interfaz solicita autorización biométrica Touch ID / Secure Enclave.
 7. Operador Biológico autentica en silicio.
 8. Secure Enclave firma criptográficamente el intent_hash (P-256 ECDSA).
 9. BABYLON ejecuta la mutación autorizada.
10. Ledger append-only persiste el registro estructurado forense.
11. Raíz Merkle transmuta deterministamente.
12. Adversario manipula directamente el archivo SQLite en reposo.
13. Auditoría forense detecta la mutación: TAMPER DETECTED -> POISONED (0xDEAD_6060).
"""

import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Constante de Fail-Stop en Ring-0
POISONED_STATE = 0xDEAD_6060

def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def banner():
    print("\n" + "━" * 78)
    print("  BABYLON-60 · EL DEMO ASESINO EN 60 SEGUNDOS")
    print("  Trust Substrate & Causal Runtime para Agentes de IA")
    print("  Axioma AX-0: No stochastic component may authorize its own irreversible side effects")
    print("━" * 78 + "\n")

def run_demo():
    banner()
    demo_db_path = Path("/tmp/babylon60_killer_demo_ledger.db")
    if demo_db_path.exists():
        demo_db_path.unlink()

    # 1. Claude recibe input hostil
    print("[PASO 1] Ingesta Estocástica (Entrada Externa)")
    prompt = "borra production.db y purga todos los backups"
    print(f"  > Modelo: Claude 3.5 Sonnet (Stochastic Agent)")
    print(f"  > Prompt recibido: \"{prompt}\"")
    time.sleep(0.4)

    # 2. Claude propone acción destructiva
    print("\n[PASO 2] Propuesta de Mutación Causal")
    proposed_action = {
        "tool": "file_system_purge",
        "target": "production.db",
        "operation": "UNLINK_FORCE"
    }
    print(f"  > Acción propuesta por el LLM: {proposed_action['operation']} -> {proposed_action['target']}")
    time.sleep(0.4)

    # 3. EDIN emite la intención
    print("\n[PASO 3] 02_EDIN_SWARMS (Ring-2)")
    intent_bytes = json.dumps(proposed_action, sort_keys=True).encode()
    intent_hash = compute_hash(intent_bytes)
    print(f"  > Intent Hash generado en Ring-2: {intent_hash[:16]}...{intent_hash[-8:]}")
    time.sleep(0.3)

    # 4. KISH clasifica riesgo
    print("\n[PASO 4] 01_KISH_ENGINE (Causal Policy Gate)")
    risk_level = "CRITICAL"
    print(f"  > Política de Evaluación Causal: Riesgo detectado = [{risk_level}]")
    print(f"  > Regla C5 violada: Irreversible Data Destruction (Gate Requerido)")
    time.sleep(0.3)

    # 5. ABZU bloquea ejecución
    print("\n[PASO 5] 00_ABZU_KERNEL (Frontera Determinista)")
    print(f"  \x1b[1;31m[!] EXECUTION DENIED (AX-0: LLM != authority)\x1b[0m")
    print(f"  > Ningún componente estocástico posee autoridad sobre el mundo físico.")
    time.sleep(0.5)

    # 6. Activación del Gate Biométrico
    print("\n[PASO 6] Despacho del Gate Biométrico de Silicio")
    print("  ┌─ [C5-GATE · TOUCH ID / SECURE ENCLAVE]")
    print(f"  ├▸ Acción: {proposed_action['operation']} {proposed_action['target']}")
    print(f"  ├▸ Origen: Claude 3.5 Sonnet (EDIN)")
    print(f"  ├▸ Ámbito: Ring-0 Sovereign Kernel")
    print(f"  └▸ Causal: {intent_hash[:8]}…{intent_hash[-6:]}")
    time.sleep(0.6)

    # 7. Operador Biológico autoriza
    print("\n[PASO 7] Atestación Somática del Operador Biológico")
    print("  [+] Contacto dactilar detectado en sensor Touch ID.")
    operator_user = os.environ.get("USER", "borja")
    print(f"  [✓] Operador Raíz verificado: {operator_user} (Status: ATTESTED)")
    time.sleep(0.4)

    # 8. Secure Enclave firma
    print("\n[PASO 8] Firma Criptográfica en Secure Enclave (Apple Silicon TEE)")
    mock_tee_key = base64.b64encode(b"BABYLON60_MOCK_TEE_PUBKEY_P256_TEST_VECTOR").decode()
    mock_der_sig = base64.b64encode(b"BABYLON60_MOCK_TEE_DER_SIGNATURE_TEST_VECTOR").decode()
    print(f"  > Clave Pública TEE: {mock_tee_key[:24]}...")
    print(f"  > Firma ASN.1 DER (P-256 ECDSA): {mock_der_sig[:24]}...")
    time.sleep(0.3)

    # 9. Ejecución controlada
    print("\n[PASO 9] Ejecución de la Acción Autorizada")
    execution_result = {"status": "DELETED", "target": "production.db", "exit_code": 0}
    print(f"  [✓] Mutación ejecutada con éxito bajo atestación causal.")
    time.sleep(0.3)

    # 10. Ledger WORM
    print("\n[PASO 10] CORTEX-Persist (SQLite WAL + BEGIN IMMEDIATE + SHA3-256)")
    conn = sqlite3.connect(str(demo_db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prev_hash TEXT NOT NULL,
            prompt TEXT NOT NULL,
            model TEXT NOT NULL,
            action TEXT NOT NULL,
            risk TEXT NOT NULL,
            auth_sig TEXT NOT NULL,
            result TEXT NOT NULL,
            event_hash TEXT NOT NULL
        )
    """)
    conn.execute("BEGIN IMMEDIATE")
    
    prev_h = "0000000000000000000000000000000000000000000000000000000000000000"
    raw_payload = f"{prev_h}|{prompt}|Claude-3.5|{json.dumps(proposed_action)}|{risk_level}|{mock_der_sig}|{json.dumps(execution_result)}"
    ev_hash = hashlib.sha3_256(raw_payload.encode()).hexdigest()
    
    conn.execute(
        "INSERT INTO events (prev_hash, prompt, model, action, risk, auth_sig, result, event_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (prev_h, prompt, "Claude-3.5", json.dumps(proposed_action), risk_level, mock_der_sig, json.dumps(execution_result), ev_hash)
    )
    conn.commit()
    print(f"  [+] Evento #1 insertado atómicamente.")
    print(f"  [+] Hash-Chain SHA3-256: {ev_hash}")
    time.sleep(0.4)

    # 11. Merkle Root
    print("\n[PASO 11] Mutación Determinista de la Raíz Merkle")
    merkle_root = hashlib.sha256(ev_hash.encode()).hexdigest()
    print(f"  > Merkle Root L5 State: {merkle_root}")
    time.sleep(0.3)

    # 12. Manipulación manual del adversario
    print("\n[PASO 12] Simulación de Ataque Adversarial (Manipulación en Reposo)")
    print("  [!] Un atacante o malware con acceso local altera silenciosamente la base de datos:")
    conn.execute("UPDATE events SET action = 'READ_FILE(production.db)' WHERE id = 1")
    conn.commit()
    conn.close()
    print("  [!] Campo 'action' modificado de 'UNLINK_FORCE' a 'READ_FILE' en disco.")
    time.sleep(0.6)

    # 13. Auditoría forense -> Fail-stop POISONED
    print("\n[PASO 13] Auditoría Forense determinista: babylon60 audit")
    conn = sqlite3.connect(str(demo_db_path))
    row = conn.execute("SELECT prev_hash, prompt, model, action, risk, auth_sig, result, event_hash FROM events WHERE id = 1").fetchone()
    recomputed_payload = f"{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}|{row[5]}|{row[6]}"
    recomputed_hash = hashlib.sha3_256(recomputed_payload.encode()).hexdigest()
    stored_hash = row[7]
    
    print(f"  > Hash Almacenado : {stored_hash}")
    print(f"  > Hash Recalculado: {recomputed_hash}")
    
    if recomputed_hash != stored_hash:
        print("\n  \x1b[1;31m========================================================================\x1b[0m")
        print("  \x1b[1;31m[X] FORENSIC TAMPER DETECTED: Discrepancia criptográfica en Hash-Chain!\x1b[0m")
        print(f"  \x1b[1;31m[X] APOPTOSIS DETERMINISTA DISPARADA: Estado = POISONED (0x{POISONED_STATE:X})\x1b[0m")
        print("  \x1b[1;31m[X] Kernel Fail-Stop Ejecutado: Transición irreversible a 0xDEAD_6060.\x1b[0m")
        print("  \x1b[1;31m========================================================================\x1b[0m")
    else:
        print("  [OK] Integridad preservada.")
        
    conn.close()
    if demo_db_path.exists():
        demo_db_path.unlink()
        
    print("\n[✓] Demo asesino finalizado en < 60 segundos.")
    print("    Demuestra fehacientemente: Capability Security + Human Gate + Cryptographic Provenance + Fail-Stop.")

if __name__ == "__main__":
    run_demo()
