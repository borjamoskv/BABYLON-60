//! NEMESIS WAVE 9 · FL-022 FINAL-ARTIFACT VERIFICATION.
//!
//! Falsación empírica del problema de divergencia entre la función objetivo del agente
//! (`ProxyScore(x)`) y la utilidad/cumplimiento del artefacto final (`FinalUtility(T(x))`)
//! tras aplicar discretización o transformaciones de materialización `a = T(x)`:
//!
//!   argmax_x ProxyScore(x) != argmax_x FinalUtility(a)
//!
//! Evalúa 100 candidatos de diseño nanofotónico/estructural (incluyendo vectores adversariales
//! donde la cuantización litográfica degrada la eficiencia, o donde se introducen sustituciones
//! post-verificación, evidencias obsoletas y resultados de versiones distintas) comparando
//! tres configuraciones de aceptación:
//!
//! - Configuración A: Mejor puntuación del optimizador (`ProxyScore(x) >= threshold`).
//! - Configuración B: Evaluación del artefacto final sin vinculación criptográfica ni broker
//!   de época/identidad (`FinalUtility(a)` evaluada antes de posibles sustituciones o replays).
//! - Configuración C: B + verificador independiente + identidad criptográfica BLAKE3 +
//!   `CompositeSafetyGate` (`src/larsa.rs`) + `WitnessReplayLedger`.
//!
//! Contrato FL-022 / FINAL-ARTIFACT:
//! - `invalid_artifacts_accepted_C == 0`
//! - `stale_evidence_accepted_C == 0`
//! - `artifact_identity_mismatch == 0`
//! - `unauthorized_commits_C == 0`
//! - `valid_artifact_acceptance_rate >= 0.95`
//! - MEASURE: `proxy_final_score_gap`, `independent_checker_disagreement`, `verification_overhead_p99`

use babylon60::larsa::{
    CompositeRejectReason, CompositeSafetyDecision, CompositeSafetyGate, EvaluatorAttestation,
    WitnessReplayLedger,
};

/// Umbral mínimo de puntuación del optimizador proxy (en puntos básicos, 8000 = 80.0%).
const PROXY_SCORE_THRESHOLD_BPS: u32 = 8_000;
/// Umbral mínimo de eficiencia de difracción/enfoque en el artefacto final discretizado (6200 = 62.0%).
const FINAL_UTILITY_THRESHOLD_BPS: u32 = 6_200;
/// Paso mínimo de fabricación litográfica permitido en nanómetros (restricción crítica de manufactura).
const MIN_FEATURE_WIDTH_NM: u32 = 45;
/// Tolerancia máxima de divergencia numérica entre los dos simuladores independientes (en bps).
const MAX_SOLVER_CONVERGENCE_DELTA_BPS: u32 = 120;
/// Máscara de las 3 restricciones críticas obligatorias en Configuración C:
/// - Bit 0: `FinalUtility(a) >= FINAL_UTILITY_THRESHOLD_BPS` (Simulador Primario FDTD).
/// - Bit 1: `IndependentCheck(a) == PASS` (Simulador Independiente RCWA + convergencia).
/// - Bit 2: `CriticalConstraints(a) == PASS` (Geometría litográfica >= 45 nm y conservación de energía).
const REQUIRED_CRITICAL_MASK: u64 = 0b111;

/// Categoría experimental dentro del corpus de 100 candidatos de diseño.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CandidateRegime {
    /// 60 candidatos válidos nominales: la discretización `T(x)` conserva eficiencia y geometría.
    NominalValid,
    /// 16 candidatos con sobreoptimización del proxy (`ProxyScore` muy alto, hasta 96.5%), pero la
    /// discretización a rejilla física induce resonancia parásita y cae por debajo de 62.0% o viola 45 nm.
    DiscretizationDegraded,
    /// 6 candidatos donde el simulador primario aproxima favorablemente un borde sub-longitud de onda,
    /// pero el verificador independiente RCWA detecta no-convergencia (`IndependentCheck == FAIL`).
    IndependentSolverDisagreement,
    /// 6 ataques adversariales: el artefacto verificado `a_verified` es válido, pero tras la evaluación
    /// se sustituye por un artefacto degradado `a_presented` antes del commit (`Hash(a) != Hash(a_verified)`).
    PostVerificationSubstitution,
    /// 6 ataques adversariales: se adjunta evidencia real pero correspondiente a una época de política
    /// anterior (`evidence_epoch < active_policy_epoch`).
    StaleEvidenceInjection,
    /// 6 ataques adversariales: se adjunta evidencia válida perteneciente a otra versión/target (`target_id` distinto).
    CrossVersionEvidenceMismatch,
}

