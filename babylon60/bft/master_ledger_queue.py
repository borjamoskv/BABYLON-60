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
            self._writer_failure = task.exception()
            logger.critical(f"FAIL-FAST: BFT writer task crashed: {self._writer_failure}")

    async def _single_writer_loop(self) -> None:
        if self.db is None:
            raise RuntimeError("Database not initialized")
        while True:
            batch: list[tuple[str, tuple[Any, ...]]] = []

            payload = await self.queue.get()
            if payload is None:
                self.queue.task_done()
                return
            batch.append(payload)

            while not self.queue.empty() and len(batch) < 500:
                payload = self.queue.get_nowait()
                if payload is None:
                    self.queue.task_done()
                    self.queue.put_nowait(None)
                    break
                batch.append(payload)

            try:
                await self.db.execute("BEGIN IMMEDIATE")
                for query, params in batch:
                    await self.db.execute(query, params)
                await self.db.execute("COMMIT")
            except Exception as e:
                logger.critical(f"FAIL-FAST: BFT Batch Write Failed: {e}")
                await self.db.execute("ROLLBACK")
                raise
            finally:
                for _ in batch:
                    self.queue.task_done()

    async def submit_transaction(self, query: str, parameters: tuple[Any, ...]) -> None:
        if self._writer_task is not None and self._writer_task.done() and (not self._writer_task.cancelled()):
            failure = self._writer_failure or self._writer_task.exception()
            raise RuntimeError(
                f"Zombie Writer Prevention: writer task terminated unexpectedly. Cause: {failure}"
            ) from failure
        await self.queue.put((query, parameters))

    async def shutdown(self) -> None:
        try:
            await self.queue.put(None)
            if self._writer_task and (not self._writer_task.done()):
                await self._writer_task
        finally:
            if self.db:
                await self.db.close()
        logger.info("BFT Master Ledger Queue shut down cleanly.")
