# C5-REAL EXERGY CERTIFIED
import sqlite3
import time
import os
import json
import logging

DB_PATH = os.getenv("CORTEX_DB_PATH", "cortex_scheduler.db")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | CORTEX-SCHEDULER | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class CortexScheduler:
    """Motor Causal Base 60 - Autonomous Scheduler (C5-REAL)."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        # R10 · Concurrencia Confiable de DB
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduler_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    entropy_level REAL NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    created_at REAL NOT NULL,
                    executed_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reality_loop_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tick_timestamp REAL NOT NULL,
                    action_taken TEXT NOT NULL,
                    target_id INTEGER
                )
            """)

    def inject_task(self, task_name: str, entropy_level: float) -> int:
        """Inyecta una tarea en el bucle de realidad."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO scheduler_queue (task_name, entropy_level, created_at) VALUES (?, ?, ?)",
                (task_name, entropy_level, time.time())
            )
            return cursor.lastrowid

    def tick(self) -> dict:
        """Ejecuta un ciclo termodinámico y colapsa la entropía."""
        with self._get_conn() as conn:
            # 1. Extraer la tarea con menor entropía (T=0.0 Flash routing by default)
            cursor = conn.execute(
                "SELECT * FROM scheduler_queue WHERE status = 'PENDING' ORDER BY entropy_level ASC LIMIT 1"
            )
            task = cursor.fetchone()

            if not task:
                return {"status": "IDLE", "action": "NO_TASKS"}

            # 2. Mutar estado (Atomic Execution)
            task_id = task["id"]
            action_desc = f"EXECUTED_VIA_SCHEDULER: {task['task_name']}"
            now = time.time()

            conn.execute(
                "UPDATE scheduler_queue SET status = 'EXECUTED', executed_at = ? WHERE id = ?",
                (now, task_id)
            )

            # 3. Anclar el log de la realidad
            conn.execute(
                "INSERT INTO reality_loop_logs (tick_timestamp, action_taken, target_id) VALUES (?, ?, ?)",
                (now, action_desc, task_id)
            )

            logger.info(f"Colapso de Entropía -> {action_desc} (Entropía: {task['entropy_level']})")

            return {
                "status": "COLLAPSED",
                "task_id": task_id,
                "action": action_desc
            }

if __name__ == "__main__":
    scheduler = CortexScheduler()
    logger.info("Iniciando Autonomous Scheduler en modo de prueba singular...")
    scheduler.inject_task("CORTEX_DIAGNOSTIC", 0.1)
    scheduler.inject_task("ARCHITECT_REFACTOR", 0.9)
    res = scheduler.tick()
    print(json.dumps(res, indent=2))
