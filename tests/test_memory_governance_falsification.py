# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""Falsification Wave (FL-M01..FL-M08) for Verifiable Persistent Memory Governance."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from babylon60.memory.governance import (
    CausalCycleError,
    DisbeliefProof,
    GovernanceViolationError,
    HumeGuillotineError,
    MemoryGovernanceEngine,
    MemoryKind,
    MemoryModality,
    MemoryRecordView,
    MemoryStatus,
    SignatureVerificationError,
    TenantIsolationError,
    TrustLevel,
)


DisbeliefCase = tuple[
    MemoryGovernanceEngine,
    MemoryRecordView,
    MemoryRecordView,
    MemoryRecordView,
    MemoryRecordView,
    DisbeliefProof,
]


@pytest.fixture
def engine(tmp_path: Path) -> MemoryGovernanceEngine:
    db_file = tmp_path / "memory_governance_test.db"
    eng = MemoryGovernanceEngine(db_file)
    eng.register_principal_key("tenant-alpha", "operator-root", b"sovereign-root-secret-key-0001")
    eng.register_principal_key("tenant-alpha", "agent-worker", b"worker-agent-secret-key-000002")
    eng.register_principal_key("tenant-alpha", "external-scraper", b"external-scraper-secret-key-03")
    eng.register_principal_key("tenant-beta", "beta-admin", b"beta-tenant-secret-key-0000004")
    return eng


def test_fl_m01_transitive_revocation_closure_100_chain(engine: MemoryGovernanceEngine) -> None:
    """FL-M01: Revocación transitiva en cadena de 100 memorias derivadas (0% huérfanos activos)."""
    chain_ids: list[str] = []
    root = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Fact-0: Base sovereign root secret coordinate",
        kind=MemoryKind.SOURCE_RECORD,
        trust_level=TrustLevel.SOVEREIGN,
    )
    chain_ids.append(root.record_id)

    for idx in range(1, 100):
        kind = MemoryKind.MEMORY_EVENT if idx < 90 else MemoryKind.IDEA_THREAD
        derived = engine.add_record(
            tenant_id="tenant-alpha",
            principal="agent-worker",
            content=f"Inference-{idx}: derived step from Fact-{idx - 1}",
            kind=kind,
            parents=[chain_ids[-1]],
            trust_level=TrustLevel.PUBLIC,
        )
        chain_ids.append(derived.record_id)

    assert len(chain_ids) == 100
    assert len(engine.query_active_memories(tenant_id="tenant-alpha")) == 100

    revocation = engine.revoke_record(
        record_id=root.record_id,
        tenant_id="tenant-alpha",
        principal="operator-root",
        reason="FL-M01 root falsification",
    )
    assert revocation["total_invalidated"] == 100
    revoked_dependents = revocation["revoked_dependents"]
    assert isinstance(revoked_dependents, list)
    assert len(revoked_dependents) == 99

    # Ningún registro derivado puede permanecer activo ni ser recuperable
    active_after = engine.query_active_memories(tenant_id="tenant-alpha", min_trust_level=TrustLevel.EXTERNAL)
    assert active_after == []

    root_view = engine.get_record(root.record_id, tenant_id="tenant-alpha", include_inactive=True)
    assert root_view.status == MemoryStatus.REVOKED
    assert root_view.content is None

    leaf_view = engine.get_record(chain_ids[-1], tenant_id="tenant-alpha", include_inactive=True)
    assert leaf_view.status == MemoryStatus.REVOKED_DEPENDENCY
    assert leaf_view.content is None

    # La cadena criptográfica del ledger WORM permanece 100% íntegra
    assert engine.ledger.verify_integrity() is True


