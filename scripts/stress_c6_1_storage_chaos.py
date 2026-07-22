"""C6.1 Storage Chaos — kill_during_checkpoint validation."""

import multiprocessing
import os
import signal
import sqlite3
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, ".cortex", "stress_c6_1.db")

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

def writer_and_checkpointer_loop() -> None:
    """Runs continuous writes and periodic explicit WAL checkpoints."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    # Lower wal_autocheckpoint so it happens frequently, 
    # but we will also trigger it explicitly to maximize kill probability during the checkpoint.
    conn.execute("PRAGMA wal_autocheckpoint = 100;") 
    
    idx = 0
    while True:
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            # Simulate a multi-step transaction to ensure atomicity
            # If the process is killed between these inserts or during commit/checkpoint,
            # we should never see a PARTIAL state persist.
            cursor.execute("INSERT INTO stress_log (tx_data, status) VALUES (?, ?)", (f"payload_{idx}_A", "PARTIAL"))
            cursor.execute("INSERT INTO stress_log (tx_data, status) VALUES (?, ?)", (f"payload_{idx}_B", "COMMITTED"))
            conn.commit()
            
            # Explicitly force a WAL checkpoint to create contention and vulnerability
            # RESTART will block until all readers are finished and then checkpoint
            if idx % 50 == 0:
                conn.execute("PRAGMA wal_checkpoint(RESTART);")
                
        except sqlite3.Error:
            pass
            
        idx += 1

def run_chaos(duration_sec: int = 15, kill_interval: float = 0.2) -> None:
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  C6.1 STORAGE CHAOS — kill_during_checkpoint                     ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    init_db()
    
    start_time = time.time()
    crashes = 0
    
    print(f"\n[C6.1] Iniciando asedio kill_during_checkpoint (Duración: {duration_sec}s)...")
    while time.time() - start_time < duration_sec:
        p = multiprocessing.Process(target=writer_and_checkpointer_loop)
        p.start()
        
        # Sleep a fraction to let it build some WAL and start checkpointing
        time.sleep(kill_interval)
        
        if p.is_alive() and p.pid is not None:
            os.kill(p.pid, signal.SIGKILL)
            p.join()
            crashes += 1
            print(f"  💥 SIGKILL inyectado en vuelo (Crash #{crashes})")
            
    # Audit
    print("\n[!] Asedio completado. Verificando Invariantes C6.1...")
    conn = sqlite3.connect(DB_PATH)
    
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stress_log")
    total_tx = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stress_log WHERE status = 'PARTIAL'")
    partial_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stress_log WHERE status = 'COMMITTED'")
    committed_count = cursor.fetchone()[0]
    
    conn.close()
    
    leaks = partial_count - committed_count
    
    print(f"  Crashes Inyectados                 : {crashes}")
    print(f"  Operaciones Totales (Filas)        : {total_tx:,}")
    print(f"  Integrity Check del FS             : {integrity.upper()}")
    print(f"  Filas PARTIAL / COMMITTED          : {partial_count:,} / {committed_count:,}")
    print(f"  Transacciones Huérfanas (Fugas)    : {leaks}")
    
    if integrity == "ok" and leaks == 0:
        print("\n✓ C6.1 STORAGE CHAOS: SUPERADO.")
        print("  - safety: database_not_corrupted = TRUE")
        print("  - durability: uncommitted_tx_visibility = 0")
        print("  - atomicity: partial_transaction_state = FALSE")
    else:
        print("\n⚠ ANERGÍA DETECTADA: Corrupción o fuga transaccional.")
        sys.exit(1)

if __name__ == "__main__":
    run_chaos()
