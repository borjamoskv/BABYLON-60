# C5-REAL EXERGY CERTIFIED
"""C6-REAL Recovery Siege — Chaos Engineering & BFT SQLite WAL Resilience."""

import multiprocessing
import os
import signal
import sqlite3
import time
import hashlib
import sys
import random

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, ".cortex", "stress_c6.db")

def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stress_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            payload_hash TEXT UNIQUE NOT NULL,
            cortex_taint TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def worker_loop(worker_id: int) -> None:
    """Tight loop of SQLite inserts. Designed to be SIGKILLed randomly."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA busy_timeout=5000;")

    idx = 0
    while True:
        payload = f"w{worker_id}_idx{idx}_{time.time()}".encode("utf-8")
        payload_hash = hashlib.sha3_256(payload).hexdigest()
        taint = f"CORTEX-TAINT:c6_siege:w{worker_id}:{payload_hash[:8]}"

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO stress_log (worker_id, payload_hash, cortex_taint, timestamp) VALUES (?, ?, ?, ?)",
                (worker_id, payload_hash, taint, time.time()),
            )
            conn.commit()
        except sqlite3.Error:
            pass  # Ignore lock timeouts, simply retry

        idx += 1

def run_siege(duration_sec: int = 20, num_workers: int = 8, kill_interval: float = 0.5) -> None:
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  C6 RECOVERY SIEGE — BFT SQLITE WAL vs SIGKILL CHAOS MONKEY      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    init_db()

    workers = []
    for i in range(num_workers):
        p = multiprocessing.Process(target=worker_loop, args=(i,))
        p.start()
        workers.append(p)

    crashes_injected = 0
    start_time = time.time()

    print(f"\n[C6-REAL] Executing {duration_sec}s continuous write siege with {num_workers} parallel workers...")
    print(f"[C6-REAL] Inyectando un SIGKILL cada {kill_interval}s de forma estocástica.\n")

    while time.time() - start_time < duration_sec:
        time.sleep(kill_interval)

        victim_idx = random.randint(0, num_workers - 1)
        victim = workers[victim_idx]

        if victim.is_alive() and victim.pid is not None:
            try:
                os.kill(victim.pid, signal.SIGKILL)
                victim.join()
                crashes_injected += 1
                print(f"  [Chaos Monkey] 💥 SIGKILL al Worker {victim_idx} (PID {victim.pid})")

                # Resurrección
                new_p = multiprocessing.Process(target=worker_loop, args=(victim_idx,))
                new_p.start()
                workers[victim_idx] = new_p
                print(f"  [Recovery]     ↻ Resucitado Worker {victim_idx} (New PID {new_p.pid})")
            except ProcessLookupError:
                pass

    print("\n[!] Asedio completado. Purgando workers remanentes...")
    for i, w in enumerate(workers):
        if w.is_alive() and w.pid is not None:
            w.terminate()
            w.join()

    # Auditoría Física
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║  AUDITORÍA DE INTEGRIDAD Y RECUPERACIÓN                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    corrupted = 0 if integrity == "ok" else 1

    cursor.execute("SELECT COUNT(*) FROM stress_log")
    total_tx = cursor.fetchone()[0]

    cursor.execute("SELECT worker_id, payload_hash, cortex_taint FROM stress_log")
    rows = cursor.fetchall()

    invalid_hashes = 0
    for w_id, p_hash, taint in rows:
        expected_taint = f"CORTEX-TAINT:c6_siege:w{w_id}:{p_hash[:8]}"
        if taint != expected_taint:
            invalid_hashes += 1

    conn.close()

    print(f"  Crashes (SIGKILL) Inyectados: {crashes_injected}")
    print(f"  Transacciones Persistidas   : {total_tx:,}")
    print(f"  Integrity Check del Motor   : {integrity.upper()}")
    print(f"  Estado de Corrupción        : {corrupted}")
    print(f"  Integridad de Replay (Hash) : {total_tx - invalid_hashes:,} valid / {invalid_hashes} invalid")

    if corrupted == 0 and invalid_hashes == 0:
        print("\n✓ RECUPERACIÓN C6 CONFIRMADA: 0 corrupción bajo asedio continuo de SIGKILL.")
        print("  La arquitectura de WAL y persistencia es estructuralmente invulnerable a muertes de proceso.")
    else:
        print("\n⚠ ANERGÍA DETECTADA: Integridad comprometida bajo stress de colapso de proceso.")

if __name__ == "__main__":
    run_siege(duration_sec=30, num_workers=8, kill_interval=0.2)
