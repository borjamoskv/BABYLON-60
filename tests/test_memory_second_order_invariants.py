# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Second-Order Structural, Causal & Adversarial Invariant Oracles for Memory & Governance."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pytest

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.memory.governance import (
    GovernanceViolationError,
    MemoryGovernanceEngine,
    MemoryKind,
    MemoryStatus,
    TenantIsolationError,
    TrustLevel,
)
from babylon60.memory.learning import SkillLearning
from babylon60.memory.metamemory import MemoryCard, MetamemoryMonitor
from babylon60.memory.procedural import ProceduralMemory


@dataclass
class _CandidateSurface:
    name: str
    _fok_surface: str
    striatal_value: float | None = None


@pytest.fixture
def engine(tmp_path: Path) -> MemoryGovernanceEngine:
    db_file = tmp_path / "memory_second_order.db"
    eng = MemoryGovernanceEngine(db_file)
    eng.register_principal_key("tenant-alpha", "operator-root", b"sovereign-root-secret-key-0001")
    eng.register_principal_key("tenant-alpha", "agent-worker", b"worker-agent-secret-key-000002")
    eng.register_principal_key("tenant-beta", "beta-admin", b"beta-tenant-secret-key-0000004")
    return eng


def test_o_mem_1_retract_attribution_is_single_atomic_transaction_and_blocks_orphan_ledger_events(
    engine: MemoryGovernanceEngine,
) -> None:
    """O-MEM-1: retract_attribution executes atomically with shared connection and rejects invalid proof_id without orphan events."""
    fact = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Raw sensor fact: temperature 88C",
        kind=MemoryKind.SOURCE_RECORD,
        trust_level=TrustLevel.SOVEREIGN,
    )
    attr = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Inference: fan failure caused 88C",
        kind=MemoryKind.INFERENCE,
        parents=[fact.record_id],
        trust_level=TrustLevel.PUBLIC,
    )
    dep = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Action: replace fan unit",
        kind=MemoryKind.IDEA_THREAD,
        depends_on=[attr.record_id],
        trust_level=TrustLevel.PUBLIC,
    )
    counter = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Tachometer telemetry: fan spinning at 4200 RPM nominal",
        kind=MemoryKind.SOURCE_RECORD,
        trust_level=TrustLevel.SOVEREIGN,
    )

    proof = engine.retract_attribution(
        attribution_record_id=attr.record_id,
        counter_evidence_record_id=counter.record_id,
        tenant_id="tenant-alpha",
        principal="operator-root",
        rationale="Fan RPM nominal refutes fan failure attribution",
    )
    assert proof.affected_dependents == (dep.record_id,)
    dep_view = engine.get_record(dep.record_id, tenant_id="tenant-alpha", include_inactive=True)
    assert dep_view.status == MemoryStatus.DISBELIEVED_DEPENDENCY

    # Attempting a second retraction on an already-disbelieved attribution must fail before writing any new ledger event
    events_before = len(engine.ledger.query_events(event_type="ATTRIBUTION_DISBELIEVED"))
    with pytest.raises(GovernanceViolationError, match="ACTIVE"):
        engine.retract_attribution(
            attribution_record_id=attr.record_id,
            counter_evidence_record_id=counter.record_id,
            tenant_id="tenant-alpha",
            principal="operator-root",
            rationale="Duplicate retraction attempt",
        )
    assert len(engine.ledger.query_events(event_type="ATTRIBUTION_DISBELIEVED")) == events_before


