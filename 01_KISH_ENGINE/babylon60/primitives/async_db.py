#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
async_db.py - Zero-Dependency Async SQLite Wrapper.

Replaces third-party `aiosqlite` using Python standard library `sqlite3`
and a dedicated worker per connection for non-blocking ledger operations.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from collections.abc import Callable
from typing import Any, List, Optional, Tuple, TypeVar, cast

_Result = TypeVar("_Result")


class AsyncCursor:
    """Async wrapper for sqlite3.Cursor."""

    def __init__(self, cursor: sqlite3.Cursor, connection: "AsyncConnection") -> None:
        self._cursor = cursor
        self._connection = connection

    async def fetchone(self) -> Optional[sqlite3.Row]:
        return await self._connection._run(self._cursor.fetchone)

    async def fetchall(self) -> List[sqlite3.Row]:
        return await self._connection._run(self._cursor.fetchall)

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> Optional[int]:
        return self._cursor.lastrowid


class AsyncConnection:
    """Async wrapper for sqlite3.Connection."""

    def __init__(self, database: str, **kwargs: Any) -> None:
        self._database = database
        self._kwargs = kwargs
        self._conn: Optional[sqlite3.Connection] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._connect_lock = asyncio.Lock()

    async def _run(self, operation: Callable[[], _Result]) -> _Result:
        if self._executor is None:
            raise sqlite3.ProgrammingError("Connection is closed")
        return await asyncio.get_running_loop().run_in_executor(self._executor, operation)

    async def _connect(self) -> "AsyncConnection":
        async with self._connect_lock:
            if self._conn is not None:
                return self

            def _open() -> sqlite3.Connection:
                conn = cast(sqlite3.Connection, sqlite3.connect(self._database, **self._kwargs))
                conn.row_factory = sqlite3.Row
                return conn

            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="babylon-sqlite")
            opening = asyncio.create_task(self._run(_open))
            try:
                self._conn = await asyncio.shield(opening)
            except BaseException:
                try:
                    conn = await opening
                    await self._run(conn.close)
                finally:
                    self._executor.shutdown(wait=False)
                    self._executor = None
                raise
        return self

    async def execute(self, sql: str, parameters: Tuple[Any, ...] = ()) -> AsyncCursor:
        if self._conn is None:
            await self._connect()
        assert self._conn is not None
        conn = self._conn
        return await self._run(lambda: AsyncCursor(conn.execute(sql, parameters), self))

    async def executemany(self, sql: str, seq_of_parameters: List[Tuple[Any, ...]]) -> AsyncCursor:
        if self._conn is None:
            await self._connect()
        assert self._conn is not None
        conn = self._conn
        return await self._run(lambda: AsyncCursor(conn.executemany(sql, seq_of_parameters), self))

    async def commit(self) -> None:
        if self._conn is not None:
            await self._run(self._conn.commit)

    async def rollback(self) -> None:
        if self._conn is not None:
            await self._run(self._conn.rollback)

    async def close(self) -> None:
        async with self._connect_lock:
            try:
                if self._conn is not None:
                    await self._run(self._conn.close)
            finally:
                self._conn = None
                if self._executor is not None:
                    self._executor.shutdown(wait=False)
                    self._executor = None

    async def __aenter__(self) -> "AsyncConnection":
        await self._connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.close()


async def connect(database: str, **kwargs: Any) -> AsyncConnection:
    """
    Asynchronously connects to a SQLite database.
    """
    conn = AsyncConnection(database, **kwargs)
    await conn._connect()
    return conn
