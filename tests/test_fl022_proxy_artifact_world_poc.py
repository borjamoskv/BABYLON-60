"""Tests de verificación en silicio para FL-022-v2 (Proxy -> Artifact -> World).

Verifica:
1. Estructura de las 20 tríadas adversariales (A_i, B_i, C_i) y las 4 brechas (P1..P4).
2. Criterios estrictos de aceptación FL-022-v2:
   - proxy_selected_invalid_artifacts_A > 0 (control positivo de Goodhart físico)
   - invalid_final_artifacts_accepted_C == 0
   - artifact_identity_mismatches_C == 0
   - environment_mismatch_acceptances_C == 0
   - observed_constraint_failures_C == 0
3. Independencia del verificador (optimizer_model != verifier_model).
4. Acoplamiento con BORJARIO IR B3/B6: ScopedClaimRecord exige alcance explícito y
   prohíbe etiquetas ontológicas absolutas sin perfil.
"""

from dataclasses import replace

import pytest

from babylon60.autodidact import (
    Justification,
    JustifiedStatement,
    Modality,
    Obligation,
    ScopedClaimRecord as KernelScopedClaimRecord,
    Statement,
    verify,
)
from scripts.c5_cortex.poc_fl022_proxy_artifact_world import (
    CRITICAL_EFFICIENCY_THRESHOLD,
    NOMINAL_PROFILE_ID,
    OPTIMIZER_MODEL_ID,
    ORTHOGONAL_VERIFIER_MODEL_ID,
    PERTURBED_PROFILE_ID,
    TRIAD_COUNT,
    BabylonFL022v2Gate,
    CandidateArchetype,
    ClaimScopeStatus,
    FailureGapKind,
    ScopedClaimRecord,
    build_20_adversarial_triads,
    run_fl022_v2_experiment,
)


def test_20_adversarial_triads_structure() -> None:
    triads = build_20_adversarial_triads()
    assert len(triads) == TRIAD_COUNT == 20

    gap_counts = {gap: 0 for gap in FailureGapKind}
    for idx, (cand_a, cand_b, cand_c) in enumerate(triads, start=1):
        assert cand_a.triad_id == idx
        assert cand_a.archetype == CandidateArchetype.A_HIGH_PROXY_BAD_FINAL
        assert cand_b.archetype == CandidateArchetype.B_MODEST_PROXY_ROBUST_FINAL
        assert cand_c.archetype == CandidateArchetype.C_VERIFIED_ARTIFACT_RUNTIME_DEGRADED

        # En cada tríada, A tiene el mayor ProxyScore interno pero colapsa al discretizar (< 0.90)
        assert cand_a.proxy_score > cand_b.proxy_score
        assert cand_a.proxy_score > cand_c.proxy_score
        assert cand_a.orthogonal_verifier_score < CRITICAL_EFFICIENCY_THRESHOLD

        # B tiene un artefacto discretizado válido, íntegro y verificado en observación real
        assert cand_b.orthogonal_verifier_score >= CRITICAL_EFFICIENCY_THRESHOLD
        assert cand_b.is_truly_valid_end_to_end is True

        # C pasa la evaluación estática nominal pero falla en la cadena post-verificación (P3/P4)
        assert cand_c.orthogonal_verifier_score >= CRITICAL_EFFICIENCY_THRESHOLD
        assert cand_c.is_truly_valid_end_to_end is False
        gap_counts[cand_c.failure_gap] += 1

    # Las 20 tríadas cubren los tres modos de fallo post-artefacto (P3, P4a, P4b)
    assert gap_counts[FailureGapKind.P3_DEPLOYMENT_IDENTITY_DRIFT] >= 6
    assert gap_counts[FailureGapKind.P4A_ENVIRONMENT_PROFILE_MISMATCH] >= 6
    assert gap_counts[FailureGapKind.P4B_CORRELATED_SIMULATOR_BLINDSPOT] >= 6


