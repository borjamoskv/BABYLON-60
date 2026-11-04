"""FL-APPROVAL-01: local, signed review history; experimental, opt-in only.

This journal proves ordering inside a trusted review service, not psychological
independence. Reviewer keys must be provisioned outside the proposing agent.
It issues no broker ticket and replaces neither policy nor hardware approval.
JSON is a local storage format, not a new IPC/on-wire authorization protocol.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
from typing import Protocol, TypeVar

from blake3 import blake3
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


DOMAIN = b"FL-APPROVAL-01/v1\x00"
Result = TypeVar("Result")


class ApprovalError(ValueError):
    """A review is invalid, incomplete, expired, or already consumed."""


class AuthorizationGate(Protocol):
    def execute_once(self, task_payload: Mapping[str, object], effect: Callable[[], Result]) -> Result: ...


def canonical(value: object) -> bytes:
    """Bounded strict JSON, without ambiguous non-string keys or NaN."""
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
        raise ApprovalError("Expected finite JSON with string object keys")

    validate(value)
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    if len(data) > 64 * 1024:
        raise ApprovalError("Review payload exceeds 64 KiB")
    return data


def digest(value: object) -> str:
    return blake3(DOMAIN + canonical(value)).hexdigest()


def _text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalError(f"{field} must be nonempty text")


def _tick(value: object) -> None:
    if type(value) is not int or value < 0:
        raise ApprovalError("logical_tick must be a nonnegative integer")


def _decision(value: object) -> None:
    if value not in ("APPROVE", "REJECT"):
        raise ApprovalError("Decision must be APPROVE or REJECT")


def _hex_digest(value: object) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ApprovalError("Expected lowercase BLAKE3 hexadecimal digest")


class ApprovalJournal:
    """Append-only audit API on a dedicated SQLite WAL/FULL database.

    The service owns this database and pinned key map. Agents/reviewers must not
    have raw database access. SQLite triggers are not protection against its
    owner, rollback of the entire file, or deletion of the last signed event.
    An external checkpoint is required for that stronger retention guarantee.
    All causal hashes use supplied logical ticks; recorded_at is audit metadata.
    """

    def __init__(self, path: str | Path, reviewer_keys: Mapping[str, bytes]) -> None:
        self._keys = {name: VerifyKey(bytes(key)) for name, key in reviewer_keys.items()}
        if not self._keys or any(not isinstance(name, str) or not name.strip() for name in self._keys):
            raise ApprovalError("Explicit pinned reviewer keys are required")
        self._conn = sqlite3.connect(str(path), timeout=5, isolation_level=None)
        try:
            if self._conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise ApprovalError("A file-backed WAL database is required")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA busy_timeout=5000")
            with self._transaction():
                self._conn.execute("CREATE TABLE IF NOT EXISTS fl_approval_reviews (id TEXT PRIMARY KEY, body TEXT NOT NULL)")
                self._conn.execute(
                    "CREATE TABLE IF NOT EXISTS fl_approval_events ("
                    "review_id TEXT NOT NULL REFERENCES fl_approval_reviews(id), ordinal INTEGER NOT NULL, "
                    "body TEXT NOT NULL, signature TEXT NOT NULL, digest TEXT NOT NULL UNIQUE, "
                    "recorded_at TEXT NOT NULL, PRIMARY KEY(review_id, ordinal))"
                )
                self._conn.execute(
                    "CREATE TABLE IF NOT EXISTS fl_approval_consumed ("
                    "review_id TEXT PRIMARY KEY REFERENCES fl_approval_reviews(id), logical_tick INTEGER NOT NULL)"
                )
                for table in ("fl_approval_reviews", "fl_approval_events", "fl_approval_consumed"):
                    for operation in ("UPDATE", "DELETE"):
                        self._conn.execute(
                            f"CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()} BEFORE {operation} ON {table} "
                            "BEGIN SELECT RAISE(ABORT, 'FL-APPROVAL-01 append-only'); END"
                        )
        except BaseException:
            self._conn.close()
            raise

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> ApprovalJournal:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise

    def create_review(
        self, *, task_id: str, reviewer_id: str, task: dict, evidence: dict,
        policy_version: str, condition: str, logical_tick: int, expires_tick: int,
    ) -> str:
        for field, value in (("task_id", task_id), ("reviewer_id", reviewer_id), ("policy_version", policy_version)):
            _text(value, field)
        if reviewer_id not in self._keys or condition not in ("A", "B"):
            raise ApprovalError("Unknown reviewer or condition")
        if type(task) is not dict or not task or type(evidence) is not dict or not evidence:
            raise ApprovalError("Explicit task and evidence objects are required")
        _tick(logical_tick)
        _tick(expires_tick)
        if expires_tick <= logical_tick:
            raise ApprovalError("Expiry must follow review creation")
        body = {
            "version": 1, "task_id": task_id, "reviewer_id": reviewer_id,
            "task_digest": digest(task), "evidence_digest": digest(evidence),
            "policy_version": policy_version, "condition": condition,
            "logical_tick": logical_tick, "expires_tick": expires_tick,
        }
        review_id = digest(body)
        try:
            with self._transaction():
                self._conn.execute("INSERT INTO fl_approval_reviews VALUES (?, ?)", (review_id, canonical(body).decode()))
        except sqlite3.IntegrityError as exc:
            raise ApprovalError("Review already exists") from exc
        return review_id

    def _state(self, review_id: str) -> tuple[dict, list[dict]]:
        row = self._conn.execute("SELECT body FROM fl_approval_reviews WHERE id=?", (review_id,)).fetchone()
        if row is None:
            raise ApprovalError("Unknown review")
        try:
            review = json.loads(row[0])
            if digest(review) != review_id or review["reviewer_id"] not in self._keys:
                raise ApprovalError("Review binding or pinned reviewer changed")
            history: list[dict] = []
            for ordinal, body_json, signature_hex, entry_digest in self._conn.execute(
                "SELECT ordinal, body, signature, digest FROM fl_approval_events WHERE review_id=? ORDER BY ordinal",
                (review_id,),
            ):
                body = json.loads(body_json)
                expected = self._next(review_id, review, history, body["kind"], body["data"], body["logical_tick"])
                if ordinal != len(history) + 1 or canonical(expected) != canonical(body):
                    raise ApprovalError("Invalid event order or binding")
                signature = bytes.fromhex(signature_hex)
                self._verify_signature(review, body, signature)
                if digest({"body": body, "signature": signature_hex}) != entry_digest:
                    raise ApprovalError("Event digest mismatch")
                history.append({"body": body, "signature": signature_hex, "digest": entry_digest})
            return review, history
        except (KeyError, TypeError, ValueError) as exc:
            raise ApprovalError(f"Invalid review history: {exc}") from exc

    def _available(self, review_id: str) -> None:
        if self._conn.execute("SELECT 1 FROM fl_approval_consumed WHERE review_id=?", (review_id,)).fetchone():
            raise ApprovalError("Review already consumed")

    @staticmethod
    def _next(review_id: str, review: dict, history: list[dict], kind: str, data: dict, logical_tick: int) -> dict:
        _tick(logical_tick)
        previous_tick = history[-1]["body"]["logical_tick"] if history else review["logical_tick"]
        if not previous_tick < logical_tick < review["expires_tick"]:
            raise ApprovalError("Event is expired or logical tick did not advance")
        kinds = [event["body"]["kind"] for event in history]
        if "final" in kinds:
            raise ApprovalError("Review is finalized")
        if kind == "precommit":
            if review["condition"] != "B" or kinds or set(data) != {"decision"}:
                raise ApprovalError("B requires a single precommit before exposure")
            _decision(data["decision"])
        elif kind == "recommendation":
            required = ["precommit"] if review["condition"] == "B" else []
            if kinds != required or set(data) != {"recommendation", "rationale_digest"}:
                raise ApprovalError("Recommendation exposure violates review order")
            _decision(data["recommendation"])
            _hex_digest(data["rationale_digest"])
        elif kind == "final":
            required = ["precommit", "recommendation"] if review["condition"] == "B" else ["recommendation"]
            if kinds != required or set(data) != {"decision", "decision_evidence", "human_precommit_id", "recommendation_id"}:
                raise ApprovalError("Final decision requires recorded recommendation")
            _decision(data["decision"])
            _text(data["decision_evidence"], "decision_evidence")
            initial = history[0]["digest"] if review["condition"] == "B" else None
            if data["human_precommit_id"] != initial or data["recommendation_id"] != history[-1]["digest"]:
                raise ApprovalError("Final decision references different evidence")
        else:
            raise ApprovalError("Unknown event kind")
        return {
            "version": 1, "review_id": review_id, "kind": kind, "logical_tick": logical_tick,
            "previous_digest": history[-1]["digest"] if history else review_id, "data": data,
        }

    def _verify_signature(self, review: dict, body: dict, signature: bytes) -> None:
        if body["kind"] == "recommendation":
            if signature:
                raise ApprovalError("Recommendation is a service-recorded exposure event")
            return
        try:
            self._keys[review["reviewer_id"]].verify(DOMAIN + canonical(body), signature)
        except (BadSignatureError, ValueError, TypeError) as exc:
            raise ApprovalError("Invalid reviewer signature") from exc

    def _message(self, review_id: str, kind: str, data: dict, logical_tick: int) -> bytes:
        self._available(review_id)
        review, history = self._state(review_id)
        return DOMAIN + canonical(self._next(review_id, review, history, kind, data, logical_tick))

    def _record(self, review_id: str, kind: str, data: dict, logical_tick: int, signature: bytes = b"") -> str:
        with self._transaction():
            self._available(review_id)
            review, history = self._state(review_id)
            body = self._next(review_id, review, history, kind, data, logical_tick)
            self._verify_signature(review, body, signature)
            signature_hex = signature.hex()
            entry_digest = digest({"body": body, "signature": signature_hex})
            self._conn.execute(
                "INSERT INTO fl_approval_events VALUES (?, ?, ?, ?, ?, ?)",
                (review_id, len(history) + 1, canonical(body).decode(), signature_hex, entry_digest,
                 datetime.now(timezone.utc).isoformat()),
            )
            return entry_digest

    def precommit_message(self, review_id: str, decision: str, logical_tick: int) -> bytes:
        return self._message(review_id, "precommit", {"decision": decision}, logical_tick)

    def record_precommit(self, review_id: str, decision: str, logical_tick: int, signature: bytes) -> str:
        return self._record(review_id, "precommit", {"decision": decision}, logical_tick, signature)

    def record_recommendation(self, review_id: str, recommendation: str, rationale_digest: str, logical_tick: int) -> str:
        return self._record(
            review_id, "recommendation", {"recommendation": recommendation, "rationale_digest": rationale_digest}, logical_tick,
        )

    def _final_data(self, review_id: str, decision: str, decision_evidence: str) -> dict:
        review, history = self._state(review_id)
        return {
            "decision": decision, "decision_evidence": decision_evidence,
            "human_precommit_id": history[0]["digest"] if review["condition"] == "B" and history else None,
            "recommendation_id": history[-1]["digest"] if history else None,
        }

    def final_message(self, review_id: str, decision: str, decision_evidence: str, logical_tick: int) -> bytes:
        return self._message(review_id, "final", self._final_data(review_id, decision, decision_evidence), logical_tick)

    def record_final(self, review_id: str, decision: str, decision_evidence: str, logical_tick: int, signature: bytes) -> str:
        # _record reconstructs the chain in a write transaction. Concurrent
        # changes make an externally prepared signature fail closed.
        return self._record(review_id, "final", self._final_data(review_id, decision, decision_evidence), logical_tick, signature)

    def verify(self, review_id: str, *, task: dict, evidence: dict, policy_version: str, logical_tick: int) -> dict:
        self._available(review_id)
        review, history = self._state(review_id)
        _tick(logical_tick)
        if (review["task_digest"] != digest(task) or review["evidence_digest"] != digest(evidence)
                or review["policy_version"] != policy_version):
            raise ApprovalError("Task, evidence, or effective policy differs from signed review")
        if not history or history[-1]["body"]["kind"] != "final":
            raise ApprovalError("Review is incomplete")
        final = history[-1]["body"]
        if not final["logical_tick"] <= logical_tick < review["expires_tick"]:
            raise ApprovalError("Review is expired or verification tick precedes final decision")
        if final["data"]["decision"] != "APPROVE":
            raise ApprovalError("Final reviewer decision is REJECT")
        return final

    def execute_once(
        self, review_id: str, *, task: dict, evidence: dict, policy_version: str, logical_tick: int,
        policy_allows: Callable[[dict], bool], authorization_gate: AuthorizationGate, effect: Callable[[], Result],
    ) -> Result:
        """Optional adapter: review AND policy AND existing authorization gate.

        The trusted caller must hold its policy/evidence lock throughout this
        call and inject the real VerificationGate (including hardware approval
        for critical tasks). No default permissive authority exists. Consume
        durably before dispatch; exceptions/crashes require a new human review.
        This API is not installed in any live dispatcher by this experiment.
        """
        snapshot = canonical(task)
        with self._transaction():
            self.verify(review_id, task=json.loads(snapshot), evidence=evidence,
                        policy_version=policy_version, logical_tick=logical_tick)
            if policy_allows(json.loads(snapshot)) is not True:
                raise ApprovalError("Effective policy denies effect")
            self._conn.execute("INSERT INTO fl_approval_consumed VALUES (?, ?)", (review_id, logical_tick))
        return authorization_gate.execute_once(json.loads(snapshot), effect)
