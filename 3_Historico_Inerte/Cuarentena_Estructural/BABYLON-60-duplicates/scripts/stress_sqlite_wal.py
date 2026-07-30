# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Stress test for SQLite WAL and busy_timeout (INV_BFT_02).
Simulates a hostile swarm of independent processes trying to write
to the same database concurrently, bypassing the BFTLedgerActor's
single-writer queue to test the physical database layer defenses.

If INV_BFT_02 is active, WAL + busy_timeout=5000ms will allow all
processes to eventually write without 'database is locked' errors.
If it fails, the constraint is violated.
"""

import sqlite3
import sys
import os
import time
import concurrent.futures
import uuid
import random

DB_PATH = "stress_test.db"
NUM_WORKERS = 40
WRITES_PER_WORKER = 50

def init_db() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    # This matches babylon60.database.core.connect configuration
    with sqlite3.connect(DB_PATH, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute('''
            CREATE TABLE ledger (
                id TEXT PRIMARY KEY,
                worker_id INTEGER,
                data TEXT
            )
        ''')
        conn.commit()

def hostile_writer(worker_id: int) -> int:
    """Attempts to spam the DB with writes."""
    success_count = 0

    # We create a new connection per worker, mimicking independent swarm agents
    try:
        with sqlite3.connect(DB_PATH, timeout=5.0) as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            for _ in range(WRITES_PER_WORKER):
                # Small random sleep to maximize collision probability at different execution phases
                time.sleep(random.uniform(0.001, 0.01))

                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO ledger (id, worker_id, data) VALUES (?, ?, ?)",
                    (str(uuid.uuid4()), worker_id, "stress_payload")
                )
                conn.commit()
                success_count += 1
    except sqlite3.OperationalError as e:
        print(f"Worker {worker_id} failed: {e}")
        return success_count
    except Exception as e:
        print(f"Worker {worker_id} hard crash: {e}")
        return success_count

    return success_count

def main() -> None:
    print(f"Initializing Stress Test: {NUM_WORKERS} workers, {WRITES_PER_WORKER} writes each")
    init_db()

    start_t = time.time()
    total_successful = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(hostile_writer, i) for i in range(NUM_WORKERS)]
        for f in concurrent.futures.as_completed(futures):
            total_successful += f.result()

    end_t = time.time()

    expected_writes = NUM_WORKERS * WRITES_PER_WORKER
    print(f"Stress Test Completed in {end_t - start_t:.2f}s")
    print(f"Expected writes: {expected_writes}")
    print(f"Successful writes: {total_successful}")

    if total_successful == expected_writes:
        print("VERDICT: INV_BFT_02 (WAL + 5000ms timeout) holds. Zero lock failures under stress.")
        sys.exit(0)
    else:
        print(f"VERDICT: INV_BFT_02 VIOLATED. {expected_writes - total_successful} writes lost to contention.")
        sys.exit(1)

if __name__ == "__main__":
    main()
