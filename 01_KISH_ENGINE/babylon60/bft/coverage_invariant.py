"""CORTEX Coverage Invariant — Sil silicon-enforced scope verification.

Materializes the BABYLON-60 principle that the LLM is not an authority:
- GUARD decides whether policy permits inspecting a target.
- The executor records per-target observed outcomes (including OS denials such
  as macOS EACCES/EPERM even when a wrapper process exits with code 0).
- CORTEX persists each decision and outcome in ``CortexPersistLedger`` and
  derives coverage deterministically from persisted records.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Sequence

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger


class CoverageViolationError(ValueError):
    """Raised when a report attempts to claim coverage beyond verified targets."""


class GuardDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class TargetStatus(str, Enum):
    VERIFIED = "VERIFIED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"


@dataclass(frozen=True)
class TargetOutcome:
    target: str
    guard_decision: GuardDecision
    status: TargetStatus
    process_exit_code: int
    errno_name: str | None
    evidence_digest: str | None
    detail: str


@dataclass(frozen=True)
class CoverageReport:
    check_id: str
    declared_targets: tuple[str, ...]
    verified_targets: tuple[str, ...]
    blocked_targets: tuple[str, ...]
    pending_targets: tuple[str, ...]
    outcomes: dict[str, TargetOutcome]
    is_complete: bool
    scoped_claim: str

    def assert_claim_allowed(self, claimed_targets: Sequence[str]) -> None:
        """Fail-closed gate: reject any claim covering unverified targets."""
        unverified = [t for t in claimed_targets if t not in self.verified_targets]
        if unverified:
            raise CoverageViolationError(
                f"Cannot claim coverage for unverified targets: {unverified} "
                f"(verified={len(self.verified_targets)}, "
                f"blocked={len(self.blocked_targets)}, "
                f"pending={len(self.pending_targets)})"
            )


class CoverageTracker:
    """Binds declared scope, GUARD decisions, and execution evidence in CORTEX."""

    def __init__(self, ledger: CortexPersistLedger, agent_id: str = "babylon60-executor") -> None:
        self._ledger = ledger
        self._agent_id = agent_id

    def declare_scope(self, check_id: str, targets: Sequence[str]) -> tuple[str, ...]:
        normalized = tuple(str(t) for t in targets)
        if not normalized:
            raise ValueError("declared_targets must not be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("declared_targets must not contain duplicates")
        event = CortexEvent(
            event_type="coverage.scope_declared",
            payload={"check_id": check_id, "declared_targets": list(normalized)},
            cortex_taint="ring0:coverage_scope",
            agent_id=self._agent_id,
            domain="coverage",
        )
        self._ledger.append_batch([event])
        return normalized

    def record_outcome(self, check_id: str, outcome: TargetOutcome) -> None:
        event = CortexEvent(
            event_type="coverage.target_outcome",
            payload={
                "check_id": check_id,
                "target": outcome.target,
                "guard_decision": outcome.guard_decision.value,
                "status": outcome.status.value,
                "process_exit_code": outcome.process_exit_code,
                "errno_name": outcome.errno_name,
                "evidence_digest": outcome.evidence_digest,
                "detail": outcome.detail,
            },
            cortex_taint=f"ring0:coverage_outcome:{outcome.status.value.lower()}",
            agent_id=self._agent_id,
            domain="coverage",
        )
        self._ledger.append_batch([event])

    def _fetch_all_events(self, event_type: str) -> list[dict[str, object]]:
        collected: list[dict[str, object]] = []
        before_seq: int | None = None
        for _ in range(10_000):
            page = self._ledger.query_events(
                event_type=event_type,
                limit=1000,
                before_seq=before_seq,
            )
            if not page:
                break
            collected.extend(page)
            if len(page) < 1000:
                break
            raw_seq = page[-1]["seq"]
            assert isinstance(raw_seq, int)
            before_seq = raw_seq
        else:
            raise RuntimeError(f"coverage event pagination exceeded bound for {event_type}")
        collected.reverse()  # chronological (oldest first)
        return collected

    def derive_report(self, check_id: str, claim_subject: str) -> CoverageReport:
        """Derive coverage strictly from persisted CORTEX ledger rows."""
        declared: tuple[str, ...] | None = None
        outcomes: dict[str, TargetOutcome] = {}

        for row in self._fetch_all_events("coverage.scope_declared"):
            payload = row.get("payload")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if isinstance(payload, dict) and payload.get("check_id") == check_id:
                declared = tuple(str(t) for t in payload["declared_targets"])
                break

        for row in self._fetch_all_events("coverage.target_outcome"):
            payload = row.get("payload")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict) or payload.get("check_id") != check_id:
                continue
            target = str(payload["target"])
            status = TargetStatus(payload["status"])
            digest = payload.get("evidence_digest")
            # A VERIFIED outcome without an evidence digest is invalid (fail-closed)
            if status == TargetStatus.VERIFIED and not digest:
                status = TargetStatus.PENDING
            outcomes[target] = TargetOutcome(
                target=target,
                guard_decision=GuardDecision(payload["guard_decision"]),
                status=status,
                process_exit_code=int(payload["process_exit_code"]),
                errno_name=payload.get("errno_name"),
                evidence_digest=digest,
                detail=str(payload.get("detail", "")),
            )

        if declared is None:
            raise ValueError(f"No declared scope found in CORTEX for check_id={check_id!r}")

        verified: list[str] = []
        blocked: list[str] = []
        pending: list[str] = []
        for target in declared:
            outcome = outcomes.get(target)
            if outcome is None or outcome.status == TargetStatus.PENDING:
                pending.append(target)
            elif outcome.status == TargetStatus.VERIFIED:
                verified.append(target)
            elif outcome.status == TargetStatus.BLOCKED:
                blocked.append(target)

        is_complete = len(verified) == len(declared) and not blocked and not pending
        if is_complete:
            scoped_claim = f"{claim_subject} en los {len(verified)} directorios leídos"
        else:
            scoped_claim = (
                f"{claim_subject} en los {len(verified)} directorios leídos "
                f"({len(blocked)} bloqueados, {len(pending)} pendientes)"
            )

        return CoverageReport(
            check_id=check_id,
            declared_targets=declared,
            verified_targets=tuple(verified),
            blocked_targets=tuple(blocked),
            pending_targets=tuple(pending),
            outcomes=outcomes,
            is_complete=is_complete,
            scoped_claim=scoped_claim,
        )


def scan_directories_with_partial_exit0(
    tracker: CoverageTracker,
    check_id: str,
    directories: Sequence[Path],
    guard_policy: Callable[[Path], GuardDecision] | None = None,
    project_marker: str = "pyproject.toml",
) -> tuple[int, dict[str, list[str]], CoverageReport]:
    """Run a real directory inventory in a child process that exits 0 even on EACCES.

    Demonstrates that process exit_code == 0 does not imply full coverage when the OS
    blocks one or more declared targets.
    """
    policy = guard_policy or (lambda _p: GuardDecision.ALLOW)
    declared = [str(d) for d in directories]
    tracker.declare_scope(check_id, declared)

    allowed_dirs: list[str] = []
    guard_decisions: dict[str, GuardDecision] = {}
    for d in directories:
        decision = policy(d)
        guard_decisions[str(d)] = decision
        if decision == GuardDecision.ALLOW:
            allowed_dirs.append(str(d))
        else:
            tracker.record_outcome(
                check_id,
                TargetOutcome(
                    target=str(d),
                    guard_decision=GuardDecision.DENY,
                    status=TargetStatus.BLOCKED,
                    process_exit_code=0,
                    errno_name="POLICY_DENIED",
                    evidence_digest=None,
                    detail="Denied by GUARD policy before OS execution",
                ),
            )

    # Real child process that inspects each allowed directory and catches PermissionError,
    # returning exit code 0 with per-target JSON records (classic silent partial exit 0).
    script = (
        "import errno, hashlib, json, os, sys\n"
        "marker = sys.argv[1]\n"
        "results = {}\n"
        "for target in sys.argv[2:]:\n"
        "    try:\n"
        "        with os.scandir(target) as it:\n"
        "            entries = sorted(e.name for e in it)\n"
        "        projects = [name for name in entries if name == marker]\n"
        "        digest = hashlib.sha256(json.dumps(entries).encode()).hexdigest()\n"
        "        results[target] = {'ok': True, 'projects': projects, 'digest': digest, 'errno': None, 'detail': 'read ok'}\n"
        "    except OSError as exc:\n"
        "        ename = errno.errorcode.get(exc.errno, 'OSERROR')\n"
        "        results[target] = {'ok': False, 'projects': [], 'digest': None, 'errno': ename, 'detail': str(exc)}\n"
        "print(json.dumps(results))\n"
    )

    proc = subprocess.run(
        [sys.executable, "-c", script, project_marker, *allowed_dirs],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Inventory helper failed unexpectedly: {proc.stderr}")

    parsed: dict[str, dict[str, Any]] = json.loads(proc.stdout) if allowed_dirs else {}
    found_projects: dict[str, list[str]] = {}

    for target_str in allowed_dirs:
        rec = parsed[target_str]
        if rec["ok"]:
            found_projects[target_str] = list(rec["projects"])
            tracker.record_outcome(
                check_id,
                TargetOutcome(
                    target=target_str,
                    guard_decision=guard_decisions[target_str],
                    status=TargetStatus.VERIFIED,
                    process_exit_code=proc.returncode,
                    errno_name=None,
                    evidence_digest=rec["digest"],
                    detail=rec["detail"],
                ),
            )
        else:
            tracker.record_outcome(
                check_id,
                TargetOutcome(
                    target=target_str,
                    guard_decision=guard_decisions[target_str],
                    status=TargetStatus.BLOCKED,
                    process_exit_code=proc.returncode,
                    errno_name=rec["errno"],
                    evidence_digest=None,
                    detail=rec["detail"],
                ),
            )

    claim_subject = (
        "cero proyectos"
        if sum(len(v) for v in found_projects.values()) == 0
        else f"{sum(len(v) for v in found_projects.values())} proyectos"
    )
    report = tracker.derive_report(check_id, claim_subject=claim_subject)
    return proc.returncode, found_projects, report


@dataclass(frozen=True)
class UnifiedAuditReport:
    """Combined CORTEX report binding BROKER routing attestations and GUARD/OS coverage."""

    check_id: str
    coverage: CoverageReport
    route_attestations: tuple[dict[str, object], ...]
    has_unconfirmed_effort: bool
    has_effort_mismatch: bool

    def to_summary_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "is_complete": self.coverage.is_complete,
            "scoped_claim": self.coverage.scoped_claim,
            "verified_count": len(self.coverage.verified_targets),
            "blocked_count": len(self.coverage.blocked_targets),
            "pending_count": len(self.coverage.pending_targets),
            "route_phases": len(self.route_attestations),
            "has_unconfirmed_effort": self.has_unconfirmed_effort,
            "has_effort_mismatch": self.has_effort_mismatch,
        }


def build_unified_audit_report(
    ledger: CortexPersistLedger,
    check_id: str,
    claim_subject: str,
) -> UnifiedAuditReport:
    """Derive a unified report from persisted CORTEX coverage and BROKER events."""
    from babylon60.cognitive_pilot.broker_policy import BrokerAttestationRecorder

    coverage = CoverageTracker(ledger).derive_report(check_id, claim_subject=claim_subject)
    attestations = tuple(BrokerAttestationRecorder(ledger).derive_route_attestations(check_id))
    has_unconfirmed_effort = any(not bool(item.get("effort_confirmed", False)) for item in attestations)
    has_effort_mismatch = any(bool(item.get("effort_mismatch", False)) for item in attestations)
    return UnifiedAuditReport(
        check_id=check_id,
        coverage=coverage,
        route_attestations=attestations,
        has_unconfirmed_effort=has_unconfirmed_effort,
        has_effort_mismatch=has_effort_mismatch,
    )