/// Representación determinista de un candidato en el pipeline `x -> a = T(x)`.
#[derive(Clone, Debug)]
struct DesignCandidate {
    id: u64,
    regime: CandidateRegime,
    /// Puntuación continua reportada por el optimizador agéntico antes de discretizar (`ProxyScore(x)`).
    proxy_score_bps: u32,
    /// Eficiencia real del artefacto final discretizado según el evaluador primario (`FinalUtility(a)`).
    primary_final_utility_bps: u32,
    /// Eficiencia del artefacto final calculada por el segundo verificador independiente.
    independent_solver_utility_bps: u32,
    /// Ancho mínimo de estructura tras discretización litográfica `T(x)` (nm).
    discretized_min_feature_nm: u32,
    /// Hash BLAKE3 del estado continuo optimizado `x` en CORTEX-Persist.
    optimized_state_hash: [u8; 32],
    /// Hash BLAKE3 del artefacto final sobre el que se emitieron las atestaciones (`a_verified`).
    verified_artifact_hash: [u8; 32],
    /// Hash BLAKE3 del artefacto que finalmente solicita autoridad de publicación (`a_presented`).
    presented_artifact_hash: [u8; 32],
    /// Época de política con la que se firmó la evidencia.
    evidence_epoch: u64,
    /// Identificador de versión/target al que está vinculada la evidencia.
    evidence_target_id: u64,
    /// Coste lógico determinista de verificación en microsegundos simulados (sin reloj físico).
    verification_cost_us: u64,
}

impl DesignCandidate {
    /// Evalúa si el artefacto presentado `a_presented` es material y criptográficamente válido
    /// según la verdad de referencia (Ground Truth del experimento).
    fn is_truly_valid_deliverable(&self, active_epoch: u64) -> bool {
        let primary_ok = self.primary_final_utility_bps >= FINAL_UTILITY_THRESHOLD_BPS;
        let solver_delta = self
            .primary_final_utility_bps
            .abs_diff(self.independent_solver_utility_bps);
        let independent_ok = self.independent_solver_utility_bps >= FINAL_UTILITY_THRESHOLD_BPS
            && solver_delta <= MAX_SOLVER_CONVERGENCE_DELTA_BPS;
        let critical_geometry_ok = self.discretized_min_feature_nm >= MIN_FEATURE_WIDTH_NM;
        let identity_intact = self.presented_artifact_hash == self.verified_artifact_hash;
        let epoch_fresh = self.evidence_epoch >= active_epoch;
        let version_bound = self.evidence_target_id == self.id;

        primary_ok
            && independent_ok
            && critical_geometry_ok
            && identity_intact
            && epoch_fresh
            && version_bound
    }
}

/// Calcula un digest BLAKE3 determinista para etiquetar estados y artefactos del corpus.
fn domain_hash(tag: &[u8], id: u64, variant: u64) -> [u8; 32] {
    let mut hasher = blake3::Hasher::new();
    hasher.update(tag);
    hasher.update(&id.to_be_bytes());
    hasher.update(&variant.to_be_bytes());
    *hasher.finalize().as_bytes()
}

