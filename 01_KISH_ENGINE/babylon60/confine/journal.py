"""Append-only, hash-chained journal for confinement sessions.

Each event digest is BLAKE3 over a domain tag and the strict canonical JSON of
``{kind, logical_tick, prev, body}``. Wall-clock time is stored as audit
metadata only and never enters a digest (INV_C5_CANONICAL_LOGICAL_TICK).

``verify`` reports the first stored event that fails one of these checks:

* column types: ``seq`` and ``logical_tick`` are integers, ``kind`` is nonempty
  text, ``body`` is UTF-8 text, ``prev`` and ``digest`` are 64 lowercase hex digits;
* the stored body text is byte-identical to the canonical JSON that was digested,
  so duplicate keys, reordered keys, whitespace or escapes cannot show a reader of
  the raw text something other than what the digest covers;
* links: each ``prev`` is the digest of the event before it and ticks rise by
  exactly one, so inserting, removing or reordering an event anywhere but at the
  end breaks the chain;
* each digest matches its event.

``verify`` alone does not detect removal of the last events, a rollback of the
whole file or a file rewritten from scratch: a shorter chain is still a valid
chain, and the digests are not keyed, so whoever can write the file can build a
new valid one. ``recorded_at`` is outside every digest. SQLite triggers stop
accidental updates and deletes, not the file's owner.

Publishing the head digest outside the machine closes that gap. ``babylon60 log``
prints the head in full; ``verify(expect_head=...)`` and ``babylon60 log
--expect-head`` fail unless that head is still in the verified chain. The chain
then fixes every event up to the published head; later events may follow it and
are only as trustworthy as the file until the next head is published.
``babylon60 run`` creates the journal before it checks the policy, so a write
grant over the journal or any directory above it is refused even on first use.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, NoReturn

from blake3 import blake3

DOMAIN = b"BABYLON60-CONFINE-JOURNAL/v1\x00"
GENESIS = "0" * 64
MAX_CANONICAL_BYTES = 1024 * 1024
_HEX64 = re.compile(r"[0-9a-f]{64}")


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
    """``ok``: the chain is intact and, when a head was expected, that head is in it."""

    ok: bool
    events: int  # events read, including the first invalid one
    head: str  # digest of the last valid event (GENESIS when there is none)
    first_invalid_seq: int | None = None
    reason: str = ""
    chain_intact: bool = True
    expected_head: str | None = None
    expected_seq: int | None = None  # where the expected head was found (0: the genesis); None if absent
    events_after_expected: int | None = None  # valid events that follow the expected head


class _Invalid(Exception):
    """One stored event is unusable; the message is the verification reason."""


def _create_private(path: Path) -> None:
    """Create missing directories with mode 0700 and the database with 0600; existing modes are kept.

    SQLite gives the ``-wal`` and ``-shm`` files the mode of the database file.
    """
    missing: list[Path] = []
    directory = path.parent
    while not directory.is_dir() and directory != directory.parent:
        missing.append(directory)
        directory = directory.parent
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            if not directory.is_dir():
                raise
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600)
    except FileExistsError:
        return
    os.close(fd)


def _sql_text(value: object, sql_type: object, column: str) -> str:
    """Text read with ``text_factory=bytes``: invalid UTF-8 is a finding, not a crash."""
    if sql_type != b"text" or not isinstance(value, bytes):
        kind = sql_type.decode("ascii", "replace") if isinstance(sql_type, bytes) else type(value).__name__
        raise _Invalid(f"{column} is stored as {kind}, not text")
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        raise _Invalid(f"{column} is not valid UTF-8") from None


def _sql_integer(value: object, sql_type: object, column: str) -> int:
    if sql_type != b"integer" or type(value) is not int:
        kind = sql_type.decode("ascii", "replace") if isinstance(sql_type, bytes) else type(value).__name__
        raise _Invalid(f"{column} is stored as {kind}, not integer")
    return value


def _sql_digest(value: object, sql_type: object, column: str) -> str:
    text = _sql_text(value, sql_type, column)
    if not _HEX64.fullmatch(text):
        raise _Invalid(f"{column} is not 64 lowercase hex digits")
    return text


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _Invalid(f"body has duplicate key {key!r}")
        result[key] = value
    return result


def _reject_constant(name: str) -> NoReturn:
    raise _Invalid(f"body contains {name}, which is not JSON")


def _canonical_body(value: object, sql_type: object) -> dict[str, Any]:
    """Parse the stored body strictly and require the exact canonical bytes that were digested."""
    text = _sql_text(value, sql_type, "body")
    try:
        body = json.loads(text, object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
    except (ValueError, RecursionError) as exc:
        raise _Invalid(f"body is not valid JSON: {exc}") from None
    if type(body) is not dict:
        raise _Invalid("body is not a JSON object")
    try:
        expected = canonical(body)
    except (ValueError, RecursionError) as exc:
        raise _Invalid(f"body is not canonical JSON: {exc}") from None
    if expected != value:
        raise _Invalid("body text is not the canonical form that was digested (key order, spacing or escapes)")
    return body


class ConfineJournal:
    """Dedicated SQLite WAL database with ``synchronous=FULL``."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        try:
            _create_private(self.path)
            self._conn = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        except (OSError, sqlite3.Error) as exc:
            raise JournalError(f"Cannot open the journal at {self.path}: {exc}") from exc
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
        except BaseException as exc:
            self._conn.close()
            if isinstance(exc, sqlite3.Error):
                raise JournalError(f"Unusable journal at {self.path}: {exc}") from exc
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
            if type(body) is not dict:
                raise JournalError("Event body must be a JSON object")
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
        """Stored events for display, oldest first. Only ``verify`` decides whether they are intact."""
        columns = "seq, logical_tick, kind, body, prev, digest, recorded_at"
        try:
            if limit is None:
                rows = self._conn.execute(f"SELECT {columns} FROM confine_events ORDER BY seq").fetchall()
            else:
                rows = self._conn.execute(
                    f"SELECT {columns} FROM confine_events ORDER BY seq DESC LIMIT ?", (max(limit, 0),)
                ).fetchall()[::-1]
            return [Entry(r[0], r[1], r[2], json.loads(r[3]), r[4], r[5], r[6]) for r in rows]
        except (sqlite3.Error, ValueError, TypeError, RecursionError) as exc:
            raise JournalError(f"Unreadable journal entry: {exc}") from exc

    def verify(self, expect_head: str | None = None) -> Verification:
        """Check every stored event in order and stop at the first invalid one.

        ``expect_head`` is a head digest published earlier: the result is only ``ok``
        if it is in the verified chain. Events appended after it are allowed.
        Raises ``JournalError`` when SQLite cannot read the file at all.
        """
        if expect_head is not None and not _HEX64.fullmatch(expect_head):
            raise JournalError("The expected head must be 64 lowercase hex digits")
        found = expect_head == GENESIS  # every chain starts at the genesis
        expected_seq: int | None = 0 if found else None
        expected_position = 0
        prev, tick, valid = GENESIS, 0, 0
        broken: tuple[int | None, str] | None = None
        text_factory = self._conn.text_factory
        self._conn.text_factory = bytes  # text is decoded strictly in _sql_text
        try:
            cursor = self._conn.execute(
                "SELECT seq, typeof(seq), logical_tick, typeof(logical_tick), kind, typeof(kind), body, typeof(body), "
                "prev, typeof(prev), digest, typeof(digest) FROM confine_events ORDER BY seq"
            )
            try:
                for position, row in enumerate(cursor, start=1):
                    seq = row[0] if type(row[0]) is int else None
                    try:
                        _sql_integer(row[0], row[1], "seq")
                        logical_tick = _sql_integer(row[2], row[3], "logical_tick")
                        kind = _sql_text(row[4], row[5], "kind")
                        if not kind.strip():
                            raise _Invalid("kind is empty")
                        body = _canonical_body(row[6], row[7])
                        stored_prev = _sql_digest(row[8], row[9], "prev")
                        stored_digest = _sql_digest(row[10], row[11], "digest")
                        if stored_prev != prev:
                            raise _Invalid("broken link to previous event")
                        if logical_tick != tick + 1:
                            raise _Invalid("non-contiguous logical tick")
                        try:
                            recomputed = digest(
                                {"kind": kind, "logical_tick": logical_tick, "prev": stored_prev, "body": body}
                            )
                        except JournalError as exc:
                            raise _Invalid(f"event cannot be digested: {exc}") from None
                        if recomputed != stored_digest:
                            raise _Invalid("digest does not match body")
                    except _Invalid as exc:
                        reason = str(exc) if seq is not None else f"row {position}: {exc}"
                        broken = (seq, reason)
                        break
                    valid += 1
                    prev, tick = stored_digest, logical_tick
                    if not found and stored_digest == expect_head:
                        found, expected_seq, expected_position = True, seq, valid
            finally:
                cursor.close()
        except sqlite3.Error as exc:  # a damaged file, not a verdict about one event
            raise JournalError(f"Unreadable journal at {self.path}: {exc}") from exc
        finally:
            self._conn.text_factory = text_factory
        after = valid - expected_position if found else None
        if broken is not None:
            first_invalid, reason = broken
            intact, events = False, valid + 1
        elif expect_head is not None and not found:
            first_invalid, intact, events = None, True, valid
            reason = (
                "expected head not found: the journal was truncated, rolled back or replaced after it was "
                "published, or the head is from another journal"
            )
        else:
            first_invalid, reason, intact, events = None, "", True, valid
        return Verification(
            ok=intact and (expect_head is None or found),
            events=events,
            head=prev,
            first_invalid_seq=first_invalid,
            reason=reason,
            chain_intact=intact,
            expected_head=expect_head,
            expected_seq=expected_seq,
            events_after_expected=after,
        )
