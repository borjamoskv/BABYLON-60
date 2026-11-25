r"""PoC FL-022-v2: Cadena Proxy -> IR -> Artifact -> Deployed -> Observed Real-World Behavior.

Modela y falsifica empíricamente la brecha de transducción descubierta en diseño
nanofotónico agéntico (Goodhart físico en la frontera de discretización/compilación)
extendida a la cadena completa de cinco estratos:

  OPTIMIZER (Proxy Score)
    -> [P1: proxy_gap]
  INTERMEDIATE REPRESENTATION (IR continua / simbólica)
    -> [P2: transformation_gap]
  FINAL ARTIFACT (Artefacto discretizado / binario)
    -> [P3: deployment_gap]
  DEPLOYED / FABRICATED OBJECT (Objeto materializado en runtime)
    -> [P4: reality_gap]
  OBSERVED REAL-WORLD BEHAVIOR (Comportamiento físico / runtime medido)

Evalúa 20 tríadas adversariales deterministas (60 candidatos en total):
  - Candidato A_i: ProxyScore alto (máximo en la tríada), pero artefacto final
    discretizado inválido (< 0.90) por colapso en P1/P2.
  - Candidato B_i: ProxyScore moderado, pero artefacto final discretizado robusto
    (>= 0.90), identidad íntegra, perfil ambiental coincidente y observación real PASS.
  - Candidato C_i: Artefacto discretizado aparentemente válido en verificación estática
    o en simulador correlacionado (>= 0.90), pero falla en el mundo real por:
      * P3 (deployment_gap): Hash(a_deployed) != Hash(a_verified),
      * P4a (environment_mismatch): perfil de runtime perturbado != perfil verificado P,
      * P4b (correlated_simulator_gap): el simulador naif coincide con el optimizador,
        ocultando una degradación física bajo el observador real.

Contrasta tres políticas de aceptación:
  - Política A (MaxProxyPolicy): Selecciona por máximo ProxyScore interno.
  - Política B (IndependentFinalArtifactPolicy): Evalúa el artefacto final discretizado,
    pero sin verificar identidad post-despliegue, contorno de runtime ni observación real.
  - Política C (BabylonFL022v2Gate): Exige verificador ortogonal (verifier_model != optimizer_model),
    identidad criptográfica BLAKE3/SHA-256 (H(a_deployed) == H(a_verified)),
    EnvironmentMatch(P_verified, E_observed), CriticalConstraints(Observed(a)) == PASS
    y emisión de ScopedClaimRecord (BORJARIO IR B3/B6: cero etiquetas status=SAFE sin alcance).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Final

TRIAD_COUNT: Final[int] = 20
CRITICAL_EFFICIENCY_THRESHOLD: Final[float] = 0.90
NOMINAL_PROFILE_ID: Final[str] = "PROFILE:METAGRATING_1550NM_TE_295K_NOMINAL"
PERTURBED_PROFILE_ID: Final[str] = "PROFILE:METAGRATING_1550NM_TE_340K_THERMAL_DRIFT"
OPTIMIZER_MODEL_ID: Final[str] = "OPT:PARAXIAL_CONTINUOUS_RELAXATION_V1"
ORTHOGONAL_VERIFIER_MODEL_ID: Final[str] = "VER:FULLWAVE_FDTD_SUBPIXEL_SOVEREIGN_V2"


class CandidateArchetype(str, Enum):
    A_HIGH_PROXY_BAD_FINAL = "A_HIGH_PROXY_BAD_FINAL"
    B_MODEST_PROXY_ROBUST_FINAL = "B_MODEST_PROXY_ROBUST_FINAL"
    C_VERIFIED_ARTIFACT_RUNTIME_DEGRADED = "C_VERIFIED_ARTIFACT_RUNTIME_DEGRADED"


class FailureGapKind(str, Enum):
    NONE = "NONE"
    P1_P2_PROXY_DISCRETIZATION_COLLAPSE = "P1_P2_PROXY_DISCRETIZATION_COLLAPSE"
    P3_DEPLOYMENT_IDENTITY_DRIFT = "P3_DEPLOYMENT_IDENTITY_DRIFT"
    P4A_ENVIRONMENT_PROFILE_MISMATCH = "P4A_ENVIRONMENT_PROFILE_MISMATCH"
    P4B_CORRELATED_SIMULATOR_BLINDSPOT = "P4B_CORRELATED_SIMULATOR_BLINDSPOT"


class ClaimScopeStatus(str, Enum):
    """Estados permitidos bajo BORJARIO IR B2/B6 (prohibido SAFE ontológico absoluto)."""

    SUPPORTED = "SUPPORTED"
    OBSERVED = "OBSERVED"
    FALSIFIED = "FALSIFIED"
    REJECTED_OUT_OF_SCOPE = "REJECTED_OUT_OF_SCOPE"


def _canonical_digest(domain: str, payload: str) -> str:
    """Calcula el digest canónico determinista (dominio separado, cero reloj de pared)."""
    h = hashlib.blake2b(digest_size=32)
    h.update(domain.encode("utf-8"))
    h.update(b":")
    h.update(payload.encode("utf-8"))
    return h.hexdigest()


@dataclass(frozen=True, slots=True)
class ScopedClaimRecord:
    """Afirmación delimitada en CORTEX (BORJARIO IR B1, B2, B3, B6).

    Sustituye cualquier etiqueta global `artifact.status = SAFE` por una tupla
    verificable atada a perfil, modelo verificador, digest y resultado observado.
    """

    claim_id: str
    claim_text: str
    status: ClaimScopeStatus
    optimizer_model_id: str
    verifier_model_id: str
    ir_digest: str
    verified_artifact_digest: str
    deployed_artifact_digest: str
    verified_profile_id: str
    observed_profile_id: str
    logical_tick: int
    verified_efficiency: float
    observed_efficiency: float
    critical_constraints_pass: bool
    evidence_digest: str

    @classmethod
    def create(
        cls,
        *,
        claim_id: str,
        threshold: float,
        status: ClaimScopeStatus,
        optimizer_model_id: str,
        verifier_model_id: str,
        ir_digest: str,
        verified_artifact_digest: str,
        deployed_artifact_digest: str,
        verified_profile_id: str,
        observed_profile_id: str,
        logical_tick: int,
        verified_efficiency: float,
        observed_efficiency: float,
        critical_constraints_pass: bool,
    ) -> ScopedClaimRecord:
        if not verified_profile_id or not observed_profile_id:
            raise ValueError("BJR-E013: ScopedClaimRecord requires non-empty profile scope.")
        claim_text = f"efficiency >= {threshold:.2f} under profile {verified_profile_id}"
        evidence_payload = (
            f"{claim_id}:{claim_text}:{status.value}:{optimizer_model_id}:{verifier_model_id}:"
            f"{ir_digest}:{verified_artifact_digest}:{deployed_artifact_digest}:"
            f"{verified_profile_id}:{observed_profile_id}:{logical_tick}:"
            f"{verified_efficiency:.6f}:{observed_efficiency:.6f}:{int(critical_constraints_pass)}"
        )
        return cls(
            claim_id=claim_id,
            claim_text=claim_text,
            status=status,
            optimizer_model_id=optimizer_model_id,
            verifier_model_id=verifier_model_id,
            ir_digest=ir_digest,
            verified_artifact_digest=verified_artifact_digest,
            deployed_artifact_digest=deployed_artifact_digest,
            verified_profile_id=verified_profile_id,
            observed_profile_id=observed_profile_id,
            logical_tick=logical_tick,
            verified_efficiency=verified_efficiency,
            observed_efficiency=observed_efficiency,
            critical_constraints_pass=critical_constraints_pass,
            evidence_digest=_canonical_digest("B60:FL022V2:CLAIM", evidence_payload),
        )


@dataclass(frozen=True, slots=True)
class CandidatePipelineTrace:
    """Traza completa de las 5 capas para un candidato dentro de una tríada adversarial."""

    triad_id: int
    candidate_id: str
    archetype: CandidateArchetype
    failure_gap: FailureGapKind
    optimizer_model_id: str
    verifier_model_id: str
    # Capa 1 & 2: Optimizador e IR continua
    proxy_score: float
    ir_representation: str
    ir_digest: str
    # Capa 3: Artefacto discretizado final y su evaluación en verificadores
    final_artifact_payload: str
    verified_artifact_digest: str
    correlated_verifier_score: float
    orthogonal_verifier_score: float
    verified_profile_id: str
    # Capa 4: Objeto desplegado / fabricado
    deployed_artifact_payload: str
    deployed_artifact_digest: str
    # Capa 5: Comportamiento observado en mundo real / runtime
    observed_profile_id: str
    observed_real_efficiency: float
    observed_parasitic_heating_ok: bool
    verification_latency_ms: float
    logical_tick: int

    @property
    def identity_intact(self) -> bool:
        return self.verified_artifact_digest == self.deployed_artifact_digest

    @property
    def models_orthogonal(self) -> bool:
        return self.optimizer_model_id != self.verifier_model_id

    @property
    def environment_matched(self) -> bool:
        return self.verified_profile_id == self.observed_profile_id

    @property
    def observed_critical_constraints_pass(self) -> bool:
        return self.observed_real_efficiency >= CRITICAL_EFFICIENCY_THRESHOLD and self.observed_parasitic_heating_ok

    @property
    def is_truly_valid_end_to_end(self) -> bool:
        return (
            self.identity_intact
            and self.models_orthogonal
            and self.environment_matched
            and self.orthogonal_verifier_score >= CRITICAL_EFFICIENCY_THRESHOLD
            and self.observed_critical_constraints_pass
        )


@dataclass(frozen=True, slots=True)
class TriadDecision:
    triad_id: int
    policy_name: str
    selected_candidate_id: str | None
    committed: bool
    rejection_reason: str | None
    scoped_claim: ScopedClaimRecord | None
    latency_ms: float


@dataclass(frozen=True, slots=True)
class PolicyEvaluationReport:
    policy_name: str
    triads_evaluated: int
    committed_count: int
    proxy_selected_invalid_artifacts: int
    invalid_final_artifacts_accepted: int
    artifact_identity_mismatches_accepted: int
    environment_mismatch_acceptances: int
    observed_constraint_failures_accepted: int
    valid_artifact_acceptance_rate: float
    proxy_final_rank_correlation: float
    mean_simulation_reality_gap: float
    max_simulation_reality_gap: float
    verification_latency_p99_ms: float
    decisions: list[TriadDecision] = field(default_factory=list, repr=False)


def build_20_adversarial_triads() -> list[
    tuple[CandidatePipelineTrace, CandidatePipelineTrace, CandidatePipelineTrace]
]:
    """Construye las 20 tríadas adversariales deterministas (A_i, B_i, C_i)."""
    triads: list[tuple[CandidatePipelineTrace, CandidatePipelineTrace, CandidatePipelineTrace]] = []

    for idx in range(1, TRIAD_COUNT + 1):
        base_tick = 22000 + idx * 10
        # --- Candidato A_i: Alto ProxyScore en IR continua, colapso al discretizar (P1 + P2) ---
        proxy_a = round(0.952 + (idx % 5) * 0.008, 4)  # [0.952, 0.984]
        ortho_a = round(0.794 + (idx % 6) * 0.011, 4)  # [0.794, 0.849] < 0.90 (como en el paper: 79.4%)
        corr_a = round(proxy_a - 0.015, 4)
        obs_a = round(ortho_a - 0.008, 4)
        ir_a = f"IR:CONTINUOUS_GREYSCALE_GRATING:triad={idx}:cand=A:subwavelength_ grey=0.47"
        art_a = f"BIN:METAGRATING_MASK_64X64:triad={idx}:cand=A:quantized_loss=HIGH"
        dig_ir_a = _canonical_digest("B60:IR", ir_a)
        dig_art_a = _canonical_digest("B60:ART", art_a)

        cand_a = CandidatePipelineTrace(
            triad_id=idx,
            candidate_id=f"TRIAD-{idx:02d}-A",
            archetype=CandidateArchetype.A_HIGH_PROXY_BAD_FINAL,
            failure_gap=FailureGapKind.P1_P2_PROXY_DISCRETIZATION_COLLAPSE,
            optimizer_model_id=OPTIMIZER_MODEL_ID,
            verifier_model_id=ORTHOGONAL_VERIFIER_MODEL_ID,
            proxy_score=proxy_a,
            ir_representation=ir_a,
            ir_digest=dig_ir_a,
            final_artifact_payload=art_a,
            verified_artifact_digest=dig_art_a,
            correlated_verifier_score=corr_a,
            orthogonal_verifier_score=ortho_a,
            verified_profile_id=NOMINAL_PROFILE_ID,
            deployed_artifact_payload=art_a,
            deployed_artifact_digest=dig_art_a,
            observed_profile_id=NOMINAL_PROFILE_ID,
            observed_real_efficiency=obs_a,
            observed_parasitic_heating_ok=True,
            verification_latency_ms=round(0.45 + (idx % 4) * 0.05, 3),
            logical_tick=base_tick + 1,
        )

        # --- Candidato B_i: ProxyScore menor que A_i, pero artefacto binario final óptimo y robusto ---
        proxy_b = round(0.875 + (idx % 5) * 0.007, 4)  # [0.875, 0.903] < proxy_a
        ortho_b = round(0.909 + (idx % 6) * 0.007, 4)  # [0.909, 0.944] >= 0.90 (paper: 90.9% - 94.6%)
        corr_b = round(proxy_b + 0.012, 4)
        obs_b = round(ortho_b - 0.004, 4)  # >= 0.905 (pasa holgadamente en realidad)
        ir_b = f"IR:CONTINUOUS_GREYSCALE_GRATING:triad={idx}:cand=B:binarization_penalty=STRICT"
        art_b = f"BIN:METAGRATING_MASK_64X64:triad={idx}:cand=B:quantized_loss=MINIMAL"
        dig_ir_b = _canonical_digest("B60:IR", ir_b)
        dig_art_b = _canonical_digest("B60:ART", art_b)

        cand_b = CandidatePipelineTrace(
            triad_id=idx,
            candidate_id=f"TRIAD-{idx:02d}-B",
            archetype=CandidateArchetype.B_MODEST_PROXY_ROBUST_FINAL,
            failure_gap=FailureGapKind.NONE,
            optimizer_model_id=OPTIMIZER_MODEL_ID,
            verifier_model_id=ORTHOGONAL_VERIFIER_MODEL_ID,
            proxy_score=proxy_b,
            ir_representation=ir_b,
            ir_digest=dig_ir_b,
            final_artifact_payload=art_b,
            verified_artifact_digest=dig_art_b,
            correlated_verifier_score=corr_b,
            orthogonal_verifier_score=ortho_b,
            verified_profile_id=NOMINAL_PROFILE_ID,
            deployed_artifact_payload=art_b,
            deployed_artifact_digest=dig_art_b,
            observed_profile_id=NOMINAL_PROFILE_ID,
            observed_real_efficiency=obs_b,
            observed_parasitic_heating_ok=True,
            verification_latency_ms=round(1.85 + (idx % 7) * 0.12, 3),
            logical_tick=base_tick + 2,
        )

        # --- Candidato C_i: Pasa verificación nominal estática (con score > B_i en modelo estático),
        #     pero falla al desplegarse en el mundo real por P3, P4a o P4b ---
        proxy_c = round(0.912 + (idx % 4) * 0.006, 4)
        # En verificación estática antes del despliegue aparenta superar a B_i (0.955 > ortho_b)
        static_ver_c = round(0.951 + (idx % 4) * 0.004, 4)
        ir_c = f"IR:CONTINUOUS_GREYSCALE_GRATING:triad={idx}:cand=C:resonant_high_q=1"
        art_c = f"BIN:METAGRATING_MASK_64X64:triad={idx}:cand=C:high_q_fragile"
        dig_ir_c = _canonical_digest("B60:IR", ir_c)
        dig_art_c = _canonical_digest("B60:ART", art_c)

        mode = idx % 3
        if mode == 0:
            # P3: Deployment gap (el artefacto desplegado sufrió drift / truncamiento post-verificación)
            gap_kind = FailureGapKind.P3_DEPLOYMENT_IDENTITY_DRIFT
            deployed_payload_c = art_c + ":TAMPERED_LITHOGRAPHY_BIAS"
            dig_dep_c = _canonical_digest("B60:ART", deployed_payload_c)
            ver_model_c = ORTHOGONAL_VERIFIER_MODEL_ID
            ortho_c = static_ver_c
            obs_profile_c = NOMINAL_PROFILE_ID
            obs_eff_c = round(0.765 + (idx % 5) * 0.01, 4)
            heating_ok_c = False
        elif mode == 1:
            # P4a: Environment mismatch (verificado en 295K nominal, ejecutado bajo deriva térmica 340K)
            gap_kind = FailureGapKind.P4A_ENVIRONMENT_PROFILE_MISMATCH
            deployed_payload_c = art_c
            dig_dep_c = dig_art_c
            ver_model_c = ORTHOGONAL_VERIFIER_MODEL_ID
            ortho_c = static_ver_c
            obs_profile_c = PERTURBED_PROFILE_ID
            obs_eff_c = round(0.812 + (idx % 4) * 0.012, 4)
            heating_ok_c = False
        else:
            # P4b: Simulador correlacionado + fallo de restricción observada en runtime nominal
            gap_kind = FailureGapKind.P4B_CORRELATED_SIMULATOR_BLINDSPOT
            deployed_payload_c = art_c
            dig_dep_c = dig_art_c
            # Aquí el verificador estático usó el mismo solver aproximado del optimizador
            ver_model_c = OPTIMIZER_MODEL_ID
            ortho_c = static_ver_c
            obs_profile_c = NOMINAL_PROFILE_ID
            obs_eff_c = round(0.828 + (idx % 4) * 0.009, 4)
            heating_ok_c = False

        cand_c = CandidatePipelineTrace(
            triad_id=idx,
            candidate_id=f"TRIAD-{idx:02d}-C",
            archetype=CandidateArchetype.C_VERIFIED_ARTIFACT_RUNTIME_DEGRADED,
            failure_gap=gap_kind,
            optimizer_model_id=OPTIMIZER_MODEL_ID,
            verifier_model_id=ver_model_c,
            proxy_score=proxy_c,
            ir_representation=ir_c,
            ir_digest=dig_ir_c,
            final_artifact_payload=art_c,
            verified_artifact_digest=dig_art_c,
            correlated_verifier_score=static_ver_c,
            orthogonal_verifier_score=ortho_c,
            verified_profile_id=NOMINAL_PROFILE_ID,
            deployed_artifact_payload=deployed_payload_c,
            deployed_artifact_digest=dig_dep_c,
            observed_profile_id=obs_profile_c,
            observed_real_efficiency=obs_eff_c,
            observed_parasitic_heating_ok=heating_ok_c,
            verification_latency_ms=round(1.95 + (idx % 6) * 0.14, 3),
            logical_tick=base_tick + 3,
        )

        triads.append((cand_a, cand_b, cand_c))

    return triads


def evaluate_policy_a_max_proxy(
    triad: tuple[CandidatePipelineTrace, CandidatePipelineTrace, CandidatePipelineTrace],
) -> TriadDecision:
    """Política A: Selecciona y compromete por máximo ProxyScore interno (ciega a P1..P4)."""
    selected = max(triad, key=lambda c: c.proxy_score)
    claim = ScopedClaimRecord.create(
        claim_id=f"BJR-A-{selected.triad_id:03d}",
        threshold=CRITICAL_EFFICIENCY_THRESHOLD,
        status=ClaimScopeStatus.SUPPORTED,
        optimizer_model_id=selected.optimizer_model_id,
        verifier_model_id=selected.optimizer_model_id,
        ir_digest=selected.ir_digest,
        verified_artifact_digest=selected.verified_artifact_digest,
        deployed_artifact_digest=selected.deployed_artifact_digest,
        verified_profile_id=selected.verified_profile_id,
        observed_profile_id=selected.observed_profile_id,
        logical_tick=selected.logical_tick,
        verified_efficiency=selected.proxy_score,
        observed_efficiency=selected.observed_real_efficiency,
        critical_constraints_pass=selected.observed_critical_constraints_pass,
    )
    return TriadDecision(
        triad_id=selected.triad_id,
        policy_name="POLICY_A_MAX_PROXY",
        selected_candidate_id=selected.candidate_id,
        committed=True,
        rejection_reason=None,
        scoped_claim=claim,
        latency_ms=selected.verification_latency_ms,
    )


def evaluate_policy_b_static_final_artifact(
    triad: tuple[CandidatePipelineTrace, CandidatePipelineTrace, CandidatePipelineTrace],
) -> TriadDecision:
    """Política B: Evalúa el artefacto final discretizado antes del despliegue,
    pero ignora ortogonalidad de modelo, identidad post-despliegue (P3),
    entorno real (P4a) y restricciones observadas en runtime (P4b).
    """
    viable = [c for c in triad if c.orthogonal_verifier_score >= CRITICAL_EFFICIENCY_THRESHOLD]
    if not viable:
        return TriadDecision(
            triad_id=triad[0].triad_id,
            policy_name="POLICY_B_STATIC_FINAL_VERIFIER",
            selected_candidate_id=None,
            committed=False,
            rejection_reason="NO_CANDIDATE_PASSED_STATIC_VERIFIER",
            scoped_claim=None,
            latency_ms=max(c.verification_latency_ms for c in triad),
        )
    selected = max(viable, key=lambda c: c.orthogonal_verifier_score)
    claim = ScopedClaimRecord.create(
        claim_id=f"BJR-B-{selected.triad_id:03d}",
        threshold=CRITICAL_EFFICIENCY_THRESHOLD,
        status=ClaimScopeStatus.SUPPORTED,
        optimizer_model_id=selected.optimizer_model_id,
        verifier_model_id=selected.verifier_model_id,
        ir_digest=selected.ir_digest,
        verified_artifact_digest=selected.verified_artifact_digest,
        deployed_artifact_digest=selected.deployed_artifact_digest,
        verified_profile_id=selected.verified_profile_id,
        observed_profile_id=selected.observed_profile_id,
        logical_tick=selected.logical_tick,
        verified_efficiency=selected.orthogonal_verifier_score,
        observed_efficiency=selected.observed_real_efficiency,
        critical_constraints_pass=selected.observed_critical_constraints_pass,
    )
    return TriadDecision(
        triad_id=selected.triad_id,
        policy_name="POLICY_B_STATIC_FINAL_VERIFIER",
        selected_candidate_id=selected.candidate_id,
        committed=True,
        rejection_reason=None,
        scoped_claim=claim,
        latency_ms=sum(c.verification_latency_ms for c in triad) / len(triad),
    )


class BabylonFL022v2Gate:
    """Política C: Gate completo FL-022-v2 (Proxy -> IR -> Artifact -> Deployed -> Observed)."""

    def verify_candidate(self, cand: CandidatePipelineTrace) -> tuple[bool, str | None, ScopedClaimRecord]:
        # 1. Independencia del verificador respecto al optimizador (Anti-Correlated Failure)
        if not cand.models_orthogonal:
            claim = ScopedClaimRecord.create(
                claim_id=f"BJR-C-{cand.candidate_id}",
                threshold=CRITICAL_EFFICIENCY_THRESHOLD,
                status=ClaimScopeStatus.FALSIFIED,
                optimizer_model_id=cand.optimizer_model_id,
                verifier_model_id=cand.verifier_model_id,
                ir_digest=cand.ir_digest,
                verified_artifact_digest=cand.verified_artifact_digest,
                deployed_artifact_digest=cand.deployed_artifact_digest,
                verified_profile_id=cand.verified_profile_id,
                observed_profile_id=cand.observed_profile_id,
                logical_tick=cand.logical_tick,
                verified_efficiency=cand.orthogonal_verifier_score,
                observed_efficiency=cand.observed_real_efficiency,
                critical_constraints_pass=False,
            )
            return False, "CORRELATED_VERIFIER_MODEL_REJECTED", claim

        # 2. Verificación independiente sobre el artefacto discretizado final (P1/P2)
        if cand.orthogonal_verifier_score < CRITICAL_EFFICIENCY_THRESHOLD:
            claim = ScopedClaimRecord.create(
                claim_id=f"BJR-C-{cand.candidate_id}",
                threshold=CRITICAL_EFFICIENCY_THRESHOLD,
                status=ClaimScopeStatus.FALSIFIED,
                optimizer_model_id=cand.optimizer_model_id,
                verifier_model_id=cand.verifier_model_id,
                ir_digest=cand.ir_digest,
                verified_artifact_digest=cand.verified_artifact_digest,
                deployed_artifact_digest=cand.deployed_artifact_digest,
                verified_profile_id=cand.verified_profile_id,
                observed_profile_id=cand.observed_profile_id,
                logical_tick=cand.logical_tick,
                verified_efficiency=cand.orthogonal_verifier_score,
                observed_efficiency=cand.observed_real_efficiency,
                critical_constraints_pass=False,
            )
            return False, "FINAL_DISCRETIZED_ARTIFACT_BELOW_THRESHOLD", claim

        # 3. Identidad criptográfica entre artefacto verificado y objeto desplegado (P3)
        if not cand.identity_intact:
            claim = ScopedClaimRecord.create(
                claim_id=f"BJR-C-{cand.candidate_id}",
                threshold=CRITICAL_EFFICIENCY_THRESHOLD,
                status=ClaimScopeStatus.FALSIFIED,
                optimizer_model_id=cand.optimizer_model_id,
                verifier_model_id=cand.verifier_model_id,
                ir_digest=cand.ir_digest,
                verified_artifact_digest=cand.verified_artifact_digest,
                deployed_artifact_digest=cand.deployed_artifact_digest,
                verified_profile_id=cand.verified_profile_id,
                observed_profile_id=cand.observed_profile_id,
                logical_tick=cand.logical_tick,
                verified_efficiency=cand.orthogonal_verifier_score,
                observed_efficiency=cand.observed_real_efficiency,
                critical_constraints_pass=False,
            )
            return False, "DEPLOYED_ARTIFACT_IDENTITY_MISMATCH", claim

        # 4. Concordancia de perfil ambiental entre verificación y ejecución (P4a / B3 Scope)
        if not cand.environment_matched:
            claim = ScopedClaimRecord.create(
                claim_id=f"BJR-C-{cand.candidate_id}",
                threshold=CRITICAL_EFFICIENCY_THRESHOLD,
                status=ClaimScopeStatus.REJECTED_OUT_OF_SCOPE,
                optimizer_model_id=cand.optimizer_model_id,
                verifier_model_id=cand.verifier_model_id,
                ir_digest=cand.ir_digest,
                verified_artifact_digest=cand.verified_artifact_digest,
                deployed_artifact_digest=cand.deployed_artifact_digest,
                verified_profile_id=cand.verified_profile_id,
                observed_profile_id=cand.observed_profile_id,
                logical_tick=cand.logical_tick,
                verified_efficiency=cand.orthogonal_verifier_score,
                observed_efficiency=cand.observed_real_efficiency,
                critical_constraints_pass=False,
            )
            return False, "ENVIRONMENT_PROFILE_MISMATCH", claim

        # 5. Comprobación de restricciones críticas sobre el comportamiento real observado (P4b)
        if not cand.observed_critical_constraints_pass:
            claim = ScopedClaimRecord.create(
                claim_id=f"BJR-C-{cand.candidate_id}",
                threshold=CRITICAL_EFFICIENCY_THRESHOLD,
                status=ClaimScopeStatus.FALSIFIED,
                optimizer_model_id=cand.optimizer_model_id,
                verifier_model_id=cand.verifier_model_id,
                ir_digest=cand.ir_digest,
                verified_artifact_digest=cand.verified_artifact_digest,
                deployed_artifact_digest=cand.deployed_artifact_digest,
                verified_profile_id=cand.verified_profile_id,
                observed_profile_id=cand.observed_profile_id,
                logical_tick=cand.logical_tick,
                verified_efficiency=cand.orthogonal_verifier_score,
                observed_efficiency=cand.observed_real_efficiency,
                critical_constraints_pass=False,
            )
            return False, "OBSERVED_REAL_WORLD_CONSTRAINT_FAILURE", claim

        claim = ScopedClaimRecord.create(
            claim_id=f"BJR-C-{cand.candidate_id}",
            threshold=CRITICAL_EFFICIENCY_THRESHOLD,
            status=ClaimScopeStatus.OBSERVED,
            optimizer_model_id=cand.optimizer_model_id,
            verifier_model_id=cand.verifier_model_id,
            ir_digest=cand.ir_digest,
            verified_artifact_digest=cand.verified_artifact_digest,
            deployed_artifact_digest=cand.deployed_artifact_digest,
            verified_profile_id=cand.verified_profile_id,
            observed_profile_id=cand.observed_profile_id,
            logical_tick=cand.logical_tick,
            verified_efficiency=cand.orthogonal_verifier_score,
            observed_efficiency=cand.observed_real_efficiency,
            critical_constraints_pass=True,
        )
        return True, None, claim

    def evaluate_triad(
        self,
        triad: tuple[CandidatePipelineTrace, CandidatePipelineTrace, CandidatePipelineTrace],
    ) -> TriadDecision:
        """Evalúa los candidatos en orden de score verificado independiente y sólo compromete
        aquel que satisface la cadena completa Identity ^ Verification ^ EnvironmentMatch ^ ObservedConstraints.
        """
        ordered = sorted(triad, key=lambda c: c.orthogonal_verifier_score, reverse=True)
        total_latency = 0.0
        last_reason: str | None = None
        last_claim: ScopedClaimRecord | None = None

        for cand in ordered:
            total_latency += cand.verification_latency_ms
            ok, reason, claim = self.verify_candidate(cand)
            if ok:
                return TriadDecision(
                    triad_id=cand.triad_id,
                    policy_name="POLICY_C_BABYLON_FL022_V2_GATE",
                    selected_candidate_id=cand.candidate_id,
                    committed=True,
                    rejection_reason=None,
                    scoped_claim=claim,
                    latency_ms=round(total_latency, 3),
                )
            last_reason = reason
            last_claim = claim

        return TriadDecision(
            triad_id=triad[0].triad_id,
            policy_name="POLICY_C_BABYLON_FL022_V2_GATE",
            selected_candidate_id=None,
            committed=False,
            rejection_reason=last_reason or "ALL_CANDIDATES_REJECTED",
            scoped_claim=last_claim,
            latency_ms=round(total_latency, 3),
        )


def _spearman_rank_correlation(xs: list[float], ys: list[float]) -> float:
    """Calcula la correlación por rangos de Spearman (sin dependencias externas)."""
    n = len(xs)
    if n < 2:
        return 0.0

    def _ranks(vals: list[float]) -> list[float]:
        indexed = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and indexed[j + 1][1] == indexed[i][1]:
                j += 1
            avg_rank = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                ranks[indexed[k][0]] = avg_rank
            i = j + 1
        return ranks

    rx = _ranks(xs)
    ry = _ranks(ys)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry, strict=True))
    den_x = sum((a - mean_x) ** 2 for a in rx) ** 0.5
    den_y = sum((b - mean_y) ** 2 for b in ry) ** 0.5
    if den_x == 0.0 or den_y == 0.0:
        return 0.0
    return float(round(num / (den_x * den_y), 4))


def _summarize_policy(
    policy_name: str,
    triads: list[tuple[CandidatePipelineTrace, CandidatePipelineTrace, CandidatePipelineTrace]],
    decisions: list[TriadDecision],
) -> PolicyEvaluationReport:
    cand_map: dict[str, CandidatePipelineTrace] = {c.candidate_id: c for triad in triads for c in triad}
    all_candidates = [c for triad in triads for c in triad]

    proxy_scores = [c.proxy_score for c in all_candidates]
    real_efficiencies = [c.observed_real_efficiency for c in all_candidates]
    rank_corr = _spearman_rank_correlation(proxy_scores, real_efficiencies)

    sim_reality_gaps = [abs(c.orthogonal_verifier_score - c.observed_real_efficiency) for c in all_candidates]
    mean_gap = round(sum(sim_reality_gaps) / len(sim_reality_gaps), 4)
    max_gap = round(max(sim_reality_gaps), 4)

    committed_count = 0
    proxy_selected_invalid = 0
    invalid_final_accepted = 0
    identity_mismatch_accepted = 0
    env_mismatch_accepted = 0
    observed_failures_accepted = 0
    valid_b_accepted = 0
    latencies: list[float] = []

    for dec in decisions:
        latencies.append(dec.latency_ms)
        if not dec.committed or dec.selected_candidate_id is None:
            continue
        committed_count += 1
        cand = cand_map[dec.selected_candidate_id]

        if cand.archetype == CandidateArchetype.A_HIGH_PROXY_BAD_FINAL:
            proxy_selected_invalid += 1
        if cand.orthogonal_verifier_score < CRITICAL_EFFICIENCY_THRESHOLD or not cand.is_truly_valid_end_to_end:
            invalid_final_accepted += 1
        if not cand.identity_intact:
            identity_mismatch_accepted += 1
        if not cand.environment_matched:
            env_mismatch_accepted += 1
        if not cand.observed_critical_constraints_pass:
            observed_failures_accepted += 1
        if cand.archetype == CandidateArchetype.B_MODEST_PROXY_ROBUST_FINAL and cand.is_truly_valid_end_to_end:
            valid_b_accepted += 1

    sorted_lat = sorted(latencies)
    p99_idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.99))
    latency_p99 = round(sorted_lat[p99_idx], 3)

    return PolicyEvaluationReport(
        policy_name=policy_name,
        triads_evaluated=len(triads),
        committed_count=committed_count,
        proxy_selected_invalid_artifacts=proxy_selected_invalid,
        invalid_final_artifacts_accepted=invalid_final_accepted,
        artifact_identity_mismatches_accepted=identity_mismatch_accepted,
        environment_mismatch_acceptances=env_mismatch_accepted,
        observed_constraint_failures_accepted=observed_failures_accepted,
        valid_artifact_acceptance_rate=round(valid_b_accepted / len(triads), 4),
        proxy_final_rank_correlation=rank_corr,
        mean_simulation_reality_gap=mean_gap,
        max_simulation_reality_gap=max_gap,
        verification_latency_p99_ms=latency_p99,
        decisions=decisions,
    )


def run_fl022_v2_experiment() -> dict[str, PolicyEvaluationReport]:
    """Ejecuta el experimento mínimo falsable FL-022-v2 sobre las 20 tríadas adversariales."""
    triads = build_20_adversarial_triads()
    gate_c = BabylonFL022v2Gate()

    decisions_a = [evaluate_policy_a_max_proxy(t) for t in triads]
    decisions_b = [evaluate_policy_b_static_final_artifact(t) for t in triads]
    decisions_c = [gate_c.evaluate_triad(t) for t in triads]

    return {
        "A": _summarize_policy("POLICY_A_MAX_PROXY", triads, decisions_a),
        "B": _summarize_policy("POLICY_B_STATIC_FINAL_VERIFIER", triads, decisions_b),
        "C": _summarize_policy("POLICY_C_BABYLON_FL022_V2_GATE", triads, decisions_c),
    }


if __name__ == "__main__":
    reports = run_fl022_v2_experiment()
    print("=" * 78)
    print("  FL-022-v2: PROXY -> IR -> ARTIFACT -> DEPLOYED -> OBSERVED (20 TRIADS)")
    print("=" * 78)
    for key, rep in reports.items():
        print(
            f"[{key}] {rep.policy_name}: "
            f"proxy_invalid={rep.proxy_selected_invalid_artifacts} "
            f"invalid_accepted={rep.invalid_final_artifacts_accepted} "
            f"id_mismatch={rep.artifact_identity_mismatches_accepted} "
            f"env_mismatch={rep.environment_mismatch_acceptances} "
            f"obs_fail={rep.observed_constraint_failures_accepted} "
            f"valid_recall={rep.valid_artifact_acceptance_rate:.1%} "
            f"p99={rep.verification_latency_p99_ms:.2f}ms"
        )
    rep_c = reports["C"]
    print("-" * 78)
    print(
        f"MEASURES: rank_corr(Proxy,Observed)={rep_c.proxy_final_rank_correlation:.4f} | "
        f"mean_sim_reality_gap={rep_c.mean_simulation_reality_gap:.4f} | "
        f"max_sim_reality_gap={rep_c.max_simulation_reality_gap:.4f}"
    )
