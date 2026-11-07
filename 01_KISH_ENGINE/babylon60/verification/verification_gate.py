# ============================================================================
# BABYLON-60 Swarm Extension
# █ VERIFICATION_GATE | Swarm Execution Causal Risk Gate & Safety Arbiter
# ============================================================================

from __future__ import annotations

import enum
import hashlib
import json
import sqlite3
import secrets
import subprocess
from pathlib import Path
import time
from collections.abc import Mapping
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict, Optional
from typing import TypeVar

from .hardware_attestation import configured_public_key, request_attestation, verify_attestation
from .moloch_landauer_gate import ActionClass, AgentAction, MolochLandauerGate, SettlementReceipt, is_moloch_extraction

__all__ = ["RiskLevel", "AgentState", "CausalSignOffReceipt", "VerificationGate", "InterventionChannel"]

EffectResult = TypeVar("EffectResult")


def _action_integer(value: object) -> int:
    """Convert scalar action fields, rejecting containers and opaque objects."""
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        raise ValueError("Action integer fields require scalar values")
    return int(value)


class InterventionChannel(enum.Enum):
    SOFT_BAYESIAN = "SOFT_BAYESIAN"  # Update paramétrico, métrica de Fisher preservada, topología WL intacta
    HARD_SURGERY = "HARD_SURGERY"  # Mutación do-calculus, topología WL bifurcada (requiere reset de MerklePulse)


class RiskLevel(enum.Enum):
    LOW = enum.auto()
    MEDIUM = enum.auto()
    HIGH = enum.auto()
    CRITICAL = enum.auto()