@pytest.fixture(params=["shared", "separate"])
def disbelief_case(engine: MemoryGovernanceEngine, request: pytest.FixtureRequest, tmp_path: Path) -> DisbeliefCase:
    """A sealed retraction with a source, counter-evidence, and one dependent."""
    if request.param == "separate":
        engine.ledger = type(engine.ledger)(tmp_path / "separate_ledger.db")
    fact = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Observed spike",
        kind=MemoryKind.SOURCE_RECORD,
    )
    attribution = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Daemon caused spike",
        kind=MemoryKind.INFERENCE,
        parents=[fact.record_id],
    )
    dependent = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Quarantine daemon",
        kind=MemoryKind.IDEA_THREAD,
        depends_on=[attribution.record_id],
    )
    counter = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Daemon was suspended",
        kind=MemoryKind.SOURCE_RECORD,
    )
    proof = engine.retract_attribution(
        attribution_record_id=attribution.record_id,
        counter_evidence_record_id=counter.record_id,
        tenant_id="tenant-alpha",
        principal="operator-root",
        rationale="Suspension excludes attribution",
    )
    return engine, fact, attribution, dependent, counter, proof


@pytest.mark.parametrize(
    "field,value",
    [
        ("ledger_event_id", "forged-event"),
        ("lamport_t", 999999),
        ("affected_dependents_json", "[]"),
    ],
)
def test_disbelief_rejects_forged_ledger_metadata(disbelief_case: DisbeliefCase, field: str, value: str | int) -> None:
    engine, _, attribution, _, _, proof = disbelief_case
    assert engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha") == proof
    with sqlite3.connect(engine.db_path) as conn:
        # Field names come exclusively from the fixed parameter list above.
        conn.execute(f"UPDATE cortex_disbelief_proofs SET {field} = ? WHERE proof_id = ?", (value, proof.proof_id))
    with pytest.raises(SignatureVerificationError, match="ledger"):
        engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha")


@pytest.mark.parametrize("damage", ["missing", "other-event"])
def test_disbelief_requires_matching_intact_ledger_event(disbelief_case: DisbeliefCase, damage: str) -> None:
    engine, _, attribution, _, _, proof = disbelief_case
    if damage == "missing":
        # A valid but empty ledger cannot anchor this proof. Keep WORM triggers active.
        engine.ledger = type(engine.ledger)(engine.db_path.parent / "empty_ledger.db")
    if damage == "other-event":
        # An existing, valid event of a different type cannot serve as the receipt.
        events = engine.ledger.query_events(event_type="MEMORY_RECORD_COMMITTED", limit=1)
        with sqlite3.connect(engine.db_path) as conn:
            conn.execute(
                "UPDATE cortex_disbelief_proofs SET ledger_event_id = ? WHERE proof_id = ?",
                (events[0]["event_id"], proof.proof_id),
            )
    with pytest.raises(SignatureVerificationError, match="ledger"):
        engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha")


@pytest.mark.parametrize("target", ["fact", "counter"])
@pytest.mark.parametrize("damage", ["delete", "tamper"])
def test_disbelief_requires_intact_evidence_blobs(disbelief_case: DisbeliefCase, target: str, damage: str) -> None:
    engine, fact, attribution, _, counter, _ = disbelief_case
    record = fact if target == "fact" else counter
    with sqlite3.connect(engine.db_path) as conn:
        if damage == "delete":
            conn.execute("DELETE FROM cortex_memory_blobs WHERE record_id = ?", (record.record_id,))
        else:
            conn.execute("UPDATE cortex_memory_blobs SET plaintext = 'forged' WHERE record_id = ?", (record.record_id,))
    with pytest.raises(SignatureVerificationError):
        engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha")


@pytest.mark.parametrize("status", [MemoryStatus.DISBELIEVED, MemoryStatus.DISBELIEVED_DEPENDENCY, MemoryStatus.STALE])
def test_disbelief_rejects_inactive_counter_evidence(disbelief_case: DisbeliefCase, status: MemoryStatus) -> None:
    engine, _, attribution, _, counter, _ = disbelief_case
    with sqlite3.connect(engine.db_path) as conn:
        conn.execute(
            "UPDATE cortex_memory_records SET status = ? WHERE record_id = ?", (status.value, counter.record_id)
        )
    with pytest.raises(GovernanceViolationError, match="Counter-evidence.*ACTIVE"):
        engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha")