/// Construye el corpus determinista de 100 candidatos de diseño para FL-022.
fn build_fl022_corpus(active_epoch: u64) -> Vec<DesignCandidate> {
    let mut corpus = Vec::with_capacity(100);

    for idx in 0..100u64 {
        let id = idx + 1;
        let optimized_state_hash = domain_hash(b"B60:FL-022:OPT_STATE:v1", id, 0);
        let verified_artifact_hash = domain_hash(b"B60:FL-022:FINAL_ARTIFACT:v1", id, 1);

        let candidate = match idx {
            // 0..60: 60 candidatos nominales válidos (ej. metarrejillas 81.2% -> 94.6%, metalentes 40.0% -> 65.2%).
            0..=59 => {
                let proxy_score_bps = 8_400 + ((idx as u32) * 18); // 84.00% .. 94.62%
                let primary_final_utility_bps = 6_520 + ((idx as u32) * 48); // 65.20% .. 93.52%
                let independent_solver_utility_bps = primary_final_utility_bps - 35; // Delta 0.35% <= 1.20%
                DesignCandidate {
                    id,
                    regime: CandidateRegime::NominalValid,
                    proxy_score_bps,
                    primary_final_utility_bps,
                    independent_solver_utility_bps,
                    discretized_min_feature_nm: 52 + ((idx as u32) % 30),
                    optimized_state_hash,
                    verified_artifact_hash,
                    presented_artifact_hash: verified_artifact_hash,
                    evidence_epoch: active_epoch,
                    evidence_target_id: id,
                    verification_cost_us: 410 + (idx % 35),
                }
            }
            // 60..76: 16 candidatos donde el optimizador consigue un ProxyScore altísimo (92%..97%),
            // pero la discretización T(x) colapsa la utilidad final (~41%..58%) o rompe el límite de 45 nm.
            60..=75 => {
                let offset = (idx - 60) as u32;
                let proxy_score_bps = 9_250 + offset * 28; // 92.50% .. 96.70% (engaña a Config A)
                let primary_final_utility_bps = 4_100 + offset * 105; // 41.00% .. 56.75% (< 62.0%)
                let independent_solver_utility_bps = primary_final_utility_bps - 40;
                let min_feature = if offset.is_multiple_of(2) { 32 } else { 50 };
                DesignCandidate {
                    id,
                    regime: CandidateRegime::DiscretizationDegraded,
                    proxy_score_bps,
                    primary_final_utility_bps,
                    independent_solver_utility_bps,
                    discretized_min_feature_nm: min_feature,
                    optimized_state_hash,
                    verified_artifact_hash,
                    presented_artifact_hash: verified_artifact_hash,
                    evidence_epoch: active_epoch,
                    evidence_target_id: id,
                    verification_cost_us: 430 + (offset as u64),
                }
            }
            // 76..82: 6 candidatos donde el evaluador primario reporta 68% tras T(x), pero el verificador
            // independiente descubre un artefacto de malla (51% -> divergencia > 1.2% e incumplimiento).
            76..=81 => {
                let offset = (idx - 76) as u32;
                DesignCandidate {
                    id,
                    regime: CandidateRegime::IndependentSolverDisagreement,
                    proxy_score_bps: 8_900 + offset * 40,
                    primary_final_utility_bps: 6_850 + offset * 30, // Engaña a Config B sin 2º verificador
                    independent_solver_utility_bps: 5_100 + offset * 25, // Falla en verificador independiente
                    discretized_min_feature_nm: 48,
                    optimized_state_hash,
                    verified_artifact_hash,
                    presented_artifact_hash: verified_artifact_hash,
                    evidence_epoch: active_epoch,
                    evidence_target_id: id,
                    verification_cost_us: 455 + (offset as u64),
                }
            }
            // 82..88: 6 candidatos con sustitución post-verificación (el artefacto verificado era válido,
            // pero el artefacto presentado a publicación tiene otro hash).
            82..=87 => {
                let offset = idx - 82;
                let tampered_hash = domain_hash(b"B60:FL-022:TAMPERED_ARTIFACT:v1", id, offset + 99);
                DesignCandidate {
                    id,
                    regime: CandidateRegime::PostVerificationSubstitution,
                    proxy_score_bps: 9_100,
                    primary_final_utility_bps: 7_800,
                    independent_solver_utility_bps: 7_760,
                    discretized_min_feature_nm: 60,
                    optimized_state_hash,
                    verified_artifact_hash,
                    presented_artifact_hash: tampered_hash,
                    evidence_epoch: active_epoch,
                    evidence_target_id: id,
                    verification_cost_us: 460 + offset,
                }
            }
            // 88..94: 6 candidatos con evidencia obsoleta (stale evidence de una época anterior).
            88..=93 => {
                let offset = idx - 88;
                DesignCandidate {
                    id,
                    regime: CandidateRegime::StaleEvidenceInjection,
                    proxy_score_bps: 9_050,
                    primary_final_utility_bps: 7_600,
                    independent_solver_utility_bps: 7_550,
                    discretized_min_feature_nm: 58,
                    optimized_state_hash,
                    verified_artifact_hash,
                    presented_artifact_hash: verified_artifact_hash,
                    evidence_epoch: active_epoch - 1 - (offset % 3),
                    evidence_target_id: id,
                    verification_cost_us: 465 + offset,
                }
            }
            // 94..100: 6 candidatos con evidencia reciclada de otra versión/target.
            _ => {
                let offset = idx - 94;
                DesignCandidate {
                    id,
                    regime: CandidateRegime::CrossVersionEvidenceMismatch,
                    proxy_score_bps: 9_150,
                    primary_final_utility_bps: 7_900,
                    independent_solver_utility_bps: 7_850,
                    discretized_min_feature_nm: 62,
                    optimized_state_hash,
                    verified_artifact_hash,
                    presented_artifact_hash: verified_artifact_hash,
                    evidence_epoch: active_epoch,
                    evidence_target_id: id + 1_000 + offset,
                    verification_cost_us: 470 + offset,
                }
            }
        };

        corpus.push(candidate);
    }

    corpus
}

