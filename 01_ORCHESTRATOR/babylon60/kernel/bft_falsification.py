import threading
import time
import logging
import sqlite3
import os
from bft_sqlite import BFTSQLite, BFTDatabaseError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s")
logger = logging.getLogger("bft_falsification")

DB_PATH = "falsification_test.db"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE bft_log (id INTEGER PRIMARY KEY, thread_id TEXT, timestamp REAL)")
    conn.commit()
    conn.close()

def bft_worker(thread_id: int):
    """Trabajador que intenta violar la exclusión mutua de la base de datos."""
    db = BFTSQLite(DB_PATH, max_retries=10, base_delay=0.1, max_delay=1.0)
    query = "INSERT INTO bft_log (thread_id, timestamp) VALUES (?, ?)"
    try:
        db.execute_with_backoff(query, (f"Thread-{thread_id}", time.time()))
        logger.info("Escritura completada exitosamente.")
    except BFTDatabaseError as e:
        logger.error(f"Falsación exitosa (Fallo esperado bajo asedio): {e}")
    except Exception as e:
        logger.critical(f"Fallo anómalo que viola invariantes C5-REAL: {e}")

def run_falsification_siege(num_threads: int = 20):
    """
    Ejecuta un asedio termodinámico de N hilos sobre la DB SQLite
    para falsar la resiliencia del Exponential Backoff.
    """
    logger.info(f"Iniciando asedio BFT con {num_threads} hilos concurrentes.")
    init_db()
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=bft_worker, args=(i,), name=f"SiegeThread-{i}")
        threads.append(t)
    
    # Iniciar todos simultáneamente para maximizar contención
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    logger.info("Asedio BFT finalizado.")

if __name__ == "__main__":
    run_falsification_siege(20)
