from __future__ import annotations

import aiosqlite


async def checkpoint(conn: aiosqlite.Connection, mode: str = 'PASSIVE') -> dict[str, int]:
    """Execute WAL checkpoint. Modes: PASSIVE, FULL, RESTART, TRUNCATE."""
    cursor = await conn.execute(f'PRAGMA wal_checkpoint({mode})')
    row = await cursor.fetchone()
    if row:
        return {'busy': row[0], 'log_pages': row[1], 'checkpointed_pages': row[2]}
    return {}
