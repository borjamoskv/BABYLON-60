# [C5-REAL] Exergy-Maximized

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from babylon60.extensions.hypervisor.belief_object import (
    BeliefConfidence,
    BeliefObject,
    BeliefStatus,
    BeliefVerdict,
    ProvenanceEnvelope,
    BeliefRelations,
    VerdictAction,
)

# ─── BeliefConfidence ───────────────────────────────────────────────────────


class TestBeliefConfidence:
    def test_values(self):
        assert BeliefConfidence.C1_HYPOTHESIS.value == "C1"
        assert BeliefConfidence.C5_AXIOMATIC.value == "C5"

    def test_from_string(self):
        assert BeliefConfidence("C3") == BeliefConfidence.C3_PROBABLE


# ─── BeliefStatus ───────────────────────────────────────────────────────────


class TestBeliefStatus:
    def test_lifecycle_states(self):
        assert BeliefStatus.ACTIVE.value == "active"
        assert BeliefStatus.QUARANTINED.value == "quarantined"
        assert BeliefStatus.DEPRECATED.value == "deprecated"
        assert BeliefStatus.CONTESTED.value == "contested"


# ─── ProvenanceEnvelope ─────────────────────────────────────────────────────


class TestProvenanceEnvelope:
    def test_frozen(self):
        prov = ProvenanceEnvelope(
            source_hash="hash-123",
            source_type="tool",
            tenant_id="default",
        )
        with pytest.raises(FrozenInstanceError):
            prov.source_type = "human"  # type: ignore[misc]

    def test_default_initialization(self):
        env = ProvenanceEnvelope()
        assert env.source_type == "agent"
        assert env.cortex_taint == "taint:system:0000:none:000"

    def test_custom_initialization(self):
        env = ProvenanceEnvelope(
            source_type="human", signer_id="operator", cortex_taint="taint:operator:0000:none:123"
        )
        assert env.source_type == "human"
        assert env.signer_id == "operator"


# ─── BeliefObject ───────────────────────────────────────────────────────────


class TestBeliefObject:
    def test_creation_defaults(self):
        belief = BeliefObject(
            proposition="The launch is Q2 2026",
            project="cortex",
        )
        assert belief.confidence_score == 0.5
        assert belief.state == BeliefStatus.ACTIVE
        assert belief.revision_count == 0
        assert belief.relations.entails == ()
        assert belief.relations.discards == ()
        assert belief.arbitrated_by is None
        assert belief.tenant_id == "default"

    def test_frozen(self):
        belief = BeliefObject(proposition="test", project="p")
        with pytest.raises(FrozenInstanceError):
            belief.proposition = "altered"  # type: ignore[misc]

    def test_is_axiomatic(self):
        belief = BeliefObject(
            proposition="Entropy always increases",
            project="physics",
            confidence_score=0.98,
        )
        assert belief.is_axiomatic() is True

    def test_is_quarantined(self):
        belief = BeliefObject(
            proposition="Contradicted claim",
            project="test",
            state=BeliefStatus.QUARANTINED,
        )
        assert belief.is_quarantined() is True

    def test_replace_creates_new(self):
        original = BeliefObject(proposition="v1", project="test")
        revised = replace(original, proposition="v2", revision_count=1)
        assert original.content == "v1"
        assert revised.content == "v2"
        assert revised.revision_count == 1

    def test_serialization_roundtrip(self):
        prov = ProvenanceEnvelope(
            source_hash="abcd",
            source_type="agent",
            tenant_id="test-tenant",
            signer_id="test-signer",
            signature="test-sig",
        )
        rels = BeliefRelations(
            entails=("fact-99", "fact-100"),
            discards=("belief-old-1",),
        )
        belief = BeliefObject(
            proposition="SQLite is the persistence layer",
            project="cortex",
            confidence_score=0.9,
            provenance=prov,
            relations=rels,
            arbitrated_by="deep_think",
        )

        data = belief.to_dict()
        restored = BeliefObject.from_dict(data)

        assert restored.content == belief.content
        assert restored.confidence_score == belief.confidence_score
        assert restored.relations.discards == belief.relations.discards
        assert restored.relations.entails == belief.relations.entails
        assert restored.arbitrated_by == belief.arbitrated_by
        assert restored.provenance.source_hash == "abcd"
        assert restored.provenance.signature == "test-sig"

    def test_id_is_time_sortable(self):
        b1 = BeliefObject(proposition="first", project="test")
        b2 = BeliefObject(proposition="second", project="test")
        assert b1.id[:14] <= b2.id[:14]


# ─── BeliefVerdict ──────────────────────────────────────────────────────────


class TestBeliefVerdict:
    def test_accept_verdict(self):
        verdict = BeliefVerdict(
            action=VerdictAction.ACCEPT,
            model="deep_think",
        )
        assert verdict.action == VerdictAction.ACCEPT
        assert verdict.contradictions == ()
        assert verdict.cost_tokens == 0

    def test_quarantine_verdict(self):
        verdict = BeliefVerdict(
            action=VerdictAction.QUARANTINE,
            model="opus",
            contradictions=("b-1", "b-2"),
            reason="Belief contradicts axiomatic B-1 and B-2",
        )
        assert verdict.action == VerdictAction.QUARANTINE
        assert len(verdict.contradictions) == 2

    def test_frozen(self):
        verdict = BeliefVerdict(action=VerdictAction.SKIP, model="infra")
        with pytest.raises(FrozenInstanceError):
            verdict.action = VerdictAction.ACCEPT  # type: ignore[misc]