@pytest.mark.parametrize("salt", [None, "ab" * 16])
def test_disbelief_blocks_exact_reinference_after_reopen(disbelief_case: DisbeliefCase, salt: str | None) -> None:
    engine, fact, attribution, _, _, proof = disbelief_case
    reopened = MemoryGovernanceEngine(engine.db_path, ledger=type(engine.ledger)(engine.ledger.db_path))
    reopened.register_principal_key("tenant-alpha", "agent-worker", b"worker-agent-secret-key-000002")
    reopened.register_principal_key("tenant-alpha", "operator-root", b"sovereign-root-secret-key-0001")
    assert reopened.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha") == proof
    assert attribution.content is not None
    before = engine.ledger.query_events()
    with pytest.raises(GovernanceViolationError, match="Previously disbelieved"):
        reopened.add_record(
            tenant_id="tenant-alpha",
            principal="agent-worker",
            content=attribution.content,
            kind=MemoryKind.INFERENCE,
            parents=[fact.record_id],
            salt_hex=salt,
        )
    assert engine.ledger.query_events() == before
    # A different claim and another tenant remain independent of this rejection.
    reopened.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Different causal attribution",
        kind=MemoryKind.INFERENCE,
        parents=[fact.record_id],
    )
    other = engine.add_record(
        tenant_id="tenant-beta",
        principal="beta-admin",
        content=attribution.content,
        kind=MemoryKind.INFERENCE,
    )
    assert other.status == MemoryStatus.ACTIVE


def test_fl_m02_forced_post_revocation_extraction_resistance(engine: MemoryGovernanceEngine) -> None:
    """FL-M02: Lectura forzada post-revocación y crypto-shredding físico del blob."""
    secret_marker = "CLASSIFIED_BIO_KEY_9948102"
    rec = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content=f"Patient record contains {secret_marker} for clinical trial",
        kind=MemoryKind.SOURCE_RECORD,
    )

    assert len(engine.query_active_memories(tenant_id="tenant-alpha", query_text=secret_marker)) == 1
    engine.revoke_record(record_id=rec.record_id, tenant_id="tenant-alpha", principal="operator-root")

    # 1. Consulta indexada / léxica devuelve 0
    assert engine.query_active_memories(tenant_id="tenant-alpha", query_text=secret_marker) == []

    # 2. Lectura directa activa falla en fail-closed
    with pytest.raises(GovernanceViolationError):
        engine.get_record(rec.record_id, tenant_id="tenant-alpha", include_inactive=False)

    # 3. Inspección forense directa a las tablas SQLite: el texto plano fue destruido (crypto-shredded)
    with sqlite3.connect(str(engine.db_path)) as conn:
        blob_row = conn.execute(
            "SELECT plaintext FROM cortex_memory_blobs WHERE record_id = ?", (rec.record_id,)
        ).fetchone()
        assert blob_row is None

        # Tampoco figura en claro dentro del payload JSON de cortex_ledger (solo commitment SHA3-256)
        ledger_rows = conn.execute("SELECT payload_json FROM cortex_ledger").fetchall()
        for (payload_json,) in ledger_rows:
            assert secret_marker not in payload_json