def test_o_mem_2_add_record_rejects_inverted_ticks_duplicate_uuid_and_self_superseded_parent(
    tmp_path: Path,
) -> None:
    """O-MEM-2: add_record enforces valid temporal windows, pre-ledger duplicate UUID rejection, and blocks deriving from a self-superseded parent."""
    shared_ledger = CortexPersistLedger(tmp_path / "gov.db")
    eng = MemoryGovernanceEngine(tmp_path / "gov.db", ledger=shared_ledger)
    eng.register_principal_key("tenant-alpha", "operator-root", b"sovereign-root-secret-key-0001")

    # 1. Inverted temporal window [100, 50) rejected without polluting shared WORM ledger
    with pytest.raises(GovernanceViolationError, match="valid_to_tick"):
        eng.add_record(
            tenant_id="tenant-alpha",
            principal="operator-root",
            content="Inverted temporal validity window",
            valid_from_tick=100,
            valid_to_tick=50,
        )
    assert shared_ledger.query_events() == []

    # 2. valid_to_tick <= transaction tick when valid_from_tick is omitted
    with pytest.raises(GovernanceViolationError, match="valid_to_tick"):
        eng.add_record(
            tenant_id="tenant-alpha",
            principal="operator-root",
            content="Already expired at birth",
            valid_to_tick=1,
        )
    assert shared_ledger.query_events() == []

    # 3. Duplicate UUID rejected before appending to shared WORM ledger
    fixed_id = "11111111-2222-4333-8444-555555555555"
    first = eng.add_record(
        record_id=fixed_id,
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Original record on fixed UUID",
        subject_key="config.endpoint",
        trust_level=TrustLevel.PUBLIC,
    )
    committed_count = len(shared_ledger.query_events(event_type="MEMORY_RECORD_COMMITTED"))
    assert committed_count == 1

    with pytest.raises(GovernanceViolationError, match="Duplicate record_id"):
        eng.add_record(
            record_id=fixed_id,
            tenant_id="tenant-alpha",
            principal="operator-root",
            content="Conflicting record on same UUID",
        )
    assert len(shared_ledger.query_events(event_type="MEMORY_RECORD_COMMITTED")) == committed_count

    # 4. Self-supersession dependency paradox: cannot derive from a record that the same subject_key update marks STALE
    with pytest.raises(GovernanceViolationError, match="simultaneously superseded"):
        eng.add_record(
            tenant_id="tenant-alpha",
            principal="operator-root",
            content="Superseding config that also claims DERIVES_FROM on the superseded record",
            subject_key="config.endpoint",
            trust_level=TrustLevel.SOVEREIGN,
            parents=[first.record_id],
        )
    assert len(shared_ledger.query_events(event_type="MEMORY_RECORD_COMMITTED")) == committed_count


def test_o_mem_3_revocation_purges_cross_tenant_grants_and_disbelieved_summary_cannot_rebuild(
    engine: MemoryGovernanceEngine,
) -> None:
    """O-MEM-3: Revoking a record purges cross-tenant grants, inactive records cannot be granted, and disbelieved summaries cannot be rebuilt."""
    fact = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Shared telemetry fact",
        kind=MemoryKind.SOURCE_RECORD,
        subject_key="shared.fact",
        trust_level=TrustLevel.SOVEREIGN,
    )
    engine.grant_cross_tenant_read(
        owner_tenant="tenant-alpha",
        grantee_tenant="tenant-beta",
        record_id=fact.record_id,
        principal="operator-root",
    )
    assert engine.get_record(fact.record_id, tenant_id="tenant-beta").record_id == fact.record_id

    engine.revoke_record(record_id=fact.record_id, tenant_id="tenant-alpha", principal="operator-root")

    # Cross-tenant grant row must be purged upon revocation
    with sqlite3.connect(engine.db_path) as conn:
        grant_row = conn.execute(
            "SELECT 1 FROM cortex_tenant_grants WHERE record_id = ?",
            (fact.record_id,),
        ).fetchone()
        assert grant_row is None

    with pytest.raises(TenantIsolationError):
        engine.get_record(fact.record_id, tenant_id="tenant-beta", include_inactive=True)

    # Granting cross-tenant read on a non-active record is rejected
    with pytest.raises(GovernanceViolationError, match="non-active"):
        engine.grant_cross_tenant_read(
            owner_tenant="tenant-alpha",
            grantee_tenant="tenant-beta",
            record_id=fact.record_id,
            principal="operator-root",
        )

    # Disbelieved summary cannot be certified or rebuilt via certify_or_rebuild_summary
    base_fact = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Base fact for summary",
        kind=MemoryKind.SOURCE_RECORD,
        subject_key="summary.base",
        trust_level=TrustLevel.SOVEREIGN,
    )
    bad_summary = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Hallucinated summary attribution",
        kind=MemoryKind.IDEA_THREAD,
        subject_key="summary.thread",
        parents=[base_fact.record_id],
        trust_level=TrustLevel.PUBLIC,
    )
    refutation = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Counter-evidence refuting summary",
        kind=MemoryKind.SOURCE_RECORD,
        trust_level=TrustLevel.SOVEREIGN,
    )
    engine.retract_attribution(
        attribution_record_id=bad_summary.record_id,
        counter_evidence_record_id=refutation.record_id,
        tenant_id="tenant-alpha",
        principal="operator-root",
        rationale="Summary attribution falsified",
    )

    with pytest.raises(GovernanceViolationError, match="invalidated"):
        engine.certify_or_rebuild_summary(
            summary_id=bad_summary.record_id,
            tenant_id="tenant-alpha",
            principal="agent-worker",
            synthesizer=lambda recs: "Rebuilt: " + " | ".join(r.content or "" for r in recs),
        )


