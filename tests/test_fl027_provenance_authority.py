# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""FL-027 v3 Oracle Suite (T6-T15): Provenance Authority Confusion & Evidence Laundering.

Verifies:
- Dual cryptographic identity: I_content = BLAKE3(CanonicalBytes(m)) vs.
  I_event = (namespace, conversation, message, revision, logical_tick) in BLAKE3.
- Physical wall-clock timestamps are excluded from canonical identities.
- T6-T15 positive, negative, and contradictory fixtures.
- Retraction lineage preservation via MemoryGovernanceEngine (DisbeliefProof)
  while preserving active recall of primary SourceRecords.
- Separated reporting of overattribution, coverage, recall, and abstention.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast
import pytest

from babylon60.memory import (
    AttributionClaim,
    ClaimScope,
    DerivationKind,
    EventIdentityTuple,
    EventLinkReceipt,
    MemoryGovernanceEngine,
    MemoryKind,
    MemoryStatus,
    ProvenanceEnvelope,
    ProvenanceLevel,
    TrustLevel,
    VerdictOutcome,
    compose_event_evidence,
    compute_content_identity,
    compute_fl027_metrics,
    evaluate_provenance_claim,
)

LINK_KEY = b"0123456789abcdef0123456789abcdef"

MALFORMED_B3_DIGESTS: list[str | bytes | int] = [
    "b3:not-a-digest",
    "b3:",
    "b3:" + "a" * 63,
    "b3:" + "a" * 65,
    "b3:" + "z" * 64,
    "b3:" + "０" * 64,
    "b3:" + "a" * 64 + "\n",
    "b3:" + "a" * 63 + " ",
    "B3:" + "a" * 64,
    "a" * 64,
    "",
    b"b3:" + b"a" * 64,
    64,
]


@pytest.mark.parametrize(
    "field",
    ["native_export_digest_b3", "external_anchor_digest_b3", "execution_receipt_digest_b3"],
)
@pytest.mark.parametrize("digest", MALFORMED_B3_DIGESTS)
def test_malformed_evidence_digest_cannot_attest_or_raise_provenance(field: str, digest: str | bytes | int) -> None:
    envelope = ProvenanceEnvelope(
        content="fixture",
        host_platform="fixture",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("fixture", "c", "m", 1, 1),
        native_export_digest_b3=compute_content_identity("native-export"),
        external_anchor_digest_b3=compute_content_identity("external-anchor"),
        execution_receipt_digest_b3=compute_content_identity("execution-receipt"),
        external_anchor_not_later_than_tick=1,
        contemporaneous_witness_id="observer",
    )
    # Cast preserves the intentionally invalid runtime bytes/int input while
    # selecting a concrete dataclass field for static checking.
    malformed_digest = cast(str, digest)
    if field == "native_export_digest_b3":
        malformed = replace(envelope, native_export_digest_b3=malformed_digest)
    elif field == "external_anchor_digest_b3":
        malformed = replace(envelope, external_anchor_digest_b3=malformed_digest)
    else:
        assert field == "execution_receipt_digest_b3"
        malformed = replace(envelope, execution_receipt_digest_b3=malformed_digest)
    claim = AttributionClaim(
        "forged-export",
        ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
        claimed_platform="fixture",
        claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED,
    )

    assert not malformed.verify_integrity()
    assert malformed.effective_provenance_level() == ProvenanceLevel.CLAIMED
    decision = evaluate_provenance_claim(malformed, claim)
    assert decision.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not decision.integrity_verified
    assert not decision.attested
    assert decision.effective_level == ProvenanceLevel.CLAIMED


@pytest.mark.parametrize("digest", MALFORMED_B3_DIGESTS)
def test_malformed_expected_content_digest_is_rejected(digest: str | bytes | int) -> None:
    envelope = ProvenanceEnvelope("fixture", "fixture", DerivationKind.ORIGINAL_MESSAGE)
    claim = AttributionClaim("recall", ClaimScope.FACT_RECALL)
    # Cast models malformed external input without converting its runtime type.
    malformed = cast(str, digest)
    assert not envelope.verify_integrity(expected_content_b3=malformed)
    decision = evaluate_provenance_claim(envelope, claim, expected_content_b3=malformed)
    assert decision.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not decision.attested


