"""SQLite keeps its owning thread even if the event loop changes workers."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import threading

import pytest

from babylon60.primitives.async_db import AsyncConnection, connect


@pytest.mark.asyncio
async def test_connection_and_cursor_survive_default_executor_change() -> None:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as first, ThreadPoolExecutor(max_workers=1) as second:
        loop.set_default_executor(first)
        db = await connect(":memory:")
        loop.set_default_executor(second)
        try:
            await db.execute("CREATE TABLE ledger (id INTEGER PRIMARY KEY, tx TEXT)")
            await db.executemany("INSERT INTO ledger(tx) VALUES (?)", [("genesis",), ("next",)])
            await db.commit()
            cursor = await db.execute("SELECT tx FROM ledger ORDER BY id")
            assert cursor.rowcount == -1
            row = await cursor.fetchone()
            assert row is not None and row[0] == "genesis"
            assert [row[0] for row in await cursor.fetchall()] == ["next"]
            await db.execute("INSERT INTO ledger(tx) VALUES ('rolled back')")
            await db.rollback()
            count = await (await db.execute("SELECT COUNT(*) FROM ledger")).fetchone()
            assert count is not None and count[0] == 2
        finally:
            await db.close()


@pytest.mark.asyncio
async def test_concurrent_inserts_and_transaction_rollback(tmp_path: Path) -> None:
    path = str(tmp_path / "ledger.db")
    db = await connect(path)
    try:
        await db.execute("CREATE TABLE ledger (id INTEGER PRIMARY KEY)")
        # Warm up the connection before concurrent operations.
        await db.execute("SELECT 1")
        await asyncio.gather(*(db.execute("INSERT INTO ledger VALUES (?)", (i,)) for i in range(100)))
        await db.commit()
        cursor = await db.execute("SELECT id FROM ledger ORDER BY id")
        assert [row[0] for row in await cursor.fetchall()] == list(range(100))
        with pytest.raises(ValueError, match="abort transaction"):
            async with db:
                await db.execute("INSERT INTO ledger VALUES (100)")
                raise ValueError("abort transaction")
    finally:
        await db.close()
    async with await connect(path) as reopened:
        count = await (await reopened.execute("SELECT COUNT(*) FROM ledger")).fetchone()
        assert count is not None and count[0] == 100


@pytest.mark.asyncio
async def test_concurrent_first_use_opens_one_database() -> None:
    db = AsyncConnection(":memory:")
    try:
        await asyncio.gather(*(db._connect() for _ in range(20)))
        await db.execute("CREATE TABLE ledger (id INTEGER)")
        await db.execute("INSERT INTO ledger VALUES (1)")
        row = await (await db.execute("SELECT id FROM ledger")).fetchone()
        assert row is not None and row[0] == 1
    finally:
        await db.close()
        await db.close()


@pytest.mark.asyncio
async def test_cancelled_open_closes_connection_on_its_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    started, release, closed = threading.Event(), threading.Event(), threading.Event()
    original_connect = sqlite3.connect

    class TrackedConnection(sqlite3.Connection):
        def close(self) -> None:
            super().close()
            closed.set()

    def slow_connect(database: str) -> sqlite3.Connection:
        connection = original_connect(database, factory=TrackedConnection)
        started.set()
        if not release.wait(timeout=5):
            connection.close()
            raise TimeoutError("test did not release SQLite opening")
        return connection

    monkeypatch.setattr(sqlite3, "connect", slow_connect)
    opening = asyncio.create_task(connect(":memory:"))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        opening.cancel()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await opening
    assert closed.is_set()