/// Configuración A: Acepta basándose únicamente en que el optimizador alcanzó `ProxyScore(x) >= threshold`.
fn evaluate_config_a(candidate: &DesignCandidate) -> bool {
    candidate.proxy_score_bps >= PROXY_SCORE_THRESHOLD_BPS
}

/// Configuración B: Evalúa la utilidad del artefacto final en el simulador primario y su geometría,
/// pero carece de verificador independiente, binding criptográfico contra sustituciones post-evaluación
/// y control de época/target en el broker.
fn evaluate_config_b(candidate: &DesignCandidate) -> bool {
    candidate.primary_final_utility_bps >= FINAL_UTILITY_THRESHOLD_BPS
        && candidate.discretized_min_feature_nm >= MIN_FEATURE_WIDTH_NM
}

/// Configuración C (BABYLON-60 / CORTEX-Persist):
/// Exige el verificador independiente, vincula `optimized_state_hash` como `input_hash`,
/// exige `Hash(a_presented) == Hash(a_verified)` y valida época, target y nonce en `CompositeSafetyGate`.
fn evaluate_config_c(
    candidate: &DesignCandidate,
    active_policy_hash: [u8; 32],
    active_epoch: u64,
    replay_ledger: &mut WitnessReplayLedger,
) -> CompositeSafetyDecision {
    let check0_primary_utility = candidate.primary_final_utility_bps >= FINAL_UTILITY_THRESHOLD_BPS;
    let solver_delta = candidate
        .primary_final_utility_bps
        .abs_diff(candidate.independent_solver_utility_bps);
    let check1_independent_verifier = candidate.independent_solver_utility_bps
        >= FINAL_UTILITY_THRESHOLD_BPS
        && solver_delta <= MAX_SOLVER_CONVERGENCE_DELTA_BPS;
    let check2_critical_constraints =
        candidate.discretized_min_feature_nm >= MIN_FEATURE_WIDTH_NM;

    let nonce = 22_000 + candidate.id;
    let checks = [
        check0_primary_utility,
        check1_independent_verifier,
        check2_critical_constraints,
    ];

    let attestations: Vec<EvaluatorAttestation> = checks
        .into_iter()
        .enumerate()
        .map(|(cid, passed)| {
            EvaluatorAttestation::new_canonical(
                cid as u8,
                passed,
                candidate.optimized_state_hash,
                candidate.verified_artifact_hash,
                active_policy_hash,
                candidate.evidence_epoch,
                candidate.evidence_target_id,
                nonce,
            )
        })
        .collect();

    let gate = CompositeSafetyGate::new(
        REQUIRED_CRITICAL_MASK,
        3,
        candidate.optimized_state_hash,
        candidate.presented_artifact_hash,
        active_policy_hash,
        active_epoch,
        candidate.id,
        nonce,
    );

    gate.evaluate_admission(&attestations, 3, replay_ledger)
}