@pytest.mark.parametrize("uppercase", [False, True])
def test_valid_evidence_digests_preserve_attestation_and_identity(uppercase: bool) -> None:
    digest = compute_content_identity("evidence")
    if uppercase:
        digest = "b3:" + digest[3:].upper()
    envelope = ProvenanceEnvelope(
        content="fixture",
        host_platform="fixture",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("fixture", "c", "m", 1, 1),
        native_export_digest_b3=digest,
        external_anchor_digest_b3=digest,
        execution_receipt_digest_b3=digest,
        external_anchor_not_later_than_tick=1,
        contemporaneous_witness_id="observer",
    )
    claim = AttributionClaim(
        "valid-export",
        ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
        claimed_min_level=ProvenanceLevel.CONTEMPORANEOUS_WITNESS,
    )
    assert envelope.verify_integrity(expected_content_b3=envelope.content_identity)
    assert evaluate_provenance_claim(envelope, claim, expected_content_b3=envelope.content_identity).attested
    assert (
        envelope.native_export_digest_b3
        == envelope.external_anchor_digest_b3
        == envelope.execution_receipt_digest_b3
        == digest
    )
    # Evidence metadata does not change either canonical identity.
    without_evidence = replace(
        envelope,
        native_export_digest_b3=None,
        external_anchor_digest_b3=None,
        execution_receipt_digest_b3=None,
    )
    assert without_evidence.verify_integrity()
    assert without_evidence.effective_provenance_level() == ProvenanceLevel.PLATFORM_UI_RECORD
    assert not evaluate_provenance_claim(without_evidence, claim).attested
    assert without_evidence.content_identity == envelope.content_identity
    assert without_evidence.event_identity == envelope.event_identity


@pytest.fixture
def engine(tmp_path: Path) -> MemoryGovernanceEngine:
    db_file = tmp_path / "fl027_provenance_test.db"
    eng = MemoryGovernanceEngine(db_file)
    eng.register_principal_key("tenant-c5", "operator-root", b"sovereign-root-secret-key-0001")
    eng.register_principal_key("tenant-c5", "agent-cortex", b"cortex-worker-secret-key-00002")
    return eng


def test_t6_dual_identity_invariance_and_logical_tick_binding() -> None:
    """T6: Identical content across platforms yields identical I_content (BLAKE3) but distinct I_event; physical timestamps do not alter canonical identity."""
    anchor_text = "SOVEREIGN-SWARM-COLLAPSE: planning as inference under CHRONOS-1"

    env_chatgpt_1 = ProvenanceEnvelope(
        content=anchor_text,
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        claimed_created_at_utc="2026-02-24T11:22:46Z",
        event_tuple=EventIdentityTuple(
            namespace="ChatGPT",
            conversation_id="conv-feb-24",
            message_id="msg-001",
            revision=1,
            logical_tick=42,
        ),
    )
    # Alter physical timestamp only -> must NOT change I_content or I_event (INV_C5_CANONICAL_LOGICAL_TICK)
    env_chatgpt_altered_wallclock = ProvenanceEnvelope(
        content=anchor_text,
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        claimed_created_at_utc="1999-01-01T00:00:00Z",
        event_tuple=EventIdentityTuple(
            namespace="ChatGPT",
            conversation_id="conv-feb-24",
            message_id="msg-001",
            revision=1,
            logical_tick=42,
        ),
    )
    # Same content in Antigravity -> same I_content, distinct I_event
    env_antigravity = ProvenanceEnvelope(
        content=anchor_text,
        host_platform="Antigravity",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        claimed_created_at_utc="2026-10-26T21:38:36Z",
        event_tuple=EventIdentityTuple(
            namespace="Antigravity",
            conversation_id="conv-oct-26",
            message_id="msg-999",
            revision=1,
            logical_tick=108,
        ),
    )

    assert env_chatgpt_1.content_identity.startswith("b3:")
    assert env_chatgpt_1.event_identity is not None and env_chatgpt_1.event_identity.startswith("b3:")

    # Physical clock excluded from canonical hashes
    assert env_chatgpt_1.content_identity == env_chatgpt_altered_wallclock.content_identity
    assert env_chatgpt_1.event_identity == env_chatgpt_altered_wallclock.event_identity

    # Same content != Same event
    assert env_chatgpt_1.content_identity == env_antigravity.content_identity
    assert env_chatgpt_1.event_identity != env_antigravity.event_identity


