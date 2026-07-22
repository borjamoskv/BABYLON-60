"""C6.1 Checkpoint Chaos reproducible experiment (V1.1)."""
import os
import sys
import multiprocessing
import ctypes
import sqlite3
import platform
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
    print("║  C6.1 DETERMINISTIC CHECKPOINT STORM                             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    init_db()
    
    shared_phase = multiprocessing.Array(ctypes.c_char, 32)
    shared_phase.value = b"INIT"
    
    stop_event = multiprocessing.Event()
    
    # Deterministic campaigns
    campaigns = {
        "WAL_APPEND": 20,
        "CHECKPOINT": 40,
        "FSYNC_BOUNDARY": 20,
        "AFTER_COMMIT_BEFORE_ACK": 20
    }
    
    total_attacks = sum(campaigns.values())
    crashes = 0
    
    print(f"\n[C6-REAL] Inyectando campaña determinista: {total_attacks} asedios totales...")
    
    for i in range(total_attacks):
        worker = multiprocessing.Process(target=target_worker, args=(shared_phase,))
        worker.start()
        
        if worker.pid is not None:
            orchestrator = multiprocessing.Process(
                target=chaos_orchestrator, 
                args=(worker.pid, campaigns, shared_phase, stop_event)
            )
            orchestrator.start()
            
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
        
    print(f"\n[!] Asedio completado ({crashes} crashes exitosos). Analizando recuperación...")
    
    recovery_result = analyze_sqlite_recovery(DB_PATH)
    
    env_data = {
        "sqlite_version": sqlite3.sqlite_version,
        "kernel": platform.release(),
        "filesystem": "APFS" if platform.system() == "Darwin" else "UNKNOWN"
    }
    
    attestation = generate_attestation(
        experiment_id="C6.1_CHECKPOINT_STORM_001",
        environment=env_data,
        attacks_injected=crashes,
        storage_recovery=recovery_result
    )
    
    print("\n" + attestation.to_yaml_str())
    
    if attestation.safety_pass and attestation.durability_pass and attestation.recovery_pass:
        print("\n✓ C6.1 STORAGE CHAOS: ATTESTATION 1.0 (VERIFIED)")
    else:
        print("\n⚠ ANERGÍA DETECTADA: La identidad temporal colapsó.")
        sys.exit(1)

if __name__ == "__main__":
    run_c6_1_experiment()