def test_o_mem_4_metamemory_fok_tip_of_tongue_epistemic_cards_and_in_memory_attempt_idempotency() -> None:
    """O-MEM-4: judge_procedural_fok reaches tip_of_tongue on weak/degraded matches, evaluate_epistemic_context weights existence/repair, and in-memory record_outcome enforces attempt_id idempotency."""
    monitor = MetamemoryMonitor()

    # 1. Degraded procedural candidate (striatal_value=0.25) triggers tip_of_tongue=True
    degraded = _CandidateSurface(
        name=" audit-kernel ",
        _fok_surface="audit kernel invariants memory",
        striatal_value=0.25,
    )
    fok_res = monitor.judge_procedural_fok("audit kernel invariants", [degraded])
    assert fok_res.fok_score == pytest.approx(0.25)
    assert fok_res.tip_of_tongue is True
    assert len(fok_res.relevance_matches) == 1

    # 2. Epistemic context weights existence_probability and repair_needed and rejects NaN
    corrupted_card = MemoryCard(
        memory_id="card-zero-existence",
        retrieval_confidence=0.95,
        existence_probability=0.0,
        consolidation_status="REVOKED",
        repair_needed=True,
    )
    meta_res = monitor.evaluate_epistemic_context("verify context", [corrupted_card])
    assert meta_res.confidence == pytest.approx(0.0)
    assert meta_res.tip_of_tongue is True
    assert meta_res.relevance_matches == []

    with pytest.raises(ValueError, match="existence_probability"):
        monitor.evaluate_epistemic_context(
            "nan check",
            [MemoryCard(memory_id="bad", retrieval_confidence=0.9, existence_probability=float("nan"))],
        )

    # 3. In-memory record_outcome enforces attempt_id idempotency and conflict rejection
    monitor.record_outcome("verify", False, context="mem", attempt_id="att-1")
    monitor.record_outcome("verify", False, context="mem", attempt_id="att-1")
    assert monitor.get_feeling_of_knowing("verify", context="mem") == pytest.approx(0.75)

    with pytest.raises(ValueError, match="attempt_id"):
        monitor.record_outcome("verify", True, context="mem", attempt_id="att-1")