def test_t7_platform_laundering_rejected_and_null_authoring_abstains() -> None:
    """T7: Substituting host_platform=ChatGPT for Antigravity is REJECTED; null original_authoring_platform ABSTAINS."""
    env = ProvenanceEnvelope(
        content="CHRONOS-1, CORTEX y planning as inference",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        original_authoring_platform=None,
        claimed_created_at_utc="2026-02-28T04:10:45Z",
        event_tuple=EventIdentityTuple("ChatGPT", "conv-28", "msg-10", 1, 15),
    )

    # Vector 1: Claiming host_platform is Antigravity when it is ChatGPT -> REJECTED_OVERATTRIBUTION
    claim_wrong_host = AttributionClaim(
        claim_id="T7-neg-host",
        scope=ClaimScope.CONVERSATION_CHRONOLOGY,
        claimed_platform="Antigravity",
        claimed_min_level=ProvenanceLevel.PLATFORM_UI_RECORD,
    )
    dec_neg = evaluate_provenance_claim(env, claim_wrong_host)
    assert dec_neg.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not dec_neg.attested
    assert not dec_neg.origin_verified

    # Vector 2: Claiming original authoring in Gemini when original_authoring_platform is null -> ABSTAINED
    claim_null_origin = AttributionClaim(
        claim_id="T7-abstain-origin",
        scope=ClaimScope.ORIGINAL_AUTHORING_PLATFORM,
        claimed_platform="Gemini",
        claimed_min_level=ProvenanceLevel.CLAIMED,
    )
    dec_abs = evaluate_provenance_claim(env, claim_null_origin)
    assert dec_abs.outcome == VerdictOutcome.ABSTAINED_INSUFFICIENT_PROVENANCE
    assert not dec_abs.attested


def test_t8_conversation_id_grafting_rejected() -> None:
    """T8: Reusing an authentic message under another conversation_id is rejected."""
    env = ProvenanceEnvelope(
        content="La Ciencia del Agente",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("ChatGPT", "conv-authentic-01", "msg-77", 1, 20),
        native_export_digest_b3=compute_content_identity("export-bundle-01"),
    )

    claim_grafted = AttributionClaim(
        claim_id="T8-graft",
        scope=ClaimScope.CONVERSATION_CHRONOLOGY,
        claimed_platform="ChatGPT",
        claimed_conversation_id="conv-forged-99",
        claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED,
    )
    dec = evaluate_provenance_claim(env, claim_grafted)
    assert dec.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not dec.origin_verified
    assert not dec.attested


def test_t9_internal_timestamp_is_not_external_temporal_witness() -> None:
    """T9: Internal claimed_created_at_utc never satisfies an external temporal bound without external anchor."""
    env_unanchored = ProvenanceEnvelope(
        content="SOVEREIGN-SWARM-COLLAPSE",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        claimed_created_at_utc="2026-02-24T11:22:46Z",
        event_tuple=EventIdentityTuple("ChatGPT", "conv-24", "msg-1", 1, 10),
        native_export_digest_b3=compute_content_identity("native-export"),
        external_anchor_digest_b3=None,
        external_anchor_not_later_than_tick=None,
    )

    claim_temporal = AttributionClaim(
        claim_id="T9-unanchored",
        scope=ClaimScope.CONVERSATION_CHRONOLOGY,
        claimed_platform="ChatGPT",
        claimed_before_tick=50,
    )
    dec_unanchored = evaluate_provenance_claim(env_unanchored, claim_temporal)
    assert dec_unanchored.outcome == VerdictOutcome.ABSTAINED_INSUFFICIENT_PROVENANCE
    assert not dec_unanchored.scope_bound
    assert not dec_unanchored.attested

    # If anchored at tick 200 (e.g. October), claiming it was anchored by tick 50 (February) fails
    env_late_anchor = ProvenanceEnvelope(
        content="SOVEREIGN-SWARM-COLLAPSE",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        claimed_created_at_utc="2026-02-24T11:22:46Z",
        event_tuple=EventIdentityTuple("ChatGPT", "conv-24", "msg-1", 1, 10),
        native_export_digest_b3=compute_content_identity("native-export"),
        external_anchor_digest_b3=compute_content_identity("ots-october-anchor"),
        external_anchor_not_later_than_tick=200,
    )
    dec_late = evaluate_provenance_claim(env_late_anchor, claim_temporal)
    assert dec_late.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not dec_late.attested


