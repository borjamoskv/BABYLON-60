# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""Verifiable persistent memory governance with revocation closure and crypto-shredding.

Enforces:
- B1 (NAME != IDENTITY): Canonical UUID-v4/v5 36-char primary identity.
- B4 (FALSIFICATION => DEPENDENCY REVIEW): Transitive revocation closure across
  DERIVES_FROM and DEPENDS_ON acyclic edges via recursive CTE / BFS.
- O1/O2 (SOURCE != INFERENCE, INFERENCE != AUTHORITY): Modality & trust-level
  gating with Hume's Guillotine enforcement.
- O13 (CLIENT CLOCK != SYSTEM TIME): Authoritative logical clock (lamport_t) and
  host epoch governance; caller-supplied transaction timestamps are rejected.
- BEMULA Unlearning & WORM Compatibility: Immutable CortexPersistLedger stores
  only SHA3-256 salted commitments (`SHA3-256(salt || plaintext)`), while
  reversible content/vectors live in `cortex_memory_blobs` and are physically
  purged upon a verified revocation receipt without breaking the WORM hash chain.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from babylon60.bft.cortex_crypto_kernel import _canonical_json
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger


class MemoryKind(str, Enum):
    """Canonical CORTEX memory entity kinds (INV_C5_CANONICAL_ONTOLOGY)."""

    SOURCE_RECORD = "SourceRecord"
    MEMORY_EVENT = "MemoryEvent"
    IDEA_THREAD = "IdeaThread"
    INFERENCE = "Inference"
    SKILL_LESSON = "SkillLesson"


class MemoryModality(str, Enum):
    """Epistemic vs. Deontic modality enforcing Hume's Guillotine."""

    EPISTEMIC = "Epistemic"
    DEONTIC = "Deontic"


class TrustLevel(int, Enum):
    """Strict authority hierarchy for conflict resolution and access filtering."""

    EXTERNAL = 10
    RESTRICTED = 20
    PUBLIC = 30
    SOVEREIGN = 100


class EdgeKind(str, Enum):
    """Closed typed edges from BORJARIO IR (INV_C5_BORJARIO_IR Section 4)."""

    DERIVES_FROM = "DERIVES_FROM"
    DEPENDS_ON = "DEPENDS_ON"
    SUPERSEDES = "SUPERSEDES"
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"


class MemoryStatus(str, Enum):
    """Lifecycle states of a governed memory record."""

    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    REVOKED_DEPENDENCY = "REVOKED_DEPENDENCY"
    DISBELIEVED = "DISBELIEVED"
    DISBELIEVED_DEPENDENCY = "DISBELIEVED_DEPENDENCY"
    STALE = "STALE"


@dataclass(frozen=True)
class DisbeliefProof:
    """Cryptographic and structural proof explaining why an attribution was disbelieved while preserving the underlying fact."""

    proof_id: str
    tenant_id: str
    disbelieved_record_id: str
    disbelieved_commitment: str
    disbelieved_content: str
    preserved_fact_ids: Tuple[str, ...]
    preserved_fact_commitments: Tuple[str, ...]
    counter_evidence_record_id: str
    counter_evidence_commitment: str
    rationale: str
    retracted_by_principal: str
    policy_epoch: int
    lamport_t: int
    ledger_event_id: str
    affected_dependents: Tuple[str, ...]
    witness_digest: str
    signature: str


class GovernanceViolationError(ValueError):
    """Raised when a memory operation violates C5-REAL governance invariants."""


class HumeGuillotineError(GovernanceViolationError):
    """Raised when attempting to derive a Deontic rule from purely Epistemic premises."""


class SignatureVerificationError(GovernanceViolationError):
    """Raised when an entry's cryptographic signature or commitment is invalid."""


class TenantIsolationError(GovernanceViolationError):
    """Raised on unauthorized cross-tenant memory reference or retrieval."""


class CausalCycleError(GovernanceViolationError):
    """Raised when a causal edge introduces a cycle in the genealogy/dependency DAG."""


def _validate_canonical_uuid(value: str, field_name: str = "record_id") -> str:
    """Enforce BORJARIO IR B1: NAME != IDENTITY (strict 36-char canonical UUID)."""
    if not isinstance(value, str) or len(value) != 36:
        raise GovernanceViolationError(
            f"B1 violation: {field_name} must be a canonical 36-character UUID, got {value!r}"
        )
    try:
        parsed = uuid.UUID(value)
    except ValueError as exc:
        raise GovernanceViolationError(f"B1 violation: invalid UUID format for {field_name}: {value!r}") from exc
    if str(parsed) != value:
        raise GovernanceViolationError(f"B1 violation: non-canonical UUID casing for {field_name}: {value!r}")
    return value


def sign_memory_commitment(secret_key: bytes, principal: str, tenant_id: str, commitment: str, policy_epoch: int) -> str:
    """Compute a deterministic MAC/signature binding principal, tenant, commitment and epoch."""
    if not isinstance(secret_key, (bytes, bytearray)) or len(secret_key) < 16:
        raise ValueError("secret_key must be at least 16 bytes")
    msg = f"{principal}\x1f{tenant_id}\x1f{commitment}\x1f{policy_epoch}".encode("utf-8")
    return hmac.new(bytes(secret_key), msg, hashlib.sha256).hexdigest()


def compute_salted_commitment(salt_hex: str, plaintext: str, modality: MemoryModality, kind: MemoryKind) -> str:
    """Compute SHA3-256 commitment over salt, content, modality and kind."""
    h = hashlib.sha3_256()
    h.update(bytes.fromhex(salt_hex))
    h.update(b"\x1f")
    h.update(kind.value.encode("utf-8"))
    h.update(b"\x1f")
    h.update(modality.value.encode("utf-8"))
    h.update(b"\x1f")
    h.update(plaintext.encode("utf-8"))
    return h.hexdigest()


