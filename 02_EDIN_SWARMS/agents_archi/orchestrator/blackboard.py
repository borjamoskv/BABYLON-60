#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SOVEREIGN TYPED BLACKBOARD & DETERMINISTIC ARBITER | DOMAIN: agents.archi
# ============================================================================
"""
Sovereign Typed Blackboard (`BlackboardArbiter`) and Post-Mortem Epistemic
Garbage Collector (`ColdPathCurator`).

Replaces the O(N^2) NLP "agent forum" anti-pattern with a deterministic
Blackboard Architecture backed by SQLite WAL (`PRAGMA synchronous = FULL`):
  - Zero LLM moderator in the hot path (AX-0: Authority != Cognition).
  - Strict anti-cheap-talk bound (`MAX_CLAIM_CHARS = 280`).
  - Two-Man Rule (`verifier_agent_id != author_agent_id`) + SHA-256 `evidence_hash`
    required for any `OPEN -> VERIFIED | FALSIFIED` transition.
  - 100% deterministic `ColdPathCurator` post-mortem compaction (`VERIFIED | FALSIFIED -> COMPACTED`)
    with an optional on-demand synthesis hook.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..clients.openrouter import SensitivePathGuard
from .royal_rumble import CortexWalStore

MAX_CLAIM_CHARS: int = 280
_SHA256_HEX_RE: re.Pattern[str] = re.compile(r"^[0-9a-fA-F]{64}$")


class BlackboardTopic(str, Enum):
    """Canonical typed topics for inter-agent blackboard coordination."""

    HYPOTHESIS = "HYPOTHESIS"
    PATCH_PROPOSAL = "PATCH_PROPOSAL"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    INVARIANT_ALERT = "INVARIANT_ALERT"


class BlackboardStatus(str, Enum):
    """Finite state machine for blackboard tuples."""

    OPEN = "OPEN"
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    COMPACTED = "COMPACTED"


def compute_tuple_id(
    task_id: str,
    logical_tick: int,
    topic: str,
    target_path: str,
    claim: str,
) -> str:
    """
    Computes a deterministic causal SHA-256 identifier for a blackboard tuple
    (`INV_C5_CANONICAL_LOGICAL_TICK` — zero physical clock dependency).
    """
    raw = (f"task:{task_id}|tick:{logical_tick}|topic:{topic}|path:{target_path}|claim:{claim.strip()}").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class BlackboardTuple:
    """Immutable typed state artifact published on the blackboard."""

    tuple_id: str
    task_id: str
    logical_tick: int
    topic: str
    author_agent_id: str
    target_path: str
    claim: str
    payload: Dict[str, Any]
    status: str = BlackboardStatus.OPEN.value
    verifier_agent_id: str = ""
    evidence_hash: str = ""
    resolved_at_tick: int = 0


@dataclass(frozen=True)
class BlackboardAdmissionResult:
    """Deterministic admission verdict returned by `BlackboardArbiter.publish`."""

    admitted: bool
    reason: str
    tuple_id: str
    tuple_record: Optional[BlackboardTuple] = None


@dataclass(frozen=True)
class BlackboardDigest:
    """
    Post-mortem compacted knowledge artifact produced by `ColdPathCurator`.
    Preserves verified invariants and falsified dead-ends while purging raw tuple clutter.
    """

    task_id: str
    compacted_at_tick: int
    verified_claims: Tuple[str, ...]
    falsified_claims: Tuple[str, ...]
    compacted_tuple_ids: Tuple[str, ...]
    executive_summary: str

    def to_system_note(self) -> Dict[str, str]:
        """Formats the compacted digest as a constant-size system checkpoint note."""
        return {
            "role": "system",
            "content": (
                f"[BLACKBOARD-DIGEST tick={self.compacted_at_tick}] "
                f"verified={json.dumps(list(self.verified_claims))} | "
                f"falsified={json.dumps(list(self.falsified_claims))} | "
                f"summary={self.executive_summary}"
            ),
        }


class BlackboardArbiter:
    """
    Deterministic control-plane broker for the inter-agent blackboard.
    Enforces schema bounds, sensitive-path confinement, O(1) deduplication,
    and Two-Man Rule verification over `CortexWalStore` (`PRAGMA synchronous = FULL`).
    """

    def __init__(self, wal_store: CortexWalStore) -> None:
        self.wal = wal_store
        self._init_blackboard_schema()

    def _init_blackboard_schema(self) -> None:
        cur = self.wal._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS blackboard_tuples (
                tuple_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                logical_tick INTEGER NOT NULL,
                topic TEXT NOT NULL,
                author_agent_id TEXT NOT NULL,
                target_path TEXT NOT NULL,
                claim TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                verifier_agent_id TEXT NOT NULL DEFAULT '',
                evidence_hash TEXT NOT NULL DEFAULT '',
                resolved_at_tick INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        self.wal._conn.commit()

    def get_tuple(self, tuple_id: str) -> Optional[BlackboardTuple]:
        """Retrieves a single tuple by its deterministic SHA-256 `tuple_id`."""
        cur = self.wal._conn.cursor()
        row = cur.execute(
            "SELECT * FROM blackboard_tuples WHERE tuple_id = ?;",
            (tuple_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_tuple(row)

    def publish(
        self,
        *,
        task_id: str,
        logical_tick: int,
        topic: BlackboardTopic | str,
        author_agent_id: str,
        target_path: str,
        claim: str,
        payload: Optional[Dict[str, Any]] = None,
        author_model: str = "poolside/laguna-s-2.1:free",
        allow_sensitive_on_free: bool = False,
    ) -> BlackboardAdmissionResult:
        """
        Deterministically validates and publishes a typed tuple to the blackboard.
        Rejects empty claims, cheap-talk prose (>280 chars), invalid topics, and
        sensitive Ring-0/Lean4 leakage on `:free` models.
        """
        if logical_tick < 0:
            raise ValueError("logical_tick must be non-negative (INV_C5_CANONICAL_LOGICAL_TICK)")
        if not author_agent_id.strip():
            raise ValueError("author_agent_id must be non-empty")

        topic_str = topic.value if isinstance(topic, BlackboardTopic) else str(topic).strip().upper()
        valid_topics = {t.value for t in BlackboardTopic}
        if topic_str not in valid_topics:
            return BlackboardAdmissionResult(
                admitted=False,
                reason="DENY_INVALID_TOPIC",
                tuple_id="",
            )

        clean_claim = claim.strip()
        if not clean_claim:
            return BlackboardAdmissionResult(
                admitted=False,
                reason="DENY_EMPTY_CLAIM",
                tuple_id="",
            )
        if len(clean_claim) > MAX_CLAIM_CHARS:
            return BlackboardAdmissionResult(
                admitted=False,
                reason="DENY_CHEAP_TALK_LENGTH",
                tuple_id="",
            )

        safe_payload: Dict[str, Any] = dict(payload) if payload is not None else {}
        tuple_id = compute_tuple_id(
            task_id=task_id,
            logical_tick=logical_tick,
            topic=topic_str,
            target_path=target_path,
            claim=clean_claim,
        )

        # Sensitive path / Ring-0 guard on telemetry-collecting :free endpoints
        if not allow_sensitive_on_free and SensitivePathGuard.is_free_model(author_model):
            if SensitivePathGuard.is_sensitive(
                prompt=f"{clean_claim}\n{json.dumps(safe_payload, sort_keys=True)}",
                context_paths=[target_path],
            ):
                return BlackboardAdmissionResult(
                    admitted=False,
                    reason="DENY_SENSITIVE_PATH_ON_FREE_ENDPOINT",
                    tuple_id=tuple_id,
                )

        existing = self.get_tuple(tuple_id)
        if existing is not None:
            return BlackboardAdmissionResult(
                admitted=True,
                reason="IDEMPOTENT_DUPLICATE",
                tuple_id=tuple_id,
                tuple_record=existing,
            )

        cur = self.wal._conn.cursor()
        cur.execute(
            """
            INSERT INTO blackboard_tuples (
                tuple_id, task_id, logical_tick, topic, author_agent_id,
                target_path, claim, payload_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                tuple_id,
                task_id,
                logical_tick,
                topic_str,
                author_agent_id.strip(),
                target_path,
                clean_claim,
                json.dumps(safe_payload, sort_keys=True, separators=(",", ":")),
                BlackboardStatus.OPEN.value,
            ),
        )
        self.wal._conn.commit()

        record = self.get_tuple(tuple_id)
        return BlackboardAdmissionResult(
            admitted=True,
            reason="ADMITTED_OPEN",
            tuple_id=tuple_id,
            tuple_record=record,
        )

    def resolve(
        self,
        *,
        tuple_id: str,
        verifier_agent_id: str,
        new_status: BlackboardStatus | str,
        evidence_hash: str,
        logical_tick: int,
    ) -> BlackboardTuple:
        """
        Transitions an `OPEN` tuple to `VERIFIED` or `FALSIFIED`.
        Enforces:
          1. Two-Man Rule (`verifier_agent_id != author_agent_id`).
          2. 64-character hex SHA-256 `evidence_hash` (`INV_C5_EMPTY_TAUTOLOGY`).
          3. Monotonic causal `logical_tick >= tuple.logical_tick`.
        """
        existing = self.get_tuple(tuple_id)
        if existing is None:
            raise KeyError(f"Blackboard tuple not found: {tuple_id}")
        if existing.status != BlackboardStatus.OPEN.value:
            raise ValueError(f"Cannot resolve tuple in status '{existing.status}'; must be OPEN")

        clean_verifier = verifier_agent_id.strip()
        if not clean_verifier:
            raise ValueError("verifier_agent_id must be non-empty")
        if clean_verifier == existing.author_agent_id:
            raise ValueError("Two-Man Rule violation: author_agent_id cannot self-verify its own tuple")

        status_str = new_status.value if isinstance(new_status, BlackboardStatus) else str(new_status).strip().upper()
        if status_str not in {BlackboardStatus.VERIFIED.value, BlackboardStatus.FALSIFIED.value}:
            raise ValueError(f"Invalid resolution status '{status_str}'; expected VERIFIED or FALSIFIED")

        clean_hash = evidence_hash.strip().lower()
        if not _SHA256_HEX_RE.match(clean_hash):
            raise ValueError("Invalid evidence_hash: must be a 64-character hexadecimal SHA-256 digest")

        if logical_tick < existing.logical_tick:
            raise ValueError(f"Non-monotonic logical_tick: {logical_tick} < {existing.logical_tick}")

        cur = self.wal._conn.cursor()
        cur.execute(
            """
            UPDATE blackboard_tuples
            SET status = ?, verifier_agent_id = ?, evidence_hash = ?, resolved_at_tick = ?
            WHERE tuple_id = ?;
            """,
            (status_str, clean_verifier, clean_hash, logical_tick, tuple_id),
        )
        self.wal._conn.commit()

        updated = self.get_tuple(tuple_id)
        if updated is None:
            raise RuntimeError("Failed to reload resolved blackboard tuple")
        return updated

    def poll_subscription(
        self,
        task_id: str,
        *,
        topics: Optional[Sequence[BlackboardTopic | str]] = None,
        status: BlackboardStatus | str = BlackboardStatus.OPEN,
    ) -> List[BlackboardTuple]:
        """
        Event-driven topic filter: returns only tuples matching `task_id`, `status`,
        and optional `topics`, ordered by `logical_tick ASC`.
        """
        status_str = status.value if isinstance(status, BlackboardStatus) else str(status).strip().upper()
        cur = self.wal._conn.cursor()
        if topics:
            topic_list = [t.value if isinstance(t, BlackboardTopic) else str(t).strip().upper() for t in topics]
            placeholders = ",".join("?" for _ in topic_list)
            query = (
                f"SELECT * FROM blackboard_tuples "
                f"WHERE task_id = ? AND status = ? AND topic IN ({placeholders}) "
                f"ORDER BY logical_tick ASC, tuple_id ASC;"
            )
            rows = cur.execute(query, [task_id, status_str, *topic_list]).fetchall()
        else:
            rows = cur.execute(
                """
                SELECT * FROM blackboard_tuples
                WHERE task_id = ? AND status = ?
                ORDER BY logical_tick ASC, tuple_id ASC;
                """,
                (task_id, status_str),
            ).fetchall()

        return [self._row_to_tuple(r) for r in rows]

    @staticmethod
    def _row_to_tuple(row: Any) -> BlackboardTuple:
        return BlackboardTuple(
            tuple_id=str(row["tuple_id"]),
            task_id=str(row["task_id"]),
            logical_tick=int(row["logical_tick"]),
            topic=str(row["topic"]),
            author_agent_id=str(row["author_agent_id"]),
            target_path=str(row["target_path"]),
            claim=str(row["claim"]),
            payload=json.loads(str(row["payload_json"])),
            status=str(row["status"]),
            verifier_agent_id=str(row["verifier_agent_id"]),
            evidence_hash=str(row["evidence_hash"]),
            resolved_at_tick=int(row["resolved_at_tick"]),
        )


