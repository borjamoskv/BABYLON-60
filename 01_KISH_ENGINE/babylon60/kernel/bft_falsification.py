from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time

try:
    from babylon60.kernel.bft_sqlite import BFTDatabaseError, BFTSQLite
except ImportError:
    from .bft_sqlite import BFTDatabaseError, BFTSQLite

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s")
logger = logging.getLogger("bft_falsification")

DB_PATH = "falsification_test.db"


def init_db(db_path: str = DB_PATH) -> None:
    for suffix in ("", "-wal", "-shm"):
        candidate = f"{db_path}{suffix}"
        if os.path.exists(candidate):
            os.remove(candidate)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute("CREATE TABLE bft_log (id INTEGER PRIMARY KEY, thread_id TEXT, timestamp REAL)")
        conn.commit()
    finally:
        conn.close()


def bft_worker(
    thread_id: int,
    db_path: str = DB_PATH,
    failures: list[str] | None = None,
    lock: threading.Lock | None = None,
) -> bool:
    """Trabajador que compite por la exclusión mutua de la base de datos bajo backoff."""
    db = BFTSQLite(db_path, max_retries=12, base_delay=0.02, max_delay=0.5)
    query = "INSERT INTO bft_log (thread_id, timestamp) VALUES (?, ?)"
    try:
        db.execute_with_backoff(query, (f"Thread-{thread_id}", time.time()))
        logger.info("Escritura completada exitosamente.")
        return True
    except (BFTDatabaseError, Exception) as e:
        logger.error(f"Fallo en trabajador BFT Thread-{thread_id}: {e}")
        if failures is not None and lock is not None:
            with lock:
                failures.append(f"Thread-{thread_id}: {e}")
        return False


def run_falsification_siege(num_threads: int = 20, db_path: str = DB_PATH) -> dict[str, int]:
    """
    Ejecuta un asedio termodinámico de N hilos sobre la DB SQLite
    y verifica empíricamente que las N escrituras hayan sido persistidas sin pérdida.
    """
    logger.info(f"Iniciando asedio BFT con {num_threads} hilos concurrentes.")
    init_db(db_path)

    failures: list[str] = []
    lock = threading.Lock()
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=bft_worker, args=(i, db_path, failures, lock), name=f"SiegeThread-{i}")
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    db = BFTSQLite(db_path)
    cur = db.execute_with_backoff("SELECT COUNT(*) FROM bft_log")
    row = cur.fetchone()
    persisted_count = int(row[0]) if row is not None else 0

    logger.info(f"Asedio BFT finalizado. Persistidos: {persisted_count}/{num_threads}.")
    if failures or persisted_count != num_threads:
        raise BFTDatabaseError(f"BFT siege lost writes: persisted {persisted_count}/{num_threads}, failures={failures}")
    return {"expected": num_threads, "persisted": persisted_count}


if __name__ == "__main__":
    run_falsification_siege(20)
