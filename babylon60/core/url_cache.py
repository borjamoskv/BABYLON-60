"""
[Causal-Determinist] babylon60.core.url_cache — Strict Thermodynamic Cache for Browser Agent.

Enforces Level 0 Anti-429 Fallback and Exergy Conservation.
Prevents duplicate external network requests within a TTL window (default 24h).

Fulfills INV_BFT_02 (WAL mode via babylon60.database.core) and
INV_BFT_03 (causal_taint required on all writes).
"""

from __future__ import annotations

import hashlib
import time
from typing import Optional
from babylon60.database.core import connect_sync, connect

DB_NAME = "browser_url_cache.db"

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS url_cache (
    url_hash TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    causal_taint TEXT NOT NULL
);
"""

def hash_url(url: str) -> str:
    """Computes deterministic SHA256 hash of a normalized URL."""
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()

class URLCacheSync:
    """Synchronous URL Cache interface for CLI tools and scripts."""

    def __init__(self, db_name: str = DB_NAME):
        self.conn = connect_sync(db_name, synchronous="NORMAL")
        self.conn.execute(_INIT_SQL)

    def get(self, url: str, max_age_seconds: int = 86400) -> Optional[str]:
        """Retrieve cached payload if not expired."""
        u_hash = hash_url(url)
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT payload, created_at FROM url_cache WHERE url_hash = ?",
            (u_hash,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        payload, created_at = row
        if time.time() - created_at > max_age_seconds:
            # Expired cache entry
            return None
        return payload

    def put(self, url: str, payload: str, causal_taint: str) -> None:
        """Store payload with causal_taint audit metadata (INV_BFT_03)."""
        if not causal_taint:
            raise ValueError("INV_BFT_03: causal_taint is mandatory for writes.")
            
        u_hash = hash_url(url)
        now = int(time.time())
        self.conn.execute(
            """
            INSERT OR REPLACE INTO url_cache (url_hash, url, payload, created_at, causal_taint)
            VALUES (?, ?, ?, ?, ?)
            """,
            (u_hash, url, payload, now, causal_taint)
        )

class URLCacheAsync:
    """Async URL Cache interface for event loops."""

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name

    async def _init_db(self, conn):
        await conn.execute(_INIT_SQL)

    async def get(self, url: str, max_age_seconds: int = 86400) -> Optional[str]:
        u_hash = hash_url(url)
        conn = await connect(self.db_name, synchronous="NORMAL")
        try:
            await self._init_db(conn)
            async with conn.execute(
                "SELECT payload, created_at FROM url_cache WHERE url_hash = ?",
                (u_hash,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                payload, created_at = row
                if time.time() - created_at > max_age_seconds:
                    return None
                return payload
        finally:
            await conn.close()

    async def put(self, url: str, payload: str, causal_taint: str) -> None:
        if not causal_taint:
            raise ValueError("INV_BFT_03: causal_taint is mandatory for writes.")
        u_hash = hash_url(url)
        now = int(time.time())
        conn = await connect(self.db_name, synchronous="NORMAL")
        try:
            await self._init_db(conn)
            await conn.execute(
                """
                INSERT OR REPLACE INTO url_cache (url_hash, url, payload, created_at, causal_taint)
                VALUES (?, ?, ?, ?, ?)
                """,
                (u_hash, url, payload, now, causal_taint)
            )
        finally:
            await conn.close()
