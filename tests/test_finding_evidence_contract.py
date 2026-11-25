"""Falsadores de FL-VERIFY-01 sobre el contrato mínimo de evidencia (nivel bloque)."""

import hashlib

import pytest

from babylon60.verification.finding_contract import (
    Authorization,
    ContractViolation,
    Finding,
    Outcome,
    ReproductionRun,
    authorize_effect,
    is_verified,
    verify_authorization_in_ledger,
)
from babylon60.verification.verification_gate import RiskLevel, VerificationGate


def _d(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _finding() -> Finding:
    return Finding("F1", "BEH_AUTH_BYPASS", _d("artifact-v1"), producer_id="writer")


def _run(
    *,
    finding_id: str = "F1",
    artifact_digest: str = _d("artifact-v1"),
    observed_behavior_id: str = "BEH_AUTH_BYPASS",
    outcome: Outcome = Outcome.REPRODUCED,
    verifier_id: str = "verifier",
) -> ReproductionRun:
    return ReproductionRun(
        finding_id=finding_id,
        artifact_digest=artifact_digest,
        observed_behavior_id=observed_behavior_id,
        outcome=outcome,
        verifier_id=verifier_id,
    )


def test_verified_when_run_matches_artifact_and_behavior():
    assert is_verified(_finding(), [_run()])


def test_not_verified_without_run():
    assert not is_verified(_finding(), [])


def test_not_verified_on_artifact_hash_mismatch():
    assert not is_verified(_finding(), [_run(artifact_digest=_d("artifact-v2"))])


def test_not_verified_when_behavior_differs():
    # Lección ETH: reproducir algo distinto a lo afirmado no verifica el hallazgo.
    assert not is_verified(_finding(), [_run(observed_behavior_id="BEH_CRASH")])


def test_not_verified_when_not_reproduced():
    assert not is_verified(_finding(), [_run(outcome=Outcome.NOT_REPRODUCED)])


def test_not_verified_when_producer_is_verifier():
    assert not is_verified(_finding(), [_run(verifier_id="writer")])


def test_empty_digest_rejected():
    with pytest.raises(ContractViolation):
        Finding("F2", "B", hashlib.sha256(b"").hexdigest(), "w")
    with pytest.raises(ContractViolation):
        _run(artifact_digest="")


@pytest.mark.parametrize("record_type", [Finding, ReproductionRun, Authorization])
@pytest.mark.parametrize(
    "digest",
    ["z" * 64, "a" * 63 + "g", "é" * 64, "０" * 64, "ａ" * 64, "a" * 63 + "\n", "a" * 63, "a" * 65, "", None, 42, 64],
)
def test_all_evidence_records_reject_malformed_digests(record_type, digest):
    with pytest.raises(ContractViolation):
        if record_type is Finding:
            Finding("F1", "behavior", digest, "writer")
        elif record_type is ReproductionRun:
            _run(artifact_digest=digest)
        else:
            Authorization("F1", "apply_patch", digest)


@pytest.mark.parametrize("digest", [_d("artifact"), _d("artifact").upper()])
def test_hex_digest_case_is_preserved(digest):
    finding = Finding("F1", "behavior", digest, "writer")
    run = _run(artifact_digest=digest, observed_behavior_id="behavior")
    authorization = Authorization("F1", "apply_patch", digest)
    assert finding.inspected_artifact_digest == run.artifact_digest == authorization.signoff_receipt_digest == digest
    assert is_verified(finding, [run])


@pytest.mark.parametrize("record_type", [Finding, ReproductionRun, Authorization])
def test_uppercase_empty_content_digest_rejected(record_type):
    digest = hashlib.sha256(b"").hexdigest().upper()
    with pytest.raises(ContractViolation):
        if record_type is Finding:
            Finding("F1", "behavior", digest, "writer")
        elif record_type is ReproductionRun:
            _run(artifact_digest=digest)
        else:
            Authorization("F1", "apply_patch", digest)


@pytest.mark.parametrize("digest", ["abcdef0123456789" * 4, "ABCDEF0123456789" * 4])
def test_hexadecimal_digests_preserve_supported_case(digest):
    finding = Finding("F1", "B", digest, "writer")
    run = ReproductionRun("F1", digest, "B", Outcome.REPRODUCED, "verifier")
    assert is_verified(finding, [run])


def test_effect_requires_authorization_for_same_finding_and_action():
    f, runs = _finding(), [_run()]
    auth = Authorization("F1", "apply_patch", _d("receipt"))
    authorize_effect(f, runs, auth, "apply_patch")
    with pytest.raises(ContractViolation):
        authorize_effect(f, runs, None, "apply_patch")
    with pytest.raises(ContractViolation):
        authorize_effect(f, runs, auth, "merge")


def test_effect_blocked_on_unverified_finding_even_if_authorized():
    auth = Authorization("F1", "apply_patch", _d("receipt"))
    with pytest.raises(ContractViolation):
        authorize_effect(_finding(), [], auth, "apply_patch")


# --- Vínculo con el ledger de VerificationGate ---


def _gate_with_receipt(finding_id="F1", action="apply_patch", decision="APPROVED"):
    gate = VerificationGate()
    receipt = gate.register_sign_off(finding_id, action, RiskLevel.HIGH, decision)
    return gate, receipt.cryptographic_digest


def test_ledger_accepts_matching_approved_receipt():
    gate, digest = _gate_with_receipt()
    verify_authorization_in_ledger(Authorization("F1", "apply_patch", digest), gate)


def test_ledger_rejects_unknown_receipt():
    gate, _ = _gate_with_receipt()
    with pytest.raises(ContractViolation):
        verify_authorization_in_ledger(Authorization("F1", "apply_patch", _d("forged")), gate)


@pytest.mark.parametrize(
    ("finding_id", "action", "decision"),
    [("F2", "apply_patch", "APPROVED"), ("F1", "merge", "APPROVED"), ("F1", "apply_patch", "REJECTED")],
)
def test_ledger_rejects_receipt_for_other_finding_action_or_decision(finding_id, action, decision):
    gate, digest = _gate_with_receipt(finding_id, action, decision)
    with pytest.raises(ContractViolation):
        verify_authorization_in_ledger(Authorization("F1", "apply_patch", digest), gate)


def test_ledger_rejects_tampered_chain():
    gate, digest = _gate_with_receipt()
    gate._conn.execute("UPDATE audit_ledger SET decision = 'APPROVED', action_name = 'tampered'")
    with pytest.raises(ContractViolation):
        verify_authorization_in_ledger(Authorization("F1", "apply_patch", digest), gate)
