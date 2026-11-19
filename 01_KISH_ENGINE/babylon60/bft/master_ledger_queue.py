# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Cola auxiliar de escritura serializada (superficies NO-ledger).
# LEY (AGENTS.md, escritor-único): este queue NO puede apuntar a la base del
# Master Ledger — `BFTLedgerActor` es el ÚNICO escritor del ledger. Superficie
# permitida: DBs auxiliares (telemetría, sidecars). Génesis ITERA-2: NEW-E
# (durabilidad rival NORMAL→FULL vía babylon60.database.core) + INV_C5_07
# (SIGKILL en done-callback → Zombie Writer Prevention).
from __future__ import annotations

import asyncio
import logging
from typing import Union

import aiosqlite

from babylon60.database import core as database_core

logger = logging.getLogger("babylon60.bft.master_ledger")

SqliteParam = Union[str, int, float, bytes, None]
SqliteParams = tuple[SqliteParam, ...]


class MasterLedgerQueue:
    """Single-loop auxiliary writer; submission acknowledges admission, not durability."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.queue: asyncio.Queue[tuple[str, SqliteParams] | None] = asyncio.Queue(maxsize=1024)
        self.db: aiosqlite.Connection | None = None
        self._writer_task: asyncio.Task[None] | None = None
        self._writer_failure: BaseException | None = None
        self._initialization_task: asyncio.Task[None] | None = None
        self._shutdown_task: asyncio.Task[None] | None = None
        self._accepting = False
        self._failed_transactions: list[tuple[str, SqliteParams]] = []

    @property
    def failed_transactions(self) -> tuple[tuple[str, SqliteParams], ...]:
        """Failed batch/backlog retained in RAM; a failed COMMIT may be ambiguous."""
        return tuple(self._failed_transactions)

    async def initialize(self) -> None:
        if self._initialization_task is not None or self._shutdown_task is not None:
            raise RuntimeError("Queue already initialized or closed")
        self._initialization_task = asyncio.create_task(self._open_connection())
        try:
            await asyncio.shield(self._initialization_task)
        except asyncio.CancelledError:
            self._accepting = False
            if self._shutdown_task is None:
                self._shutdown_task = asyncio.create_task(self._finish_shutdown())
            raise
        logger.info("Auxiliary writer initialized on %s [WAL + synchronous=FULL]", self.db_path)

    async def _open_connection(self) -> None:
        # A cancelled initialize caller must not abandon a connection being opened.
        self.db = await database_core.connect(self.db_path, synchronous="FULL")
        if self._shutdown_task is not None:
            raise RuntimeError("Queue closed during initialization")
        self._accepting = True
        self._writer_task = asyncio.create_task(self._single_writer_loop())
        self._writer_task.add_done_callback(self._on_writer_done)

    def _on_writer_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            self._writer_failure = self._writer_failure or RuntimeError("Auxiliary writer was cancelled")
        else:
            self._writer_failure = self._writer_failure or task.exception()
        if self._writer_failure is not None:
            logger.error("Auxiliary writer failed: %s", self._writer_failure)

    def _settle_backlog(self) -> None:
        while not self.queue.empty():
            payload = self.queue.get_nowait()
            if payload is not None:
                self._failed_transactions.append(payload)
            self.queue.task_done()

    async def _single_writer_loop(self) -> None:
        if self.db is None:
            raise RuntimeError("Database not initialized")
        stop_found = False
        try:
            # INV_C5_19: the stop sentinel (None) is the explicit termination condition.
            while not stop_found:
                payload = await self.queue.get()
                if payload is None:
                    self.queue.task_done()
                    return
                batch = [payload]
                while not self.queue.empty() and len(batch) < 500:
                    payload = self.queue.get_nowait()
                    if payload is None:
                        self.queue.task_done()
                        stop_found = True
                        break
                    batch.append(payload)
                try:
                    await self.db.execute("BEGIN IMMEDIATE")
                    for query, params in batch:
                        await self.db.execute(query, params)
                    await self.db.execute("COMMIT")
                except BaseException:
                    self._failed_transactions.extend(batch)
                    if self.db.in_transaction:
                        await self.db.rollback()
                    raise
                finally:
                    for _ in batch:
                        self.queue.task_done()
        except BaseException as exc:
            self._writer_failure = exc
            raise
        finally:
            self._accepting = False
            self._settle_backlog()

    async def submit_transaction(self, query: str, parameters: SqliteParams = ()) -> None:
        task = self._writer_task
        if self._writer_failure is not None or (task is not None and task.done()):
            failure = self._writer_failure
            raise RuntimeError("Zombie Writer Prevention: writer task terminated unexpectedly") from failure
        if not self._accepting:
            raise RuntimeError("Auxiliary writer is not accepting transactions")
        # No await between admission check and insertion: shutdown cannot overtake it.
        self.queue.put_nowait((query, parameters))

    async def _finish_shutdown(self) -> None:
        if self._initialization_task is not None:
            await asyncio.gather(self._initialization_task, return_exceptions=True)
        writer = self._writer_task
        sentinel: asyncio.Task[None] | None = None
        try:
            if writer is not None:
                if not writer.done():
                    sentinel = asyncio.create_task(self.queue.put(None))
                    await asyncio.wait({sentinel, writer}, return_when=asyncio.FIRST_COMPLETED)
                    if not sentinel.done():
                        sentinel.cancel()
                        await asyncio.gather(sentinel, return_exceptions=True)
                try:
                    await writer
                except BaseException as exc:
                    raise RuntimeError("Auxiliary writer failed; shutdown did not confirm persistence") from exc
                if self._writer_failure is not None:
                    raise RuntimeError(
                        "Auxiliary writer failed; shutdown did not confirm persistence"
                    ) from self._writer_failure
        finally:
            if sentinel is not None and not sentinel.done():
                sentinel.cancel()
                await asyncio.gather(sentinel, return_exceptions=True)
            self._settle_backlog()
            if self.db is not None:
                await self.db.close()
                self.db = None
        logger.info("Auxiliary writer drained accepted transactions and closed")

    async def shutdown(self) -> None:
        self._accepting = False
        if self._shutdown_task is None:
            self._shutdown_task = asyncio.create_task(self._finish_shutdown())
        # Cancelling one caller cannot cancel the shared drain/connection cleanup.
        await asyncio.shield(self._shutdown_task)
