# ============================================================================
# BABYLON-60 Swarm Extension
# █ VERIFICATION_GATE | Swarm Execution Causal Risk Gate & Safety Arbiter
# ============================================================================

from __future__ import annotations

import enum
import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

__all__ = ["RiskLevel", "AgentState", "CausalSignOffReceipt", "VerificationGate", "InterventionChannel"]


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

    def __init__(self, db_path: str = ":memory:", default_risk: RiskLevel = RiskLevel.LOW):
        self.db_path = db_path
        self.default_risk = default_risk
        self._conn = sqlite3.connect(self.db_path)
        self._init_db()

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
            conn.commit()

    def evaluate_task(self, task_payload: Dict[str, Any]) -> RiskLevel:
        """
        Evaluate task payload risk based on action type, mutability, and impact scope.
        """
        action = str(task_payload.get("action", "")).lower()
        command = str(task_payload.get("command", "")).lower()
        is_mutative = task_payload.get("is_mutative", False)

        if is_mutative or any(
            kw in action or kw in command for kw in ["deploy", "push", "purge", "rm", "delete", "format"]
        ):
            return RiskLevel.CRITICAL
        elif any(kw in action or kw in command for kw in ["patch", "refactor", "write", "commit", "update"]):
            return RiskLevel.HIGH
        elif any(kw in action or kw in command for kw in ["build", "test", "compile", "run"]):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def is_allowed(self, task_payload: Dict[str, Any]) -> bool:
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

        cur = self._conn.cursor()
        cur.execute(
            "SELECT decision FROM audit_ledger WHERE execution_id=? AND risk_level=? ORDER BY id DESC LIMIT 1",
            (exec_id, RiskLevel.CRITICAL.name),
        )
        row = cur.fetchone()
        return row is not None and row[0] == "APPROVED"

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

    def enforce_biometric_sign_off(self, execution_id: str, action_name: str, description: str) -> bool:
        """
        [C5-REAL] Invoca el Secure Enclave (TouchID) para atestar criptográficamente una cirugía causal.
        """
        import subprocess
        from pathlib import Path

        # Calcular un hash preliminar para atestar
        now = time.time()
        raw_pre_hash = f"{execution_id}|{action_name}|{now:.6f}"
        causal_hash = hashlib.sha256(raw_pre_hash.encode("utf-8")).hexdigest()

        script_path = Path(__file__).parent.parent / "guards" / "c5_biometric_gate"
        swift_script = Path(__file__).parent.parent / "guards" / "c5_biometric_gate.swift"

        if script_path.exists():
            cmd = [str(script_path), "--causal-hash", causal_hash, "--message", description]
        elif swift_script.exists():
            cmd = ["swift", str(swift_script), "--causal-hash", causal_hash, "--message", description]
        else:
            print(f"[!] Binario/script no encontrado: {script_path}")
            return False

        try:
            print(f"\n[🛡️ C5-REAL] Solicitando firma biométrica para: {action_name}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            signature = result.stdout.strip()
            print(f"[✓] Firma Biométrica obtenida: {signature}")

            # Registrar formalmente en el Ledger Inmutable
            self.register_sign_off(
                execution_id=execution_id,
                action_name=action_name,
                risk_level=RiskLevel.CRITICAL,
                decision="APPROVED",
                intervention_channel=InterventionChannel.HARD_SURGERY,
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"[X] Causal Sign-Off RECHAZADO o Timeout. Error: {e.stderr.strip()}")
            self.register_sign_off(
                execution_id=execution_id,
                action_name=action_name,
                risk_level=RiskLevel.CRITICAL,
                decision="REJECTED",
                intervention_channel=InterventionChannel.HARD_SURGERY,
            )
            return False

    def check_authorized_bifurcation(self, time_window_seconds: float = 300.0) -> bool:
        """
        [Frontera 2: Do-Calculus Surgery]
        Verifica si hay una autorización global y reciente de 'HARD_SURGERY' que justifique
        una mutación de la topología 1-WL.
        """
        threshold = time.time() - time_window_seconds
        cur = self._conn.cursor()
        cur.execute(
            "SELECT 1 FROM audit_ledger WHERE intervention_channel=? AND decision='APPROVED' AND timestamp >= ? LIMIT 1",
            (InterventionChannel.HARD_SURGERY.value, threshold),
        )
        return cur.fetchone() is not None

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
