# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""Legacy erasure markers; cryptographic destruction is unsupported.

The current encrypter uses tenant keys derived from a recoverable master key.
Neither a database marker nor cache invalidation destroys that capability.
Keep historical markers readable, but refuse new erasure claims until an
independent per-fact key lifecycle with verified destruction exists.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TypedDict

import aiosqlite

logger = logging.getLogger("babylon60.crypto.shredder")

__all__ = ["CryptoShredder", "ShredAuditReport", "ShredBatchResult", "ShredReasonStats", "ShredResult"]


class ShredReasonStats(TypedDict):
    count: int
    earliest: str | None
    latest: str | None


class ShredAuditReport(TypedDict):
    total_shredded: int
    by_reason: dict[str, ShredReasonStats]
    compliant: bool
    audit_timestamp: str


@dataclass
class ShredResult:
    """Outcome of a single fact shred operation."""

    fact_id: int
    tenant_id: str
    success: bool
    reason: str = "gdpr_erasure"
    error: str | None = None
    was_already_shredded: bool = False


@dataclass
class ShredBatchResult:
    """Aggregate result of a batch shred operation."""

    total_requested: int = 0
    shredded: int = 0
    already_shredded: int = 0
    failed: int = 0
    results: list[ShredResult] = field(default_factory=list)


class CryptoShredder:
    """Read historical markers and fail closed on unsupported key destruction."""

    def __init__(self, conn: aiosqlite.Connection | sqlite3.Connection) -> None:
        self._conn = conn
        self._ensure_schema()

    @property
    def _sync_conn(self) -> sqlite3.Connection:
        if isinstance(self._conn, sqlite3.Connection):
            return self._conn
        raise TypeError("Use async methods for aiosqlite connections")

    @property
    def _async_conn(self) -> aiosqlite.Connection:
        if isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use sync methods for sqlite3 connections")
        return self._conn

    def _ensure_schema(self) -> None:
        """Create shredded_keys table if it doesn't exist."""
        sql = """
            CREATE TABLE IF NOT EXISTS shredded_keys (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id     INTEGER NOT NULL,
                tenant_id   TEXT    NOT NULL DEFAULT 'default',
                reason      TEXT    NOT NULL DEFAULT 'gdpr_erasure',
                shredded_by TEXT,
                shredded_at TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(fact_id, tenant_id)
            );
        """
        try:
            if isinstance(self._conn, sqlite3.Connection):
                self._conn.execute(sql)
                self._conn.commit()
        except sqlite3.Error as e:
            logger.warning("Schema creation skipped (may exist): %s", e)

    async def _ensure_schema_async(self) -> None:
        """Async variant for aiosqlite connections."""
        sql = """
            CREATE TABLE IF NOT EXISTS shredded_keys (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id     INTEGER NOT NULL,
                tenant_id   TEXT    NOT NULL DEFAULT 'default',
                reason      TEXT    NOT NULL DEFAULT 'gdpr_erasure',
                shredded_by TEXT,
                shredded_at TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(fact_id, tenant_id)
            );
        """
        try:
            await self._async_conn.execute(sql)
            await self._async_conn.commit()
        except (sqlite3.Error, OSError) as e:
            logger.warning("Async schema creation skipped: %s", e)

    def is_shredded(self, fact_id: int, tenant_id: str = "default") -> bool:
        """Check for a historical marker; this is not proof of erasure (sync)."""
        cursor = self._sync_conn.execute(
            "SELECT 1 FROM shredded_keys WHERE fact_id = ? AND tenant_id = ?",
            (fact_id, tenant_id),
        )
        return cursor.fetchone() is not None

    async def is_shredded_async(self, fact_id: int, tenant_id: str = "default") -> bool:
        """Check for a historical marker; this is not proof of erasure (async)."""
        cursor = await self._async_conn.execute(
            "SELECT 1 FROM shredded_keys WHERE fact_id = ? AND tenant_id = ?",
            (fact_id, tenant_id),
        )
        return (await cursor.fetchone()) is not None

    def get_shredded_fact_ids(self, tenant_id: str = "default") -> set[int]:
        """Return all shredded fact IDs for a tenant (sync)."""
        cursor = self._sync_conn.execute(
            "SELECT fact_id FROM shredded_keys WHERE tenant_id = ?",
            (tenant_id,),
        )
        return {int(row[0]) for row in cursor.fetchall()}

    async def get_shredded_fact_ids_async(self, tenant_id: str = "default") -> set[int]:
        """Return all shredded fact IDs for a tenant (async)."""
        cursor = await self._async_conn.execute(
            "SELECT fact_id FROM shredded_keys WHERE tenant_id = ?",
            (tenant_id,),
        )
        rows = await cursor.fetchall()
        return {int(row[0]) for row in rows}

    def shred_fact(
        self,
        fact_id: int,
        tenant_id: str = "default",
        reason: str = "gdpr_erasure",
        shredded_by: str | None = None,
    ) -> ShredResult:
        """Refuse erasure: the legacy key schedule remains recoverable."""
        if not isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use shred_fact_async for async connections")
        return self._unsupported_result(fact_id, tenant_id, reason)

    @staticmethod
    def _unsupported_result(fact_id: int, tenant_id: str, reason: str) -> ShredResult:
        return ShredResult(
            fact_id=fact_id,
            tenant_id=tenant_id,
            success=False,
            reason=reason,
            error="CRYPTO_ERASURE_UNSUPPORTED: no independently destructible per-fact key",
        )

    async def shred_fact_async(
        self,
        fact_id: int,
        tenant_id: str = "default",
        reason: str = "gdpr_erasure",
        shredded_by: str | None = None,
    ) -> ShredResult:
        """Refuse erasure without writing a marker or resolving operator keys."""
        if isinstance(self._conn, sqlite3.Connection):
            raise TypeError("Use shred_fact for sync connections")
        return self._unsupported_result(fact_id, tenant_id, reason)

    async def shred_by_project(
        self,
        project: str,
        tenant_id: str = "default",
        reason: str = "project_erasure",
        shredded_by: str | None = None,
    ) -> ShredBatchResult:
        """Shred all facts in a project."""
        cursor = await self._async_conn.execute(
            "SELECT id FROM facts WHERE project = ? AND tenant_id = ?",
            (project, tenant_id),
        )
        rows = await cursor.fetchall()
        fact_ids = [int(row[0]) for row in rows]

        return await self._shred_batch(fact_ids, tenant_id, reason, shredded_by)

    async def _shred_batch(
        self,
        fact_ids: list[int],
        tenant_id: str,
        reason: str,
        shredded_by: str | None,
    ) -> ShredBatchResult:
        """Internal batch shred implementation."""
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

    def audit_shredding(self) -> ShredAuditReport:
        """Report on all shredded facts for compliance auditing.

        Returns aggregate statistics without revealing content.
        """
        cursor = self._sync_conn.execute(
            "SELECT COUNT(*), reason, MIN(shredded_at), MAX(shredded_at) FROM shredded_keys GROUP BY reason"
        )
        rows = cursor.fetchall()

        reasons: dict[str, ShredReasonStats] = {}
        total = 0
        for row in rows:
            count = int(row[0])
            reason = str(row[1])
            earliest = str(row[2]) if row[2] is not None else None
            latest = str(row[3]) if row[3] is not None else None
            total += count
            reasons[reason] = {
                "count": count,
                "earliest": earliest,
                "latest": latest,
            }

        return {
            "total_shredded": total,
            "by_reason": reasons,
            "compliant": False,
            "audit_timestamp": datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat(),
        }
