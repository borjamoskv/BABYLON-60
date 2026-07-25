from __future__ import annotations
import asyncio
from pathlib import Path
import aiosqlite

async def apply_migrations(conn: aiosqlite.Connection, migrations_dir: str | Path) -> None:
    migrations_dir = Path(migrations_dir)
    if not migrations_dir.exists():
        return
    
    await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    await conn.commit()

    cursor = await conn.execute('SELECT filename FROM _migrations ORDER BY id ASC')
    applied = {row[0] for row in await cursor.fetchall()}

    files = sorted([f for f in migrations_dir.iterdir() if f.suffix == '.sql'])
    
    for f in files:
        if f.name not in applied:
            sql = f.read_text(encoding='utf-8')
            await conn.executescript(sql)
            await conn.execute('INSERT INTO _migrations (filename) VALUES (?)', (f.name,))
            await conn.commit()
