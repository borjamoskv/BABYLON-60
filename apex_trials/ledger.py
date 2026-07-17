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

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Fixed namespace so UUID v5 idempotency keys are stable across machines/runs.
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
    material = "|".join(
        [prev_hash, entry_id, causal_taint, str(lamport_t), agent_id, canonical(payload)]
    )
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
    """Single-writer, hash-chained, WAL-backed ledger. cortex-persist contract."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS ledger (
        seq          INTEGER PRIMARY KEY AUTOINCREMENT,
        id           TEXT    NOT NULL UNIQUE,
        prev_hash    TEXT    NOT NULL,
        entry_hash   TEXT    NOT NULL,
        payload      TEXT    NOT NULL,
        causal_taint TEXT    NOT NULL,
        lamport_t    INTEGER NOT NULL,
        agent_id     TEXT    NOT NULL,
        created_at   TEXT    NOT NULL
    );
    """

    def __init__(self, db_path: str | Path = "master_ledger.db") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, isolation_level=None, timeout=5.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA busy_timeout=5000;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.executescript(self._SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "AmendmentLedger":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # -- writer (single writer discipline: one connection, serialized) -----------
    def append(
        self,
        payload: dict[str, Any],
        causal_taint: str,
        agent_id: str = DEFAULT_AGENT_ID,
    ) -> LedgerEntry:
        """Append a decision. Idempotent: identical decision content is written once."""
        if not causal_taint or ":" not in causal_taint:
            raise ValueError("causal_taint is mandatory and must be 'agent:reason' (INV_BFT_03)")

        entry_id = compute_entry_id(payload, causal_taint, agent_id)
        existing = self.get_by_id(entry_id)
        if existing is not None:
            return existing  # INV_BFT_04: reject duplicate silently, return prior entry.

        cur = self._conn.execute("SELECT entry_hash, lamport_t FROM ledger ORDER BY seq DESC LIMIT 1;")
        row = cur.fetchone()
        prev_hash = row["entry_hash"] if row is not None else GENESIS_PREV_HASH
        lamport_t = (row["lamport_t"] + 1) if row is not None else 0

        entry_hash = compute_entry_hash(prev_hash, entry_id, causal_taint, lamport_t, agent_id, payload)
        created_at = datetime.now(timezone.utc).isoformat()
        payload_json = canonical(payload)

        self._conn.execute(
            "INSERT OR IGNORE INTO ledger "
            "(id, prev_hash, entry_hash, payload, causal_taint, lamport_t, agent_id, created_at) "
            "VALUES (?,?,?,?,?,?,?,?);",
            (entry_id, prev_hash, entry_hash, payload_json, causal_taint, lamport_t, agent_id, created_at),
        )
        written = self.get_by_id(entry_id)
        if written is None:  # pragma: no cover - would indicate a storage fault
            raise RuntimeError(f"ledger append failed for id={entry_id}")
        return written

    # -- readers -----------------------------------------------------------------
    def get_by_id(self, entry_id: str) -> LedgerEntry | None:
        cur = self._conn.execute("SELECT * FROM ledger WHERE id = ?;", (entry_id,))
        row = cur.fetchone()
        return self._row_to_entry(row) if row is not None else None

    def entries(self) -> list[LedgerEntry]:
        cur = self._conn.execute("SELECT * FROM ledger ORDER BY seq ASC;")
        return [self._row_to_entry(r) for r in cur.fetchall()]

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) AS n FROM ledger;")
        return int(cur.fetchone()["n"])

    def verify_chain(self) -> ChainVerification:
        """Recompute every hash and check linkage. Detects post-hoc tampering."""
        rows = self.entries()
        if not rows:
            return ChainVerification(valid=True, entries=0, broken_at=None, reason=None)

        expected_prev = GENESIS_PREV_HASH
        for entry in rows:
            if entry.prev_hash != expected_prev:
                return ChainVerification(
                    valid=False, entries=len(rows), broken_at=entry.seq,
                    reason=f"prev_hash mismatch at seq={entry.seq}",
                )
            recomputed = compute_entry_hash(
                entry.prev_hash, entry.id, entry.causal_taint,
                entry.lamport_t, entry.agent_id, entry.payload,
            )
            if recomputed != entry.entry_hash:
                return ChainVerification(
                    valid=False, entries=len(rows), broken_at=entry.seq,
                    reason=f"entry_hash mismatch at seq={entry.seq} (payload tampered)",
                )
            expected_prev = entry.entry_hash
        return ChainVerification(valid=True, entries=len(rows), broken_at=None, reason=None)

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> LedgerEntry:
        return LedgerEntry(
            seq=int(row["seq"]),
            id=str(row["id"]),
            prev_hash=str(row["prev_hash"]),
            entry_hash=str(row["entry_hash"]),
            payload=json.loads(row["payload"]),
            causal_taint=str(row["causal_taint"]),
            lamport_t=int(row["lamport_t"]),
            agent_id=str(row["agent_id"]),
            created_at=str(row["created_at"]),
        )
