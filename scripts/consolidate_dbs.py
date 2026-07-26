#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
"""
Consolidación BFT (Erradicación del Antipatrón de Dispersión SQLite)
====================================================================
Script para consolidar todas las bases de datos de CORTEX PERSIST en
un único directorio maestro soberano (~/.babylon60/dbs/) y purgar
(unlink) todas las bases de datos redundantes o de pruebas.

Authorship: Telmo Dinámico de Moskv (borjamoskv)
"""

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CENTRAL_DIR = Path.home() / ".babylon60" / "dbs"

MASTER_LEDGERS = {
    "cortex.db",
    "master_ledger.db",
    "cortex_memory.db",
    "ultrathink_ledger.db",
    "telemetry.db"
}

def consolidate_dbs():
    print(f"🟢 Iniciando Consolidación BFT C5-REAL hacia {CENTRAL_DIR}")
    CENTRAL_DIR.mkdir(parents=True, exist_ok=True)
    
    db_paths = [
        p for p in REPO_ROOT.rglob("*.db")
        if not any(part in ("venv", ".venv", ".git", "__pycache__") for part in p.parts)
    ]
    
    purged = 0
    moved = 0
    
    for db_path in db_paths:
        name = db_path.name
        
        # Determine if it should be preserved/moved or purged
        if name in MASTER_LEDGERS and "archive" not in db_path.parts:
            # Move to central dir
            dest = CENTRAL_DIR / name
            if db_path != dest:
                if not dest.exists():
                    print(f"📦 Moviendo Ledger Maestro: {db_path.relative_to(REPO_ROOT)} -> {dest}")
                    shutil.copy2(db_path, dest)
                else:
                    print(f"⚠️ Ledger Maestro ya existe en destino, ignorando: {name}")
                moved += 1
        
        # Purgar archivo original de la ruta local
        try:
            db_path.unlink(missing_ok=True)
            purged += 1
            print(f"🧹 Purgada DB local: {db_path.relative_to(REPO_ROOT)}")
            
            # Purgar también wal y shm
            wal_path = db_path.with_suffix(".db-wal")
            if wal_path.exists():
                wal_path.unlink()
            
            shm_path = db_path.with_suffix(".db-shm")
            if shm_path.exists():
                shm_path.unlink()
        except Exception as e:
            print(f"🔴 Error al purgar {name}: {e}")
            
    print(f"\n============================================================")
    print(f" CONSOLIDACIÓN COMPLETADA")
    print(f"============================================================")
    print(f" Ledgers Maestros movidos a ~/.babylon60/dbs/ : {moved}")
    print(f" Bases de datos de entropía local purgadas      : {purged}")
    print(f"============================================================\n")

if __name__ == "__main__":
    consolidate_dbs()
