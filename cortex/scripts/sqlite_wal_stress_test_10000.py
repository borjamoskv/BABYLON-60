import sqlite3
import os
import time
import concurrent.futures
import random
import hashlib
import numpy as np
from datetime import datetime, timezone

# Configuration
DB_PATH = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/ledger/stress_test_10000.db"
TOTAL_REQUESTS = 10000
CONCURRENCY = 200

# Rule Σ15 compliant stress test script for SQLite WAL concurrency
def init_db():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Rule R10 WAL mode + busy_timeout configuration
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stress_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            worker_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def perform_write(worker_id):
    start = time.monotonic()
    try:
        conn = sqlite3.connect(DB_PATH)
        # Apply WAL + timeout per connection thread
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        
        # Generate random payload
        payload = f"worker_{worker_id}_{random.random()}"
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        conn.execute(
            "INSERT INTO stress_log (timestamp, payload_hash, worker_id) VALUES (?, ?, ?)",
            (timestamp, payload_hash, worker_id)
        )
        conn.commit()
        conn.close()
        return "SUCCESS", time.monotonic() - start
    except sqlite3.OperationalError as e:
        return f"LOCK_ERROR: {str(e)}", time.monotonic() - start
    except Exception as e:
        return f"ERROR: {str(e)}", time.monotonic() - start

def main():
    print(f"[*] Initializing C5-REAL SQLite WAL Stress Test...")
    init_db()
    print(f"[*] Starting stress test: {TOTAL_REQUESTS} writes at concurrency {CONCURRENCY}")
    
    start_time = time.monotonic()
    
    latencies = []
    status_counts = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(perform_write, i) for i in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            status, duration = future.result()
            status_counts[status] = status_counts.get(status, 0) + 1
            latencies.append(duration * 1000) # milliseconds
            
    total_duration = time.monotonic() - start_time
    
    # Calculate percentiles (Rule Σ15 compliance)
    p50 = np.percentile(latencies, 50)
    p90 = np.percentile(latencies, 90)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    
    success = status_counts.get("SUCCESS", 0)
    anergy = TOTAL_REQUESTS - success
    
    print("\nEXECUTIVE BRIEFING — SQLITE WAL STRESS TEST")
    print("==========================================")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Concurrency:    {CONCURRENCY}")
    print(f"Total Duration: {total_duration:.3f} s")
    print(f"Throughput:     {TOTAL_REQUESTS / total_duration:.2f} writes/s")
    print("\nLatency Percentiles:")
    print(f"  p50:  {p50:.2f} ms")
    print(f"  p90:  {p90:.2f} ms")
    print(f"  p95:  {p95:.2f} ms")
    print(f"  p99:  {p99:.2f} ms")
    print("\nOutcome Matrix:")
    print(f"  SUCCESS (Exergy): {success}")
    print(f"  FAILURES (Anergia): {anergy}")
    for status, count in status_counts.items():
        if status != "SUCCESS":
            print(f"    -> {status}: {count}")
            
    if anergy > 0:
        print("\n[!] STRESS TEST FAIL: Lock collisions or database locks detected.")
        exit(1)
    else:
        print("\n[+] STRESS TEST PASS: SQLite WAL is highly stable under stress.")
        exit(0)

if __name__ == "__main__":
    main()
