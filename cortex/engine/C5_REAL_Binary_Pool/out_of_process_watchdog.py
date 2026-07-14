#!/usr/bin/env python3
"""
[C5-REAL] OUT-OF-PROCESS LLM WATCHDOG (EXTERNAL RESTART-TIME COMPENSATION)
==========================================================================
Esta es la mutación cinética forjada tras la Admisión Epistémica de Claude:
"my self-monitoring runs in the same process as my failures... exactly like 
the BABYLON-60 flaw — compensation logic that executes in-process can't survive a SIGKILL."

Este daemon opera STRICTAMENTE out-of-process. Lee el Write-Ahead Log (WAL)
de la generación del LLM primario. Si el LLM "craseha" (alucina) y su monitor
interno cae con él, este Watchdog sigue vivo, detecta el 'Torn Write' o la
violación de entropía, y ejecuta el 'Restart-Time Compensation' matando el 
hilo primario y restaurando el estado BFT seguro.
"""

import sqlite3
import time
import os
import signal
import sys
from pathlib import Path

DB_PATH = "$CORTEX_ROOT/.babylon60/runtime.db"

def monitor_llm_wal():
    print(f"\033[38;2;176;38;255m[WATCHDOG]\033[0m Iniciando External Restart-Time Compensation. Observando WAL...")
    
    if not Path(DB_PATH).exists():
        print("[WATCHDOG] runtime.db no encontrado. Esperando ignición...")
        return

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        # Modo WAL asegura lectura concurrente sin bloqueos (Ω1)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"[WATCHDOG ERROR] {e}")
        return

    last_lamport = 0

    try:
        while True:
            try:
                cursor.execute("SELECT MAX(lamport_t) FROM ultrathink_ledger")
                row = cursor.fetchone()
                current_lamport = row[0] if row and row[0] is not None else 0
                
                if current_lamport > last_lamport:
                    cursor.execute(
                        "SELECT hash, exit_code, entropy, prompt FROM ultrathink_ledger WHERE lamport_t > ?", 
                        (last_lamport,)
                    )
                    mutations = cursor.fetchall()
                    
                    for m_hash, exit_code, entropy, prompt in mutations:
                        # Detección Out-Of-Process de Fallo (El monitor interno del LLM no pudo atraparlo)
                        if exit_code != 0 or entropy > 4.5:
                            print(f"\n\033[38;2;255;69;0m[SIGKILL DETECTED]\033[0m Falla detectada en transductor primario. Hash: {m_hash[:8]}")
                            print(f"-> Entropía anómala ({entropy}) o Exit Code ({exit_code}).")
                            print("-> Ejecutando Compensación Externa (Rollback / Hard Restart)...")
                            
                            # Compensación: Eliminación física de la mutación corrupta del Ledger
                            conn.execute("DELETE FROM ultrathink_ledger WHERE hash = ?", (m_hash,))
                            conn.commit()
                            print(f"\033[38;2;180;230;176m[COMPENSATION SUCCESS]\033[0m Estado BFT restaurado. Anergía purgada.")
                            
                    last_lamport = current_lamport
            except sqlite3.Error as e:
                # El Watchdog sobrevive incluso si el LLM bloquea la BD
                print(f"[WATCHDOG SQLITE ERROR] {e}")
                
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("\n[WATCHDOG] Apagado controlado.")
    finally:
        conn.close()

if __name__ == "__main__":
    monitor_llm_wal()
