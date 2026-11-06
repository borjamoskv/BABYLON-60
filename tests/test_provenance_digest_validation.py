"""Malformed declared evidence must not acquire a verified provenance level."""

from dataclasses import replace

import pytest

from babylon60.memory.provenance_arbiter import (
    AttributionClaim,
    ClaimScope,
    DerivationKind,
    EventIdentityTuple,
    ProvenanceEnvelope,
    ProvenanceLevel,
    VerdictOutcome,
    compute_content_identity,
    evaluate_provenance_claim,
)


def envelope():
    return ProvenanceEnvelope(
        content="fixture",
        host_platform="fixture",
        derivation_kind=DerivationKind.ORIGINAL_MESSAGE,
        event_tuple=EventIdentityTuple("fixture", "conversation", "message"),
        native_export_digest_b3=compute_content_identity("export fixture"),
    )


@pytest.mark.parametrize("field", [
    "native_export_digest_b3", "external_anchor_digest_b3", "execution_receipt_digest_b3",
])
@pytest.mark.parametrize("digest", [
    "b3:not-a-digest", "b3:", "b3:" + "g" * 64, "b3:" + "a" * 63,
    "b3:" + "a" * 65, "b3:" + "a" * 64 + "\n", 42,
])
def test_malformed_evidence_is_rejected_without_promoting_its_level(field, digest):
    record = replace(envelope(), **{field: digest})
    claim = AttributionClaim(
        "malformed-export", ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
        claimed_platform="fixture", claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED,
    )
    assert not record.verify_integrity()
    assert record.effective_provenance_level() == ProvenanceLevel.CLAIMED
    decision = evaluate_provenance_claim(record, claim)
    assert decision.outcome == VerdictOutcome.REJECTED_OVERATTRIBUTION
    assert not decision.attested
    assert not decision.integrity_verified


def test_well_formed_evidence_retains_existing_decision_and_identity_binding():
    record = envelope()
    claim = AttributionClaim(
        "declared-export", ClaimScope.NATIVE_MESSAGE_TRANSCRIPT,
        claimed_platform="fixture", claimed_min_level=ProvenanceLevel.NATIVE_EXPORT_VERIFIED,
    )
    assert record.verify_integrity(record.content_identity)
    assert evaluate_provenance_claim(record, claim).attested
    assert not evaluate_provenance_claim(
        record, claim, expected_content_b3=compute_content_identity("different content"),
    ).attested


@pytest.mark.parametrize("digest", ["b3:not-a-digest", "b3:" + "ａ" * 64, 42])
def test_malformed_expected_content_is_rejected_without_a_type_error(digest):
    assert not envelope().verify_integrity(digest)