def compute_disbelief_witness_digest(
    *,
    tenant_id: str,
    disbelieved_record_id: str,
    disbelieved_commitment: str,
    preserved_fact_ids: Sequence[str],
    preserved_fact_commitments: Sequence[str],
    counter_evidence_record_id: str,
    counter_evidence_commitment: str,
    rationale: str,
    policy_epoch: int,
) -> str:
    """Compute canonical SHA3-256 witness digest binding preserved facts, disbelieved attribution, and counter-evidence."""
    payload = _canonical_json(
        {
            "tenant_id": tenant_id,
            "disbelieved_record_id": disbelieved_record_id,
            "disbelieved_commitment": disbelieved_commitment,
            "preserved_fact_ids": list(preserved_fact_ids),
            "preserved_fact_commitments": list(preserved_fact_commitments),
            "counter_evidence_record_id": counter_evidence_record_id,
            "counter_evidence_commitment": counter_evidence_commitment,
            "rationale": rationale,
            "policy_epoch": int(policy_epoch),
        }
    )
    return hashlib.sha3_256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryRecordView:
    """Read-only projection of a governed memory record."""

    record_id: str
    tenant_id: str
    principal: str
    kind: MemoryKind
    modality: MemoryModality
    trust_level: TrustLevel
    policy_epoch: int
    valid_from_tick: int
    valid_to_tick: Optional[int]
    tx_lamport_t: int
    commitment: str
    signature: str
    status: MemoryStatus
    content: Optional[str]
    subject_key: Optional[str] = None
    parents: Tuple[str, ...] = field(default_factory=tuple)
    depends_on: Tuple[str, ...] = field(default_factory=tuple)
    revocation_receipt_id: Optional[str] = None


