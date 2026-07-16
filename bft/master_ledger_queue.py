import os
import signal
import asyncio
import aiosqlite
import logging
from typing import Any
logger = logging.getLogger('babylon60.bft.master_ledger')

class MasterLedgerQueue:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue: asyncio.Queue[tuple[str, tuple[Any, ...]] | None] = asyncio.Queue()
        self.db: aiosqlite.Connection | None = None
        self._writer_task: asyncio.Task[Any] | None = None


    async def initialize(self) -> None:
        self.db = await aiosqlite.connect(self.db_path, timeout=5.0)
        await self.db.execute('PRAGMA journal_mode=WAL;')
        await self.db.execute('PRAGMA synchronous=NORMAL;')
        await self.db.commit()
        self._writer_task = asyncio.create_task(self._single_writer_loop())
        self._writer_task.add_done_callback(self._on_writer_done)
        logger.info(f'BFT Master Ledger Queue initialized on {self.db_path} [WAL Active]')

    def _on_writer_done(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            logger.warning('BFT Single-Writer Loop Cancelled (Apoptosis)')
        elif task.exception():
            logger.critical(f'FAIL-FAST: BFT writer task crashed: {task.exception()}')
            os.kill(os.getpid(), signal.SIGKILL)

    async def _single_writer_loop(self) -> None:
        if self.db is None:
            raise RuntimeError('Database not initialized')
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
                for query, params in batch:
                    await self.db.execute(query, params)
                await self.db.commit()
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
        await self.queue.put((query, parameters))

    async def shutdown(self) -> None:
        await self.queue.put(None)
        if self._writer_task and not self._writer_task.done():
            await self._writer_task
        if self.db:
            await self.db.close()

        logger.info('BFT Master Ledger Queue shut down cleanly.')