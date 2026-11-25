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
from typing import Any, TypedDict

import blake3
from babylon60.bft.cortex_crypto_kernel import ZERO_HASH_256, _canonical_json, verify_row_invariants
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.bft.integrity import LedgerCheckpoint
from babylon60.mcp import cortex_retrieval_v3 as retrieval_v3

PROJECTOR_V1 = "cortex-memory-projector/1"
PROJECTOR_V2 = "cortex-memory-projector/2"
PROJECTOR_V3 = "cortex-memory-projector/3"
PROJECTOR_VERSION = PROJECTOR_V3
SUPPORTED_VERSIONS = {PROJECTOR_V1, PROJECTOR_V2, PROJECTOR_V3}
WRITE_TYPES = ("memory.append", "memory.supersede", "memory.forget")
RECEIPT_TYPE = "memory.read_receipt"
ORDERING = "recorded_seq_asc"


def canonical_version(version: str | int | None) -> str:
    s = str(version) if version is not None else ""
    if s in ("1", PROJECTOR_V1):
        return PROJECTOR_V1
    if s in ("2", PROJECTOR_V2):
        return PROJECTOR_V2
    if s in ("3", PROJECTOR_V3):
        return PROJECTOR_V3
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
    depends_on: tuple[str, ...] = ()
    pending_revalidation: bool = False

    @property
    def status(self) -> str:
        if self.forgotten_at_seq is not None:
            return "FORGOTTEN"
        if self.superseded_by is not None:
            return "SUPERSEDED"
        return "PENDING_REVALIDATION" if self.pending_revalidation else "ACTIVE"

    def public(self, version: str | int = PROJECTOR_VERSION) -> dict[str, object]:
        out: dict[str, object] = {
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
        if canonical_version(version) == PROJECTOR_V3:
            out.update(
                depends_on=list(self.depends_on),
                status=self.status,
                superseded_by=self.superseded_by,
                forgotten_at_seq=self.forgotten_at_seq,
            )
        return out


@dataclass
class Projection:
    items: dict[str, Item] = field(default_factory=dict)
    head_seq: int = 0
    head_hash: str = ""

    def active(self, version: str | int = PROJECTOR_VERSION) -> list[Item]:
        out = [i for i in self.items.values() if i.superseded_by is None and i.forgotten_at_seq is None]
        if canonical_version(version) == PROJECTOR_V3:
            out = [i for i in out if not i.pending_revalidation]
        return sorted(out, key=lambda i: i.recorded_seq)


def load_rows(
    conn: sqlite3.Connection, project: str, snapshot_seq: int | None
) -> tuple[list[tuple[Any, ...]], int, str]:
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


def project(rows: list[tuple[Any, ...]], snap: int, head_hash: str) -> Projection:
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
                depends_on=tuple(op.get("depends_on", ())),
            )
            if event_type == "memory.supersede":
                target = p.items[op["target"]]
                target.superseded_by = event_id
                item.supersedes = target.memory_id
            p.items[event_id] = item
        elif event_type == "memory.forget":
            p.items[op["target"]].forgotten_at_seq = seq
    # Writes can depend only on existing active versions. Recorded order is thus
    # topological: one pass propagates invalidation without recursion or a cache.
    for item in p.items.values():
        item.pending_revalidation = any(
            (source := p.items.get(source_id)) is None
            or source.recorded_seq >= item.recorded_seq
            or source.status != "ACTIVE"
            for source_id in item.depends_on
        )
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


def _check_optional_int_range(raw: dict[str, Any], name: str, lo: int, hi: int) -> int | None:
    val = raw.get(name)
    if val is None:
        return None
    if isinstance(val, bool) or not isinstance(val, int) or not lo <= val <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi} or null")
    return val


