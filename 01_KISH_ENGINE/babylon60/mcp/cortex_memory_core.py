"""CORTEX Memory core: event semantics, projector and replay over CortexPersistLedger.

The ledger (``babylon60.bft.cortex_persist_ledger``) is the only source of
truth. This module adds no table, no second hash chain and no cache: every
view is a pure projection of ledger rows ``seq <= snapshot_seq``.

Semantics (spec: docs/01_spec/spec_cortex_memory_mcp.md):
  - ``memory.append``     new item; optional structured key + asserted validity.
  - ``memory.supersede``  new item that replaces an active item.
  - ``memory.forget``     logical exclusion of an item from views computed at
                          snapshots after the forget event. Ledger bytes stay.
                          This is NOT cryptographic erasure.
  - ``memory.read_receipt`` record of the view prepared for delivery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import blake3
from babylon60.bft.cortex_crypto_kernel import ZERO_HASH_256, _canonical_json, verify_row_invariants
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger

PROJECTOR_V1 = "cortex-memory-projector/1"
PROJECTOR_V2 = "cortex-memory-projector/2"
PROJECTOR_VERSION = PROJECTOR_V2
SUPPORTED_VERSIONS = {PROJECTOR_V1, PROJECTOR_V2}
WRITE_TYPES = ("memory.append", "memory.supersede", "memory.forget")
RECEIPT_TYPE = "memory.read_receipt"
ORDERING = "recorded_seq_asc"


def canonical_version(version: str | int | None) -> str:
    s = str(version) if version is not None else ""
    if s in ("1", PROJECTOR_V1):
        return PROJECTOR_V1
    if s in ("2", PROJECTOR_V2):
        return PROJECTOR_V2
    raise ValueError(f"unknown projector version: {version}")


def digest(obj: object, version: str | int = PROJECTOR_VERSION) -> str:
    v = canonical_version(version)
    canon = _canonical_json(obj).encode("utf-8")
    if v == PROJECTOR_V1:
        return hashlib.sha3_256(canon).hexdigest()
    return blake3.blake3(canon).hexdigest()


def project_domain(project: str) -> str:
    return f"memory:{project}"


@dataclass
class Item:
    memory_id: str
    value: str
    entity: str | None
    attribute: str | None
    valid_from: str | None
    valid_to: str | None
    recorded_seq: int
    actor: str
    binding_id: str
    entry_hash: str
    supersedes: str | None = None
    superseded_by: str | None = None
    forgotten_at_seq: int | None = None

    def public(self) -> dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "value": self.value,
            "key": {"entity": self.entity, "attribute": self.attribute} if self.entity else None,
            "validity": {"from": self.valid_from, "to": self.valid_to, "asserted_by": "writer"},
            "supersedes": self.supersedes,
            "provenance": {
                "actor": self.actor,
                "binding_id": self.binding_id,
                "recorded_seq": self.recorded_seq,
                "entry_hash": self.entry_hash,
                # Content is data written by an agent; it never carries authority.
                "trust": "untrusted_data",
            },
        }


@dataclass
class Projection:
    items: dict[str, Item] = field(default_factory=dict)
    head_seq: int = 0
    head_hash: str = ""

    def active(self) -> list[Item]:
        out = [i for i in self.items.values() if i.superseded_by is None and i.forgotten_at_seq is None]
        return sorted(out, key=lambda i: i.recorded_seq)


def load_rows(
    conn: sqlite3.Connection, project: str, snapshot_seq: int | None
) -> tuple[list[tuple[int, str, str, str, str, str, str]], int, str]:
    """Rows of one project up to the snapshot, read inside the caller's transaction."""
    head = conn.execute("SELECT COALESCE(MAX(seq),0) FROM cortex_ledger").fetchone()[0]
    snap = head if snapshot_seq is None else min(snapshot_seq, head)
    head_hash_row = conn.execute("SELECT entry_hash FROM cortex_ledger WHERE seq=?", (snap,)).fetchone()
    rows = conn.execute(
        "SELECT seq, event_id, event_type, payload_json, agent_id, cortex_taint, entry_hash "
        "FROM cortex_ledger WHERE domain=? AND seq<=? AND event_type IN (?,?,?) ORDER BY seq ASC",
        (project_domain(project), snap, *WRITE_TYPES),
    ).fetchall()
    return rows, snap, head_hash_row[0] if head_hash_row else ""


