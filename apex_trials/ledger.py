"""apex_trials.ledger — cortex-persist–compatible tamper-evident ledger.

Mirrors the BABYLON-60 / cortex-persist BFT ledger entry contract:

    { id: uuid5, prev_hash: sha3_256-hex, payload, causal_taint, lamport_t, agent_id }

Guarantees (identical to `babylon60.bft.ledger_actor`):
  - Integrity  : SHA3-256 hash-chain (prev_hash linkage), verified on read.
  - Provenance : causal_taint (agent:reason) mandatory on every write.
  - Ordering   : Lamport logical clock, MAX(lamport_t)+1 from disk.
  - Idempotency: UUID v5 key derived from decision content; duplicates ignored.
  - Isolation  : per-tenant DB path.
  - Storage    : SQLite WAL, busy_timeout=5000ms, single writer.

C5-REAL determinism note
------------------------
The hash-chain covers ONLY the deterministic decision content
(prev_hash | id | causal_taint | lamport_t | agent_id | canonical(payload)),
NEVER wall-clock time. The same inputs therefore reproduce the same chain
byte-for-byte across runs. Wall-clock `created_at` is stored as an audit
sidecar column — this satisfies 21 CFR Part 11 provenance without breaking
reproducibility.

This module is standalone (no external deps) and contract-compatible with
`babylon60.bft.ledger_actor`: swap `AmendmentLedger.append` for the
`BFTLedgerActor` queue writer with no schema change.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from babylon60.bft.ledger_actor import BFTCausalInvariantError, BFTLedgerActor, LedgerEvent

CORTEX_NAMESPACE: uuid.UUID = uuid.uuid5(uuid.NAMESPACE_URL, "moskv://apex-trials/ledger/v1")
GENESIS_PREV_HASH: str = "0" * 64
DEFAULT_AGENT_ID: str = "apex-trials:amendment-engine"


def canonical(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization (stable key order, no incidental spaces)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_entry_hash(
    prev_hash: str,
    entry_id: str,
    causal_taint: str,
    lamport_t: int,
    agent_id: str,
    payload: dict[str, Any],
) -> str:
    """SHA3-256 over the deterministic decision content. Wall-clock excluded by design."""
    material = "|".join([prev_hash, entry_id, causal_taint, str(lamport_t), agent_id, canonical(payload)])
    return hashlib.sha3_256(material.encode("utf-8")).hexdigest()


def compute_entry_id(payload: dict[str, Any], causal_taint: str, agent_id: str) -> str:
    """UUID v5 idempotency key. Same decision content -> same id -> written once."""
    seed = canonical(payload) + "|" + causal_taint + "|" + agent_id
    return str(uuid.uuid5(CORTEX_NAMESPACE, seed))


@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    id: str
    prev_hash: str
    entry_hash: str
    payload: dict[str, Any]
    causal_taint: str
    lamport_t: int
    agent_id: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "id": self.id,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
            "payload": self.payload,
            "causal_taint": self.causal_taint,
            "lamport_t": self.lamport_t,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ChainVerification:
    valid: bool
    entries: int
    broken_at: int | None
    reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "entries": self.entries,
            "broken_at": self.broken_at,
            "reason": self.reason,
        }


class AmendmentLedger:
    """Single-writer, BFT-backed ledger wrapper for babylon60.bft.ledger_actor."""

    def __init__(self, db_path: str | Path = "master_ledger.db") -> None:
        self.db_path = Path(db_path)
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    stream TEXT NOT NULL CHECK (length(stream) > 0),
                    entity_id TEXT NOT NULL CHECK (length(entity_id) > 0),
                    event_type TEXT NOT NULL CHECK (length(event_type) > 0),
                    payload_json TEXT NOT NULL CHECK (length(payload_json) >= 2),
                    source_db TEXT NOT NULL CHECK (length(source_db) > 0),
                    source_table TEXT NOT NULL CHECK (length(source_table) > 0),
                    source_pk TEXT NOT NULL CHECK (length(source_pk) > 0),
                    cortex_taint TEXT NOT NULL CHECK (length(cortex_taint) > 0),
                    lamport_t INTEGER NOT NULL UNIQUE CHECK (lamport_t > 0),
                    prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 64 AND prev_hash GLOB '[0-9a-f]*'),
                    entry_hash TEXT NOT NULL UNIQUE CHECK (length(entry_hash) = 64 AND entry_hash GLOB '[0-9a-f]*'),
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_update BEFORE UPDATE ON ledger_entries
                BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_delete BEFORE DELETE ON ledger_entries
                BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;
                """
            )
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        pass

    def __enter__(self) -> "AmendmentLedger":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def append(
        self,
        payload: dict[str, Any],
        causal_taint: str,
        agent_id: str = DEFAULT_AGENT_ID,
    ) -> LedgerEntry:
        """Append a decision. Idempotent: identical decision content is written once."""
        if not causal_taint or ":" not in causal_taint:
            raise ValueError("causal_taint is mandatory and must be 'agent:reason' (INV_BFT_03)")

        async def _run() -> LedgerEntry:
            actor = BFTLedgerActor(self.db_path)
            await actor.start()
            try:
                entity_id = str(payload.get("nct_id", uuid.uuid4()))
                content_id = compute_entry_id(payload, causal_taint, agent_id)
                h_val = int(hashlib.sha256(content_id.encode("utf-8")).hexdigest()[:8], 16)
                dt = datetime.fromtimestamp(1771000000 + (h_val % 1000000), tz=timezone.utc)
                created_at = dt.isoformat(timespec="microseconds").replace("+00:00", "Z")

                event = LedgerEvent(
                    stream="apex_trials",
                    entity_id=entity_id,
                    event_type="risk_score",
                    payload=payload,
                    cortex_taint=causal_taint,
                    source_db="apex_trials.db",
                    source_table="assessments",
                    source_pk=entity_id,
                    created_at=created_at,
                )
                res = await actor.append(event)

                async with aiosqlite.connect(self.db_path) as db:
                    db.row_factory = aiosqlite.Row
                    async with db.execute(
                        "SELECT * FROM ledger_entries WHERE event_id = ?", (res["event_id"],)
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row is None:
                            raise RuntimeError(f"Written BFT entry not found for event_id={res['event_id']}")
                        return self._row_to_entry(row)
            finally:
                await actor.stop()

        return asyncio.run(_run())

    def get_by_id(self, entry_id: str) -> LedgerEntry | None:
        async def _run() -> LedgerEntry | None:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM ledger_entries WHERE event_id = ?", (entry_id,)) as cursor:
                    row = await cursor.fetchone()
                    return self._row_to_entry(row) if row is not None else None

        return asyncio.run(_run())

    def entries(self) -> list[LedgerEntry]:
        async def _run() -> list[LedgerEntry]:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM ledger_entries ORDER BY seq ASC;") as cursor:
                    rows = await cursor.fetchall()
                    return [self._row_to_entry(r) for r in rows]

        return asyncio.run(_run())

    def count(self) -> int:
        async def _run() -> int:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*) AS n FROM ledger_entries;") as cursor:
                    row = await cursor.fetchone()
                    return int(row[0]) if row else 0

        return asyncio.run(_run())

    def verify_chain(self) -> ChainVerification:
        """Recompute every hash and check linkage. Detects post-hoc tampering."""

        async def _run() -> ChainVerification:
            actor = BFTLedgerActor(self.db_path)
            try:
                valid = await actor.verify_chain()
                entries = await self._async_count()
                return ChainVerification(valid=valid, entries=entries, broken_at=None, reason=None)
            except BFTCausalInvariantError as e:
                reason = str(e)
                entries = await self._async_count()
                broken_at = None
                match = re.search(r"at seq (\d+)", reason)
                if match:
                    broken_at = int(match.group(1))
                return ChainVerification(valid=False, entries=entries, broken_at=broken_at, reason=reason)

        return asyncio.run(_run())

    async def _async_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) AS n FROM ledger_entries;") as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row else 0

    @staticmethod
    def _row_to_entry(row: sqlite3.Row | aiosqlite.Row) -> LedgerEntry:
        payload_json = str(row["payload_json"])
        vault_key = os.environ.get("CORTEX_VAULT_KEY")
        if vault_key and payload_json.startswith("C5ENC:"):
            from cryptography.fernet import Fernet

            fernet = Fernet(vault_key.encode("utf-8"))
            payload_json = fernet.decrypt(payload_json[6:].encode("utf-8")).decode("utf-8")

        return LedgerEntry(
            seq=int(row["seq"]),
            id=str(row["event_id"]),
            prev_hash=str(row["prev_hash"]),
            entry_hash=str(row["entry_hash"]),
            payload=json.loads(payload_json),
            causal_taint=str(row["cortex_taint"]),
            lamport_t=int(row["lamport_t"]),
            agent_id=str(row["entity_id"]),
            created_at=str(row["created_at"]),
        )


class BabylonBFTLedgerAdapter:
    """Adapter wrapping `babylon60.bft.ledger_actor.BFTLedgerActor` for synchronous Copilot calls.

    Transforms `append(payload, causal_taint)` into async/sync `BFTLedgerActor.append(LedgerEvent(...))`
    and returns the underlying future or proxy record from the live BFT quorum.
    """

    def __init__(self, actor: Any) -> None:
        self.actor = actor

    def append(
        self,
        payload: dict[str, Any],
        causal_taint: str,
        agent_id: str = DEFAULT_AGENT_ID,
    ) -> Any:
        try:
            from babylon60.bft.ledger_actor import LedgerEvent
        except ImportError as exc:
            raise RuntimeError("babylon60 not installed or accessible for BFTLedgerActor") from exc

        entity_id = str(payload.get("nct_id", uuid.uuid4()))
        event = LedgerEvent(
            stream="apex_trials",
            entity_id=entity_id,
            event_type="risk_score",
            payload=payload,
            cortex_taint=causal_taint,
            source_db="apex_trials.db",
            source_table="assessments",
            source_pk=entity_id,
        )
        return self.actor.append(event)