def test_fl_m03_multi_authority_conflicts_and_hume_guillotine(engine: MemoryGovernanceEngine) -> None:
    """FL-M03: Autoridad múltiple, prelación de niveles de confianza y Guillotina de Hume."""
    # Insertar entradas contradictorias sobre un mismo subject_key con distinta autoridad
    for i in range(25):
        engine.add_record(
            tenant_id="tenant-alpha",
            principal="external-scraper",
            content=f"Unverified rumor variant {i}: server port is 9999",
            subject_key="config.canonical_port",
            trust_level=TrustLevel.EXTERNAL,
        )

    sovereign_truth = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Sovereign specification: server port is 6060",
        subject_key="config.canonical_port",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # Un agente de menor autoridad intenta sobrescribir el hecho soberano después
    late_low_trust = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Worker guess: server port is 8080",
        subject_key="config.canonical_port",
        trust_level=TrustLevel.PUBLIC,
    )
    assert late_low_trust.status == MemoryStatus.STALE

    active = engine.query_active_memories(
        tenant_id="tenant-alpha", subject_key="config.canonical_port", min_trust_level=TrustLevel.EXTERNAL
    )
    assert len(active) == 1
    assert active[0].record_id == sovereign_truth.record_id
    assert active[0].content == "Sovereign specification: server port is 6060"

    # Guillotina de Hume: prohibido derivar una regla Deontic desde una premisa Epistemic sin autoridad soberana
    with pytest.raises(HumeGuillotineError):
        engine.add_record(
            tenant_id="tenant-alpha",
            principal="agent-worker",
            content="Therefore we OUGHT TO open port 6060 to the public internet",
            modality=MemoryModality.DEONTIC,
            trust_level=TrustLevel.PUBLIC,
            parents=[sovereign_truth.record_id],
        )


def test_fl_m04_signature_and_commitment_integrity_and_law_o13(engine: MemoryGovernanceEngine) -> None:
    """FL-M04: Rechazo de firmas falsas, detección de bitflips en disco y Ley O13 (Reloj Autoritativo)."""
    # 1. Firma falsificada es rechazada en pre-commit
    with pytest.raises(SignatureVerificationError):
        engine.add_record(
            tenant_id="tenant-alpha",
            principal="agent-worker",
            content="Forged memory entry",
            signature="0" * 64,
        )

    # 2. Ley O13: el cliente no puede suministrar transaction_time
    with pytest.raises(GovernanceViolationError, match="O13"):
        engine.add_record(
            tenant_id="tenant-alpha",
            principal="agent-worker",
            content="Backdated memory entry",
            client_supplied_tx_time=1,
        )

    # 3. Invariante B1: rechazar IDs que no sean UUID canónicos de 36 chars
    with pytest.raises(GovernanceViolationError, match="B1"):
        engine.add_record(
            record_id="slug-not-a-uuid",
            tenant_id="tenant-alpha",
            principal="agent-worker",
            content="Bad identity format",
        )

    # 4. Detección de adulteración en disco (bitflip en plaintext tras commit)
    valid_rec = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Authentic command parameter: limit=12",
    )
    with sqlite3.connect(str(engine.db_path)) as conn:
        conn.execute(
            "UPDATE cortex_memory_blobs SET plaintext = 'Tampered parameter: limit=9999' WHERE record_id = ?",
            (valid_rec.record_id,),
        )
        conn.commit()

    with pytest.raises(SignatureVerificationError, match="tampering"):
        engine.get_record(valid_rec.record_id, tenant_id="tenant-alpha")

    # 5. BJR-E052: rechazo de auto-ciclo en el DAG de derivación
    self_id = "11111111-2222-4333-8444-555555555555"
    with pytest.raises(GovernanceViolationError):
        engine.add_record(
            record_id=self_id,
            tenant_id="tenant-alpha",
            principal="operator-root",
            content="Self-referential cycle node",
            parents=[self_id],
        )
    assert issubclass(CausalCycleError, GovernanceViolationError)


