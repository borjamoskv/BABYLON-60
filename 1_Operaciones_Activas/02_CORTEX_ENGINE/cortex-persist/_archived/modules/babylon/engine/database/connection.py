"""
Database Connection & Vector Initialization
"""

import os

import aiosqlite
import sqlite_vec

DB_PATH = os.environ.get("CORTEX_DB_PATH", "cortex.db")


async def init_db() -> aiosqlite.Connection:
    """
    Initialize SQLite with sqlite-vec extension and WAL mode.
    """
    conn = await aiosqlite.connect(DB_PATH)

    # Load sqlite-vec extension
    await conn.enable_load_extension(True)
    sqlite_vec.load(conn._conn)
    await conn.enable_load_extension(False)

    # Thermodynamic Constraints: WAL & busy_timeout
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA busy_timeout=5000;")
    await conn.execute("PRAGMA synchronous=NORMAL;")

    # Initialize Core Tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taint TEXT NOT NULL UNIQUE,
            data JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Initialize Vector Table (vec0) - Dims 1536 (e.g. OpenAI/Local Equivalent)
    await conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS cortex_embeddings_text USING vec0(
            fact_id INTEGER PRIMARY KEY,
            embedding float[1536]
        )
    """)

    await conn.commit()
    return conn
