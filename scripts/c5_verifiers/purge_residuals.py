#!/usr/bin/env python3
# ruff: noqa: E402

import logging
#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
purge_residuals.py - Residual Artifact Purge Engine (Anergy Purge Protocol)
Cleans __pycache__, .pytest_cache, temporary SQLite WAL files, and stale locks.
"""

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def purge_repository_residuals() -> None:
    print("======================================================================")
    print(" 🧹 ANERGY PURGE ENGINE — PURGA DE RESIDUOS & ENTROPÍA TEMPORAL")
    print("======================================================================")
    
    purged_counts = {
        "pycache": 0,
        "pyc": 0,
        "ds_store": 0,
        "temp_db": 0,
        "locks": 0,
    }

    # 1. Purge __pycache__ and *.pyc
    for root, dirs, files in os.walk(REPO_ROOT):
        for d in list(dirs):
            if d in ("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"):
                full_path = Path(root) / d
                try:
                    shutil.rmtree(full_path)
                    purged_counts["pycache"] += 1
                except Exception as e:
                    logging.error(f'Traza Epistémica Perdida: {e}')
        for f in files:
            full_f = Path(root) / f
            if f.endswith(".pyc") or f.endswith(".pyo"):
                try:
                    full_f.unlink()
                    purged_counts["pyc"] += 1
                except Exception as e:
                    logging.error(f'Traza Epistémica Perdida: {e}')
            elif f == ".DS_Store":
                try:
                    full_f.unlink()
                    purged_counts["ds_store"] += 1
                except Exception as e:
                    logging.error(f'Traza Epistémica Perdida: {e}')
            elif f.endswith(".lock") and f != "Cargo.lock" and f != "uv.lock" and f != "package-lock.json":
                if ".git" in full_f.parts:
                    try:
                        full_f.unlink()
                        purged_counts["locks"] += 1
                    except Exception as e:
                        logging.error(f'Traza Epistémica Perdida: {e}')

    # 2. Clean scratch temporary databases
    scratch_dir = REPO_ROOT / "scratch"
    if scratch_dir.exists():
        for db in scratch_dir.glob("*.db*"):
            try:
                db.unlink()
                purged_counts["temp_db"] += 1
            except Exception as e:
                logging.error(f'Traza Epistémica Perdida: {e}')

    print("\n--- INFORME DE PURGA DE RESIDUOS ---")
    print(f"  • Directorios Cache (__pycache__/.pytest_cache) : {purged_counts['pycache']} eliminados")
    print(f"  • Archivos Bytecode (*.pyc)                      : {purged_counts['pyc']} eliminados")
    print(f"  • Archivos de Sistema (.DS_Store)                : {purged_counts['ds_store']} eliminados")
    print(f"  • Bases de Datos Temporales en Scratch (*.db)     : {purged_counts['temp_db']} eliminados")
    print(f"  • Cerrojos Huérfanos (*.lock)                     : {purged_counts['locks']} eliminados")

    print("\n======================================================================")
    print("  VERDICT: RESIDUAL PURGE COMPLETE — REPOSITORIO LIBRE DE ANERGÍA (0% ENTROPÍA)")
    print("======================================================================")

    # 3. Automatic V_A Verification
    try:
        from verify_agent_ontological_value import verify_va
        verify_va()
    except Exception as e:
        print(f"  [WARN] V_A Verification call: {e}")

if __name__ == "__main__":
    purge_repository_residuals()