class ColdPathCurator:
    """
    Post-Mortem Epistemic Garbage Collector (Cold Path).
    Operates 100% deterministically by default (zero LLM token cost) to compact
    `VERIFIED` and `FALSIFIED` tuples into a constant-size `BlackboardDigest` and
    transition them to `COMPACTED`. Supports an optional `narrative_hook` on demand.
    """

    def __init__(self, arbiter: BlackboardArbiter) -> None:
        self.arbiter = arbiter

    def compact_resolved_tuples(
        self,
        task_id: str,
        *,
        logical_tick: int,
        narrative_hook: Optional[Callable[[Sequence[BlackboardTuple]], str]] = None,
    ) -> BlackboardDigest:
        """
        Collects all `VERIFIED` and `FALSIFIED` tuples for `task_id`, transitions them
        atomically to `COMPACTED`, and returns a deterministic `BlackboardDigest`.
        """
        verified = self.arbiter.poll_subscription(task_id, status=BlackboardStatus.VERIFIED)
        falsified = self.arbiter.poll_subscription(task_id, status=BlackboardStatus.FALSIFIED)
        all_resolved = [*verified, *falsified]

        verified_entries = tuple(
            f"[{t.topic}] {t.target_path}: {t.claim} (proof={t.evidence_hash[:12]})" for t in verified
        )
        falsified_entries = tuple(
            f"[{t.topic}] {t.target_path}: {t.claim} (refuted={t.evidence_hash[:12]})" for t in falsified
        )
        compacted_ids = tuple(t.tuple_id for t in all_resolved)

        if compacted_ids:
            placeholders = ",".join("?" for _ in compacted_ids)
            cur = self.arbiter.wal._conn.cursor()
            cur.execute(
                f"UPDATE blackboard_tuples SET status = ? WHERE tuple_id IN ({placeholders});",
                [BlackboardStatus.COMPACTED.value, *compacted_ids],
            )
            self.arbiter.wal._conn.commit()

        if narrative_hook is not None and all_resolved:
            summary = narrative_hook(all_resolved)
        else:
            summary = (
                f"deterministic_compaction: {len(verified_entries)} verified, "
                f"{len(falsified_entries)} falsified at tick={logical_tick}"
            )

        return BlackboardDigest(
            task_id=task_id,
            compacted_at_tick=logical_tick,
            verified_claims=verified_entries,
            falsified_claims=falsified_entries,
            compacted_tuple_ids=compacted_ids,
            executive_summary=summary,
        )