class AgentState(enum.Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED_AWAITING_SIGN_OFF = "PAUSED_AWAITING_SIGN_OFF"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


@dataclass
class CausalSignOffReceipt:
    execution_id: str
    action_name: str
    risk_level: RiskLevel
    intervention_channel: InterventionChannel
    decision: str
    timestamp: float
    prev_digest: str
    cryptographic_digest: str


class VerificationGate:
    """
    SOTA Causal Risk Evaluation & Safety Arbiter for Autonomous Swarms.
    Conforme a RULE[human_in_the_loop_causal_governance] y RULE[c5_real_invariants].
    """

    def __init__(self, db_path: str = ":memory:", default_risk: RiskLevel = RiskLevel.LOW) -> None:
        self.db_path = db_path
        self.default_risk = default_risk
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = FULL")
        self._trusted_key: bytes | None
        try:
            self._trusted_key = configured_public_key()
        except ValueError:
            self._trusted_key = None
        self._init_db()
        self.moloch_gate = MolochLandauerGate()

    def _init_db(self) -> None:
        with self._conn as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    execution_id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    current_step INTEGER NOT NULL,
                    state_status TEXT NOT NULL,
                    pending_action TEXT,
                    payload JSON NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    intervention_channel TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    prev_digest TEXT NOT NULL,
                    cryptographic_digest TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signed_approvals (
                    ledger_id INTEGER PRIMARY KEY REFERENCES audit_ledger(id),
                    payload TEXT NOT NULL, evidence TEXT NOT NULL
                )
            """)
            conn.commit()

    def evaluate_task(self, task_payload: Mapping[str, object]) -> RiskLevel:
        """
        Evaluate task payload risk based on action type, mutability, and impact scope.
        """
        # Evaluar si el payload contiene especificación de acción de agente (anti-Moloch)
        if isinstance(task_payload, Mapping) and "action_class" in task_payload:
            try:
                act = AgentAction(
                    agent_id=_action_integer(task_payload.get("agent_id", 0)),
                    action_class=ActionClass(str(task_payload["action_class"])),
                    claimed_benefit=_action_integer(task_payload.get("claimed_benefit", 0)),
                    internal_dissipation=_action_integer(task_payload.get("internal_dissipation", 0)),
                    externalized_entropy=_action_integer(task_payload.get("externalized_entropy", 0)),
                )
                if is_moloch_extraction(act) or self.moloch_gate.is_poisoned(act.agent_id):
                    return RiskLevel.CRITICAL
            except (ValueError, OverflowError, KeyError):
                return RiskLevel.CRITICAL

        # Only registered operations can bypass signed approval. A caller's
        # label or a substring in an arbitrary command is not an authority.
        action = task_payload.get("action")
        if not isinstance(action, str) or task_payload.get("is_mutative", False) is not False:
            return RiskLevel.CRITICAL
        if task_payload.get("command") not in (None, ""):
            return RiskLevel.CRITICAL
        known_operations = {
            "read": RiskLevel.LOW,
            "read_records": RiskLevel.LOW,
            "build": RiskLevel.MEDIUM,
            "test": RiskLevel.MEDIUM,
            "compile": RiskLevel.MEDIUM,
            "run_build_test": RiskLevel.MEDIUM,
            "patch": RiskLevel.HIGH,
            "refactor": RiskLevel.HIGH,
            "write": RiskLevel.HIGH,
            "commit": RiskLevel.HIGH,
            "update": RiskLevel.HIGH,
            "apply_code_patch": RiskLevel.HIGH,
        }
        return known_operations.get(action.lower(), RiskLevel.CRITICAL)

    def is_allowed(self, task_payload: Mapping[str, object]) -> bool:
        """
        Check if task execution is authorized under Causal Gate governance.
        Tasks with CRITICAL risk require a valid APPROVED sign-off receipt in the ledger.
        """
        risk = self.evaluate_task(task_payload)
        if risk != RiskLevel.CRITICAL:
            return True

        exec_id = task_payload.get("execution_id")
        if not exec_id:
            return False

        if self._trusted_key is None:
            return False
        row = self._conn.execute(
            "SELECT a.decision, s.payload, s.evidence FROM audit_ledger a "
            "LEFT JOIN signed_approvals s ON s.ledger_id=a.id "
            "WHERE a.execution_id=? AND a.risk_level=? ORDER BY a.id DESC LIMIT 1",
            (exec_id, RiskLevel.CRITICAL.name),
        ).fetchone()
        if row is None or row[0] != "APPROVED" or row[1] is None:
            return False
        try:
            verify_attestation(row[1].encode("utf-8"), row[2], self._trusted_key)
            proof = json.loads(row[1])
            now = time.time()
            return (
                proof["version"] == 1
                and proof["decision"] == "APPROVED"
                and proof["issued_at"] <= now < proof["expires_at"]
                and 0 < proof["expires_at"] - proof["issued_at"] <= 300
                and self._canonical_task(proof["task"]) == self._canonical_task(task_payload)
            )
        except (ValueError, TypeError, KeyError):
            return False

    def evaluate_and_settle_agent_action(self, action: AgentAction) -> SettlementReceipt:
        """
        Evalúa y liquida una acción de agente bajo la micro-economía de balance de Landauer.
        """
        return self.moloch_gate.evaluate_and_settle(action)

    def execute_once(
        self,
        task_payload: Mapping[str, object],
        effect: Callable[[], EffectResult],
    ) -> EffectResult:
        """Consume signed approval durably and serialize revocation with effect.

        A crash/exception after consumption does not permit retry. The second
        transaction keeps approval writers out until the effect returns.
        The caller must hold its policy lock for this entire operation.
        """
        if self.evaluate_task(task_payload) != RiskLevel.CRITICAL:
            raise PermissionError("Effect dispatch requires a signed critical task")
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            if not self.is_allowed(task_payload):
                raise PermissionError("Operator approval is not currently valid")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS consumed_mcp_effects (execution_id TEXT PRIMARY KEY NOT NULL)"
            )
            self._conn.execute("INSERT INTO consumed_mcp_effects VALUES (?)", (task_payload["execution_id"],))
            self._conn.commit()  # synchronous=FULL: consumption survives a crash.
            self._conn.execute("BEGIN IMMEDIATE")
            if not self.is_allowed(task_payload):
                raise PermissionError("Operator approval changed before effect")
            return effect()
        except sqlite3.IntegrityError as exc:
            raise PermissionError("MCP execution_id has already been consumed") from exc
        finally:
            self._conn.rollback()

    @staticmethod
    def _canonical_task(task: object) -> str:
        if not isinstance(task, Mapping) or not task.get("execution_id") or not task.get("action"):
            raise ValueError("Authorization requires the complete task, execution_id and action")
        return json.dumps(dict(task), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    def register_sign_off(
        self,
        execution_id: str,
        action_name: str,
        risk_level: RiskLevel,
        decision: str,
        intervention_channel: InterventionChannel = InterventionChannel.SOFT_BAYESIAN,
    ) -> CausalSignOffReceipt:
        """
        Record an operator sign-off decision into the SHA-256 SCITT tamper-evident ledger.
        """
        cur = self._conn.cursor()
        cur.execute("SELECT cryptographic_digest FROM audit_ledger ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        prev_digest = row[0] if row else "0" * 64

        now = time.time()
        raw_data = f"{execution_id}|{action_name}|{risk_level.name}|{intervention_channel.value}|{decision}|{now:.6f}|{prev_digest}"
        digest = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

        with self._conn as conn:
            conn.execute(
                """
                INSERT INTO audit_ledger (execution_id, action_name, risk_level, intervention_channel, decision, timestamp, prev_digest, cryptographic_digest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    execution_id,
                    action_name,
                    risk_level.name,
                    intervention_channel.value,
                    decision,
                    now,
                    prev_digest,
                    digest,
                ),
            )
            conn.commit()

        return CausalSignOffReceipt(
            execution_id=execution_id,
            action_name=action_name,
            risk_level=risk_level,
            intervention_channel=intervention_channel,
            decision=decision,
            timestamp=now,
            prev_digest=prev_digest,
            cryptographic_digest=digest,
        )

    def enforce_biometric_sign_off(
        self,
        execution_id: str,
        action_name: str,
        description: str,
        *,
        task_payload: Mapping[str, object] | None = None,
    ) -> bool:
        """Authorize one exact request using a pinned key, never a ledger label."""
        if self._trusted_key is None or task_payload is None:
            return False
        if task_payload.get("execution_id") != execution_id or task_payload.get("action") != action_name:
            return False
        try:
            task = json.loads(self._canonical_task(task_payload))
            now = time.time()
            proof = json.dumps(
                {
                    "version": 1,
                    "task": task,
                    "decision": "APPROVED",
                    "nonce": secrets.token_hex(32),
                    "issued_at": now,
                    "expires_at": now + 300,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            base = Path(__file__).parent.parent / "guards"
            gate = base / "c5_biometric_gate"
            if not gate.is_file():
                gate = base / "c5_biometric_gate.swift"
            evidence = request_attestation(proof.encode("utf-8"), gate, action_name, description, self._trusted_key)
            self.register_sign_off(
                execution_id, action_name, RiskLevel.CRITICAL, "APPROVED", InterventionChannel.HARD_SURGERY
            )
            ledger_id = self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            with self._conn:
                self._conn.execute("INSERT INTO signed_approvals VALUES (?, ?, ?)", (ledger_id, proof, evidence))
            return self.is_allowed(task_payload)
        except (OSError, ValueError, TypeError, subprocess.SubprocessError):
            self.register_sign_off(
                execution_id, action_name, RiskLevel.CRITICAL, "REJECTED", InterventionChannel.HARD_SURGERY
            )
            return False

    def check_authorized_bifurcation(
        self,
        time_window_seconds: float = 300.0,
        *,
        task_payload: Mapping[str, object] | None = None,
    ) -> bool:
        """A recent approval for an unrelated task is never a global permission."""
        if task_payload is None or self.evaluate_task(task_payload) != RiskLevel.CRITICAL:
            return False
        row = self._conn.execute(
            "SELECT timestamp FROM audit_ledger WHERE execution_id=? ORDER BY id DESC LIMIT 1",
            (task_payload.get("execution_id"),),
        ).fetchone()
        return bool(
            row
            and time.time() - min(time_window_seconds, 300) <= row[0] <= time.time()
            and self.is_allowed(task_payload)
        )

    def save_snapshot(
        self,
        execution_id: str,
        domain: str,
        step: int,
        status: AgentState,
        pending_action: Optional[str],
        payload: Dict[str, Any],
    ) -> None:
        """
        Persist execution state snapshot to WAL buffer for non-blocking pause/resume.
        """
        now = time.time()
        with self._conn as conn:
            conn.execute(
                """
                INSERT INTO state_snapshots (execution_id, domain, current_step, state_status, pending_action, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(execution_id) DO UPDATE SET
                    current_step=excluded.current_step,
                    state_status=excluded.state_status,
                    pending_action=excluded.pending_action,
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
            """,
                (execution_id, domain, step, status.value, pending_action, json.dumps(payload), now, now),
            )
            conn.commit()

    def load_snapshot(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Load active execution state snapshot for resumption.
        """
        cur = self._conn.cursor()
        cur.execute(
            "SELECT domain, current_step, state_status, pending_action, payload FROM state_snapshots WHERE execution_id=?",
            (execution_id,),
        )
        row = cur.fetchone()
        if row:
            return {
                "domain": row[0],
                "current_step": row[1],
                "status": AgentState(row[2]),
                "pending_action": row[3],
                "payload": json.loads(row[4]),
            }
        return None

    def verify_ledger_integrity(self) -> bool:
        """
        Verify Merkle hash chain integrity across all recorded SCITT audit ledger blocks.
        """
        cur = self._conn.cursor()
        cur.execute(
            "SELECT execution_id, action_name, risk_level, intervention_channel, decision, timestamp, prev_digest, cryptographic_digest FROM audit_ledger ORDER BY id ASC"
        )
        rows = cur.fetchall()
        expected_prev = "0" * 64
        for r in rows:
            exec_id, action, risk, channel, dec, ts, prev_d, digest = r
            if prev_d != expected_prev:
                return False
            raw_data = f"{exec_id}|{action}|{risk}|{channel}|{dec}|{ts:.6f}|{prev_d}"
            calc_digest = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
            if calc_digest != digest:
                return False
            expected_prev = digest
        return True
