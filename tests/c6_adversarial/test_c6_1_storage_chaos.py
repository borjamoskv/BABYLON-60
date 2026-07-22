"""C6.1 Checkpoint Chaos reproducible experiment."""
import os
import sys
import time
import multiprocessing
import ctypes
import sqlite3
from typing import Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.c6_harness.fault_injector import chaos_orchestrator
from cortex.c6_harness.recovery import analyze_sqlite_recovery
from cortex.c6_harness.auditor import generate_attestation

DB_PATH = os.path.join(PROJECT_ROOT, ".cortex", "c6_harness_test.db")

def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stress_log (
            id INTEGER PRIMARY KEY,
            tx_data TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def target_worker(shared_phase: Any) -> None: # type: ignore
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA wal_autocheckpoint = 10;") 
    
    idx = 0
    while True:
        try:
            shared_phase.value = b"WAL_APPEND"
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("INSERT INTO stress_log (tx_data, status) VALUES (?, ?)", (f"payload_{idx}_A", "PARTIAL"))
            cursor.execute("INSERT INTO stress_log (tx_data, status) VALUES (?, ?)", (f"payload_{idx}_B", "COMMITTED"))
            
            shared_phase.value = b"FSYNC_BOUNDARY"
            conn.commit()
            
            if idx > 0 and idx % 10 == 0:
                shared_phase.value = b"CHECKPOINT"
                conn.execute("PRAGMA wal_checkpoint(RESTART);")
                
            shared_phase.value = b"AFTER_COMMIT_BEFORE_ACK"
                
        except sqlite3.Error:
            pass
            
        idx += 1

def run_c6_1_experiment() -> None:
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  C6.1 STORAGE CHAOS HARNESS EXPERIMENT                           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    init_db()
    
    # Using shared memory for phase tracking
    shared_phase = multiprocessing.Array(ctypes.c_char, 32)
    shared_phase.value = b"INIT"
    
    stop_event = multiprocessing.Event()
    
    # We will run 10 iterations of worker + assassination
    crashes = 0
    probabilities = {
        "WAL_APPEND": 0.25,
        "CHECKPOINT": 0.50, # Boosted to attack the checkpoint boundary
        "FSYNC_BOUNDARY": 0.25,
        "AFTER_COMMIT_BEFORE_ACK": 0.25
    }
    
    print(f"\n[C6-REAL] Inyectando fallos probabilísticos a lo largo de 10 iteraciones...")
    
    for i in range(10):
        worker = multiprocessing.Process(target=target_worker, args=(shared_phase,))
        worker.start()
        
        # Start orchestrator
        if worker.pid is not None:
            orchestrator = multiprocessing.Process(
                target=chaos_orchestrator, 
                args=(worker.pid, probabilities, shared_phase, stop_event)
            )
            orchestrator.start()
            
            # Wait until the worker dies (assassinated) or timeout
            worker.join(timeout=3.0)
            
            if worker.is_alive():
                worker.terminate()
                worker.join()
            else:
                crashes += 1
                phase_decoded = shared_phase.value.decode('utf-8').strip(chr(0))
                print(f"  💥 SIGKILL inyectado en fase: {phase_decoded}")
                
            stop_event.set()
            orchestrator.join()
            stop_event.clear()
        
    print("\n[!] Asedio completado. Analizando recuperación...")
    
    recovery_result = analyze_sqlite_recovery(DB_PATH)
    attestation = generate_attestation(recovery_result)
    
    print("\n" + attestation.to_yaml_str())
    
    if attestation.temporal_identity_verified:
        print("\n✓ C6.1 STORAGE CHAOS: ATTESTATION 1.0 (VERIFIED)")
    else:
        print("\n⚠ ANERGÍA DETECTADA: La identidad temporal colapsó.")

if __name__ == "__main__":
    run_c6_1_experiment()
