# [C5-REAL] Cola auxiliar de escritura serializada (superficies NO-ledger).
# LEY (AGENTS.md, escritor-único): este queue NO puede apuntar a la base del
# Master Ledger — `BFTLedgerActor` es el ÚNICO escritor del ledger. Superficie
# permitida: DBs auxiliares (telemetría, sidecars). Génesis ITERA-2: NEW-E
# (durabilidad rival NORMAL→FULL vía babylon60.database.core) + INV_C5_07
# (SIGKILL en done-callback → Zombie Writer Prevention).
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiosqlite

from babylon60.database import core as database_core

logger = logging.getLogger("babylon60.bft.master_ledger")


class MasterLedgerQueue:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue: asyncio.Queue[tuple[str, tuple[Any, ...]] | None] = asyncio.Queue()
        self.db: aiosqlite.Connection | None = None
        self._writer_task: asyncio.Task[Any] | None = None
        self._writer_failure: BaseException | None = None

    async def initialize(self) -> None:
        self.db = await database_core.connect(self.db_path, synchronous="FULL")
        self._writer_task = asyncio.create_task(self._single_writer_loop())
        self._writer_task.add_done_callback(self._on_writer_done)
        logger.info(f"BFT Master Ledger Queue initialized on {self.db_path} [WAL + synchronous=FULL]")

    def _on_writer_done(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            logger.warning("BFT Single-Writer Loop Cancelled (Apoptosis)")
        elif task.exception():
            # INV_C5_07 (falla ruidosa): el crash se registra y aflora en el siguiente
            # submit_transaction (Zombie Writer Prevention). Cero auto-necrosis del proceso.
            self._writer_failure = task.exception()
            logger.critical(f"FAIL-FAST: BFT writer task crashed: {self._writer_failure}")

    async def _single_writer_loop(self) -> None:
        if self.db is None:
            raise RuntimeError("Database not initialized")
        while True:
            await asyncio.sleep(0)
            batch: list[tuple[str, tuple[Any, ...]]] = []
            while not self.queue.empty() and len(batch) < 500:
                payload = self.queue.get_nowait()
                if payload is None:
                    self.queue.task_done()
                    return
                batch.append(payload)
            if batch:
                # Atomicidad de lote explícita (la conexión es autocommit por diseño).
                await self.db.execute("BEGIN IMMEDIATE")
                for query, params in batch:
                    await self.db.execute(query, params)
                await self.db.execute("COMMIT")
                for _ in batch:
                    self.queue.task_done()
            else:
                payload = await self.queue.get()
                if payload is None:
                    self.queue.task_done()
                    return
                self.queue.put_nowait(payload)
                self.queue.task_done()

    async def submit_transaction(self, query: str, parameters: tuple[Any, ...]) -> None:
        if self._writer_task is not None and self._writer_task.done() and not self._writer_task.cancelled():
            failure = self._writer_failure or self._writer_task.exception()
            raise RuntimeError(
                f"Zombie Writer Prevention: writer task terminated unexpectedly. Cause: {failure}"
            ) from failure
        await self.queue.put((query, parameters))

    async def shutdown(self) -> None:
        await self.queue.put(None)
        if self._writer_task and not self._writer_task.done():
            await self._writer_task
        if self.db:
            await self.db.close()

        logger.info("BFT Master Ledger Queue shut down cleanly.")
