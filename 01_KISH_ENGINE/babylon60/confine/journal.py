"""Append-only, hash-chained journal for confinement sessions.

Each event digest is BLAKE3 over a domain tag and the strict canonical JSON of
``{kind, logical_tick, prev, body}``. Wall-clock time is stored as audit
metadata only and never enters a digest (INV_C5_CANONICAL_LOGICAL_TICK).

SQLite triggers stop accidental updates and deletes; they do not protect the
file against its owner, a rollback of the whole file or truncation of the last
events. Publishing the head digest outside the machine is what makes such a
truncation detectable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any

from blake3 import blake3

DOMAIN = b"BABYLON60-CONFINE-JOURNAL/v1\x00"
GENESIS = "0" * 64
MAX_CANONICAL_BYTES = 1024 * 1024


class JournalError(ValueError):
    """The journal is unusable, or a value cannot be recorded canonically."""


def canonical(value: object, limit: int = MAX_CANONICAL_BYTES) -> bytes:
    """Strict JSON: string keys only, finite numbers, no custom objects."""

    def validate(item: object) -> None:
        if item is None or type(item) in (str, int, bool):
            return
        if type(item) is float and math.isfinite(item):
            return
        if type(item) is list:
            for child in item:
                validate(child)
            return
        if type(item) is dict and all(type(key) is str for key in item):
            for child in item.values():
                validate(child)
            return
        raise JournalError(f"Not canonical JSON: {type(item).__name__}")

    validate(value)
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    if len(data) > limit:
        raise JournalError(f"Canonical payload exceeds {limit} bytes")
    return data


def digest(value: object, domain: bytes = DOMAIN) -> str:
    return blake3(domain + canonical(value)).hexdigest()


@dataclass(frozen=True)
class Entry:
    seq: int
    logical_tick: int
    kind: str
    body: dict[str, Any]
    prev: str
    digest: str
    recorded_at: str


@dataclass(frozen=True)
class Verification:
    ok: bool
    events: int
    head: str
    first_invalid_seq: int | None = None
    reason: str = ""


class ConfineJournal:
    """Dedicated SQLite WAL database with ``synchronous=FULL``."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._conn = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        try:
            if self._conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise JournalError("A file-backed WAL database is required")
            self._conn.execute("PRAGMA synchronous=FULL")
            if self._conn.execute("PRAGMA synchronous").fetchone()[0] != 2:
                raise JournalError("Journal requires synchronous=FULL")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "CREATE TABLE IF NOT EXISTS confine_events ("
                    "seq INTEGER PRIMARY KEY, logical_tick INTEGER NOT NULL UNIQUE, kind TEXT NOT NULL, "
                    "body TEXT NOT NULL, prev TEXT NOT NULL, digest TEXT NOT NULL UNIQUE, recorded_at TEXT NOT NULL)"
                )
                for operation in ("UPDATE", "DELETE"):
                    self._conn.execute(
                        f"CREATE TRIGGER IF NOT EXISTS confine_events_no_{operation.lower()} "
                        f"BEFORE {operation} ON confine_events "
                        "BEGIN SELECT RAISE(ABORT, 'confine journal is append-only'); END"
                    )
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        except BaseException:
            self._conn.close()
            raise

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> ConfineJournal:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def append(self, kind: str, body: dict[str, Any]) -> Entry:
        return self.append_many([(kind, body)])[0]

    def append_many(self, events: Sequence[tuple[str, dict[str, Any]]]) -> list[Entry]:
        """Append chained events in one transaction: one durable sync per batch, not per event."""
        prepared: list[tuple[str, dict[str, Any], str]] = []
        for kind, body in events:
            if not isinstance(kind, str) or not kind.strip():
                raise JournalError("Event kind must be nonempty text")
            prepared.append((kind, body, canonical(body).decode()))
        if not prepared:
            return []
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                "SELECT logical_tick, digest FROM confine_events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            tick = row[0] if row else 0
            prev = row[1] if row else GENESIS
            recorded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            entries: list[Entry] = []
            for kind, body, body_text in prepared:
                tick += 1
                event_digest = digest({"kind": kind, "logical_tick": tick, "prev": prev, "body": body})
                cursor = self._conn.execute(
                    "INSERT INTO confine_events (logical_tick, kind, body, prev, digest, recorded_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (tick, kind, body_text, prev, event_digest, recorded_at),
                )
                seq = cursor.lastrowid
                assert seq is not None
                entries.append(Entry(seq, tick, kind, json.loads(body_text), prev, event_digest, recorded_at))
                prev = event_digest
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        return entries

    def head(self) -> tuple[int, str]:
        row = self._conn.execute("SELECT seq, digest FROM confine_events ORDER BY seq DESC LIMIT 1").fetchone()
        return (row[0], row[1]) if row else (0, GENESIS)

    def entries(self, limit: int | None = None) -> list[Entry]:
        columns = "seq, logical_tick, kind, body, prev, digest, recorded_at"
        if limit is None:
            rows = self._conn.execute(f"SELECT {columns} FROM confine_events ORDER BY seq").fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT {columns} FROM confine_events ORDER BY seq DESC LIMIT ?", (max(limit, 0),)
            ).fetchall()[::-1]
        return [Entry(r[0], r[1], r[2], json.loads(r[3]), r[4], r[5], r[6]) for r in rows]

    def verify(self) -> Verification:
        prev, tick, count = GENESIS, 0, 0
        for seq, logical_tick, kind, body_text, stored_prev, stored_digest in self._conn.execute(
            "SELECT seq, logical_tick, kind, body, prev, digest FROM confine_events ORDER BY seq"
        ):
            count += 1
            try:
                body = json.loads(body_text)
                expected = digest({"kind": kind, "logical_tick": logical_tick, "prev": stored_prev, "body": body})
            except (ValueError, JournalError) as exc:
                return Verification(False, count, prev, seq, f"unreadable body: {exc}")
            if stored_prev != prev:
                return Verification(False, count, prev, seq, "broken link to previous event")
            if logical_tick != tick + 1:
                return Verification(False, count, prev, seq, "non-contiguous logical tick")
            if expected != stored_digest:
                return Verification(False, count, prev, seq, "digest does not match body")
            prev, tick = stored_digest, logical_tick
        return Verification(True, count, prev)
