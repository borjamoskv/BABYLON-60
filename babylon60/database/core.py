# [C5-REAL] babylon60.database.core — único punto de conexión SQLite del kernel.
# Génesis: CENT-03 (AGENTS.md INV_BFT_02 mandaba sobre un módulo inexistente) +
# CENT-06 (conexiones directas con pragmas divergentes). Toda conexión sale de
from __future__ import annotations

import sqlite3
from pathlib import Path

import aiosqlite

_ALLOWED_SYNCHRONOUS = frozenset({"FULL", "NORMAL"})
_BUSY_TIMEOUT_MS = 5000


def _validate_synchronous(synchronous: str) -> str:
    if synchronous not in _ALLOWED_SYNCHRONOUS:
        raise ValueError(
            f"INV_BFT_02: synchronous debe ser FULL o NORMAL, recibido {synchronous!r}. "
            "El ledger maestro exige FULL; NORMAL solo para superficies no-ledger."
        )
    return synchronous


async def connect(db_path: str | Path, *, synchronous: str = "FULL") -> aiosqlite.Connection:
    """Conexión async (aiosqlite) con los pragmas de INV_BFT_02 aplicados."""
    mode = _validate_synchronous(synchronous)
    db = await aiosqlite.connect(str(db_path), isolation_level=None, timeout=5.0)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute(f"PRAGMA synchronous={mode}")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    return db


def connect_sync(db_path: str | Path, *, synchronous: str = "FULL") -> sqlite3.Connection:
    """Conexión síncrona (CLI/scripts fuera de event loop; INV_BFT_02 prohíbe
    sqlite3 síncrono DENTRO de un event loop — para eso está connect())."""
    mode = _validate_synchronous(synchronous)
    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA synchronous={mode}")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    return conn