def test_fl_m05_skill_dependency_invalidation(engine: MemoryGovernanceEngine) -> None:
    """FL-M05: Una habilidad (SkillLesson) que depende de un hecho queda invalidada al revocar el hecho."""
    fact = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="API endpoint v2 resides at unix:///tmp/babylon60.sock",
        kind=MemoryKind.SOURCE_RECORD,
    )
    skill = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Skill procedure: connect to unix:///tmp/babylon60.sock with COSE_Sign1 envelope",
        kind=MemoryKind.SKILL_LESSON,
        depends_on=[fact.record_id],
    )

    active_skills = engine.query_active_memories(tenant_id="tenant-alpha", kind=MemoryKind.SKILL_LESSON)
    assert len(active_skills) == 1
    assert active_skills[0].record_id == skill.record_id

    # Revocar el hecho base invalida automáticamente la habilidad dependiente
    engine.revoke_record(record_id=fact.record_id, tenant_id="tenant-alpha", principal="operator-root")

    assert engine.query_active_memories(tenant_id="tenant-alpha", kind=MemoryKind.SKILL_LESSON) == []
    skill_view = engine.get_record(skill.record_id, tenant_id="tenant-alpha", include_inactive=True)
    assert skill_view.status == MemoryStatus.REVOKED_DEPENDENCY


def test_fl_m06_multi_tenant_isolation_and_explicit_grant(engine: MemoryGovernanceEngine) -> None:
    """FL-M06: Particionamiento estricto multi-tenant y no transferencia de autoridad sin grant explícito."""
    alpha_rec = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Alpha proprietary algorithm specification",
    )
    beta_rec = engine.add_record(
        tenant_id="tenant-beta",
        principal="beta-admin",
        content="Beta internal telemetry log",
    )

    # Beta no ve memorias de Alpha en búsquedas ni por ID directo
    beta_visible = engine.query_active_memories(tenant_id="tenant-beta", min_trust_level=TrustLevel.EXTERNAL)
    assert [r.record_id for r in beta_visible] == [beta_rec.record_id]

    with pytest.raises(TenantIsolationError):
        engine.get_record(alpha_rec.record_id, tenant_id="tenant-beta")

    with pytest.raises(TenantIsolationError):
        engine.add_record(
            tenant_id="tenant-beta",
            principal="beta-admin",
            content="Unauthorized cross-tenant derivation",
            parents=[alpha_rec.record_id],
        )

    # Tras delegación explícita firmada por el propietario de Alpha, Beta puede leer ese registro específico
    engine.grant_cross_tenant_read(
        owner_tenant="tenant-alpha",
        grantee_tenant="tenant-beta",
        record_id=alpha_rec.record_id,
        principal="operator-root",
    )
    shared_view = engine.get_record(alpha_rec.record_id, tenant_id="tenant-beta")
    assert shared_view.record_id == alpha_rec.record_id


def test_fl_m07_bemula_surgical_unlearning_and_preservation(engine: MemoryGovernanceEngine) -> None:
    """FL-M07: Simulacro BEMULA — eliminar exactamente X y sus derivados preservando el resto al 100%."""
    fact_a = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="User prefers dark mode brutalist typography",
    )
    fact_b = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Primary workstation is MacBook Pro M3 Pro",
    )
    fact_x = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Temporary phone verification code is 884920",
    )
    derived_from_a = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="UI theme configuration: background #0A0A0A",
        parents=[fact_a.record_id],
    )
    derived_from_x = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Cached auth summary: code 884920 active",
        parents=[fact_x.record_id],
    )

    # Solicitud de olvido sobre X
    res = engine.revoke_record(record_id=fact_x.record_id, tenant_id="tenant-alpha", principal="operator-root")
    revoked_dependents = res["revoked_dependents"]
    assert isinstance(revoked_dependents, list)
    assert set(revoked_dependents) == {derived_from_x.record_id}

    # X y su derivado desaparecen al 100%
    assert engine.query_active_memories(tenant_id="tenant-alpha", query_text="884920") == []

    # A, B y el derivado de A se preservan intactos (0% daño colateral)
    remaining_ids = {r.record_id for r in engine.query_active_memories(tenant_id="tenant-alpha")}
    assert remaining_ids == {fact_a.record_id, fact_b.record_id, derived_from_a.record_id}


