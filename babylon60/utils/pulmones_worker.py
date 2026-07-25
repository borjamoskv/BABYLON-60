import asyncio
import json
import logging
import sqlite3
import time
import typing
from importlib import import_module
from pathlib import Path

import babylon60.database.core

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CORTEX.PULMONES.WORKER")


class PulmonesWorker:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or Path.home() / '.cortex' / 'pulmones.db'
        self.running = False
        self.batch_size = 5

    def _fetch_ripe_tasks(self) -> list:
        now = time.monotonic()
        with babylon60.database.core.connect_sync(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "\n                SELECT id, target_func, payload, retries\n                FROM fallback_queue\n                WHERE next_retry_at <= ?\n                ORDER BY next_retry_at ASC\n                LIMIT ?\n                ",
                (now, self.batch_size),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _remove_task(self, task_id: int):
        with babylon60.database.core.connect_sync(self.db_path) as conn:
            conn.execute("DELETE FROM fallback_queue WHERE id = ?", (task_id,))

    def _penalize_task(self, task_id: int, retries: int):
        new_retries = retries + 1
        delay = min(60 * 2**retries, 3600)
        next_retry = time.monotonic() + delay
        with babylon60.database.core.connect_sync(self.db_path) as conn:
            conn.execute(
                "UPDATE fallback_queue SET retries = ?, next_retry_at = ? WHERE id = ?",
                (new_retries, next_retry, task_id),
            )
        logger.warning("⏳ Tarea %s penalizada. Reintento %s en %ss.", task_id, new_retries, delay)

    async def _resolve_target(self, target_func_path: str):
        module_path, func_name = target_func_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, func_name)

    async def _execute_task(self, task: dict[str, typing.Any]):
        task_id = task["id"]
        payload = json.loads(task["payload"])
        try:
            func = await self._resolve_target(task["target_func"])
            logger.info("🔄 Re-ejecutando %s [ID: %s]...", task["target_func"], task_id)
            args = payload.get("args", [])
            kwargs = payload.get("kwargs", {})
            await func(*args, **kwargs)
            self._remove_task(task_id)
            logger.info("✅ Tarea %s recuperada exitosamente.", task_id)
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
            logger.error("❌ Fallo crónico en tarea %s: %s", task_id, str(e))
            self._penalize_task(task_id, task["retries"])

    async def start_loop(self, poll_interval: float = 30.0):
        self.running = True
        logger.info("🫁 [WORKER] PULMONES Daemon iniciado. Escaneando hipoxia de red...")
        while self.running:
            try:
                tasks = self._fetch_ripe_tasks()
                if tasks:
                    logger.info("📥 Encontradas %s tareas maduras para reintento.", len(tasks))
                    await asyncio.gather(*(self._execute_task(t) for t in tasks))
                else:
                    logger.debug("O₂ levels optimal. No tasks pending.")
            except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
                logger.critical("💀 [WORKER] Fallo sistémico en el bucle principal: %s", str(e))
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    worker = PulmonesWorker()
    try:
        asyncio.run(worker.start_loop())
    except KeyboardInterrupt:
        logger.info("🛑 [WORKER] Recibida señal de apagado. Respiración artificial detenida.")
