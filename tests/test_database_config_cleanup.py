"""Fault injection denies real SQLite PRAGMAs; no production connection is mocked."""

import sqlite3

import aiosqlite
import pytest

from babylon60.database import core


def deny_pragma(monkeypatch, failure_index):
    real_connect = sqlite3.connect
    opened = []

    def connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        seen = 0

        def authorize(action, *unused):
            nonlocal seen
            if action == sqlite3.SQLITE_PRAGMA:
                seen += 1
                if seen == failure_index:
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        connection.set_authorizer(authorize)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    return opened


@pytest.mark.parametrize("failure_index", [1, 2, 3, 4])
def test_sync_configuration_failure_closes_the_real_connection(tmp_path, monkeypatch, failure_index):
    opened = deny_pragma(monkeypatch, failure_index)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            core.connect_sync(tmp_path / "ledger.db")
        assert len(opened) == 1
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            opened[0].execute("SELECT 1")
    finally:
        for connection in opened:
            connection.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_index", [1, 2, 3, 4])
async def test_async_configuration_failure_closes_the_real_connection(tmp_path, monkeypatch, failure_index):
    deny_pragma(monkeypatch, failure_index)
    real_connect = aiosqlite.connect
    opened = []

    def capture(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(aiosqlite, "connect", capture)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            await core.connect(tmp_path / "ledger.db")
        assert len(opened) == 1
        with pytest.raises(ValueError, match="no active connection|Connection closed"):
            await opened[0].execute("SELECT 1")
    finally:
        for connection in opened:
            await connection.close()