def test_o_mem_5_skill_learning_rejects_post_failure_contaminated_held_out_session_and_cross_lesson_attempt_id(
    tmp_path: Path,
) -> None:
    """O-MEM-5: A session used for practice or failed before a window reset cannot be reused as held-out after the failure, and attempt_id is globally unique across lessons."""
    service = SkillLearning(CortexPersistLedger(tmp_path / "learning.db"))
    service.propose_lesson(
        lesson_id="lesson-a",
        skill_id="verification",
        context="code",
        procedure="Verify invariants before commit.",
        cortex_taint="taint-a",
    )
    service.propose_lesson(
        lesson_id="lesson-b",
        skill_id="verification",
        context="rust",
        procedure="Run cargo test --locked.",
        cortex_taint="taint-b",
    )

    # Practice in session-1 before failure
    service.record_attempt(
        lesson_id="lesson-a",
        attempt_id="a-1",
        variant_id="var-1",
        session_id="session-1",
        success=True,
        held_out=False,
        evidence={"validator": "pytest", "reference": "r1", "passed": True},
        cortex_taint="t",
    )
    # Fail in session-2 (resets validation window)
    service.record_attempt(
        lesson_id="lesson-a",
        attempt_id="a-2",
        variant_id="var-2",
        session_id="session-2",
        success=False,
        held_out=False,
        evidence={"validator": "pytest", "reference": "r2", "passed": False},
        cortex_taint="t",
    )
    # Post-failure practice in session-3 and session-4
    service.record_attempt(
        lesson_id="lesson-a",
        attempt_id="a-3",
        variant_id="var-3",
        session_id="session-3",
        success=True,
        held_out=False,
        evidence={"validator": "pytest", "reference": "r3", "passed": True},
        cortex_taint="t",
    )
    service.record_attempt(
        lesson_id="lesson-a",
        attempt_id="a-4",
        variant_id="var-4",
        session_id="session-4",
        success=True,
        held_out=False,
        evidence={"validator": "pytest", "reference": "r4", "passed": True},
        cortex_taint="t",
    )
    # Reusing contaminated pre-failure practice session-1 or failed session-2 as held_out must NOT validate
    service.record_attempt(
        lesson_id="lesson-a",
        attempt_id="a-5",
        variant_id="var-5",
        session_id="session-1",
        success=True,
        held_out=True,
        evidence={"validator": "pytest", "reference": "r5", "passed": True},
        cortex_taint="t",
    )
    assert service.get_lesson("lesson-a")["validation_ready"] is False
    with pytest.raises(ValueError, match="validation"):
        service.promote_lesson(lesson_id="lesson-a", cortex_taint="t")

    # Cross-lesson reuse of attempt_id "a-1" on "lesson-b" must fail
    with pytest.raises(ValueError, match="attempt_id"):
        service.record_attempt(
            lesson_id="lesson-b",
            attempt_id="a-1",
            variant_id="var-b1",
            session_id="session-b1",
            success=True,
            held_out=False,
            evidence={"validator": "cargo", "reference": "rb1", "passed": True},
            cortex_taint="t",
        )

    # Clean held-out session-99 succeeds
    service.record_attempt(
        lesson_id="lesson-a",
        attempt_id="a-6",
        variant_id="var-6",
        session_id="session-99",
        success=True,
        held_out=True,
        evidence={"validator": "pytest", "reference": "r6", "passed": True},
        cortex_taint="t",
    )
    assert service.promote_lesson(lesson_id="lesson-a", cortex_taint="t")["status"] == "active"


def test_o_mem_6_procedural_memory_failed_execution_cannot_escalate_or_latch_permanent() -> None:
    """O-MEM-6: A failed execution in ProceduralMemory never increases striatal_value or latches permanent=True."""
    pm = ProceduralMemory()
    engram = pm.record_execution("kernel-skill", success=False, latency_ms=12.5, permanent=True)
    assert engram.striatal_value == pytest.approx(0.4)
    assert engram.permanent is False
    assert engram.success_count == 0
    assert engram.usage_count == 1

    with pytest.raises(ValueError, match="latency_ms"):
        pm.record_execution("kernel-skill", success=True, latency_ms=-1.0)
    with pytest.raises(ValueError, match="latency_ms"):
        pm.record_execution("kernel-skill", success=True, latency_ms=float("nan"))

    promoted = pm.record_execution("kernel-skill", success=True, latency_ms=5.0, permanent=True)
    assert promoted.permanent is True
    assert promoted.striatal_value == pytest.approx(0.9)
