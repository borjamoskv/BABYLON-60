#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
async_db.py - Zero-Dependency Async SQLite Wrapper.

Replaces third-party `aiosqlite` using Python standard library `sqlite3`
and `asyncio.to_thread` for zero-anergy non-blocking ledger operations.
"""

import asyncio
import sqlite3
from typing import Any, List, Optional, Tuple


class AsyncCursor:
    """Async wrapper for sqlite3.Cursor."""

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    async def fetchone(self) -> Optional[Tuple[Any, ...]]:
        return await asyncio.to_thread(self._cursor.fetchone)

    async def fetchall(self) -> List[Tuple[Any, ...]]:
        return await asyncio.to_thread(self._cursor.fetchall)

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> Optional[int]:
        return self._cursor.lastrowid


class AsyncConnection:
    """Async wrapper for sqlite3.Connection."""

    def __init__(self, database: str, **kwargs: Any):
        self._database = database
        self._kwargs = kwargs
        self._conn: Optional[sqlite3.Connection] = None

    async def _connect(self) -> "AsyncConnection":
        if self._conn is None:
            self._conn = await asyncio.to_thread(sqlite3.connect, self._database, **self._kwargs)
            self._conn.row_factory = sqlite3.Row
        return self

    async def execute(self, sql: str, parameters: Tuple[Any, ...] = ()) -> AsyncCursor:
        if self._conn is None:
            await self._connect()
        assert self._conn is not None
        cursor = await asyncio.to_thread(self._conn.execute, sql, parameters)
        return AsyncCursor(cursor)

    async def executemany(self, sql: str, seq_of_parameters: List[Tuple[Any, ...]]) -> AsyncCursor:
        if self._conn is None:
            await self._connect()
        assert self._conn is not None
        cursor = await asyncio.to_thread(self._conn.executemany, sql, seq_of_parameters)
        return AsyncCursor(cursor)

    async def commit(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.commit)

    async def rollback(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.rollback)

    async def close(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.close)
            self._conn = None

    async def __aenter__(self) -> "AsyncConnection":
        await self._connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.close()


async def connect(database: str, **kwargs: Any) -> AsyncConnection:
    """
    Asynchronously connects to a SQLite database.
    """
    conn = AsyncConnection(database, **kwargs)
    await conn._connect()
    return conn
