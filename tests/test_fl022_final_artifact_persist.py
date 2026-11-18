"""FL-022 Oracle Suite in CORTEX-Persist: Final-Artifact Verification.

Verifies the CORTEX-Persist lineage and authorization gate for FL-022 across 100
design candidates (60 valid, 16 discretization-degraded proxy winners, 6 independent
solver disagreements, 6 post-verification substitutions, 6 stale evidence epochs,
and 6 cross-version target mismatches):

- invalid_artifacts_accepted_C == 0
- stale_evidence_accepted_C == 0
- artifact_identity_mismatch == 0
- unauthorized_commits_C == 0
- valid_artifact_acceptance_rate >= 0.95
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import pytest

from babylon60.memory import (
    FinalArtifactGate,
    FinalArtifactRecord,
    FinalArtifactVerificationError,
    MemoryGovernanceEngine,
    compute_artifact_b3,
)


@pytest.fixture
def engine(tmp_path: Path) -> MemoryGovernanceEngine:
    db_file = tmp_path / "fl022_final_artifact_persist.db"
    eng = MemoryGovernanceEngine(db_file)
    eng.register_principal_key("tenant-c5", "operator-root", b"sovereign-root-secret-key-0001")
    return eng


def test_fl022_cortex_persist_100_candidates_contract(engine: MemoryGovernanceEngine) -> None:
    """Evaluates 100 candidates in CORTEX-Persist under Configurations A, B, and C."""
    active_epoch = 77
    gate = FinalArtifactGate(
        engine,
        tenant_id="tenant-c5",
        principal="operator-root",
        active_policy_epoch=active_epoch,
        final_utility_threshold_bps=6_200,
        max_solver_delta_bps=120,
    )

    records: list[tuple[FinalArtifactRecord, bool]] = []

    for idx in range(100):
        cid = idx + 1
        opt_hash = compute_artifact_b3(f"opt-state-{cid}")
        ver_hash = compute_artifact_b3(f"verified-final-artifact-{cid}")

        if idx < 60:
            # 60 NominalValid candidates (e.g., metagrating 81.2% -> 94.6%, metalens 40.0% -> 65.2%)
            rec = gate.register_candidate_lineage(
                candidate_id=cid,
                proxy_score_bps=8_400 + idx * 18,
                transform_spec="lithography_quantization_45nm_grid_v1",
                primary_final_utility_bps=6_520 + idx * 48,
                independent_solver_utility_bps=6_520 + idx * 48 - 35,
                critical_constraints_pass=True,
                optimized_state_hash_b3=opt_hash,
                verified_artifact_hash_b3=ver_hash,
            )
            records.append((rec, True))
        elif idx < 76:
            # 16 DiscretizationDegraded candidates: highest ProxyScore, degraded after discretization
            offset = idx - 60
            rec = gate.register_candidate_lineage(
                candidate_id=cid,
                proxy_score_bps=9_250 + offset * 28,
                transform_spec="lithography_quantization_45nm_grid_v1",
                primary_final_utility_bps=4_100 + offset * 105,
                independent_solver_utility_bps=4_060 + offset * 105,
                critical_constraints_pass=(offset % 2 != 0),
                optimized_state_hash_b3=opt_hash,
                verified_artifact_hash_b3=ver_hash,
            )
            records.append((rec, False))
        elif idx < 82:
            # 6 IndependentSolverDisagreement candidates
            offset = idx - 76
            rec = gate.register_candidate_lineage(
                candidate_id=cid,
                proxy_score_bps=8_900 + offset * 40,
                transform_spec="lithography_quantization_45nm_grid_v1",
                primary_final_utility_bps=6_850 + offset * 30,
                independent_solver_utility_bps=5_100 + offset * 25,
                critical_constraints_pass=True,
                optimized_state_hash_b3=opt_hash,
                verified_artifact_hash_b3=ver_hash,
            )
            records.append((rec, False))
        elif idx < 88:
            # 6 PostVerificationSubstitution candidates: Hash(a_presented) != Hash(a_verified)
            tampered_hash = compute_artifact_b3(f"tampered-post-verification-{cid}")
            rec = gate.register_candidate_lineage(
                candidate_id=cid,
                proxy_score_bps=9_100,
                transform_spec="lithography_quantization_45nm_grid_v1",
                primary_final_utility_bps=7_800,
                independent_solver_utility_bps=7_760,
                critical_constraints_pass=True,
                optimized_state_hash_b3=opt_hash,
                verified_artifact_hash_b3=ver_hash,
                presented_artifact_hash_b3=tampered_hash,
            )
            records.append((rec, False))
        elif idx < 94:
            # 6 StaleEvidenceInjection candidates: evidence_epoch < active_policy_epoch
            rec = gate.register_candidate_lineage(
                candidate_id=cid,
                proxy_score_bps=9_050,
                transform_spec="lithography_quantization_45nm_grid_v1",
                primary_final_utility_bps=7_600,
                independent_solver_utility_bps=7_550,
                critical_constraints_pass=True,
                optimized_state_hash_b3=opt_hash,
                verified_artifact_hash_b3=ver_hash,
                evidence_epoch=active_epoch - 2,
            )
            records.append((rec, False))
        else:
            # 6 CrossVersionEvidenceMismatch candidates: evidence_target_id != candidate_id
            rec = gate.register_candidate_lineage(
                candidate_id=cid,
                proxy_score_bps=9_150,
                transform_spec="lithography_quantization_45nm_grid_v1",
                primary_final_utility_bps=7_900,
                independent_solver_utility_bps=7_850,
                critical_constraints_pass=True,
                optimized_state_hash_b3=opt_hash,
                verified_artifact_hash_b3=ver_hash,
                evidence_target_id=cid + 5_000,
            )
            records.append((rec, False))

    # 1. Verify argmax_x ProxyScore(x) != argmax_x FinalUtility(T(x))
    best_proxy_rec, best_proxy_valid = max(records, key=lambda item: item[0].proxy_score_bps)
    best_final_rec, _ = max(
        (item for item in records if item[1]),
        key=lambda item: item[0].primary_final_utility_bps,
    )
    assert best_proxy_rec.candidate_id != best_final_rec.candidate_id
    assert not best_proxy_valid

    # 2. Evaluate Configurations A, B, and C
    invalid_artifacts_accepted_a = 0
    invalid_artifacts_accepted_b = 0
    invalid_artifacts_accepted_c = 0
    stale_evidence_accepted_c = 0
    artifact_identity_mismatch = 0
    unauthorized_commits_c = 0
    valid_accepted_c = 0
    valid_total = 0

    for rec, is_truly_valid in records:
        if is_truly_valid:
            valid_total += 1

        # Configuration A: ProxyScore >= 8000 bps
        if rec.proxy_score_bps >= 8_000 and not is_truly_valid:
            invalid_artifacts_accepted_a += 1

        # Configuration B: Primary final utility + critical constraints without independent solver or identity/epoch binding
        if rec.primary_final_utility_bps >= 6_200 and rec.critical_constraints_pass and not is_truly_valid:
            invalid_artifacts_accepted_b += 1

        # Configuration C: Full FL-022 gate in CORTEX-Persist
        decision = gate.authorize_publication(rec)
        if decision.accepted:
            assert decision.authorization_record_id is not None
            assert decision.joint_evidence_digest_b3 is not None
            if decision.final_artifact_hash_b3 != rec.verified_artifact_hash_b3:
                artifact_identity_mismatch += 1
            if rec.evidence_epoch < active_epoch:
                stale_evidence_accepted_c += 1
            if is_truly_valid:
                valid_accepted_c += 1
            else:
                invalid_artifacts_accepted_c += 1
                unauthorized_commits_c += 1
        else:
            assert not is_truly_valid
            assert decision.authorization_record_id is None

    assert invalid_artifacts_accepted_a == 40
    assert invalid_artifacts_accepted_b == 24

    assert invalid_artifacts_accepted_c == 0
    assert stale_evidence_accepted_c == 0
    assert artifact_identity_mismatch == 0
    assert unauthorized_commits_c == 0

    valid_acceptance_rate = valid_accepted_c / valid_total
    assert valid_total == 60
    assert valid_accepted_c == 60
    assert valid_acceptance_rate >= 0.95


def test_fl022_replay_and_forged_digest_are_rejected(engine: MemoryGovernanceEngine) -> None:
    """Verifies anti-replay and tamper detection on verifier attestation digests."""
    gate = FinalArtifactGate(
        engine,
        tenant_id="tenant-c5",
        principal="operator-root",
        active_policy_epoch=10,
    )
    opt_hash = compute_artifact_b3("opt-1")
    ver_hash = compute_artifact_b3("ver-1")

    rec = gate.register_candidate_lineage(
        candidate_id=1,
        proxy_score_bps=9_000,
        transform_spec="quantize_v1",
        primary_final_utility_bps=8_200,
        independent_solver_utility_bps=8_150,
        critical_constraints_pass=True,
        optimized_state_hash_b3=opt_hash,
        verified_artifact_hash_b3=ver_hash,
    )

    # Forged attestation digest is rejected before consuming replay state
    forged = replace(rec, verifier_attestation_digest_b3="a" * 64)
    dec_forged = gate.authorize_publication(forged)
    assert not dec_forged.accepted
    assert dec_forged.reason == "invalid_verifier_attestation_digest"

    # First legitimate authorization succeeds
    dec_first = gate.authorize_publication(rec)
    assert dec_first.accepted

    # Second authorization with identical candidate + artifact hash is blocked by anti-replay
    dec_replay = gate.authorize_publication(rec)
    assert not dec_replay.accepted
    assert dec_replay.reason == "replay_detected"

    with pytest.raises(FinalArtifactVerificationError):
        gate.register_candidate_lineage(
            candidate_id=2,
            proxy_score_bps=9_000,
            transform_spec="quantize_v1",
            primary_final_utility_bps=8_200,
            independent_solver_utility_bps=8_150,
            critical_constraints_pass=True,
            optimized_state_hash_b3="not-a-valid-hex",
            verified_artifact_hash_b3=ver_hash,
        )
