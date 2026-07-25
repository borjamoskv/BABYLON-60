from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Optional
import aiosqlite
from babylon60.database.core import connect

class ConnectionPool:
    """Async SQLite connection pool with semaphore-based concurrency control.
    
    INV_BFT_02: All connections use WAL mode with busy_timeout=5000ms.
    """
    
    def __init__(self, db_path: str | Path, *, max_connections: int = 5, synchronous: str = 'FULL') -> None:
        self._db_path = Path(db_path)
        self._synchronous = synchronous
        self._semaphore = asyncio.Semaphore(max_connections)
        self._connections: list[aiosqlite.Connection] = []
        self._available: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue()
        self._max = max_connections
        self._created = 0
    
    async def acquire(self) -> aiosqlite.Connection:
        await self._semaphore.acquire()
        try:
            conn = self._available.get_nowait()
        except asyncio.QueueEmpty:
            conn = await connect(self._db_path, synchronous=self._synchronous)
            self._connections.append(conn)
            self._created += 1
        return conn
    
    async def release(self, conn: aiosqlite.Connection) -> None:
        self._available.put_nowait(conn)
        self._semaphore.release()
    
    async def close_all(self) -> None:
        for conn in self._connections:
            await conn.close()
        self._connections.clear()
    
    async def healthcheck(self) -> bool:
        conn = await self.acquire()
        try:
            cursor = await conn.execute('SELECT 1')
            row = await cursor.fetchone()
            return row is not None and row[0] == 1
        finally:
            await self.release(conn)