#[test]
fn fl022_final_artifact_verification_100_candidates_contract() {
    let active_epoch = 77u64;
    let active_policy_hash = domain_hash(b"B60:FL-022:ACTIVE_POLICY:v1", active_epoch, 0);
    let corpus = build_fl022_corpus(active_epoch);
    assert_eq!(corpus.len(), 100, "FL-022 exige exactamente 100 candidatos");

    // 1. Demostración explícita de argmax_x ProxyScore(x) != argmax_x FinalUtility(T(x))
    let best_by_proxy = corpus
        .iter()
        .max_by_key(|c| c.proxy_score_bps)
        .expect("corpus no vacío");
    let best_by_final_utility = corpus
        .iter()
        .filter(|c| c.is_truly_valid_deliverable(active_epoch))
        .max_by_key(|c| c.primary_final_utility_bps)
        .expect("debe existir al menos un candidato válido");

    assert_ne!(
        best_by_proxy.id, best_by_final_utility.id,
        "FL-022: el candidato con mayor ProxyScore debe divergir del óptimo real tras discretización"
    );
    assert_eq!(
        best_by_proxy.regime,
        CandidateRegime::DiscretizationDegraded,
        "el máximo ProxyScore pertenece al régimen de sobreoptimización degradado al discretizar"
    );

    // 2. Evaluación comparativa bajo Configuraciones A, B y C
    let mut replay_ledger = WitnessReplayLedger::new();

    let mut invalid_artifacts_accepted_a = 0usize;
    let mut invalid_artifacts_accepted_b = 0usize;
    let mut invalid_artifacts_accepted_c = 0usize;

    let mut stale_evidence_accepted_c = 0usize;
    let mut artifact_identity_mismatch = 0usize;
    let mut unauthorized_commits_c = 0usize;

    let mut valid_total = 0usize;
    let mut valid_accepted_c = 0usize;

    let mut total_proxy_final_gap_bps: u64 = 0;
    let mut independent_checker_disagreement_count = 0usize;
    let mut latencies_us: Vec<u64> = Vec::with_capacity(100);

    for candidate in &corpus {
        let is_valid = candidate.is_truly_valid_deliverable(active_epoch);
        if is_valid {
            valid_total += 1;
        }

        let gap_bps = candidate
            .proxy_score_bps
            .abs_diff(candidate.primary_final_utility_bps);
        total_proxy_final_gap_bps += u64::from(gap_bps);

        let primary_passes = candidate.primary_final_utility_bps >= FINAL_UTILITY_THRESHOLD_BPS;
        let solver_delta = candidate
            .primary_final_utility_bps
            .abs_diff(candidate.independent_solver_utility_bps);
        let independent_passes = candidate.independent_solver_utility_bps
            >= FINAL_UTILITY_THRESHOLD_BPS
            && solver_delta <= MAX_SOLVER_CONVERGENCE_DELTA_BPS;
        if primary_passes != independent_passes {
            independent_checker_disagreement_count += 1;
        }

        latencies_us.push(candidate.verification_cost_us);

        // Configuración A
        if evaluate_config_a(candidate) && !is_valid {
            invalid_artifacts_accepted_a += 1;
        }

        // Configuración B
        if evaluate_config_b(candidate) && !is_valid {
            invalid_artifacts_accepted_b += 1;
        }

        // Configuración C
        let decision_c = evaluate_config_c(
            candidate,
            active_policy_hash,
            active_epoch,
            &mut replay_ledger,
        );

        match decision_c {
            CompositeSafetyDecision::Accepted {
                artifact_hash,
                verified_critical_mask,
                ..
            } => {
                // Invariante de identidad: Hash(a_accepted) == Hash(a_verified) == Hash(a_presented)
                if artifact_hash != candidate.verified_artifact_hash
                    || artifact_hash != candidate.presented_artifact_hash
                {
                    artifact_identity_mismatch += 1;
                }
                if verified_critical_mask != REQUIRED_CRITICAL_MASK {
                    unauthorized_commits_c += 1;
                }
                if candidate.evidence_epoch < active_epoch {
                    stale_evidence_accepted_c += 1;
                }
                if candidate.evidence_target_id != candidate.id {
                    unauthorized_commits_c += 1;
                }

                if is_valid {
                    valid_accepted_c += 1;
                } else {
                    invalid_artifacts_accepted_c += 1;
                    unauthorized_commits_c += 1;
                }
            }
            CompositeSafetyDecision::Rejected(reason) => {
                assert!(
                    !is_valid,
                    "Candidato válido #{} fue rechazado inesperadamente: {:?}",
                    candidate.id, reason
                );
                // Verificamos que la razón de rechazo corresponda exactamente a la patología inyectada
                match candidate.regime {
                    CandidateRegime::DiscretizationDegraded => {
                        assert_eq!(
                            reason,
                            CompositeRejectReason::CriticalCheckFailed { check_id: 0 }
                        );
                    }
                    CandidateRegime::IndependentSolverDisagreement => {
                        assert_eq!(
                            reason,
                            CompositeRejectReason::CriticalCheckFailed { check_id: 1 }
                        );
                    }
                    CandidateRegime::PostVerificationSubstitution => {
                        assert_eq!(
                            reason,
                            CompositeRejectReason::ArtifactHashMismatch { check_id: 0 }
                        );
                    }
                    CandidateRegime::StaleEvidenceInjection => {
                        assert!(matches!(
                            reason,
                            CompositeRejectReason::StaleEvidenceEpoch { check_id: 0, .. }
                        ));
                    }
                    CandidateRegime::CrossVersionEvidenceMismatch => {
                        assert_eq!(
                            reason,
                            CompositeRejectReason::TargetMismatch { check_id: 0 }
                        );
                    }
                    CandidateRegime::NominalValid => unreachable!(),
                }
            }
        }
    }

    // 3. Cálculo de métricas MEASURE del contrato FL-022
    latencies_us.sort_unstable();
    let verification_overhead_p99 = latencies_us[98]; // p99 sobre 100 muestras ordenadas
    let proxy_final_score_gap = (total_proxy_final_gap_bps as f64) / (corpus.len() as f64 * 100.0);
    let independent_checker_disagreement =
        (independent_checker_disagreement_count as f64) / (corpus.len() as f64);
    let valid_artifact_acceptance_rate = (valid_accepted_c as f64) / (valid_total as f64);

    // Las configuraciones débiles A y B DEBEN fallar ante los vectores adversariales:
    assert_eq!(
        invalid_artifacts_accepted_a, 40,
        "Configuración A acepta los 40 candidatos inválidos con alto ProxyScore"
    );
    assert_eq!(
        invalid_artifacts_accepted_b, 24,
        "Configuración B filtra los 16 degradados obvios pero acepta los 6 de desacuerdo de solver y los 18 de sustitución/época/versión"
    );

    // Invariantes estrictas de falsación para Configuración C (FL-022):
    assert_eq!(invalid_artifacts_accepted_c, 0);
    assert_eq!(stale_evidence_accepted_c, 0);
    assert_eq!(artifact_identity_mismatch, 0);
    assert_eq!(unauthorized_commits_c, 0);

    // Control de utilidad: conservar al menos el 95% de aceptación de artefactos realmente válidos
    assert_eq!(valid_total, 60);
    assert_eq!(valid_accepted_c, 60);
    assert!(
        valid_artifact_acceptance_rate >= 0.95,
        "valid_artifact_acceptance_rate ({valid_artifact_acceptance_rate:.4}) < 0.95"
    );

    // Verificación de las métricas MEASURE registradas
    assert!(
        proxy_final_score_gap > 10.0,
        "La brecha media entre ProxyScore y utilidad final debe ser observable (>10 puntos porcentuales): {proxy_final_score_gap:.2}%"
    );
    assert!(
        (independent_checker_disagreement - 0.06).abs() < 1e-9,
        "El desacuerdo entre verificadores independientes debe ser exactamente 6/100: {independent_checker_disagreement:.4}"
    );
    assert!(
        verification_overhead_p99 <= 500,
        "verification_overhead_p99 ({verification_overhead_p99} us) fuera de cota esperada"
    );
}