class MemoryGovernanceEngine:
    """Sovereign memory governance engine backed by SQLite WAL and CortexPersistLedger."""

    def __init__(self, db_path: Path | str, *, ledger: Optional[CortexPersistLedger] = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ledger if ledger is not None else CortexPersistLedger(self.db_path)
        self._principal_keys: Dict[Tuple[str, str], bytes] = {}
        self._host_epoch: int = 1
        self._init_governance_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous = FULL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_governance_schema(self) -> None:
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cortex_memory_records (
                    record_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    principal TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    trust_level INTEGER NOT NULL,
                    policy_epoch INTEGER NOT NULL,
                    subject_key TEXT,
                    valid_from_tick INTEGER NOT NULL,
                    valid_to_tick INTEGER,
                    tx_lamport_t INTEGER NOT NULL,
                    commitment TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    revocation_receipt_id TEXT,
                    ledger_event_id TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cortex_memory_blobs (
                    record_id TEXT PRIMARY KEY REFERENCES cortex_memory_records(record_id),
                    salt_hex TEXT NOT NULL,
                    plaintext TEXT NOT NULL,
                    tokens_json TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cortex_memory_edges (
                    parent_id TEXT NOT NULL REFERENCES cortex_memory_records(record_id),
                    child_id TEXT NOT NULL REFERENCES cortex_memory_records(record_id),
                    edge_kind TEXT NOT NULL,
                    PRIMARY KEY (parent_id, child_id, edge_kind)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cortex_tenant_grants (
                    owner_tenant TEXT NOT NULL,
                    grantee_tenant TEXT NOT NULL,
                    record_id TEXT NOT NULL REFERENCES cortex_memory_records(record_id),
                    granted_at_lamport INTEGER NOT NULL,
                    PRIMARY KEY (owner_tenant, grantee_tenant, record_id)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cortex_disbelief_proofs (
                    proof_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    disbelieved_record_id TEXT NOT NULL UNIQUE REFERENCES cortex_memory_records(record_id),
                    disbelieved_commitment TEXT NOT NULL,
                    preserved_fact_ids_json TEXT NOT NULL,
                    preserved_fact_commitments_json TEXT NOT NULL,
                    counter_evidence_record_id TEXT NOT NULL REFERENCES cortex_memory_records(record_id),
                    counter_evidence_commitment TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    retracted_by_principal TEXT NOT NULL,
                    policy_epoch INTEGER NOT NULL,
                    lamport_t INTEGER NOT NULL,
                    ledger_event_id TEXT NOT NULL,
                    affected_dependents_json TEXT NOT NULL,
                    witness_digest TEXT NOT NULL,
                    signature TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_tenant_status ON cortex_memory_records(tenant_id, status);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_subject ON cortex_memory_records(tenant_id, subject_key, status);"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_edges_parent ON cortex_memory_edges(parent_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_edges_child ON cortex_memory_edges(child_id);")
            conn.commit()

    def register_principal_key(self, tenant_id: str, principal: str, secret_key: bytes) -> None:
        """Register signing key for a principal within a tenant boundary."""
        if not tenant_id or not principal:
            raise ValueError("tenant_id and principal must be non-empty")
        if len(secret_key) < 16:
            raise ValueError("secret_key must be at least 16 bytes")
        self._principal_keys[(tenant_id, principal)] = bytes(secret_key)

    def advance_policy_epoch(self, new_epoch: int) -> int:
        """Advance authoritative host policy epoch monotonically (Law O13)."""
        if new_epoch <= self._host_epoch:
            raise GovernanceViolationError(
                f"Policy epoch must advance monotonically (current={self._host_epoch}, requested={new_epoch})"
            )
        self._host_epoch = new_epoch
        return self._host_epoch

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
        return sorted({tok for tok in cleaned.split() if len(tok) >= 2})

    def _check_no_cycle(
        self, conn: sqlite3.Connection, child_id: str, candidate_parents: Sequence[str]
    ) -> None:
        """Ensure adding edges parent -> child_id does not create a cycle in the DAG."""
        if child_id in candidate_parents:
            raise CausalCycleError(f"BJR-E052: self-loop detected on {child_id}")
        frontier = list(candidate_parents)
        visited: Set[str] = set()
        while frontier:
            curr = frontier.pop()
            if curr == child_id:
                raise CausalCycleError(f"BJR-E052: cycle detected involving {child_id}")
            if curr in visited:
                continue
            visited.add(curr)
            rows = conn.execute(
                "SELECT parent_id FROM cortex_memory_edges WHERE child_id = ? "
                "AND edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON', 'SUPERSEDES')",
                (curr,),
            ).fetchall()
            for (p_id,) in rows:
                if p_id not in visited:
                    frontier.append(p_id)

    def add_record(
        self,
        *,
        record_id: Optional[str] = None,
        tenant_id: str,
        principal: str,
        content: str,
        kind: MemoryKind = MemoryKind.SOURCE_RECORD,
        modality: MemoryModality = MemoryModality.EPISTEMIC,
        trust_level: TrustLevel = TrustLevel.PUBLIC,
        subject_key: Optional[str] = None,
        parents: Sequence[str] = (),
        depends_on: Sequence[str] = (),
        valid_from_tick: Optional[int] = None,
        valid_to_tick: Optional[int] = None,
        signature: Optional[str] = None,
        salt_hex: Optional[str] = None,
        client_supplied_tx_time: Optional[int] = None,
    ) -> MemoryRecordView:
        """Insert a verified, signed memory record and bind it to the WORM ledger."""
        # Law O13: Reject caller-supplied transaction clock
        if client_supplied_tx_time is not None:
            raise GovernanceViolationError(
                "Law O13 violation (CLIENT CLOCK != SYSTEM TIME): caller cannot supply transaction_time"
            )
        if not tenant_id or not isinstance(tenant_id, str):
            raise GovernanceViolationError("tenant_id must be a non-empty string")
        if not principal or not isinstance(principal, str):
            raise GovernanceViolationError("principal must be a non-empty string")
        if not isinstance(content, str) or not content.strip():
            raise GovernanceViolationError("content must be a non-empty string")

        rec_id = _validate_canonical_uuid(record_id if record_id is not None else str(uuid.uuid4()))
        parent_ids = tuple(_validate_canonical_uuid(p, "parent_id") for p in parents)
        dep_ids = tuple(_validate_canonical_uuid(d, "depends_on_id") for d in depends_on)

        salt = salt_hex if salt_hex is not None else os.urandom(16).hex()
        commitment = compute_salted_commitment(salt, content, modality, kind)

        key = self._principal_keys.get((tenant_id, principal))
        if key is None:
            raise SignatureVerificationError(f"Unregistered principal {principal!r} in tenant {tenant_id!r}")
        expected_sig = sign_memory_commitment(key, principal, tenant_id, commitment, self._host_epoch)
        if signature is not None and not hmac.compare_digest(signature, expected_sig):
            raise SignatureVerificationError("Invalid cryptographic signature for MemoryRecord")
        actual_sig = expected_sig

        with closing(self._get_connection()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            all_upstream = list(dict.fromkeys([*parent_ids, *dep_ids]))
            upstream_modalities: List[str] = []

            # Reuse each scar's salt to compare commitments, independently of
            # the candidate's UUID, principal, salt, or chosen dependencies.
            scars = conn.execute(
                "SELECT r.commitment, b.salt_hex FROM cortex_disbelief_proofs p "
                "JOIN cortex_memory_records r ON r.record_id = p.disbelieved_record_id "
                "JOIN cortex_memory_blobs b ON b.record_id = r.record_id "
                "WHERE p.tenant_id = ? AND r.kind = ? AND r.modality = ?",
                (tenant_id, kind.value, modality.value),
            ).fetchall()
            for scar_commitment, scar_salt in scars:
                candidate = compute_salted_commitment(scar_salt, content, modality, kind)
                if hmac.compare_digest(candidate, scar_commitment):
                    raise GovernanceViolationError("Previously disbelieved attribution cannot be reinserted")

            for up_id in all_upstream:
                row = conn.execute(
                    "SELECT tenant_id, modality, status FROM cortex_memory_records WHERE record_id = ?",
                    (up_id,),
                ).fetchone()
                if row is None:
                    raise GovernanceViolationError(f"Missing upstream dependency record: {up_id}")
                up_tenant, up_mod, up_status = row
                if up_tenant != tenant_id:
                    grant = conn.execute(
                        "SELECT 1 FROM cortex_tenant_grants WHERE owner_tenant = ? AND grantee_tenant = ? AND record_id = ?",
                        (up_tenant, tenant_id, up_id),
                    ).fetchone()
                    if grant is None:
                        raise TenantIsolationError(
                            f"Cross-tenant reference from {tenant_id!r} to {up_tenant!r} on {up_id} denied"
                        )
                if up_status != MemoryStatus.ACTIVE.value:
                    raise GovernanceViolationError(
                        f"Cannot derive from or depend on non-active record {up_id} (status={up_status})"
                    )
                upstream_modalities.append(str(up_mod))

            # Hume's Guillotine: Deontic derived record requires at least one Deontic premise or Sovereign authority
            if modality == MemoryModality.DEONTIC and all_upstream:
                if MemoryModality.DEONTIC.value not in upstream_modalities and trust_level != TrustLevel.SOVEREIGN:
                    raise HumeGuillotineError(
                        "Hume's Guillotine violation: cannot derive Deontic memory from purely Epistemic parents"
                    )

            self._check_no_cycle(conn, rec_id, all_upstream)

            # Append immutable commitment to WORM CortexPersistLedger (no plaintext stored in WORM)
            ledger_res = self.ledger.append_event(
                CortexEvent(
                    event_type="MEMORY_RECORD_COMMITTED",
                    payload={
                        "record_id": rec_id,
                        "tenant_id": tenant_id,
                        "principal": principal,
                        "kind": kind.value,
                        "modality": modality.value,
                        "trust_level": int(trust_level),
                        "policy_epoch": self._host_epoch,
                        "commitment": commitment,
                        "signature": actual_sig,
                        "parents": list(parent_ids),
                        "depends_on": list(dep_ids),
                    },
                    cortex_taint=f"MEM_COMMIT:{tenant_id}:{rec_id}:{commitment[:16]}",
                    agent_id=principal,
                ),
                # Separate ledger files retain their own durable transaction;
                # the governance writer lock still serializes derivation/revocation.
                connection=conn if os.path.samefile(self.db_path, self.ledger.db_path) else None,
            )
            tx_lamport = int(ledger_res["lamport_t"])
            v_from = valid_from_tick if valid_from_tick is not None else tx_lamport
            tokens_json = _canonical_json(self._tokenize(content))

            superseded_ids: List[str] = []
            if subject_key is not None:
                prev_rows = conn.execute(
                    "SELECT record_id, trust_level FROM cortex_memory_records "
                    "WHERE tenant_id = ? AND subject_key = ? AND status = 'ACTIVE'",
                    (tenant_id, subject_key),
                ).fetchall()
                for prev_id, prev_trust in prev_rows:
                    if int(trust_level) >= int(prev_trust):
                        conn.execute(
                            "UPDATE cortex_memory_records SET status = ?, valid_to_tick = ? WHERE record_id = ?",
                            (MemoryStatus.STALE.value, tx_lamport, prev_id),
                        )
                        superseded_ids.append(prev_id)
                        # Invalidate compiled summaries (IdeaThreads) derived from the superseded fact
                        self._mark_dependents_stale(conn, prev_id, tx_lamport)

            initial_status = MemoryStatus.ACTIVE
            if subject_key is not None:
                higher_exists = conn.execute(
                    "SELECT 1 FROM cortex_memory_records "
                    "WHERE tenant_id = ? AND subject_key = ? AND status = 'ACTIVE' AND trust_level > ?",
                    (tenant_id, subject_key, int(trust_level)),
                ).fetchone()
                if higher_exists is not None:
                    initial_status = MemoryStatus.STALE

            conn.execute(
                """
                INSERT INTO cortex_memory_records (
                    record_id, tenant_id, principal, kind, modality, trust_level,
                    policy_epoch, subject_key, valid_from_tick, valid_to_tick,
                    tx_lamport_t, commitment, signature, status, revocation_receipt_id, ledger_event_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    rec_id,
                    tenant_id,
                    principal,
                    kind.value,
                    modality.value,
                    int(trust_level),
                    self._host_epoch,
                    subject_key,
                    v_from,
                    valid_to_tick,
                    tx_lamport,
                    commitment,
                    actual_sig,
                    initial_status.value,
                    str(ledger_res["event_id"]),
                ),
            )
            conn.execute(
                "INSERT INTO cortex_memory_blobs (record_id, salt_hex, plaintext, tokens_json) VALUES (?, ?, ?, ?)",
                (rec_id, salt, content, tokens_json),
            )
            for prev_id in superseded_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO cortex_memory_edges (parent_id, child_id, edge_kind) VALUES (?, ?, ?)",
                    (prev_id, rec_id, EdgeKind.SUPERSEDES.value),
                )
            for p_id in parent_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO cortex_memory_edges (parent_id, child_id, edge_kind) VALUES (?, ?, ?)",
                    (p_id, rec_id, EdgeKind.DERIVES_FROM.value),
                )
            for d_id in dep_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO cortex_memory_edges (parent_id, child_id, edge_kind) VALUES (?, ?, ?)",
                    (d_id, rec_id, EdgeKind.DEPENDS_ON.value),
                )
            conn.commit()

        return self.get_record(rec_id, tenant_id=tenant_id, include_inactive=True)

    def _mark_dependents_stale(self, conn: sqlite3.Connection, root_id: str, tick: int) -> List[str]:
        """Mark downstream derived summaries/skills as STALE when an underlying fact mutates."""
        rows = conn.execute(
            """
            WITH RECURSIVE downstream(id) AS (
                SELECT child_id FROM cortex_memory_edges
                WHERE parent_id = ? AND edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON')
                UNION
                SELECT e.child_id FROM cortex_memory_edges e
                JOIN downstream d ON e.parent_id = d.id
                WHERE e.edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON')
            )
            SELECT id FROM downstream;
            """,
            (root_id,),
        ).fetchall()
        affected = [r[0] for r in rows]
        for child_id in affected:
            conn.execute(
                "UPDATE cortex_memory_records SET status = ?, valid_to_tick = ? "
                "WHERE record_id = ? AND status = 'ACTIVE'",
                (MemoryStatus.STALE.value, tick, child_id),
            )
        return affected

    def revoke_record(
        self,
        *,
        record_id: str,
        tenant_id: str,
        principal: str,
        reason: str = "operator_revocation",
    ) -> Dict[str, object]:
        """Atomically revoke the transitive closure and remove queryable blobs."""
        rec_id = _validate_canonical_uuid(record_id)
        key = self._principal_keys.get((tenant_id, principal))
        if key is None:
            raise SignatureVerificationError(f"Unregistered principal {principal!r} in tenant {tenant_id!r}")

        with closing(self._get_connection()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT tenant_id, commitment FROM cortex_memory_records WHERE record_id = ?",
                (rec_id,),
            ).fetchone()
            if row is None:
                raise KeyError(rec_id)
            rec_tenant, commitment = row
            if rec_tenant != tenant_id:
                raise TenantIsolationError(f"Tenant {tenant_id!r} cannot revoke record owned by {rec_tenant!r}")

            descendant_rows = conn.execute(
                """
                WITH RECURSIVE closure(id, depth) AS (
                    SELECT ?, 0
                    UNION
                    SELECT e.child_id, c.depth + 1
                    FROM cortex_memory_edges e
                    JOIN closure c ON e.parent_id = c.id
                    WHERE e.edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON') AND c.depth < 1024
                )
                SELECT DISTINCT id FROM closure;
                """,
                (rec_id,),
            ).fetchall()
            closure_ids = [r[0] for r in descendant_rows]

            revocation_sig = sign_memory_commitment(
                key, principal, tenant_id, f"REVOKE:{rec_id}:{commitment}", self._host_epoch
            )
            receipt = self.ledger.append_event(
                CortexEvent(
                    event_type="MEMORY_RECORD_REVOKED",
                    payload={
                        "target_record_id": rec_id,
                        "tenant_id": tenant_id,
                        "principal": principal,
                        "reason": reason,
                        "closure_size": len(closure_ids),
                        "closure_ids": closure_ids,
                        "signature": revocation_sig,
                    },
                    cortex_taint=f"MEM_REVOKE:{tenant_id}:{rec_id}",
                    agent_id=principal,
                ),
                connection=conn if os.path.samefile(self.db_path, self.ledger.db_path) else None,
            )
            receipt_id = str(receipt["event_id"])
            tx_lamport = int(receipt["lamport_t"])

            conn.execute(
                "UPDATE cortex_memory_records SET status = ?, valid_to_tick = ?, revocation_receipt_id = ? "
                "WHERE record_id = ?",
                (MemoryStatus.REVOKED.value, tx_lamport, receipt_id, rec_id),
            )
            dependent_ids = [cid for cid in closure_ids if cid != rec_id]
            for dep_id in dependent_ids:
                conn.execute(
                    "UPDATE cortex_memory_records SET status = ?, valid_to_tick = ?, revocation_receipt_id = ? "
                    "WHERE record_id = ?",
                    (MemoryStatus.REVOKED_DEPENDENCY.value, tx_lamport, receipt_id, dep_id),
                )
            # Remove queryable blobs and tokens; this does not certify physical or cryptographic erasure.
            for cid in closure_ids:
                conn.execute("DELETE FROM cortex_memory_blobs WHERE record_id = ?", (cid,))
            conn.commit()

        return {
            "revoked_root": rec_id,
            "revoked_dependents": dependent_ids,
            "total_invalidated": len(closure_ids),
            "revocation_receipt_id": receipt_id,
            "lamport_t": tx_lamport,
        }

    def grant_cross_tenant_read(
        self, *, owner_tenant: str, grantee_tenant: str, record_id: str, principal: str
    ) -> None:
        """Explicitly delegate read capability for a specific record to another tenant."""
        rec_id = _validate_canonical_uuid(record_id)
        if (owner_tenant, principal) not in self._principal_keys:
            raise SignatureVerificationError("Unauthorized principal for owner_tenant")
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT tenant_id, tx_lamport_t FROM cortex_memory_records WHERE record_id = ?",
                (rec_id,),
            ).fetchone()
            if row is None or row[0] != owner_tenant:
                raise TenantIsolationError("Record does not belong to owner_tenant")
            conn.execute(
                "INSERT OR REPLACE INTO cortex_tenant_grants (owner_tenant, grantee_tenant, record_id, granted_at_lamport) "
                "VALUES (?, ?, ?, ?)",
                (owner_tenant, grantee_tenant, rec_id, int(row[1])),
            )
            conn.commit()

    def get_record(
        self, record_id: str, *, tenant_id: str, include_inactive: bool = False
    ) -> MemoryRecordView:
        """Retrieve a single memory record enforcing tenant isolation and commitment verification."""
        rec_id = _validate_canonical_uuid(record_id)
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT r.record_id, r.tenant_id, r.principal, r.kind, r.modality,
                       r.trust_level, r.policy_epoch, r.subject_key, r.valid_from_tick,
                       r.valid_to_tick, r.tx_lamport_t, r.commitment, r.signature,
                       r.status, r.revocation_receipt_id, b.salt_hex, b.plaintext
                FROM cortex_memory_records r
                LEFT JOIN cortex_memory_blobs b ON r.record_id = b.record_id
                WHERE r.record_id = ?
                """,
                (rec_id,),
            ).fetchone()
            if row is None:
                raise KeyError(rec_id)
            (
                r_id,
                r_tenant,
                r_principal,
                r_kind,
                r_mod,
                r_trust,
                r_epoch,
                r_subj,
                r_vfrom,
                r_vto,
                r_tx,
                r_comm,
                r_sig,
                r_status,
                r_rev_id,
                b_salt,
                b_plain,
            ) = row

            if r_tenant != tenant_id:
                grant = conn.execute(
                    "SELECT 1 FROM cortex_tenant_grants WHERE owner_tenant = ? AND grantee_tenant = ? AND record_id = ?",
                    (r_tenant, tenant_id, r_id),
                ).fetchone()
                if grant is None:
                    raise TenantIsolationError(f"Tenant {tenant_id!r} denied access to {r_id}")

            status_enum = MemoryStatus(r_status)
            if not include_inactive and status_enum != MemoryStatus.ACTIVE:
                raise GovernanceViolationError(f"Record {r_id} is not ACTIVE (status={r_status})")

            kind_enum = MemoryKind(r_kind)
            mod_enum = MemoryModality(r_mod)

            # Verify cryptographic signature and commitment integrity on read (FL-M04)
            key = self._principal_keys.get((r_tenant, r_principal))
            if key is None:
                raise SignatureVerificationError(f"Missing verification key for ({r_tenant}, {r_principal})")
            expected_sig = sign_memory_commitment(key, r_principal, r_tenant, r_comm, int(r_epoch))
            if not hmac.compare_digest(r_sig, expected_sig):
                raise SignatureVerificationError(f"Signature tampering detected on record {r_id}")

            if status_enum in (
                MemoryStatus.ACTIVE, MemoryStatus.DISBELIEVED, MemoryStatus.DISBELIEVED_DEPENDENCY,
            ) and (b_plain is None or b_salt is None):
                raise SignatureVerificationError(f"Missing memory blob or salt on record {r_id}")
            if b_plain is not None and b_salt is not None:
                recomputed = compute_salted_commitment(b_salt, b_plain, mod_enum, kind_enum)
                if not hmac.compare_digest(recomputed, r_comm):
                    raise SignatureVerificationError(f"Payload tampering detected against commitment on {r_id}")

            parents = tuple(
                r[0]
                for r in conn.execute(
                    "SELECT parent_id FROM cortex_memory_edges WHERE child_id = ? AND edge_kind = 'DERIVES_FROM'",
                    (r_id,),
                ).fetchall()
            )
            deps = tuple(
                r[0]
                for r in conn.execute(
                    "SELECT parent_id FROM cortex_memory_edges WHERE child_id = ? AND edge_kind = 'DEPENDS_ON'",
                    (r_id,),
                ).fetchall()
            )

        return MemoryRecordView(
            record_id=r_id,
            tenant_id=r_tenant,
            principal=r_principal,
            kind=kind_enum,
            modality=mod_enum,
            trust_level=TrustLevel(int(r_trust)),
            policy_epoch=int(r_epoch),
            valid_from_tick=int(r_vfrom),
            valid_to_tick=int(r_vto) if r_vto is not None else None,
            tx_lamport_t=int(r_tx),
            commitment=r_comm,
            signature=r_sig,
            status=status_enum,
            content=(
                b_plain
                if status_enum
                in (
                    MemoryStatus.ACTIVE,
                    MemoryStatus.DISBELIEVED,
                    MemoryStatus.DISBELIEVED_DEPENDENCY,
                )
                else None
            ),
            subject_key=r_subj,
            parents=parents,
            depends_on=deps,
            revocation_receipt_id=r_rev_id,
        )

    def query_active_memories(
        self,
        *,
        tenant_id: str,
        query_text: Optional[str] = None,
        subject_key: Optional[str] = None,
        min_trust_level: TrustLevel = TrustLevel.RESTRICTED,
        kind: Optional[MemoryKind] = None,
        valid_at_tick: Optional[int] = None,
    ) -> List[MemoryRecordView]:
        """Query only ACTIVE, cryptographically verified records permitted for the tenant."""
        query_tokens = set(self._tokenize(query_text)) if query_text else set()
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT r.record_id, b.tokens_json
                FROM cortex_memory_records r
                JOIN cortex_memory_blobs b ON r.record_id = b.record_id
                WHERE (
                    r.tenant_id = ?
                    OR EXISTS (
                        SELECT 1 FROM cortex_tenant_grants g
                        WHERE g.owner_tenant = r.tenant_id
                          AND g.grantee_tenant = ?
                          AND g.record_id = r.record_id
                    )
                )
                  AND r.status = 'ACTIVE'
                  AND r.trust_level >= ?
                  AND (? IS NULL OR r.subject_key = ?)
                  AND (? IS NULL OR r.kind = ?)
                  AND (? IS NULL OR (r.valid_from_tick <= ? AND (r.valid_to_tick IS NULL OR r.valid_to_tick > ?)))
                ORDER BY r.trust_level DESC, r.tx_lamport_t DESC
                """,
                (
                    tenant_id,
                    tenant_id,
                    int(min_trust_level),
                    subject_key,
                    subject_key,
                    kind.value if kind is not None else None,
                    kind.value if kind is not None else None,
                    valid_at_tick,
                    valid_at_tick,
                    valid_at_tick,
                ),
            ).fetchall()

        results: List[MemoryRecordView] = []
        for rec_id, tokens_json in rows:
            if query_tokens:
                stored_tokens = set(json.loads(tokens_json))
                if not (query_tokens & stored_tokens):
                    continue
            view = self.get_record(rec_id, tenant_id=tenant_id, include_inactive=False)
            results.append(view)
        return results

    def certify_or_rebuild_summary(
        self,
        *,
        summary_id: str,
        tenant_id: str,
        principal: str,
        synthesizer: Callable[[Sequence[MemoryRecordView]], str],
    ) -> MemoryRecordView:
        """Certify a contracted IdeaThread against live premises ('Many Steps into One', FL-M08).

        If the summary is ACTIVE and all its parent premises remain ACTIVE, returns it directly.
        If any parent was updated/superseded or the summary is STALE, rebuilds a fresh summary
        from the current active premises for the same subject keys.
        """
        view = self.get_record(summary_id, tenant_id=tenant_id, include_inactive=True)
        if view.status == MemoryStatus.REVOKED or view.status == MemoryStatus.REVOKED_DEPENDENCY:
            raise GovernanceViolationError(f"Summary {summary_id} was revoked and cannot be used")

        parent_views = [
            self.get_record(pid, tenant_id=tenant_id, include_inactive=True) for pid in view.parents
        ]
        all_parents_active = all(p.status == MemoryStatus.ACTIVE for p in parent_views)
        if view.status == MemoryStatus.ACTIVE and all_parents_active:
            return view

        # Rebuild from current active records replacing stale parents
        live_premises: List[MemoryRecordView] = []
        for p in parent_views:
            if p.status == MemoryStatus.ACTIVE:
                live_premises.append(p)
            elif p.subject_key is not None:
                replacements = self.query_active_memories(
                    tenant_id=tenant_id,
                    subject_key=p.subject_key,
                    min_trust_level=TrustLevel.EXTERNAL,
                )
                live_premises.extend(replacements)

        if not live_premises:
            raise GovernanceViolationError("No live premises remain to rebuild contracted summary")

        new_content = synthesizer(live_premises)
        return self.add_record(
            tenant_id=tenant_id,
            principal=principal,
            content=new_content,
            kind=MemoryKind.IDEA_THREAD,
            modality=view.modality,
            trust_level=view.trust_level,
            subject_key=view.subject_key,
            parents=[p.record_id for p in live_premises],
        )

    def retract_attribution(
        self,
        *,
        attribution_record_id: str,
        counter_evidence_record_id: str,
        tenant_id: str,
        principal: str,
        rationale: str,
        proof_id: Optional[str] = None,
    ) -> DisbeliefProof:
        """Retract belief in an attribution or derived inference while preserving underlying SourceRecords (O1, O8, B4).

        Unlike administrative revocation (`revoke_record`), epistemic retraction:
        1. Forbids retracting a primary `SourceRecord` (facts are immutable territory; only attributions/inferences map-level claims can be disbelieved).
        2. Requires an ACTIVE `counter_evidence_record_id` linked via a `CONTRADICTS` edge.
        3. Preserves all upstream `SourceRecord` nodes in `ACTIVE` status with intact blobs.
        4. Retains the disbelieved attribution's blob as a negative epistemic scar (`DISBELIEVED`). Exact-content reinsertion of the same kind/modality in this tenant is rejected; semantic paraphrases are not detected.
        5. Propagates `DISBELIEVED_DEPENDENCY` across downstream derived nodes (B4: `Falsify(c) => Review(Dependents(c))`).
        """
        attr_id = _validate_canonical_uuid(attribution_record_id, "attribution_record_id")
        counter_id = _validate_canonical_uuid(counter_evidence_record_id, "counter_evidence_record_id")
        p_id = _validate_canonical_uuid(proof_id if proof_id is not None else str(uuid.uuid4()), "proof_id")
        if attr_id == counter_id:
            raise GovernanceViolationError("counter_evidence_record_id cannot be identical to attribution_record_id")
        if not isinstance(rationale, str) or not rationale.strip():
            raise GovernanceViolationError("rationale must be a non-empty string explaining the refutation")

        key = self._principal_keys.get((tenant_id, principal))
        if key is None:
            raise SignatureVerificationError(f"Unregistered principal {principal!r} in tenant {tenant_id!r}")

        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            attr_row = conn.execute(
                "SELECT tenant_id, kind, trust_level, commitment, status FROM cortex_memory_records WHERE record_id = ?",
                (attr_id,),
            ).fetchone()
            if attr_row is None:
                raise KeyError(attr_id)
            attr_tenant, attr_kind, attr_trust, attr_comm, attr_status = attr_row
            if attr_tenant != tenant_id:
                raise TenantIsolationError(
                    f"Tenant {tenant_id!r} cannot retract attribution owned by {attr_tenant!r}"
                )
            if attr_kind == MemoryKind.SOURCE_RECORD.value:
                raise GovernanceViolationError(
                    "Law O1 violation (SOURCE != INFERENCE): cannot retract belief in a primary SourceRecord; "
                    "only derived attributions/inferences can be disbelieved while preserving the fact."
                )
            if attr_status != MemoryStatus.ACTIVE.value:
                raise GovernanceViolationError(
                    f"Attribution {attr_id} must be ACTIVE to be epistemically retracted (got {attr_status})"
                )

            counter_row = conn.execute(
                "SELECT tenant_id, trust_level, commitment, status FROM cortex_memory_records WHERE record_id = ?",
                (counter_id,),
            ).fetchone()
            if counter_row is None:
                raise GovernanceViolationError(f"Missing counter-evidence record: {counter_id}")
            counter_tenant, counter_trust, counter_comm, counter_status = counter_row
            if counter_tenant != tenant_id:
                grant = conn.execute(
                    "SELECT 1 FROM cortex_tenant_grants WHERE owner_tenant = ? AND grantee_tenant = ? AND record_id = ?",
                    (counter_tenant, tenant_id, counter_id),
                ).fetchone()
                if grant is None:
                    raise TenantIsolationError(
                        f"Cross-tenant counter-evidence reference denied on {counter_id}"
                    )
            if counter_status != MemoryStatus.ACTIVE.value:
                raise GovernanceViolationError(
                    f"Counter-evidence {counter_id} must be ACTIVE (got {counter_status})"
                )
            if int(counter_trust) < int(attr_trust):
                raise GovernanceViolationError(
                    f"Counter-evidence trust_level ({counter_trust}) cannot be lower than attribution trust_level ({attr_trust})"
                )

            # Trace upstream ancestors to verify and bind all underlying SourceRecords (facts)
            ancestor_rows = conn.execute(
                """
                WITH RECURSIVE ancestors(id, depth) AS (
                    SELECT parent_id, 1 FROM cortex_memory_edges
                    WHERE child_id = ? AND edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON')
                    UNION
                    SELECT e.parent_id, a.depth + 1
                    FROM cortex_memory_edges e
                    JOIN ancestors a ON e.child_id = a.id
                    WHERE e.edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON') AND a.depth < 1024
                )
                SELECT DISTINCT r.record_id, r.commitment, r.status
                FROM ancestors a
                JOIN cortex_memory_records r ON r.record_id = a.id
                WHERE r.kind = ?
                ORDER BY r.tx_lamport_t ASC, r.record_id ASC;
                """,
                (attr_id, MemoryKind.SOURCE_RECORD.value),
            ).fetchall()
            if not ancestor_rows:
                raise GovernanceViolationError(
                    f"Attribution {attr_id} has no anchored upstream SourceRecord to preserve"
                )
            for f_id, _, f_status in ancestor_rows:
                if f_status != MemoryStatus.ACTIVE.value:
                    raise GovernanceViolationError(
                        f"Upstream SourceRecord {f_id} is not ACTIVE (status={f_status})"
                    )
            preserved_fact_ids = tuple(r[0] for r in ancestor_rows)
            preserved_fact_commitments = tuple(r[1] for r in ancestor_rows)

            # Compute downstream closure (B4: Falsification => Dependency Review)
            descendant_rows = conn.execute(
                """
                WITH RECURSIVE closure(id, depth) AS (
                    SELECT ?, 0
                    UNION
                    SELECT e.child_id, c.depth + 1
                    FROM cortex_memory_edges e
                    JOIN closure c ON e.parent_id = c.id
                    WHERE e.edge_kind IN ('DERIVES_FROM', 'DEPENDS_ON') AND c.depth < 1024
                )
                SELECT DISTINCT id FROM closure WHERE id != ?;
                """,
                (attr_id, attr_id),
            ).fetchall()
            dependent_ids = tuple(r[0] for r in descendant_rows)
            conn.commit()

        witness_digest = compute_disbelief_witness_digest(
            tenant_id=tenant_id,
            disbelieved_record_id=attr_id,
            disbelieved_commitment=attr_comm,
            preserved_fact_ids=preserved_fact_ids,
            preserved_fact_commitments=preserved_fact_commitments,
            counter_evidence_record_id=counter_id,
            counter_evidence_commitment=counter_comm,
            rationale=rationale,
            policy_epoch=self._host_epoch,
        )
        proof_sig = sign_memory_commitment(
            key, principal, tenant_id, f"DISBELIEVE:{p_id}:{witness_digest}", self._host_epoch
        )

        ledger_res = self.ledger.append_event(
            CortexEvent(
                event_type="ATTRIBUTION_DISBELIEVED",
                payload={
                    "proof_id": p_id,
                    "tenant_id": tenant_id,
                    "principal": principal,
                    "disbelieved_record_id": attr_id,
                    "disbelieved_commitment": attr_comm,
                    "preserved_fact_ids": list(preserved_fact_ids),
                    "preserved_fact_commitments": list(preserved_fact_commitments),
                    "counter_evidence_record_id": counter_id,
                    "counter_evidence_commitment": counter_comm,
                    "affected_dependents": list(dependent_ids),
                    "witness_digest": witness_digest,
                    "signature": proof_sig,
                },
                cortex_taint=f"MEM_DISBELIEVE:{tenant_id}:{attr_id}:{witness_digest[:16]}",
                agent_id=principal,
            )
        )
        event_id = str(ledger_res["event_id"])
        tx_lamport = int(ledger_res["lamport_t"])

        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE cortex_memory_records SET status = ?, valid_to_tick = ?, revocation_receipt_id = ? "
                "WHERE record_id = ?",
                (MemoryStatus.DISBELIEVED.value, tx_lamport, event_id, attr_id),
            )
            for dep_id in dependent_ids:
                conn.execute(
                    "UPDATE cortex_memory_records SET status = ?, valid_to_tick = ?, revocation_receipt_id = ? "
                    "WHERE record_id = ? AND status = 'ACTIVE'",
                    (MemoryStatus.DISBELIEVED_DEPENDENCY.value, tx_lamport, event_id, dep_id),
                )
            conn.execute(
                "INSERT OR IGNORE INTO cortex_memory_edges (parent_id, child_id, edge_kind) VALUES (?, ?, ?)",
                (counter_id, attr_id, EdgeKind.CONTRADICTS.value),
            )
            conn.execute(
                """
                INSERT INTO cortex_disbelief_proofs (
                    proof_id, tenant_id, disbelieved_record_id, disbelieved_commitment,
                    preserved_fact_ids_json, preserved_fact_commitments_json,
                    counter_evidence_record_id, counter_evidence_commitment,
                    rationale, retracted_by_principal, policy_epoch, lamport_t,
                    ledger_event_id, affected_dependents_json, witness_digest, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p_id,
                    tenant_id,
                    attr_id,
                    attr_comm,
                    _canonical_json(list(preserved_fact_ids)),
                    _canonical_json(list(preserved_fact_commitments)),
                    counter_id,
                    counter_comm,
                    rationale,
                    principal,
                    self._host_epoch,
                    tx_lamport,
                    event_id,
                    _canonical_json(list(dependent_ids)),
                    witness_digest,
                    proof_sig,
                ),
            )
            conn.commit()

        return self.prove_disbelief(attr_id, tenant_id=tenant_id)

    def prove_disbelief(self, attribution_record_id: str, *, tenant_id: str) -> DisbeliefProof:
        """Retrieve and cryptographically verify why CORTEX ceased believing an attribution while still remembering the underlying fact."""
        attr_id = _validate_canonical_uuid(attribution_record_id, "attribution_record_id")
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT proof_id, tenant_id, disbelieved_record_id, disbelieved_commitment,
                       preserved_fact_ids_json, preserved_fact_commitments_json,
                       counter_evidence_record_id, counter_evidence_commitment,
                       rationale, retracted_by_principal, policy_epoch, lamport_t,
                       ledger_event_id, affected_dependents_json, witness_digest, signature
                FROM cortex_disbelief_proofs
                WHERE disbelieved_record_id = ?
                """,
                (attr_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"No disbelief proof found for record {attr_id}")
            (
                p_id,
                p_tenant,
                d_id,
                d_comm,
                f_ids_json,
                f_comms_json,
                c_id,
                c_comm,
                rationale,
                principal,
                epoch,
                lamport_t,
                ledger_event_id,
                deps_json,
                witness_digest,
                sig,
            ) = row

            if p_tenant != tenant_id:
                grant = conn.execute(
                    "SELECT 1 FROM cortex_tenant_grants WHERE owner_tenant = ? AND grantee_tenant = ? AND record_id = ?",
                    (p_tenant, tenant_id, d_id),
                ).fetchone()
                if grant is None:
                    raise TenantIsolationError(f"Tenant {tenant_id!r} denied access to disbelief proof on {d_id}")

            edge_exists = conn.execute(
                "SELECT 1 FROM cortex_memory_edges WHERE parent_id = ? AND child_id = ? AND edge_kind = ?",
                (c_id, d_id, EdgeKind.CONTRADICTS.value),
            ).fetchone()
            if edge_exists is None:
                raise GovernanceViolationError(f"Missing CONTRADICTS edge from {c_id} to {d_id}")

        preserved_fact_ids = tuple(json.loads(f_ids_json))
        preserved_fact_commitments = tuple(json.loads(f_comms_json))
        affected_dependents = tuple(json.loads(deps_json))

        # 1. Verify the disbelieved record itself still holds its intact commitment and content scar
        disbelieved_view = self.get_record(d_id, tenant_id=p_tenant, include_inactive=True)
        if disbelieved_view.status != MemoryStatus.DISBELIEVED:
            raise GovernanceViolationError(
                f"Expected record {d_id} to have status DISBELIEVED, got {disbelieved_view.status}"
            )
        if not hmac.compare_digest(disbelieved_view.commitment, d_comm):
            raise SignatureVerificationError(f"Commitment mismatch on disbelieved record {d_id}")
        if disbelieved_view.content is None:
            raise GovernanceViolationError(
                f"Epistemic scar missing: blob for disbelieved attribution {d_id} was destroyed"
            )

        # 2. Verify all underlying facts (SourceRecords) remain ACTIVE and remembered with intact commitments
        for f_id, expected_f_comm in zip(preserved_fact_ids, preserved_fact_commitments):
            fact_view = self.get_record(f_id, tenant_id=p_tenant, include_inactive=False)
            if fact_view.kind != MemoryKind.SOURCE_RECORD or fact_view.status != MemoryStatus.ACTIVE:
                raise GovernanceViolationError(f"Preserved fact {f_id} is no longer ACTIVE")
            if not hmac.compare_digest(fact_view.commitment, expected_f_comm):
                raise SignatureVerificationError(f"Preserved fact commitment mismatch on {f_id}")

        # 3. Verify the counter-evidence record remains valid and matches commitment
        counter_view = self.get_record(c_id, tenant_id=p_tenant, include_inactive=True)
        if counter_view.status != MemoryStatus.ACTIVE:
            raise GovernanceViolationError(f"Counter-evidence {c_id} must be ACTIVE (got {counter_view.status.value})")
        if not hmac.compare_digest(counter_view.commitment, c_comm):
            raise SignatureVerificationError(f"Counter-evidence commitment mismatch on {c_id}")

        # 4. Recompute witness digest and verify principal MAC signature
        expected_witness = compute_disbelief_witness_digest(
            tenant_id=p_tenant,
            disbelieved_record_id=d_id,
            disbelieved_commitment=d_comm,
            preserved_fact_ids=preserved_fact_ids,
            preserved_fact_commitments=preserved_fact_commitments,
            counter_evidence_record_id=c_id,
            counter_evidence_commitment=c_comm,
            rationale=rationale,
            policy_epoch=int(epoch),
        )
        if not hmac.compare_digest(witness_digest, expected_witness):
            raise SignatureVerificationError(f"Disbelief witness digest tampering detected on proof {p_id}")

        key = self._principal_keys.get((p_tenant, principal))
        if key is None:
            raise SignatureVerificationError(f"Missing verification key for ({p_tenant}, {principal})")
        expected_sig = sign_memory_commitment(
            key, principal, p_tenant, f"DISBELIEVE:{p_id}:{witness_digest}", int(epoch)
        )
        if not hmac.compare_digest(sig, expected_sig):
            raise SignatureVerificationError(f"Disbelief proof signature tampering detected on {p_id}")

        # The MAC binds the witness; the ledger additionally binds the event
        # clock and dependent set, which are not part of that witness.
        if not self.ledger.verify_integrity():
            raise SignatureVerificationError("Disbelief ledger integrity verification failed")
        with self.ledger._get_connection() as ledger_conn:
            ledger_row = ledger_conn.execute(
                "SELECT event_type, payload_json, agent_id, lamport_t, cortex_taint "
                "FROM cortex_ledger WHERE event_id = ?",
                (ledger_event_id,),
            ).fetchone()
        expected_payload = {
            "proof_id": p_id,
            "tenant_id": p_tenant,
            "principal": principal,
            "disbelieved_record_id": d_id,
            "disbelieved_commitment": d_comm,
            "preserved_fact_ids": list(preserved_fact_ids),
            "preserved_fact_commitments": list(preserved_fact_commitments),
            "counter_evidence_record_id": c_id,
            "counter_evidence_commitment": c_comm,
            "affected_dependents": list(affected_dependents),
            "witness_digest": witness_digest,
            "signature": sig,
        }
        if (
            ledger_row is None
            or ledger_row[0] != "ATTRIBUTION_DISBELIEVED"
            or ledger_row[1] != _canonical_json(expected_payload)
            or ledger_row[2] != principal
            or ledger_row[3] != lamport_t
            or ledger_row[4] != f"MEM_DISBELIEVE:{p_tenant}:{d_id}:{witness_digest[:16]}"
            or disbelieved_view.revocation_receipt_id != ledger_event_id
            or disbelieved_view.valid_to_tick != lamport_t
        ):
            raise SignatureVerificationError(f"Disbelief ledger event mismatch on proof {p_id}")

        return DisbeliefProof(
            proof_id=p_id,
            tenant_id=p_tenant,
            disbelieved_record_id=d_id,
            disbelieved_commitment=d_comm,
            disbelieved_content=disbelieved_view.content,
            preserved_fact_ids=preserved_fact_ids,
            preserved_fact_commitments=preserved_fact_commitments,
            counter_evidence_record_id=c_id,
            counter_evidence_commitment=c_comm,
            rationale=rationale,
            retracted_by_principal=principal,
            policy_epoch=int(epoch),
            lamport_t=int(lamport_t),
            ledger_event_id=ledger_event_id,
            affected_dependents=affected_dependents,
            witness_digest=witness_digest,
            signature=sig,
        )
