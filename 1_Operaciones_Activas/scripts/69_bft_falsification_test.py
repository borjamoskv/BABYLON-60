#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
# BFT FALSIFICATION TEST: PROOF OF VULNERABILITY (POPPER)

import os
import uuid
import time
import sqlite3
import threading
import random

NAMESPACE_CORTEX = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

def init_vulnerable_db(db_path):
    conn = sqlite3.connect(db_path)
    # INYECCIÓN DE ENTROPÍA: Desactivamos WAL y protecciones síncronas
    conn.execute("PRAGMA journal_mode=DELETE;")
    conn.execute("PRAGMA synchronous=OFF;")
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
    conn = sqlite3.connect(db_path, timeout=5.0) # Timeout agresivo
    for i in range(num_injections):
        uid = str(uuid.uuid5(NAMESPACE_CORTEX, f"{worker_id}_{i}_{time.time()}"))
        try:
            conn.execute(
                "INSERT INTO bft_ledger (id, thread_id, taint_tag, timestamp) VALUES (?, ?, ?, ?)",
                (uid, f"Worker-{worker_id}", taint_tag, time.time())
            )
            conn.commit()
        except Exception:
            pass # Simulamos fallo silencioso por contención
    conn.close()

def saboteur_worker(db_path):
    # El Saboteador Bizantino elimina aleatoriamente registros para simular corrupción
    time.sleep(0.5)
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bft_ledger ORDER BY RANDOM() LIMIT 50")
        rows = cursor.fetchall()
        for row in rows:
            conn.execute("DELETE FROM bft_ledger WHERE id=?", (row[0],))
        conn.commit()
        conn.close()
    except Exception:
        pass

if __name__ == "__main__":
    db_path = "/tmp/bft_falsification_cortex.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    print(f"============================================================")
    print(f"  Ω3 FALSIFICATION TEST: INDUCED BYZANTINE CORRUPTION")
    print(f"============================================================")

    NUM_THREADS = 20
    INJECTIONS_PER_THREAD = 100
    TOTAL_INJECTIONS = NUM_THREADS * INJECTIONS_PER_THREAD

    print(f"[*] TARGET: {db_path}")
    print(f"[*] SECURITY: VULNERABLE (JOURNAL=DELETE, SYNC=OFF)")
    print(f"[*] ATTACK VECTOR: 20 Hilos Concurrentes + 1 Saboteador Activo")
    print(f"[*] CARGA ESPERADA: {TOTAL_INJECTIONS} Inyecciones")

    init_vulnerable_db(db_path)

    threads = []

    # Saboteur
    saboteur = threading.Thread(target=saboteur_worker, args=(db_path,))
    threads.append(saboteur)
    saboteur.start()

    # Workers
    for w in range(NUM_THREADS):
        t = threading.Thread(target=byzantine_worker, args=(db_path, w, f"BFT-{w}", INJECTIONS_PER_THREAD))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify Integrity
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bft_ledger")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"\n--- AUDITORÍA C5-REAL BFT ---")
    print(f"[CORTEX-TAINT:VERIFY] Total Inyecciones Consilidadas: {count}/{TOTAL_INJECTIONS}")

    if count == TOTAL_INJECTIONS:
        print("\n[OK] 100% BYZANTINE FAULT TOLERANCE ACHIEVED.")
    else:
        loss = TOTAL_INJECTIONS - count
        print(f"\n[FATAL] CORRUPTION DETECTED.")
        print(f"[CORTEX-TAINT:ERR] Integridad Comprometida. Registros perdidos o borrados: {loss}")
        print(f"■ PRINCIPIO DE FALSABILIDAD (POPPER) CONFIRMADO ■")