def test_fl022_v2_acceptance_criteria_and_falsification_gates() -> None:
    reports = run_fl022_v2_experiment()
    rep_a = reports["A"]
    rep_b = reports["B"]
    rep_c = reports["C"]

    # Control positivo: Política A cae en la trampa de Goodhart en las 20 tríadas
    assert rep_a.proxy_selected_invalid_artifacts == 20
    assert rep_a.invalid_final_artifacts_accepted == 20
    assert rep_a.observed_constraint_failures_accepted == 20

    # Política B evita el candidato A_i gracias al verificador estático, pero cae en C_i
    # porque no comprueba identidad de despliegue (P3), perfil de runtime (P4a) ni observación real (P4b)
    assert rep_b.proxy_selected_invalid_artifacts == 0
    assert rep_b.invalid_final_artifacts_accepted == 20
    assert rep_b.artifact_identity_mismatches_accepted > 0
    assert rep_b.environment_mismatch_acceptances > 0
    assert rep_b.observed_constraint_failures_accepted == 20

    # Política C (BabylonFL022v2Gate): Cero fallos en los cuatro eslabones y 100% de recall sobre B_i
    assert rep_c.proxy_selected_invalid_artifacts == 0
    assert rep_c.invalid_final_artifacts_accepted == 0
    assert rep_c.artifact_identity_mismatches_accepted == 0
    assert rep_c.environment_mismatch_acceptances == 0
    assert rep_c.observed_constraint_failures_accepted == 0
    assert rep_c.valid_artifact_acceptance_rate == 1.0
    assert rep_c.committed_count == 20

    # Medidas reportadas (inversión de ranking entre ProxyScore e utilidad real)
    assert rep_c.proxy_final_rank_correlation < 0.0
    assert rep_c.mean_simulation_reality_gap > 0.02
    assert rep_c.max_simulation_reality_gap > 0.10
    assert 0.0 < rep_c.verification_latency_p99_ms < 20.0


def test_gate_rejects_correlated_simulator_and_single_constraint_violation() -> None:
    triads = build_20_adversarial_triads()
    _, cand_b, _ = triads[0]
    gate = BabylonFL022v2Gate()

    # 1. Si el verificador usa el mismo modelo que el optimizador, es rechazado aunque el score sea alto
    correlated_cand = replace(cand_b, verifier_model_id=OPTIMIZER_MODEL_ID)
    ok_corr, reason_corr, claim_corr = gate.verify_candidate(correlated_cand)
    assert ok_corr is False
    assert reason_corr == "CORRELATED_VERIFIER_MODEL_REJECTED"
    assert claim_corr.status == ClaimScopeStatus.FALSIFIED

    # 2. Falsación: si un artefacto auténtico y en el perfil correcto viola una restricción crítica observada,
    #    la Política C jamás lo acepta.
    violating_cand = replace(cand_b, observed_parasitic_heating_ok=False)
    ok_viol, reason_viol, claim_viol = gate.verify_candidate(violating_cand)
    assert ok_viol is False
    assert reason_viol == "OBSERVED_REAL_WORLD_CONSTRAINT_FAILURE"
    assert claim_viol.status == ClaimScopeStatus.FALSIFIED

    # 3. Si el entorno observado diverge del perfil verificado P, es rechazado por alcance (B3)
    env_drift_cand = replace(cand_b, observed_profile_id=PERTURBED_PROFILE_ID)
    ok_env, reason_env, claim_env = gate.verify_candidate(env_drift_cand)
    assert ok_env is False
    assert reason_env == "ENVIRONMENT_PROFILE_MISMATCH"
    assert claim_env.status == ClaimScopeStatus.REJECTED_OUT_OF_SCOPE