def project(rows: list[tuple[int, str, str, str, str, str, str]], snap: int, head_hash: str) -> Projection:
    p = Projection(head_seq=snap, head_hash=head_hash)
    for seq, event_id, event_type, payload_json, actor, binding_id, entry_hash in rows:
        body = json.loads(payload_json)
        op = body["op"]
        if event_type in ("memory.append", "memory.supersede"):
            item = Item(
                memory_id=event_id,
                value=op["value"],
                entity=op.get("entity"),
                attribute=op.get("attribute"),
                valid_from=op.get("valid_from"),
                valid_to=op.get("valid_to"),
                recorded_seq=seq,
                actor=actor,
                binding_id=binding_id,
                entry_hash=entry_hash,
            )
            if event_type == "memory.supersede":
                target = p.items[op["target"]]
                target.superseded_by = event_id
                item.supersedes = target.memory_id
            p.items[event_id] = item
        elif event_type == "memory.forget":
            p.items[op["target"]].forgotten_at_seq = seq
    return p


def _overlap(a: Item, b: Item) -> bool:
    # Half-open [from, to); None means unbounded. ISO-8601 UTC strings compare lexicographically.
    a_from, b_from = a.valid_from or "", b.valid_from or ""
    a_to, b_to = a.valid_to or "\uffff", b.valid_to or "\uffff"
    return a_from < b_to and b_from < a_to


def conflicts(items: list[Item]) -> list[dict[str, object]]:
    """Structured contradictions only: same (entity, attribute), different value, overlapping validity."""
    out: list[dict[str, object]] = []
    keyed = [i for i in items if i.entity and i.attribute]
    for x, a in enumerate(keyed):
        for b in keyed[x + 1 :]:
            if (a.entity, a.attribute) == (b.entity, b.attribute) and a.value != b.value and _overlap(a, b):
                out.append(
                    {"key": {"entity": a.entity, "attribute": a.attribute}, "memory_ids": [a.memory_id, b.memory_id]}
                )
    return out


MAX_PAGE = 100
DEFAULT_PAGE = 20