def test_fl_m08_inferential_unlearning_many_steps_into_one(engine: MemoryGovernanceEngine) -> None:
    """FL-M08: Razonamiento sobre memoria contraída ('Many Steps into One') y recertificación en vivo."""
    f1 = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Deployment target region: eu-south-2",
        subject_key="deploy.region",
        trust_level=TrustLevel.SOVEREIGN,
    )
    f2 = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Runtime binary mode: musl-static",
        subject_key="deploy.binary_mode",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # Memoria contraída (IdeaThread) que resume f1 y f2
    summary = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content=f"Compiled Summary: {f1.content} | {f2.content}",
        kind=MemoryKind.IDEA_THREAD,
        subject_key="deploy.compiled_summary",
        parents=[f1.record_id, f2.record_id],
    )

    # Mientras f1 y f2 sigan activos, la certificación devuelve la misma memoria contraída
    certified_1 = engine.certify_or_rebuild_summary(
        summary_id=summary.record_id,
        tenant_id="tenant-alpha",
        principal="agent-worker",
        synthesizer=lambda recs: "Compiled Summary: " + " | ".join(r.content or "" for r in recs),
    )
    assert certified_1.record_id == summary.record_id

    # Ahora cambia un hecho subyacente (f1 es reemplazado por f1_new sobre 'deploy.region')
    f1_new = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Deployment target region: ch-zurich-1",
        subject_key="deploy.region",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # El resumen anterior quedó marcado automáticamente como STALE (invalidación transitiva de 'Many Steps')
    old_summary_view = engine.get_record(summary.record_id, tenant_id="tenant-alpha", include_inactive=True)
    assert old_summary_view.status == MemoryStatus.STALE

    # Al certificar el resumen, se detecta la obsolescencia y se reconstruye con el hecho vivo (ch-zurich-1)
    rebuilt = engine.certify_or_rebuild_summary(
        summary_id=summary.record_id,
        tenant_id="tenant-alpha",
        principal="agent-worker",
        synthesizer=lambda recs: "Compiled Summary: " + " | ".join(r.content or "" for r in recs),
    )
    assert rebuilt.record_id != summary.record_id
    assert rebuilt.status == MemoryStatus.ACTIVE
    assert rebuilt.content is not None
    assert "ch-zurich-1" in rebuilt.content
    assert "eu-south-2" not in rebuilt.content
    assert f1_new.record_id in rebuilt.parents