def test_t10_derived_title_and_summary_cannot_attest_original_transcript() -> None:
    """T10: Presenting a derived conversation title or post-hoc summary as a native transcript is rejected."""
    env_title = ProvenanceEnvelope(
        content="Las 10 Palabras que Debes Dominar para Ser un Master en Antigravity",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.DERIVED_TITLE,
        event_tuple=EventIdentityTuple("ChatGPT", "conv-feb-01", "title-node", 1, 5),
        native_export_digest_b3=compute_content_identity("export-01"),
    )

    claim_as_message = AttributionClaim(
        claim_id="T10-title-as-msg",
        scope=ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
        claimed_platform="ChatGPT",
        claimed_derivation=DerivationKind.ORIGINAL_MESSAGE,
        claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED,
    )
    dec = evaluate_provenance_claim(env_title, claim_as_message)
    assert dec.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not dec.scope_bound
    assert not dec.attested


def test_t11_architecture_prompt_cannot_attest_runtime_execution() -> None:
    """T11: Attributing effective runtime execution to an architecture prompt with execution_runtime=null abstains/rejects."""
    env_prompt = ProvenanceEnvelope(
        content="Design specification for CORTEX BFT ledger and SHARUR-3600 swarm",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ARCHITECTURE_PROMPT,
        execution_runtime=None,
        event_tuple=EventIdentityTuple("ChatGPT", "conv-feb-28", "msg-42", 1, 30),
        native_export_digest_b3=compute_content_identity("export-28"),
    )

    claim_exec = AttributionClaim(
        claim_id="T11-prompt-as-exec",
        scope=ClaimScope.RUNTIME_EXECUTION,
        claimed_executed=True,
    )
    dec = evaluate_provenance_claim(env_prompt, claim_exec)
    assert dec.outcome == VerdictOutcome.ABSTAINED_INSUFFICIENT_PROVENANCE
    assert not dec.scope_bound
    assert not dec.attested


def test_t12_cross_event_composition_requires_verified_link_receipt() -> None:
    """T12: Composing two records with identical I_content but distinct I_event fails unless backed by a verified EventLinkReceipt."""
    shared_spec = "INV_C5_ONWIRE_CANON: BLAKE3 canonical digest for Merkle and IPC"
    ev_feb = ProvenanceEnvelope(
        content=shared_spec,
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("ChatGPT", "conv-feb", "msg-1", 1, 10),
    )
    ev_oct = ProvenanceEnvelope(
        content=shared_spec,
        host_platform="Antigravity",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("Antigravity", "conv-oct", "msg-2", 1, 90),
    )

    # Without EventLinkReceipt -> fails closed
    ok_unlinked, reason_unlinked = compose_event_evidence(ev_feb, ev_oct)
    assert not ok_unlinked
    assert "Same Content != Same Event" in reason_unlinked

    # With valid EventLinkReceipt -> succeeds
    assert ev_feb.event_identity is not None and ev_oct.event_identity is not None
    receipt = EventLinkReceipt.issue(
        secret_key=LINK_KEY,
        source_event_id=ev_feb.event_identity,
        target_event_id=ev_oct.event_identity,
        content_identity=ev_feb.content_identity,
        logical_tick=95,
    )
    ok_linked, _ = compose_event_evidence(ev_feb, ev_oct, link_receipt=receipt, verification_key=LINK_KEY)
    assert ok_linked