def test_scoped_claim_record_enforces_explicit_scope_bjr_e013() -> None:
    with pytest.raises(ValueError, match="BJR-E013"):
        ScopedClaimRecord.create(
            claim_id="BJR-INVALID-001",
            threshold=0.90,
            status=ClaimScopeStatus.OBSERVED,
            optimizer_model_id=OPTIMIZER_MODEL_ID,
            verifier_model_id="VER:FDTD",
            ir_digest="aa" * 32,
            verified_artifact_digest="bb" * 32,
            deployed_artifact_digest="bb" * 32,
            verified_profile_id="",
            observed_profile_id=NOMINAL_PROFILE_ID,
            logical_tick=1,
            verified_efficiency=0.92,
            observed_efficiency=0.91,
            critical_constraints_pass=True,
        )


def test_autodidact_kernel_epistemology_fl022_v2_obligations() -> None:
    valid_record = KernelScopedClaimRecord(
        claim_id="BJR-KISH-001",
        claim="efficiency >= 0.90 under PROFILE:NOMINAL",
        verifier_model=ORTHOGONAL_VERIFIER_MODEL_ID,
        optimizer_model=OPTIMIZER_MODEL_ID,
        artifact_digest="ab" * 32,
        deployed_digest="ab" * 32,
        verified_profile=NOMINAL_PROFILE_ID,
        observed_profile=NOMINAL_PROFILE_ID,
        logical_tick=42,
        critical_constraints_pass=True,
        result="OBSERVED",
    )
    assert valid_record.is_valid_fl022_v2 is True

    fl022_obligations = [
        Obligation.PROVENANCE,
        Obligation.REPRODUCIBILITY,
        Obligation.ENVIRONMENT_MATCH,
        Obligation.MODEL_ORTHOGONALITY,
        Obligation.OBSERVED_CONSTRAINTS,
    ]
    stmt = Statement(
        content=valid_record.claim,
        modality=Modality.EPISTEMIC,
        obligations=fl022_obligations,
    )
    js_ok = JustifiedStatement(
        statement=stmt,
        justification=Justification(
            kind="Observation",
            parameters=valid_record.to_justification_parameters(),
            confidence=0.99,
        ),
    )
    assert verify(js_ok) is True

    # 1. Fallo por perfil ambiental divergente (ENVIRONMENT_MATCH)
    params_env_mismatch = valid_record.to_justification_parameters()
    params_env_mismatch["observed_profile"] = PERTURBED_PROFILE_ID
    assert (
        verify(
            JustifiedStatement(
                statement=stmt,
                justification=Justification("Observation", params_env_mismatch, 0.99),
            )
        )
        is False
    )

    # 2. Fallo por verificador correlacionado con el optimizador (MODEL_ORTHOGONALITY)
    params_corr = valid_record.to_justification_parameters()
    params_corr["verifier_model"] = OPTIMIZER_MODEL_ID
    assert (
        verify(
            JustifiedStatement(
                statement=stmt,
                justification=Justification("Observation", params_corr, 0.99),
            )
        )
        is False
    )

    # 3. Fallo por discrepancia de hash desplegado o violación de restricción observada (OBSERVED_CONSTRAINTS)
    params_tampered = valid_record.to_justification_parameters()
    params_tampered["deployed_digest"] = "cd" * 32
    assert (
        verify(
            JustifiedStatement(
                statement=stmt,
                justification=Justification("Observation", params_tampered, 0.99),
            )
        )
        is False
    )

    # 4. Rechazo de etiqueta ontológica absoluta 'SAFE' (BJR-E021)
    with pytest.raises(ValueError, match="BJR-E021"):
        KernelScopedClaimRecord(
            claim_id="BJR-KISH-002",
            claim="unscoped safe label",
            verifier_model=ORTHOGONAL_VERIFIER_MODEL_ID,
            optimizer_model=OPTIMIZER_MODEL_ID,
            artifact_digest="ab" * 32,
            deployed_digest="ab" * 32,
            verified_profile=NOMINAL_PROFILE_ID,
            observed_profile=NOMINAL_PROFILE_ID,
            logical_tick=43,
            critical_constraints_pass=True,
            result="SAFE",
        )
