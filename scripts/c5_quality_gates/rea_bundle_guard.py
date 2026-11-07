#!/usr/bin/env python3
"""
BABYLON-60 · REA Bundle Guard (Ring-0)
Verifica que los ejecutables y bundles .app no contengan rutas dylib huérfanas
ni vulnerabilidades de carga dinámica en macOS mediante REA de Morluto.
"""
import subprocess
import sys
from pathlib import Path

APP_PATH = Path("/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/apps/mandato/Mandato.app")

def verify_mandato_bundle():
    if not APP_PATH.exists():
        print(f"[SKIP] Mandato.app no encontrado en {APP_PATH}")
        return 0
    cmd = ["rea", "trace-dylib-resolution", str(APP_PATH), "--architecture", "arm64", "--format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[FAIL] REA rechazo la resolucion de Mandato.app: {proc.stderr}")
        return 1
    print("[PASS] Mandato.app: Resolucion dyld arm64 certificada por REA.")
    return 0

if __name__ == "__main__":
    sys.exit(verify_mandato_bundle())
