# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
import asyncio
import json
import logging
import sqlite3
import time
from collections.abc import Awaitable, Callable
from importlib import import_module
from pathlib import Path
from typing import TypedDict

import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BABYLON60.PULMONES.WORKER")


class RipeTask(TypedDict):
    id: int
    target_func: str
    payload: str
    retries: int


class PulmonesWorker:
    """Daemon soberano que drena la cola de fallos SQLite de forma asíncrona."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            base_dir = Path(os.getenv("BABYLON_HOME", str(Path.home() / ".babylon60")))
            db_path = base_dir / "pulmones.db"
        self.db_path = db_path
        self.running = False
        # Para evitar saturar APIs en la recuperación, aplicamos rate-limiting por lote
        self.batch_size = 5

    def _fetch_ripe_tasks(self) -> list[RipeTask]:
        """O(1) fetch gracias al índice idx_next_retry."""
        now = time.monotonic()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, target_func, payload, retries
                FROM fallback_queue
                WHERE next_retry_at <= ?
                ORDER BY next_retry_at ASC
                LIMIT ?
                """,
                (now, self.batch_size),
            )
            tasks: list[RipeTask] = []
            for row in cursor.fetchall():
                tasks.append(
                    {
                        "id": int(row["id"]),
                        "target_func": str(row["target_func"]),
                        "payload": str(row["payload"]),
                        "retries": int(row["retries"]),
                    }
                )
            return tasks

    def _remove_task(self, task_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM fallback_queue WHERE id = ?", (task_id,))

    def _penalize_task(self, task_id: int, retries: int) -> None:
        """Exponential backoff para tareas crónicamente fallidas."""
        new_retries = retries + 1
        # Backoff: 1m, 2m, 4m, 8m... max 60 min.
        delay = min(60 * (2**retries), 3600)
        next_retry = time.monotonic() + delay

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE fallback_queue SET retries = ?, next_retry_at = ? WHERE id = ?",
                (new_retries, next_retry, task_id),
            )
        logger.warning("⏳ Tarea %s penalizada. Reintento %s en %ss.", task_id, new_retries, delay)

    async def _resolve_target(self, target_func_path: str) -> Callable[..., Awaitable[object]]:
        """
        Resuelve dinámicamente el string de la función saved en SQLite.
        """
        module_path, func_name = target_func_path.rsplit(".", 1)
        module = import_module(module_path)
        func: Callable[..., Awaitable[object]] = getattr(module, func_name)
        return func

    async def _execute_task(self, task: RipeTask) -> None:
        task_id = task["id"]
        payload_data = json.loads(task["payload"])
        if not isinstance(payload_data, dict):
            payload_data = {}

        try:
            func = await self._resolve_target(task["target_func"])
            logger.info("🔄 Re-executing %s [ID: %s]...", task["target_func"], task_id)

            raw_args = payload_data.get("args", [])
            raw_kwargs = payload_data.get("kwargs", {})
            args = list(raw_args) if isinstance(raw_args, (list, tuple)) else []
            kwargs = dict(raw_kwargs) if isinstance(raw_kwargs, dict) else {}

            await func(*args, **kwargs)

            # Éxito de la operación. Eliminamos la impureza de la BD.
            self._remove_task(task_id)
            logger.info("✅ Tarea %s recuperada exitosamente.", task_id)

        except Exception as e:  # noqa: BLE001
            logger.error("❌ Fallo crónico en tarea %s: %s", task_id, str(e))
            self._penalize_task(task_id, task["retries"])

    async def start_loop(self, poll_interval: float = 30.0) -> None:
        """El corazón del Submarino. Late cada `poll_interval` segundos."""
        self.running = True
        logger.info("🫁 [WORKER] PULMONES Daemon iniciado. Escaneando hipoxia de red...")

        while self.running:
            try:
                tasks = self._fetch_ripe_tasks()
                if tasks:
                    logger.info("📥 Encontradas %s tareas maduras para reintento.", len(tasks))
                    # Ejecución concurrente del lote
                    await asyncio.gather(*(self._execute_task(t) for t in tasks))
                else:
                    logger.debug("O₂ levels optimal. No tasks pending.")
            except Exception as e:  # noqa: BLE001
                logger.critical("💀 [WORKER] Fallo sistémico en el bucle principal: %s", str(e))

            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    worker = PulmonesWorker()
    try:
        asyncio.run(worker.start_loop())
    except KeyboardInterrupt:
        logger.info("🛑 [WORKER] Recibida señal de apagado. Respiración artificial detenida.")