def normalize_query(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and canonicalise a read query. ``None`` on an optional field means absent.

    Raises ``ValueError`` on any type or range violation; never coerces types.
    Preserves the exact 4-key dictionary for default literal/items queries so all
    historical receipts and callers remain byte-identical.
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
    view = raw.get("view")
    if view is None:
        view = "current"
    if view not in ("current", "history"):
        raise ValueError("view must be current or history")

    mode = raw.get("mode")
    if mode is not None and mode not in retrieval_v3.RETRIEVAL_MODES:
        raise ValueError(f"mode must be one of {retrieval_v3.RETRIEVAL_MODES} or null")
    packing = raw.get("packing")
    if packing is not None and packing not in retrieval_v3.PACKING_MODES:
        raise ValueError(f"packing must be one of {retrieval_v3.PACKING_MODES} or null")

    window = _check_optional_int_range(raw, "window", 0, 8)
    max_passages = _check_optional_int_range(raw, "max_passages", 1, 50)
    context_budget = _check_optional_int_range(raw, "context_budget", 64, 32768)
    center_budget = _check_optional_int_range(raw, "center_budget", 32, 4096)
    neighbor_budget = _check_optional_int_range(raw, "neighbor_budget", 16, 2048)

    semantic_order = raw.get("semantic_order")
    if semantic_order is not None:
        if (
            not isinstance(semantic_order, list)
            or any(not isinstance(x, str) or not x for x in semantic_order)
            or len(set(semantic_order)) != len(semantic_order)
        ):
            raise ValueError("semantic_order must be a list of unique non-empty memory_id strings")

    out: dict[str, Any] = {"text": text or "", "entity": entity or None, "limit": limit, "view": view}
    v3_active = (
        (mode is not None and mode != "literal")
        or (packing is not None and packing != "items")
        or any(
            x is not None
            for x in (window, max_passages, context_budget, center_budget, neighbor_budget, semantic_order)
        )
    )
    if not v3_active:
        return out

    resolved_packing = packing if packing is not None else "items"
    if mode is None:
        resolved_mode = "fts5" if resolved_packing == "turn_window" and (text or "").strip() else "literal"
    else:
        resolved_mode = mode
    out["mode"] = resolved_mode
    out["packing"] = resolved_packing
    if resolved_packing == "turn_window" or any(
        x is not None for x in (window, max_passages, context_budget, center_budget, neighbor_budget)
    ):
        out["window"] = retrieval_v3.DEFAULT_WINDOW if window is None else window
        out["max_passages"] = retrieval_v3.DEFAULT_MAX_PASSAGES if max_passages is None else max_passages
        out["context_budget"] = retrieval_v3.DEFAULT_CONTEXT_BUDGET if context_budget is None else context_budget
        out["center_budget"] = retrieval_v3.DEFAULT_CENTER_BUDGET if center_budget is None else center_budget
        out["neighbor_budget"] = retrieval_v3.DEFAULT_NEIGHBOR_BUDGET if neighbor_budget is None else neighbor_budget
    if semantic_order is not None:
        out["semantic_order"] = list(semantic_order)
    return out


def _build_turn_records(items: list[Item]) -> list[retrieval_v3.TurnRecord]:
    return [
        retrieval_v3.TurnRecord(
            memory_id=i.memory_id,
            entry_hash=i.entry_hash,
            recorded_seq=i.recorded_seq,
            session_key=i.entity if i.entity is not None else "__default__",
            role=retrieval_v3.infer_speaker(i.attribute, i.value),
            text=i.value,
            valid_from=i.valid_from,
            item_ref=i,
        )
        for i in items
    ]


def _ordered_turn_records_for_query(
    p: Projection,
    q: dict[str, Any],
    version: str,
) -> tuple[list[Item], list[retrieval_v3.SessionGroup], list[retrieval_v3.TurnRef], list[retrieval_v3.TurnRecord]]:
    candidates = (
        sorted(p.items.values(), key=lambda i: i.recorded_seq)
        if version == PROJECTOR_V3 and q["view"] == "history"
        else p.active(version=version)
    )
    if q["entity"]:
        candidates = [i for i in candidates if i.entity == q["entity"]]
    raw_records = _build_turn_records(candidates)
    if q.get("packing", "items") == "turn_window":
        sessions, turn_refs = retrieval_v3.build_sessions_and_turn_refs(raw_records)
        ordered_records = [r.turn for r in turn_refs]
        return candidates, sessions, turn_refs, ordered_records
    return candidates, [], [], raw_records


def attach_semantic_order(
    p: Projection,
    query: dict[str, Any],
    embedder: retrieval_v3.Embedder,
    version: str | int = PROJECTOR_VERSION,
) -> dict[str, Any]:
    """Attach a deterministic ``semantic_order`` witness to ``query`` when using a custom embedder."""
    q = normalize_query(query)
    mode = q.get("mode", "literal")
    if mode not in ("hybrid", "void_hybrid") or not q["text"].strip():
        return q
    v = canonical_version(version)
    _, _, _, ordered_records = _ordered_turn_records_for_query(p, q, v)
    if not ordered_records:
        return q
    q_vec, d_vecs = retrieval_v3.encode_pair(q["text"], [tr.index_text for tr in ordered_records], embedder)
    if mode == "void_hybrid":
        sem_r = retrieval_v3.void_dense_rank_from_vecs(q_vec, d_vecs)
    else:
        sem_r = retrieval_v3.dense_rank_from_vecs(q_vec, d_vecs)
    return {**q, "semantic_order": [ordered_records[idx].memory_id for idx in sem_r]}


def query_view(
    p: Projection,
    query: dict[str, Any],
    version: str | int = PROJECTOR_VERSION,
    *,
    embedder: retrieval_v3.Embedder | None = None,
) -> dict[str, object]:
    """Paged, filtered or V3b hybrid/turn-window view for delivery. Never affects state integrity."""
    q = normalize_query(query)
    v = canonical_version(version)
    mode = q.get("mode", "literal")
    packing = q.get("packing", "items")

    if mode == "literal" and packing == "items":
        text, entity, limit = q["text"].lower(), q["entity"], q["limit"]
        candidates = (
            sorted(p.items.values(), key=lambda i: i.recorded_seq)
            if v == PROJECTOR_V3 and q["view"] == "history"
            else p.active(version=v)
        )
        hits = [
            i
            for i in candidates
            if (not entity or i.entity == entity)
            and (
                not text
                or text in i.value.lower()
                or text in (i.entity or "").lower()
                or text in (i.attribute or "").lower()
            )
        ][:limit]
        current_hits = [i for i in hits if i.status == "ACTIVE"] if v == PROJECTOR_V3 else hits
        return {"items": [i.public(version=v) for i in hits], "conflicts": conflicts(current_hits)}

    _, sessions, turn_refs, ordered_records = _ordered_turn_records_for_query(p, q, v)
    if not ordered_records:
        base_empty: dict[str, object] = {"items": [], "conflicts": []}
        if packing == "turn_window":
            base_empty["packed_context"] = {
                "mode": mode,
                "packing": "turn_window",
                "window": q.get("window", retrieval_v3.DEFAULT_WINDOW),
                "max_passages": q.get("max_passages", retrieval_v3.DEFAULT_MAX_PASSAGES),
                "context_budget": q.get("context_budget", retrieval_v3.DEFAULT_CONTEXT_BUDGET),
                "center_budget": q.get("center_budget", retrieval_v3.DEFAULT_CENTER_BUDGET),
                "neighbor_budget": q.get("neighbor_budget", retrieval_v3.DEFAULT_NEIGHBOR_BUDGET),
                "passage_count": 0,
                "session_count": 0,
                "selected_sessions": [],
                "est_units": 0,
                "truncated": False,
                "context_blake3": blake3.blake3(b"").hexdigest(),
                "context_text": "",
            }
        return base_empty

    q_text = q["text"]
    if mode == "literal":
        t_low = q_text.lower()
        matched = [
            idx
            for idx, tr in enumerate(ordered_records)
            if not t_low
            or t_low in tr.text.lower()
            or t_low in (tr.item_ref.entity or "").lower()
            or t_low in (tr.item_ref.attribute or "").lower()
        ]
        seen = set(matched)
        ranking = matched + [idx for idx in range(len(ordered_records)) if idx not in seen]
    elif not q_text.strip():
        ranking = list(range(len(ordered_records)))
    else:
        sem_ranking: list[int] | None = None
        if q.get("semantic_order") is not None:
            id_to_idx = {tr.memory_id: idx for idx, tr in enumerate(ordered_records)}
            sem_order: list[str] = q["semantic_order"]
            if len(sem_order) != len(ordered_records) or any(mid not in id_to_idx for mid in sem_order):
                raise ValueError("semantic_order does not match projected candidate items")
            sem_ranking = [id_to_idx[mid] for mid in sem_order]
        rmap = retrieval_v3.role_aware_c2_rankings(
            q_text,
            [tr.index_text for tr in ordered_records],
            embedder,
            roles=[tr.role for tr in ordered_records],
            bm25_corpus=[tr.fts_text for tr in ordered_records],
            semantic_ranking=sem_ranking,
            include_void=(mode == "void_hybrid"),
        )
        ranking = rmap[mode]

    if packing == "items":
        hits = [ordered_records[idx].item_ref for idx in ranking[: q["limit"]]]
        current_hits = [i for i in hits if i.status == "ACTIVE"] if v == PROJECTOR_V3 else hits
        return {"items": [i.public(version=v) for i in hits], "conflicts": conflicts(current_hits)}

    packed = retrieval_v3.select_turn_windows_for_budget(
        sessions,
        turn_refs,
        ranking,
        window=q["window"],
        max_passages=q["max_passages"],
        context_budget=q["context_budget"],
        center_budget=q["center_budget"],
        neighbor_budget=q["neighbor_budget"],
    )
    hits = [tr.item_ref for tr in packed.selected_turns]
    current_hits = [i for i in hits if i.status == "ACTIVE"] if v == PROJECTOR_V3 else hits
    return {
        "items": [i.public(version=v) for i in hits],
        "conflicts": conflicts(current_hits),
        "packed_context": {
            "mode": mode,
            "packing": "turn_window",
            "window": q["window"],
            "max_passages": q["max_passages"],
            "context_budget": q["context_budget"],
            "center_budget": q["center_budget"],
            "neighbor_budget": q["neighbor_budget"],
            "passage_count": packed.passage_count,
            "session_count": len(packed.selected_session_keys),
            "selected_sessions": list(packed.selected_session_keys),
            "est_units": packed.est_tokens,
            "truncated": packed.truncated,
            "context_blake3": packed.context_blake3,
            "context_text": packed.context_text,
        },
    }


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
                {**i.public(version=v), "superseded_by": i.superseded_by, "forgotten_at_seq": i.forgotten_at_seq}
                for i in items
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


def verify_chain_readonly(
    conn: sqlite3.Connection,
    *,
    expected_checkpoint: LedgerCheckpoint | None = None,
) -> tuple[bool, int]:
    """Re-verify the SHA3-256 chain with the canonical kernel check (verify_row_invariants),
    on an existing read-only connection. Same rule as CortexPersistLedger.verify_integrity,
    without that constructor's directory creation, table initialisation or migration.

    sqlite_sequence must match the verified tail. expected_checkpoint (count and
    head hash, kept outside SQLite) fails the check on mismatch. Without that
    pin, a full rewrite is undetectable.
    """
    if not conn.in_transaction:
        conn.execute("BEGIN")
    prev_hash, last_lamport, expected_seq = ZERO_HASH_256, 0, 1
    columns = {row[1] for row in conn.execute("PRAGMA table_info(cortex_ledger)")}
    observation_sql = "observation_hash" if "observation_hash" in columns else "NULL AS observation_hash"
    cur = conn.execute(
        "SELECT seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, lamport_t, "
        "prev_hash, entry_hash, timestamp, hash_version, "
        f"{observation_sql} FROM cortex_ledger ORDER BY seq ASC"
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
            observation_hash,
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
                observation_hash=observation_hash,
            )
            if not ok:
                return False, expected_seq - 1
            prev_hash, last_lamport, expected_seq = entry_hash, lamport_t, expected_seq + 1
    count = expected_seq - 1
    high_water = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='cortex_ledger'").fetchone()
    if (int(high_water[0]) if high_water and high_water[0] is not None else 0) != count:
        return False, count
    if expected_checkpoint is not None and (
        not isinstance(expected_checkpoint, LedgerCheckpoint)
        or type(expected_checkpoint.entries) is not int
        or expected_checkpoint.entries != count
        or expected_checkpoint.head_hash != prev_hash
    ):
        return False, count
    return True, count


class AuditSnapshot(TypedDict):
    seq: int
    head_hash: str
    mode: str


class ReplayReport(TypedDict):
    scope: str
    audit_snapshot: AuditSnapshot
    chain_ok: bool
    events_verified: int
    receipts_checked: int
    receipt_mismatches: list[str]
    head_state_digests: dict[str, str]
    decisions_recorded_not_replayed: int
    projector_version: str


def replay(ledger_path: Path, *, static_copy: bool = False) -> ReplayReport:
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
                view = query_view(proj, r["query"], version=v)
            except ValueError:
                checked += 1
                mismatches.append(event_id)
                continue
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
    "PROJECTOR_V3",
    "PROJECTOR_VERSION",
    "SUPPORTED_VERSIONS",
    "attach_semantic_order",
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