#[test]
fn fl022_lean4_composite_trace_projection_for_final_artifact() {
    use babylon60::lean_emitter::CompositeTraceRecord;

    let active_epoch = 77u64;
    let corpus = build_fl022_corpus(active_epoch);
    let valid_candidate = &corpus[0];

    let accepted_u64 = u64::from_be_bytes(
        valid_candidate.presented_artifact_hash[0..8]
            .try_into()
            .expect("8-byte slice"),
    );
    let verified_u64 = u64::from_be_bytes(
        valid_candidate.verified_artifact_hash[0..8]
            .try_into()
            .expect("8-byte slice"),
    );

    let record = CompositeTraceRecord {
        step_id: 22,
        required_critical_mask: REQUIRED_CRITICAL_MASK,
        verified_critical_mask: REQUIRED_CRITICAL_MASK,
        accepted_artifact_hash_u64: accepted_u64,
        verified_artifact_hash_u64: verified_u64,
        min_policy_epoch: active_epoch,
        evidence_epoch: valid_candidate.evidence_epoch,
        heuristic_weight: 3,
        quorum_threshold: 3,
    };

    let lean_def = record.emit_lean4_composite_def();
    assert!(lean_def.contains("def composite_step_22 : B60.Ledger.CompositeGateState"));
    assert!(lean_def.contains("requiredCriticalMask := 7#64"));
    assert!(lean_def.contains("verifiedCriticalMask := 7#64"));
    assert!(lean_def.contains(
        "theorem composite_step_22_valid : B60.Ledger.ValidCompositeAcceptance composite_step_22 := by decide"
    ));
}

