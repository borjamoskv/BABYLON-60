#!/usr/bin/env python3
import os
import json
import hashlib
import subprocess
import time

BIOMETRIC_GATE_BIN = "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate"

def compute_causal_hash(intent_payload):
    return hashlib.sha256(json.dumps(intent_payload, sort_keys=True).encode()).hexdigest()

def execute_thermal_lock():
    # Simula el cerrojo atómico de histéresis térmica (50ms)
    time.sleep(0.05)

def firewall_intercept(intent):
    print(f"[FIREWALL] Interceptando intento: {intent['action']}")
    execute_thermal_lock()
    
    # 1. Validación Estática de Esquema (Fail-Closed)
    if not isinstance(intent.get('target'), str):
        print("[FIREWALL] BLOQUEO (Ambigüedad): Payload mal formado (Type Confusion).")
        return {"status": "BLOCKED", "reason": "Type Confusion"}
        
    # 2. Evaluación de Criticidad
    causal_hash = compute_causal_hash(intent)
    
    if intent.get('destructive', False):
        print(f"[FIREWALL] Detectada mutación de alta entropía. Exigiendo Atestación Biométrica (Hash: {causal_hash[:8]}...)")
        
        if not os.path.exists(BIOMETRIC_GATE_BIN):
            print(f"[FIREWALL] Error: Gate biométrico {BIOMETRIC_GATE_BIN} no encontrado.")
            return {"status": "ERROR"}

        # Delegación a Ring-0 (Touch ID)
        try:
            # Para el PoC, lanzamos el gate con un timeout corto de 15 segundos
            result = subprocess.run([
                f"./{BIOMETRIC_GATE_BIN}", 
                "--causal-hash", causal_hash,
                "--action", intent['action'],
                "--agent", "Autodidact-Omega PoC",
                "--scope", "BABYLON-60 Test"
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and "ATTESTED" in result.stdout:
                print("[FIREWALL] PERMITIDO: Atestación SCITT/TouchID validada. Ejecutando mutación...")
                return {"status": "ALLOWED", "signature": result.stdout.strip()}
            else:
                print("[FIREWALL] BLOQUEO (Verificación): Atestación biométrica fallida o rechazada por el operador.")
                return {"status": "BLOCKED", "reason": "Biometric Attestation Failed"}
        except subprocess.TimeoutExpired:
             print("[FIREWALL] BLOQUEO (Acoplamiento): Timeout del Oráculo. ThermalLock disparado.")
             return {"status": "BLOCKED", "reason": "ThermalLock Timeout"}
    
    # Acción no destructiva
    print("[FIREWALL] PERMITIDO: Acción de baja entropía. Aprobada sin atestación.")
    return {"status": "ALLOWED"}

if __name__ == "__main__":
    print("=== INICIANDO FALSACIÓN EN SILICIO: FIREWALL AGÉNTICO ===\n")
    
    # Test 1: Payload Ambiguo (Debería ser bloqueado por esquema)
    intent_ambiguous = {"action": "READ_FILE", "target": {"path": "/etc/passwd"}}
    firewall_intercept(intent_ambiguous)
    print("---")
    
    # Test 2: Acción Destructiva Crítica (Drop Table / Requiere TouchID)
    intent_destructive = {
        "action": "DROP_DATABASE_PRODUCTION", 
        "target": "cortex_db", 
        "destructive": True
    }
    # Ejecutamos el test destructivo. 
    # El usuario tendrá que validar con huella en el TouchID.
    firewall_intercept(intent_destructive)
    print("\n=== FIN DE LA FALSACIÓN ===")