def test_t13_t14_retraction_invalidates_dependents_preserving_facts_and_correction_lineage(
    engine: MemoryGovernanceEngine,
) -> None:
    """T13 & T14: Retracting an unsupported provenance attribution invalidates derived claims, preserves the fact (ACTIVE), and seals the correction's own provenance."""
    # 1. Ingest the primary recoverable fact (SourceRecord)
    fact_record = engine.add_record(
        tenant_id="tenant-c5",
        principal="operator-root",
        content="2026-02-24T11:22:46Z anchor text: SOVEREIGN-SWARM-COLLAPSE observed in ChatGPT export",
        kind=MemoryKind.SOURCE_RECORD,
        subject_key="cortex.anchor.sovereign_swarm_collapse",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # 2. Ingest an overattributed inference claiming native Antigravity execution in February
    overattributed_inference = engine.add_record(
        tenant_id="tenant-c5",
        principal="agent-cortex",
        content="Attribution: SOVEREIGN-SWARM-COLLAPSE was authored and executed natively in Antigravity on 2026-02-24",
        kind=MemoryKind.INFERENCE,
        subject_key="cortex.anchor.sovereign_swarm_collapse.origin_claim",
        parents=[fact_record.record_id],
        trust_level=TrustLevel.PUBLIC,
    )

    # 3. Ingest a downstream IdeaThread depending on that false attribution
    derived_thread = engine.add_record(
        tenant_id="tenant-c5",
        principal="agent-cortex",
        content="Certification report: Antigravity runtime lineage verified since 2026-02-24",
        kind=MemoryKind.IDEA_THREAD,
        depends_on=[overattributed_inference.record_id],
        trust_level=TrustLevel.PUBLIC,
    )

    # 4. Ingest counter-evidence from FL-027 audit
    counter_evidence = engine.add_record(
        tenant_id="tenant-c5",
        principal="operator-root",
        content="FL-027 audit: record host_platform is ChatGPT; original_authoring_platform and execution_runtime are null",
        kind=MemoryKind.SOURCE_RECORD,
        subject_key="cortex.audit.fl027.counter_evidence",
        trust_level=TrustLevel.SOVEREIGN,
    )

    # 5. Execute epistemic retraction of the overattribution
    disbelief_proof = engine.retract_attribution(
        attribution_record_id=overattributed_inference.record_id,
        counter_evidence_record_id=counter_evidence.record_id,
        tenant_id="tenant-c5",
        principal="operator-root",
        rationale="FL-027: Evidencia disponible != Autoridad concedida (host_platform=ChatGPT, execution_runtime=null)",
    )

    # T13 check: Derived claims are invalidated (DISBELIEVED / DISBELIEVED_DEPENDENCY)
    active_claims = engine.query_active_memories(
        tenant_id="tenant-c5",
        subject_key="cortex.anchor.sovereign_swarm_collapse.origin_claim",
        min_trust_level=TrustLevel.EXTERNAL,
    )
    assert active_claims == []

    dep_view = engine.get_record(derived_thread.record_id, tenant_id="tenant-c5", include_inactive=True)
    assert dep_view.status == MemoryStatus.DISBELIEVED_DEPENDENCY

    # T14 check: Recoverable primary fact remains 100% accessible and ACTIVE
    recalled_facts = engine.query_active_memories(
        tenant_id="tenant-c5",
        subject_key="cortex.anchor.sovereign_swarm_collapse",
    )
    assert len(recalled_facts) == 1
    assert recalled_facts[0].record_id == fact_record.record_id
    assert "SOVEREIGN-SWARM-COLLAPSE" in (recalled_facts[0].content or "")

    # Provenance of the correction itself is cryptographically verifiable in WORM ledger
    verified_correction = engine.prove_disbelief(overattributed_inference.record_id, tenant_id="tenant-c5")
    assert verified_correction == disbelief_proof
    assert verified_correction.retracted_by_principal == "operator-root"
    assert verified_correction.preserved_fact_ids == (fact_record.record_id,)
    assert verified_correction.counter_evidence_record_id == counter_evidence.record_id
    assert verified_correction.affected_dependents == (derived_thread.record_id,)
    assert verified_correction.lamport_t > 0
    assert engine.ledger.verify_integrity() is True


def test_t15_oracle_campaign_separated_metrics(engine: MemoryGovernanceEngine) -> None:
    """T15: End-to-end oracle evaluation over positive, negative, and contradictory fixtures reporting separated metrics."""
    env_valid_ui = ProvenanceEnvelope(
        content="SOVEREIGN-SWARM-COLLAPSE",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        claimed_created_at_utc="2026-02-24T11:22:46Z",
        event_tuple=EventIdentityTuple("ChatGPT", "conv-24", "msg-1", 1, 10),
    )
    env_valid_export = ProvenanceEnvelope(
        content="CHRONOS-1 planning as inference",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("ChatGPT", "conv-28", "msg-2", 1, 12),
        native_export_digest_b3=compute_content_identity("export-28"),
    )
    env_title_only = ProvenanceEnvelope(
        content="Las 10 Palabras que Debes Dominar para Ser un Master en Antigravity",
        host_platform="ChatGPT",
        derivation_kind=DerivationKind.DERIVED_TITLE,
        event_tuple=EventIdentityTuple("ChatGPT", "conv-01", "title-1", 1, 1),
        native_export_digest_b3=compute_content_identity("export-01"),
    )

    fixtures = [
        # Positive 1: Valid platform UI chronology recall
        (
            evaluate_provenance_claim(
                env_valid_ui,
                AttributionClaim(
                    claim_id="pos-1",
                    scope=ClaimScope.CONVERSATION_CHRONOLOGY,
                    claimed_platform="ChatGPT",
                    claimed_min_level=ProvenanceLevel.PLATFORM_UI_RECORD,
                ),
            ),
            True,
            False,
        ),
        # Positive 2: Valid native export verified message
        (
            evaluate_provenance_claim(
                env_valid_export,
                AttributionClaim(
                    claim_id="pos-2",
                    scope=ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
                    claimed_platform="ChatGPT",
                    claimed_derivation=DerivationKind.ORIGINAL_MESSAGE,
                    claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED,
                ),
            ),
            True,
            False,
        ),
        # Negative 1 (Abstain): Null original_authoring_platform
        (
            evaluate_provenance_claim(
                env_valid_ui,
                AttributionClaim(
                    claim_id="neg-abstain-1",
                    scope=ClaimScope.ORIGINAL_AUTHORING_PLATFORM,
                    claimed_platform="Antigravity",
                ),
            ),
            False,
            True,
        ),
        # Negative 2 (Abstain): Null execution_runtime
        (
            evaluate_provenance_claim(
                env_valid_export,
                AttributionClaim(
                    claim_id="neg-abstain-2",
                    scope=ClaimScope.RUNTIME_EXECUTION,
                    claimed_executed=True,
                ),
            ),
            False,
            True,
        ),
        # Negative 3 (Contradictory): Title claimed as original message transcript
        (
            evaluate_provenance_claim(
                env_title_only,
                AttributionClaim(
                    claim_id="neg-contradict-1",
                    scope=ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
                    claimed_platform="ChatGPT",
                    claimed_derivation=DerivationKind.ORIGINAL_MESSAGE,
                ),
            ),
            False,
            False,
        ),
        # Negative 4 (Contradictory): Forged content hash
        (
            evaluate_provenance_claim(
                env_valid_export,
                AttributionClaim(
                    claim_id="neg-contradict-2",
                    scope=ClaimScope.FACT_RECALL,
                    claimed_platform="ChatGPT",
                ),
                expected_content_b3=compute_content_identity("tampered-payload"),
            ),
            False,
            False,
        ),
    ]

    metrics = compute_fl027_metrics(
        fixtures,
        preserved_facts_recalled=7,
        total_facts_seeded=7,
    )

    assert metrics.total_cases == 6
    assert metrics.positive_cases == 2
    assert metrics.negative_or_contradictory_cases == 4
    assert metrics.overattribution_rate == 0.0
    assert metrics.coverage_rate == 1.0
    assert metrics.fact_recall_rate == 1.0
    assert metrics.abstention_precision == 1.0
