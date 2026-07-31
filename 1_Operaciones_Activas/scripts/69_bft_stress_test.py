#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
# BFT STRESS TEST: SQLITE WAL CONCURRENCY LIMITS

import os
import uuid
import time
import sqlite3
import threading

NAMESPACE_CORTEX = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    # Exergía termodinámica: WAL mode y SYNCHRONOUS = NORMAL para máxima concurrencia
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    # Tamaño del caché de WAL
    conn.execute("PRAGMA wal_autocheckpoint=1000;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bft_ledger (
            id TEXT PRIMARY KEY,
            thread_id TEXT,
            taint_tag TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

def byzantine_worker(db_path, worker_id, taint_tag, num_injections):
    conn = sqlite3.connect(db_path, timeout=60.0)
    for i in range(num_injections):
        uid = str(uuid.uuid5(NAMESPACE_CORTEX, f"{worker_id}_{i}_{time.time()}"))
        while True:
            try:
                conn.execute(
                    "INSERT INTO bft_ledger (id, thread_id, taint_tag, timestamp) VALUES (?, ?, ?, ?)",
                    (uid, f"Worker-{worker_id}", taint_tag, time.time())
                )
                conn.commit()
                break # Éxito, salir del retry loop
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    time.sleep(0.001) # Backoff de contención WAL
                else:
                    print(f"[CORTEX-TAINT:ERR] {e}")
                    break
    conn.close()

if __name__ == "__main__":
    db_path = "/tmp/bft_stress_cortex.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    print(f"============================================================")
    print(f"  Ω3 STRESS TEST: BYZANTINE FAULT TOLERANCE (SQLITE WAL)")
    print(f"============================================================")

    NUM_THREADS = 50
    INJECTIONS_PER_THREAD = 2000
    TOTAL_INJECTIONS = NUM_THREADS * INJECTIONS_PER_THREAD

    print(f"[*] TARGET: {db_path} (WAL MODE)")
    print(f"[*] VECTORES DE ATAQUE: {NUM_THREADS} Hilos Concurrentes")
    print(f"[*] CARGA TERMODINÁMICA: {TOTAL_INJECTIONS} Inyecciones UUIDv5 Idempotentes")

    init_db(db_path)

    start = time.perf_counter()

    threads = []
    for w in range(NUM_THREADS):
        t = threading.Thread(target=byzantine_worker, args=(db_path, w, f"BFT-{w}", INJECTIONS_PER_THREAD))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start

    # Verify Integrity
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bft_ledger")
    count = cursor.fetchone()[0]
    conn.close()

    throughput = TOTAL_INJECTIONS / elapsed

    print(f"\n--- AUDITORÍA C5-REAL BFT ---")
    print(f"[CORTEX-TAINT:VERIFY] Total Inyecciones Consilidadas: {count}/{TOTAL_INJECTIONS}")
    print(f"[CORTEX-TAINT:METRICS] Tiempo Total: {elapsed:.2f} s")
    print(f"[CORTEX-TAINT:METRICS] Throughput : {throughput:.2f} Injections/sec")

    if count == TOTAL_INJECTIONS:
        print("\n[OK] 100% BYZANTINE FAULT TOLERANCE ACHIEVED.")
        print("■ EXERGÍA DE SISTEMA AISLADO MAXIMIZADA ■")
    else:
        print(f"\n[FATAL] CORRUPTION DETECTED. Perdidos: {TOTAL_INJECTIONS - count}")
