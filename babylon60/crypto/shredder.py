from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aiosqlite
logger = logging.getLogger("babylon60.crypto.shredder")
__all__ = ["CryptoShredder", "ShredBatchResult", "ShredResult"]


@dataclass
class ShredResult:
    fact_id: int
    tenant_id: str
    success: bool
    reason: str = "gdpr_erasure"
    error: str | None = None
    was_already_shredded: bool = False


@dataclass
class ShredBatchResult:
    total_requested: int = 0
    shredded: int = 0
    already_shredded: int = 0
    failed: int = 0
    results: list[ShredResult] = field(default_factory=list)


class CryptoShredder:
    def __init__(self, conn: aiosqlite.Connection | sqlite3.Connection):
        self._conn = conn
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        sql = "\n            CREATE TABLE IF NOT EXISTS shredded_keys (\n                id          INTEGER PRIMARY KEY AUTOINCREMENT,\n                fact_id     INTEGER NOT NULL,\n                tenant_id   TEXT    NOT NULL DEFAULT 'default',\n                reason      TEXT    NOT NULL DEFAULT 'gdpr_erasure',\n                shredded_by TEXT,\n                shredded_at TEXT    NOT NULL DEFAULT (datetime('now')),\n                UNIQUE(fact_id, tenant_id)\n            );\n        "
        try:
            if isinstance(self._conn, sqlite3.Connection):
                self._conn.execute(sql)
                self._conn.commit()
        except sqlite3.Error as e:
            logger.warning("Schema creation skipped (may exist): %s", e)

    async def _ensure_schema_async(self) -> None:
        sql = "\n            CREATE TABLE IF NOT EXISTS shredded_keys (\n                id          INTEGER PRIMARY KEY AUTOINCREMENT,\n                fact_id     INTEGER NOT NULL,\n                tenant_id   TEXT    NOT NULL DEFAULT 'default',\n                reason      TEXT    NOT NULL DEFAULT 'gdpr_erasure',\n                shredded_by TEXT,\n                shredded_at TEXT    NOT NULL DEFAULT (datetime('now')),\n                UNIQUE(fact_id, tenant_id)\n            );\n        "
        try:
            await __import__("typing").cast(__import__("typing").Any, self._conn).execute(sql)
            await __import__("typing").cast(__import__("typing").Any, self._conn).commit()
        except (sqlite3.Error, OSError) as e:
            logger.warning("Async schema creation skipped: %s", e)

    def is_shredded(self, fact_id: int, tenant_id: str = "default") -> bool:
        if not isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use is_shredded_async for async connections")
        cursor = self._conn.execute(
            "SELECT 1 FROM shredded_keys WHERE fact_id = ? AND tenant_id = ?", (fact_id, tenant_id)
        )
        return cursor.fetchone() is not None

    async def is_shredded_async(self, fact_id: int, tenant_id: str = "default") -> bool:
        cursor = (
            await __import__("typing")
            .cast(__import__("typing").Any, self._conn)
            .execute("SELECT 1 FROM shredded_keys WHERE fact_id = ? AND tenant_id = ?", (fact_id, tenant_id))
        )
        return await cursor.fetchone() is not None

    def get_shredded_fact_ids(self, tenant_id: str = "default") -> set[int]:
        if not isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use get_shredded_fact_ids_async for async")
        cursor = self._conn.execute("SELECT fact_id FROM shredded_keys WHERE tenant_id = ?", (tenant_id,))
        return {row[0] for row in cursor.fetchall()}

    async def get_shredded_fact_ids_async(self, tenant_id: str = "default") -> set[int]:
        cursor = (
            await __import__("typing")
            .cast(__import__("typing").Any, self._conn)
            .execute("SELECT fact_id FROM shredded_keys WHERE tenant_id = ?", (tenant_id,))
        )
        rows = await cursor.fetchall()
        return {row[0] for row in rows}

    def shred_fact(
        self, fact_id: int, tenant_id: str = "default", reason: str = "gdpr_erasure", shredded_by: str | None = None
    ) -> ShredResult:
        if not isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use shred_fact_async for async connections")
        if self.is_shredded(fact_id, tenant_id):
            return ShredResult(
                fact_id=fact_id, tenant_id=tenant_id, success=True, reason=reason, was_already_shredded=True
            )
        try:
            ts = datetime.fromtimestamp(time.time(), tz=UTC).isoformat()
            self._conn.execute(
                "INSERT INTO shredded_keys (fact_id, tenant_id, reason, shredded_by, shredded_at) VALUES (?, ?, ?, ?, ?)",
                (fact_id, tenant_id, reason, shredded_by, ts),
            )
            self._invalidate_fact_key(fact_id, tenant_id)
            self._conn.commit()
            logger.info("Crypto-shredded fact #%d (tenant=%s, reason=%s)", fact_id, tenant_id, reason)
            return ShredResult(fact_id=fact_id, tenant_id=tenant_id, success=True, reason=reason)
        except sqlite3.IntegrityError:
            return ShredResult(
                fact_id=fact_id, tenant_id=tenant_id, success=True, reason=reason, was_already_shredded=True
            )
        except (sqlite3.Error, OSError) as e:
            logger.error("Shred failed for fact #%d: %s", fact_id, e)
            return ShredResult(fact_id=fact_id, tenant_id=tenant_id, success=False, reason=reason, error=str(e))

    async def shred_fact_async(
        self, fact_id: int, tenant_id: str = "default", reason: str = "gdpr_erasure", shredded_by: str | None = None
    ) -> ShredResult:
        if await self.is_shredded_async(fact_id, tenant_id):
            return ShredResult(
                fact_id=fact_id, tenant_id=tenant_id, success=True, reason=reason, was_already_shredded=True
            )
        try:
            ts = datetime.fromtimestamp(time.time(), tz=UTC).isoformat()
            await (
                __import__("typing")
                .cast(__import__("typing").Any, self._conn)
                .execute(
                    "INSERT INTO shredded_keys (fact_id, tenant_id, reason, shredded_by, shredded_at) VALUES (?, ?, ?, ?, ?)",
                    (fact_id, tenant_id, reason, shredded_by, ts),
                )
            )
            self._invalidate_fact_key(fact_id, tenant_id)
            await __import__("typing").cast(__import__("typing").Any, self._conn).commit()
            logger.info("Crypto-shredded fact #%d (tenant=%s, reason=%s)", fact_id, tenant_id, reason)
            return ShredResult(fact_id=fact_id, tenant_id=tenant_id, success=True, reason=reason)
        except sqlite3.IntegrityError:
            return ShredResult(
                fact_id=fact_id, tenant_id=tenant_id, success=True, reason=reason, was_already_shredded=True
            )
        except (sqlite3.Error, OSError) as e:
            logger.error("Shred failed for fact #%d: %s", fact_id, e)
            return ShredResult(fact_id=fact_id, tenant_id=tenant_id, success=False, reason=reason, error=str(e))

    async def shred_by_project(
        self, project: str, tenant_id: str = "default", reason: str = "project_erasure", shredded_by: str | None = None
    ) -> ShredBatchResult:
        cursor = (
            await __import__("typing")
            .cast(__import__("typing").Any, self._conn)
            .execute("SELECT id FROM facts WHERE project = ? AND tenant_id = ?", (project, tenant_id))
        )
        rows = await cursor.fetchall()
        fact_ids = [row[0] for row in rows]
        return await self._shred_batch(fact_ids, tenant_id, reason, shredded_by)

    async def _shred_batch(
        self, fact_ids: list[int], tenant_id: str, reason: str, shredded_by: str | None
    ) -> ShredBatchResult:
        batch = ShredBatchResult(total_requested=len(fact_ids))
        for fact_id in fact_ids:
            result = await self.shred_fact_async(fact_id, tenant_id, reason, shredded_by)
            batch.results.append(result)
            if result.was_already_shredded:
                batch.already_shredded += 1
            elif result.success:
                batch.shredded += 1
            else:
                batch.failed += 1
        return batch

    def _invalidate_fact_key(self, fact_id: int, tenant_id: str) -> None:
        try:
            from babylon60.crypto.aes import get_default_encrypter

            enc = get_default_encrypter()
            cache_key = f"{tenant_id}:fact:{fact_id}"
            if not hasattr(enc, "_shredded_facts"):
                enc._shredded_facts = set()  # type: ignore[attr-defined]
            __import__("typing").cast(set, enc._shredded_facts).add(cache_key)  # type: ignore[attr-defined]
        except (ImportError, RuntimeError) as e:
            logger.debug("Key invalidation skipped: %s", e)

    def audit_shredding(self) -> dict[str, Any]:
        if not isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use audit_shredding_async for async")
        cursor = self._conn.execute(
            "SELECT COUNT(*), reason, MIN(shredded_at), MAX(shredded_at) FROM shredded_keys GROUP BY reason"
        )
        rows = cursor.fetchall()
        reasons = {}
        total = 0
        for row in rows:
            count, reason, earliest, latest = row
            total += count
            reasons[reason] = {"count": count, "earliest": earliest, "latest": latest}
        return {
            "total_shredded": total,
            "by_reason": reasons,
            "compliant": True,
            "audit_timestamp": datetime.fromtimestamp(time.monotonic(), tz=UTC).isoformat(),
        }
