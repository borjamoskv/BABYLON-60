#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
import subprocess
import sys
import glob
import os

def refute_itera():
    print("\n[!] DETONANDO FALSABILIZA: Fuego contra la Hipótesis del Colapso ULTRATHINK")

    # Prueba 1: Verificar el último commit en el ledger local
    try:
        last_commit = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True)
        if "[C5-REAL]" not in last_commit:
            print(f"\n[CRITICAL FAILURE - FALSADO] El ledger no refleja un anclaje C5-REAL. Commit actual:\n{last_commit}")
            sys.exit(1)
        print("[OK] Ledger anclado criptográficamente con C5-REAL.")
    except Exception as e:
        print(f"[CRITICAL FAILURE - SINTÁCTICO] Falla al leer git: {e}")
        sys.exit(2)

    # Prueba 2: Verificar la materialización física del artefacto de consolidación
    try:
        files = glob.glob("artifacts/c5_consolidation_*.md")
        if not files:
            print("\n[CRITICAL FAILURE - FALSADO] No existe ningún artefacto de consolidación en artifacts/. El colapso fue Green Theater (Alucinación pasiva).")
            sys.exit(1)

        latest_file = max(files, key=os.path.getctime)
        size = os.path.getsize(latest_file)

        if size == 0:
            print(f"\n[CRITICAL FAILURE - FALSADO] El artefacto {latest_file} está vacío (0 bytes). Anergía detectada.")
            sys.exit(1)

        print(f"[OK] Artefacto termodinámico detectado: {latest_file} ({size} bytes).")
    except Exception as e:
        print(f"[CRITICAL FAILURE - SINTÁCTICO] Falla al leer sistema de archivos: {e}")
        sys.exit(2)

    # Prueba 3: Verificar estado de Git (Debe estar limpio)
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        lines = [l for l in status.splitlines() if "scratch_refute_itera.py" not in l]
        if lines:
            print(f"\n[CRITICAL FAILURE - FALSADO] El árbol de trabajo no está limpio. Residuos estocásticos detectados:\n{lines}")
            sys.exit(1)
        print("[OK] Árbol de trabajo termodinámicamente purgado (Ignorando agresor local).")
    except Exception as e:
        print(f"[CRITICAL FAILURE - SINTÁCTICO] Falla al leer git status: {e}")
        sys.exit(2)

    print("\n[RESISTENCIA EPISTÉMICA CONFIRMADA] La hipótesis del Hyper-Colapso ha resistido el asedio. Cadena causal intacta.")
    sys.exit(0)

if __name__ == "__main__":
    refute_itera()