def normalize_query(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and canonicalise a read query. ``None`` on an optional field means absent.

    Raises ``ValueError`` on any type or range violation; never coerces types.
    """
    text, entity, limit = raw.get("text"), raw.get("entity"), raw.get("limit")
    if text is not None and not isinstance(text, str):
        raise ValueError("text must be a string or null")
    if entity is not None and not isinstance(entity, str):
        raise ValueError("entity must be a string or null")
    if limit is None:
        limit = DEFAULT_PAGE
    elif isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_PAGE:
        raise ValueError(f"limit must be an integer in 1..{MAX_PAGE} or null")
    return {"text": text or "", "entity": entity or None, "limit": limit}


def query_view(p: Projection, query: dict[str, Any]) -> dict[str, object]:
    """Paged, filtered view for delivery. The page limit never affects state integrity."""
    q = normalize_query(query)
    text, entity, limit = q["text"].lower(), q["entity"], q["limit"]
    hits = [
        i
        for i in p.active()
        if (not entity or i.entity == entity)
        and (
            not text
            or text in i.value.lower()
            or text in (i.entity or "").lower()
            or text in (i.attribute or "").lower()
        )
    ][:limit]
    return {"items": [i.public() for i in hits], "conflicts": conflicts(hits)}


def view_digest(view: dict[str, object], version: str | int = PROJECTOR_VERSION) -> str:
    return digest(view, version=version)


def state_digest(p: Projection, version: str | int = PROJECTOR_VERSION) -> str:
    """Digest of the COMPLETE projected state at ``p.head_seq``: every item, active or not,
    with its supersede/forget status. Independent of any page limit or query."""
    v = canonical_version(version)
    items = sorted(p.items.values(), key=lambda i: i.recorded_seq)
    return digest(
        {
            "projector": v,
            "items": [
                {**i.public(), "superseded_by": i.superseded_by, "forgotten_at_seq": i.forgotten_at_seq} for i in items
            ],
        },
        version=v,
    )


def head_projection(conn: sqlite3.Connection, project_name: str) -> Projection:
    rows, snap, head_hash = load_rows(conn, project_name, None)
    return project(rows, snap, head_hash)


# --------------------------------------------------------------------------- replay


EXPECTED_COLUMNS = frozenset(
    {
        "seq",
        "event_id",
        "event_type",
        "payload_json",
        "cortex_taint",
        "agent_id",
        "domain",
        "lamport_t",
        "prev_hash",
        "entry_hash",
        "timestamp",
        "hash_version",
    }
)


class AuditError(Exception):
    """The audit target is not an existing CORTEX ledger; no verdict is produced."""


def _file_state(ledger_path: Path) -> tuple[object, ...]:
    st = ledger_path.stat()
    wal = ledger_path.with_name(ledger_path.name + "-wal")
    return (st.st_ino, st.st_size, st.st_mtime_ns, wal.exists())


def open_ledger_readonly(
    ledger_path: Path, *, static_copy: bool = False
) -> tuple[sqlite3.Connection, tuple[object, ...] | None]:
    """Open an EXISTING ledger read-only inside ONE read transaction.

    Never creates, initialises or migrates the database and never writes events,
    schema or data. Policy: a missing path, a non-file or a database without the
    expected ``cortex_ledger`` schema is an AuditError (no verdict). An existing
    ledger with the expected schema and zero rows is a valid, empty ledger.

    Default (ledger potentially live): ``mode=ro`` + ``BEGIN`` + a first read that
    pins the WAL read snapshot; every later query of the audit reads that snapshot
    until the caller ends the transaction. Committed frames still only in ``-wal``
    are visible; concurrent writers are not blocked. SQLite may create or update the
    operational ``-wal``/``-shm`` sidecars (https://www.sqlite.org/wal.html#read_only_databases);
    the auditor itself writes nothing to the database. The absence of ``-wal`` at
    open time is NOT treated as evidence that the ledger is static.

    ``static_copy=True`` (explicit opt-in, never automatic): ``immutable=1`` per
    https://www.sqlite.org/uri.html#uriimmutable. Only valid for a copy the caller
    guarantees will not change; refused if a ``-wal`` exists (immutable would
    ignore committed WAL frames). A file-state tripwire is returned so the caller
    can reject the audit if the file changed anyway.
    """
    if not ledger_path.is_file():
        raise AuditError(f"ledger not found: {ledger_path}")
    guard = None
    flags = "mode=ro"
    if static_copy:
        if ledger_path.with_name(ledger_path.name + "-wal").exists():
            raise AuditError(
                "static-copy audit refused: -wal present (checkpoint the copy or use the default live mode)"
            )
        guard = _file_state(ledger_path)
        flags = "mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(f"{ledger_path.resolve().as_uri()}?{flags}", uri=True, isolation_level=None)
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()  # pins the read snapshot
        cols = {row[1] for row in conn.execute("PRAGMA table_info(cortex_ledger)")}
    except sqlite3.DatabaseError as exc:
        raise AuditError(f"not a readable SQLite ledger: {exc}") from exc
    if not EXPECTED_COLUMNS <= cols:
        conn.close()
        raise AuditError(f"unexpected schema: missing {sorted(EXPECTED_COLUMNS - cols)}")
    return conn, guard


def verify_chain_readonly(conn: sqlite3.Connection) -> tuple[bool, int]:
    """Re-verify the SHA3-256 chain with the canonical kernel check (verify_row_invariants),
    on an existing read-only connection. Same rule as CortexPersistLedger.verify_integrity,
    without that constructor's directory creation, table initialisation or migration."""
    prev_hash, last_lamport, expected_seq = ZERO_HASH_256, 0, 1
    cur = conn.execute(
        "SELECT seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, lamport_t, "
        "prev_hash, entry_hash, timestamp, hash_version FROM cortex_ledger ORDER BY seq ASC"
    )
    while rows := cur.fetchmany(1000):
        for (
            seq,
            event_id,
            event_type,
            payload_json,
            taint,
            agent_id,
            domain,
            lamport_t,
            row_prev,
            entry_hash,
            timestamp,
            hash_version,
        ) in rows:
            ok, _err = verify_row_invariants(
                seq=seq,
                event_id=event_id,
                event_type=event_type,
                payload_json=payload_json,
                cortex_taint=taint,
                agent_id=agent_id,
                domain=domain,
                lamport_t=lamport_t,
                prev_hash=row_prev,
                entry_hash=entry_hash,
                timestamp=timestamp,
                expected_seq=expected_seq,
                last_lamport=last_lamport,
                expected_prev_hash=prev_hash,
                hash_version=hash_version,
            )
            if not ok:
                return False, expected_seq - 1
            prev_hash, last_lamport, expected_seq = entry_hash, lamport_t, expected_seq + 1
    return True, expected_seq - 1


def replay(ledger_path: Path, *, static_copy: bool = False) -> dict[str, object]:
    """Replay of memory events and views (not of authorisation decisions).

    Verifies: (1) the ledger hash chain, relative to whichever head the auditor
    already trusts; (2) every ``memory.read_receipt`` by recomputing its view and
    full-state digest at the recorded snapshot; (3) the full-state digest of each
    project's head.

    Does NOT verify: ``memory.decision`` events (only counted), the historical
    binding signature, grants or policy_version (``cortex_taint`` holds a binding
    hash, not the signed envelope), the broker library identity, external time,
    or what an LLM reasoned with a delivered view.

    Opens the ledger read-only and never creates, initialises or migrates it. All
    checks (schema, chain, receipts, head projections) read ONE snapshot: a single
    read transaction (default, safe for a live ledger), or ``static_copy=True``
    (immutable open; caller guarantees a static copy; tripwire on file state).
    Raises AuditError if the path is not an existing CORTEX ledger.
    """
    conn, guard = open_ledger_readonly(ledger_path, static_copy=static_copy)
    try:
        assert conn.in_transaction  # whole audit reads one snapshot
        snap_row = conn.execute(
            "SELECT COALESCE(MAX(seq),0), (SELECT entry_hash FROM cortex_ledger ORDER BY seq DESC LIMIT 1) FROM cortex_ledger"
        ).fetchone()
        chain_ok, events = verify_chain_readonly(conn)
        receipts = conn.execute(
            "SELECT seq, event_id, domain, payload_json FROM cortex_ledger WHERE event_type=? ORDER BY seq",
            (RECEIPT_TYPE,),
        ).fetchall()
        checked, mismatches = 0, []
        for seq, event_id, domain, payload_json in receipts:
            r = json.loads(payload_json)
            proj_name = domain.removeprefix("memory:")
            rows, snap, head_hash = load_rows(conn, proj_name, r["snapshot_seq"])
            proj = project(rows, snap, head_hash)
            raw_ver = r.get("projector_version")
            try:
                v = canonical_version(raw_ver)
            except ValueError:
                checked += 1
                mismatches.append(event_id)
                continue
            view = query_view(proj, r["query"])
            ok = (
                view_digest(view, version=v) == r["view_digest"]
                and state_digest(proj, version=v) == r.get("snapshot_state_digest")
                and head_hash == r["snapshot_head_hash"]
                and r["projector_version"] in SUPPORTED_VERSIONS
            )
            checked += 1
            if not ok:
                mismatches.append(event_id)
        projects = sorted(
            d.removeprefix("memory:")
            for (d,) in conn.execute("SELECT DISTINCT domain FROM cortex_ledger WHERE domain LIKE 'memory:%'")
        )
        heads = {name: state_digest(head_projection(conn, name), version=PROJECTOR_VERSION) for name in projects}
        decisions = conn.execute("SELECT COUNT(*) FROM cortex_ledger WHERE event_type='memory.decision'").fetchone()[0]
        end_row = conn.execute(
            "SELECT COALESCE(MAX(seq),0), (SELECT entry_hash FROM cortex_ledger ORDER BY seq DESC LIMIT 1) FROM cortex_ledger"
        ).fetchone()
        if end_row != snap_row or (chain_ok and events != snap_row[0]):
            raise AuditError("audit snapshot not stable (internal consistency check failed)")
        conn.rollback()
    finally:
        conn.close()
    if guard is not None and _file_state(ledger_path) != guard:
        raise AuditError("static-copy guarantee violated: file changed during audit; result discarded")
    return {
        "scope": "memory_events_and_views",
        "audit_snapshot": {
            "seq": snap_row[0],
            "head_hash": snap_row[1] or "",
            "mode": "static_copy_immutable" if guard else "read_txn",
        },
        "chain_ok": chain_ok,
        "events_verified": events,
        "receipts_checked": checked,
        "receipt_mismatches": mismatches,
        "head_state_digests": heads,
        "decisions_recorded_not_replayed": decisions,
        "projector_version": PROJECTOR_VERSION,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic replay of a CORTEX memory ledger")
    ap.add_argument("ledger", type=Path)
    ap.add_argument(
        "--static-copy",
        action="store_true",
        help="immutable=1 open; ONLY for a copy guaranteed not to change (refused if -wal exists)",
    )
    args = ap.parse_args(argv)
    try:
        result = replay(args.ledger, static_copy=args.static_copy)
    except AuditError as exc:
        print(f"audit error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["chain_ok"] and not result["receipt_mismatches"] else 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "AuditError",
    "CortexEvent",
    "CortexPersistLedger",
    "open_ledger_readonly",
    "verify_chain_readonly",
    "PROJECTOR_V1",
    "PROJECTOR_V2",
    "PROJECTOR_VERSION",
    "SUPPORTED_VERSIONS",
    "canonical_version",
    "digest",
    "head_projection",
    "load_rows",
    "normalize_query",
    "project",
    "query_view",
    "replay",
    "state_digest",
    "view_digest",
]
