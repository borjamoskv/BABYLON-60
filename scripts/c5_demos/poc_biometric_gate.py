#!/usr/bin/env python3
import subprocess
import sys
import os
import hashlib
import time
from pathlib import Path

print("[AX-4] Iniciando PoC Causal: Puente Biométrico TouchID")

# Determinar si estamos en un entorno interactivo crudo (fuera del sandbox del agente)
is_sovereign_tty = sys.stdout.isatty() and os.environ.get("TERM_PROGRAM") != "vscode"

print(f"[!] TTY Soberano: {is_sovereign_tty}")
print(f"[!] TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'N/A')}")

# Generar un hash señuelo
raw_pre_hash = f"poc_execution|test_action|{time.time()}"
causal_hash = hashlib.sha256(raw_pre_hash.encode("utf-8")).hexdigest()

_root = Path(os.environ.get("BABYLON_HOME", Path(__file__).resolve().parent.parent.parent))
script_path = _root / "01_KISH_ENGINE" / "babylon60" / "guards" / "c5_biometric_gate.swift"

print("\n--- Ejecutando Falsación Biométrica ---")
try:
    # Usar timeout para prevenir deadlocks en el sandbox
    result = subprocess.run(
        ["swift", str(script_path), "--causal-hash", causal_hash, "--message", "PoC de Validación Causal"],
        capture_output=True,
        text=True,
        timeout=10, 
    )
    if result.returncode == 0:
        print(f"[✓] ÉXITO. Firma obtenida:\n{result.stdout.strip()}")
    else:
        print(f"[X] FALLO ESPERADO (Sandbox). Código: {result.returncode}")
        print(f"Stderr: {result.stderr.strip()}")
except subprocess.TimeoutExpired:
    print("[X] COLAPSO TERMODINÁMICO: El proceso entró en Deadlock (Silenciamiento del WindowServer).")
except Exception as e:
    print(f"[X] ERROR NO CONTROLADO: {e}")

print("\nDICTAMEN: El despliegue biométrico exige ejecución manual soberana.")
