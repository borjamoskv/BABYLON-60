from __future__ import annotations

import sqlite3
from pathlib import Path

import aiosqlite

_ALLOWED_SYNCHRONOUS = frozenset({'FULL', 'NORMAL'})
_BUSY_TIMEOUT_MS = 5000

def _validate_synchronous(synchronous: str) -> str:
    if synchronous not in _ALLOWED_SYNCHRONOUS:
        raise ValueError(f'INV_BFT_02: synchronous debe ser FULL o NORMAL, recibido {synchronous!r}. El ledger maestro exige FULL; NORMAL solo para superficies no-ledger.')
    return synchronous

import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

async def connect(db_path: str | Path, *, synchronous: str='FULL') -> aiosqlite.Connection:
    mode = _validate_synchronous(synchronous)
    for attempt in range(3):
        try:
            db = await aiosqlite.connect(str(db_path), isolation_level=None, timeout=5.0)
            await db.execute('PRAGMA journal_mode=WAL')
            await db.execute(f'PRAGMA synchronous={mode}')
            await db.execute('PRAGMA foreign_keys=ON')
            await db.execute(f'PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}')
            # SOTA Exergy Optimizations
            await db.execute('PRAGMA mmap_size=30000000000')
            await db.execute('PRAGMA temp_store=MEMORY')
            await db.execute('PRAGMA cache_size=-64000')
            return db
        except sqlite3.OperationalError as e:
            if 'busy' in str(e).lower() and attempt < 2:
                await asyncio.sleep(0.1 * (2 ** attempt))
            else:
                raise

@asynccontextmanager
async def get_connection(db_path: str | Path, *, synchronous: str='FULL'):
    conn = await connect(db_path, synchronous=synchronous)
    try:
        yield conn
    finally:
        try:
            await conn.execute('PRAGMA optimize')
        except Exception as e:
            logger.warning(f"Failed to optimize DB: {e}")
        await conn.close()

def connect_sync(db_path: str | Path, *, synchronous: str='FULL') -> sqlite3.Connection:
    mode = _validate_synchronous(synchronous)
    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=5.0)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute(f'PRAGMA synchronous={mode}')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute(f'PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}')
    # SOTA Exergy Optimizations
    conn.execute('PRAGMA mmap_size=30000000000')
    conn.execute('PRAGMA temp_store=MEMORY')
    conn.execute('PRAGMA cache_size=-64000')
    return conn