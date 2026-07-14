import os
import signal
import os
import signal
import asyncio
import aiosqlite
import logging
logger = logging.getLogger('babylon60.bft.master_ledger')

class MasterLedgerQueue:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue: asyncio.Queue[tuple[str, tuple] | None] = asyncio.Queue()
        self.db: aiosqlite.Connection | None = None
        self._writer_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        self.db = await aiosqlite.connect(self.db_path, timeout=5.0)
        await self.db.execute('PRAGMA journal_mode=WAL;')
        await self.db.execute('PRAGMA synchronous=NORMAL;')
        await self.db.commit()
        self._writer_task = asyncio.create_task(self._single_writer_loop())
        logger.info(f'BFT Master Ledger Queue initialized on {self.db_path} [WAL Active]')

    async def _single_writer_loop(self) -> None:
        if self.db is None:
            raise RuntimeError('Database not initialized')
        try:
            while True:
                batch: list[tuple[str, tuple]] = []
                while not self.queue.empty() and len(batch) < 500:
                    payload = await self.queue.get()
                    if payload is None:
                        self.queue.task_done()
                        return
                    batch.append(payload)
                if batch:
                    try:
                        for query, params in batch:
                            await self.db.execute(query, params)
                        await self.db.commit()
                    except Exception as e:
                        os.kill(os.getpid(), signal.SIGKILL)
                        raise RuntimeError('FAIL-FAST: General Exception intercepted.')
                    finally:
                        for _ in batch:
                            self.queue.task_done()
                else:
                    payload = await self.queue.get()
                    if payload is None:
                        self.queue.task_done()
                        return
                    self.queue.put_nowait(payload)
                    self.queue.task_done()
        except asyncio.CancelledError:
            logger.warning('BFT Single-Writer Loop Cancelled (Apoptosis)')

    async def submit_transaction(self, query: str, parameters: tuple) -> None:
        await self.queue.put((query, parameters))

    async def shutdown(self) -> None:
        await self.queue.put(None)
        if self._writer_task:
            await self._writer_task
        if self.db:
            await self.db.close()
        logger.info('BFT Master Ledger Queue shut down cleanly.')