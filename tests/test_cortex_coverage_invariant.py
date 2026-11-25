"""Acceptance tests for the CORTEX Coverage Invariant (no mocks, real SQLite + OS)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.bft.coverage_invariant import (
    CoverageTracker,
    CoverageViolationError,
    GuardDecision,
    TargetOutcome,
    TargetStatus,
    build_unified_audit_report,
    scan_directories_with_partial_exit0,
)
from babylon60.cognitive_pilot.broker_policy import (
    BrokerAttestationRecorder,
    recommend_phase_effort,
)
from babylon60.cognitive_pilot.execution import Provider


def test_partial_exit0_macos_denial_records_three_verified_one_blocked(tmp_path: Path) -> None:
    """GUARD allows 4 dirs; macOS denies the 4th while the scanner exits 0."""
    if os.geteuid() == 0:
        pytest.skip("chmod 000 does not deny root reads")

    dirs = [tmp_path / f"dir_{i}" for i in range(1, 5)]
    for d in dirs:
        d.mkdir()
        (d / "notes.txt").write_text("empty\n", encoding="utf-8")

    blocked_dir = dirs[3]
    os.chmod(blocked_dir, 0o000)

    ledger = CortexPersistLedger(tmp_path / "cortex_coverage.db")
    tracker = CoverageTracker(ledger)

    try:
        exit_code, found_projects, report = scan_directories_with_partial_exit0(
            tracker=tracker,
            check_id="chk-macos-partial-001",
            directories=dirs,
            guard_policy=lambda _p: GuardDecision.ALLOW,
        )
    finally:
        os.chmod(blocked_dir, 0o755)

    # Exit 0 alone must never be treated as full coverage.
    assert exit_code == 0
    assert found_projects == {str(d): [] for d in dirs[:3]}

    assert report.is_complete is False
    assert len(report.verified_targets) == 3
    assert len(report.blocked_targets) == 1
    assert len(report.pending_targets) == 0
    assert report.blocked_targets == (str(blocked_dir),)

    blocked_outcome = report.outcomes[str(blocked_dir)]
    assert blocked_outcome.guard_decision == GuardDecision.ALLOW
    assert blocked_outcome.status == TargetStatus.BLOCKED
    assert blocked_outcome.errno_name in {"EACCES", "EPERM"}
    assert blocked_outcome.evidence_digest is None

    assert report.scoped_claim.startswith("cero proyectos en los 3 directorios leídos")

    # Claiming all 4 targets must fail closed; claiming only the 3 verified targets succeeds.
    with pytest.raises(CoverageViolationError):
        report.assert_claim_allowed([str(d) for d in dirs])

    report.assert_claim_allowed(report.verified_targets)


def test_full_coverage_when_all_four_directories_readable(tmp_path: Path) -> None:
    dirs = [tmp_path / f"dir_{i}" for i in range(1, 5)]
    for d in dirs:
        d.mkdir()

    ledger = CortexPersistLedger(tmp_path / "cortex_full.db")
    tracker = CoverageTracker(ledger)

    exit_code, _found, report = scan_directories_with_partial_exit0(
        tracker=tracker,
        check_id="chk-full-002",
        directories=dirs,
    )

    assert exit_code == 0
    assert report.is_complete is True
    assert len(report.verified_targets) == 4
    assert len(report.blocked_targets) == 0
    assert len(report.pending_targets) == 0
    assert report.scoped_claim == "cero proyectos en los 4 directorios leídos"
    report.assert_claim_allowed([str(d) for d in dirs])


def test_missing_outcome_or_missing_digest_stays_pending_and_blocks_claim(tmp_path: Path) -> None:
    dirs = [str(tmp_path / f"dir_{i}") for i in range(1, 5)]
    ledger = CortexPersistLedger(tmp_path / "cortex_pending.db")
    tracker = CoverageTracker(ledger)

    tracker.declare_scope("chk-pending-003", dirs)
    # Two verified with real digest, one claiming VERIFIED without digest, one omitted.
    for d in dirs[:2]:
        tracker.record_outcome(
            "chk-pending-003",
            TargetOutcome(
                target=d,
                guard_decision=GuardDecision.ALLOW,
                status=TargetStatus.VERIFIED,
                process_exit_code=0,
                errno_name=None,
                evidence_digest="a" * 64,
                detail="ok",
            ),
        )
    tracker.record_outcome(
        "chk-pending-003",
        TargetOutcome(
            target=dirs[2],
            guard_decision=GuardDecision.ALLOW,
            status=TargetStatus.VERIFIED,
            process_exit_code=0,
            errno_name=None,
            evidence_digest=None,
            detail="missing digest must downgrade to pending",
        ),
    )

    report = tracker.derive_report("chk-pending-003", claim_subject="cero proyectos")
    assert report.is_complete is False
    assert report.verified_targets == tuple(dirs[:2])
    assert report.pending_targets == tuple(dirs[2:])
    with pytest.raises(CoverageViolationError):
        report.assert_claim_allowed(dirs)


def test_unified_audit_report_combines_broker_and_partial_coverage(tmp_path: Path) -> None:
    if os.geteuid() == 0:
        pytest.skip("chmod 000 does not deny root reads")

    dirs = [tmp_path / f"dir_{i}" for i in range(1, 5)]
    for d in dirs:
        d.mkdir()
    os.chmod(dirs[3], 0o000)

    ledger = CortexPersistLedger(tmp_path / "unified_audit.db")
    check_id = "chk-unified-004"

    provider = Provider(
        {
            "backend": "gemini_compat",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "model": "gemini-4-hydrogen",
            "reasoning_effort": "low",
            "max_tokens": 4096,
            "max_calls": 4,
            "timeout": 10.0,
            "temperature": 0.0,
            "memory_bytes": 4096,
        }
    )
    provider._consume(
        {
            "id": "resp-unified-1",
            "model": "gemini-4-hydrogen",
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
            "choices": [{"message": {"content": '{"action": "final"}'}}],
        }
    )

    rec = recommend_phase_effort("phase-scan", "triage")
    BrokerAttestationRecorder(ledger).record_phase_route(check_id, rec, provider.observations[0])

    try:
        exit_code, _found, _cov = scan_directories_with_partial_exit0(
            tracker=CoverageTracker(ledger),
            check_id=check_id,
            directories=dirs,
        )
    finally:
        os.chmod(dirs[3], 0o755)

    assert exit_code == 0
    unified = build_unified_audit_report(ledger, check_id=check_id, claim_subject="cero proyectos")
    summary = unified.to_summary_dict()

    assert summary == {
        "check_id": check_id,
        "is_complete": False,
        "scoped_claim": "cero proyectos en los 3 directorios leídos (1 bloqueados, 0 pendientes)",
        "verified_count": 3,
        "blocked_count": 1,
        "pending_count": 0,
        "route_phases": 1,
        "has_unconfirmed_effort": True,
        "has_effort_mismatch": False,
    }


def test_ledger_readers_page_past_1000_events_in_chronological_order(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "cortex_paging.db")
    # 2001 rows: two full pages and a partial one.
    ledger.append_batch(
        [
            CortexEvent(
                event_type="broker.route_attestation",
                payload={"check_id": "chk-paging", "n": n},
                cortex_taint="ring0:test_paging",
            )
            for n in range(2001)
        ]
    )
    attestations = BrokerAttestationRecorder(ledger).derive_route_attestations("chk-paging")
    assert [row["n"] for row in attestations] == list(range(2001))

    # Exactly one full page: the reader must ask once more and stop on the empty page.
    ledger.append_batch(
        [
            CortexEvent(event_type="coverage.target_outcome", payload={"n": n}, cortex_taint="ring0:test_paging")
            for n in range(1000)
        ]
    )
    rows = CoverageTracker(ledger)._fetch_all_events("coverage.target_outcome")
    assert [row["payload"] for row in rows] == [{"n": n} for n in range(1000)]