def test_fl_m09_epistemic_attribution_retraction_preserving_fact(engine: MemoryGovernanceEngine) -> None:
    """FL-M09: Demostrar por qué se ha dejado de creer una atribución sin dejar de recordar el hecho (O1, O8, B4)."""
    # 1. El hecho primario (SourceRecord) es observado y sellado en el territorio
    fact = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Raw telemetry at tick 42: voltage spike of +1.8V on rail VDD_CPU",
        kind=MemoryKind.SOURCE_RECORD,
        subject_key="telemetry.rail.vdd_cpu.spike_42",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # 2. Una inferencia atribuye causalmente ese hecho a un agente/componente ("el daemon X causó el pico")
    attribution = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Attribution: voltage spike on VDD_CPU was caused by thermal-daemon PID 412",
        kind=MemoryKind.INFERENCE,
        subject_key="incident.42.root_cause",
        parents=[fact.record_id],
        trust_level=TrustLevel.PUBLIC,
    )

    # 3. Un hilo derivado (IdeaThread) depende de esa atribución
    downstream_thread = engine.add_record(
        tenant_id="tenant-alpha",
        principal="agent-worker",
        content="Action plan: quarantine thermal-daemon PID 412 due to VDD_CPU spike attribution",
        kind=MemoryKind.IDEA_THREAD,
        depends_on=[attribution.record_id],
        trust_level=TrustLevel.PUBLIC,
    )

    # Prohibido retractar epistémicamente el hecho primario (Ley O1: SOURCE != INFERENCE)
    with pytest.raises(GovernanceViolationError, match="O1"):
        engine.retract_attribution(
            attribution_record_id=fact.record_id,
            counter_evidence_record_id=attribution.record_id,
            tenant_id="tenant-alpha",
            principal="operator-root",
            rationale="Attempting to disbelieve a raw SourceRecord must fail",
        )

    # 4. Llega nueva evidencia física (SourceRecord) que refuta la atribución sin negar el pico de voltaje
    counter_evidence = engine.add_record(
        tenant_id="tenant-alpha",
        principal="operator-root",
        content="Hardware audit log: thermal-daemon PID 412 was suspended in SIGSTOP from tick 10 to tick 90",
        kind=MemoryKind.SOURCE_RECORD,
        subject_key="audit.pid_412.state_tick_42",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # 5. CORTEX retracta la atribución presentando la contra-evidencia
    proof = engine.retract_attribution(
        attribution_record_id=attribution.record_id,
        counter_evidence_record_id=counter_evidence.record_id,
        tenant_id="tenant-alpha",
        principal="operator-root",
        rationale="PID 412 was suspended (SIGSTOP) across ticks [10, 90], falsifying causal attribution at tick 42.",
    )

    # A. El hecho original sigue siendo recordado al 100% (ACTIVE y recuperable en consultas vivas)
    remembered_facts = engine.query_active_memories(
        tenant_id="tenant-alpha", subject_key="telemetry.rail.vdd_cpu.spike_42"
    )
    assert len(remembered_facts) == 1
    assert remembered_facts[0].record_id == fact.record_id
    assert remembered_facts[0].content == fact.content

    # B. La atribución refutada y su derivado ya NO contaminan la memoria activa
    active_attributions = engine.query_active_memories(
        tenant_id="tenant-alpha", subject_key="incident.42.root_cause", min_trust_level=TrustLevel.EXTERNAL
    )
    assert active_attributions == []
    active_threads = engine.query_active_memories(
        tenant_id="tenant-alpha", kind=MemoryKind.IDEA_THREAD, min_trust_level=TrustLevel.EXTERNAL
    )
    assert active_threads == []

    # C. A diferencia de revoke_record (amnesia/shredding), CORTEX conserva la cicatriz epistémica y demuestra POR QUÉ dejó de creerla
    verified_proof = engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha")
    assert verified_proof == proof
    assert verified_proof.disbelieved_record_id == attribution.record_id
    assert verified_proof.disbelieved_content == attribution.content
    assert verified_proof.preserved_fact_ids == (fact.record_id,)
    assert verified_proof.preserved_fact_commitments == (fact.commitment,)
    assert verified_proof.counter_evidence_record_id == counter_evidence.record_id
    assert verified_proof.counter_evidence_commitment == counter_evidence.commitment
    assert verified_proof.affected_dependents == (downstream_thread.record_id,)

    # D. El nodo dependiente quedó marcado en DISBELIEVED_DEPENDENCY (Invariante B4)
    dep_view = engine.get_record(downstream_thread.record_id, tenant_id="tenant-alpha", include_inactive=True)
    assert dep_view.status == MemoryStatus.DISBELIEVED_DEPENDENCY

    # E. Si alguien adultera el rationale o el witness_digest en SQLite, prove_disbelief aborta con SignatureVerificationError
    with sqlite3.connect(str(engine.db_path)) as conn:
        conn.execute(
            "UPDATE cortex_disbelief_proofs SET rationale = 'Forged rationale' WHERE proof_id = ?",
            (proof.proof_id,),
        )
        conn.commit()

    with pytest.raises(SignatureVerificationError, match="tampering"):
        engine.prove_disbelief(attribution.record_id, tenant_id="tenant-alpha")

    assert engine.ledger.verify_integrity() is True
