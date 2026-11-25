// LARSA bicameral — quórum determinista con veto formal estricto (B60-01 / FL-026 / FL-018).

use std::collections::BTreeSet;

/// Voto emitido por una cámara heurística o formal.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum VoteKind {
    /// Aprobación heurística con peso.
    HeuristicApprove {
        /// Peso del voto.
        weight: u32,
    },
    /// Rechazo heurístico (no suma peso).
    HeuristicReject {
        /// Peso del voto (ignorado por el acumulador).
        weight: u32,
    },
    /// Testigo formal verificado por el prover.
    FormalWitnessVerified {
        /// Hash BLAKE3 de la traza certificada.
        trace_hash: [u8; 32],
    },
    /// Refutación formal: veto terminal e irreversible si no existe testigo formal previo (`FL-026/H1`).
    FormalRefutation {
        /// Teorema refutado.
        theorem_id: u16,
    },
}

/// Resultado del quórum.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ConsensusOutcome {
    /// Aún sin testigo formal o sin peso suficiente.
    Pending,
    /// Conflicting witnesses permanently invalidate this quorum instance.
    AbortedByWitnessConflict,
    /// Commit: testigo formal presente y peso heurístico suficiente.
    Committed {
        /// Hash de la traza certificada.
        trace_hash: [u8; 32],
        /// Peso heurístico acumulado en el instante del commit terminal.
        heuristic_weight: u32,
    },
    /// Abortado por veto formal (estado terminal).
    AbortedByFormalVeto {
        /// Teorema que originó el veto.
        theorem_id: u16,
    },
}

/// Registro determinista anti-replay para testigos formales y compuertas `FL-026`/`FL-018`.
#[derive(Clone, Debug, Default)]
pub struct WitnessReplayLedger {
    consumed_witness_bindings: BTreeSet<([u8; 32], u64, u64)>,
    consumed_witness_hashes: BTreeSet<[u8; 32]>,
}

impl WitnessReplayLedger {
    /// Crea un registro vacío de testigos consumidos.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            consumed_witness_bindings: BTreeSet::new(),
            consumed_witness_hashes: BTreeSet::new(),
        }
    }

    /// Intenta consumir un testigo formal verificando unicidad global de `trace_hash` y `(trace_hash, target_id, nonce)`.
    pub fn try_consume(&mut self, trace_hash: [u8; 32], target_id: u64, nonce: u64) -> bool {
        if self.consumed_witness_hashes.contains(&trace_hash)
            || self
                .consumed_witness_bindings
                .contains(&(trace_hash, target_id, nonce))
        {
            return false;
        }
        self.consumed_witness_hashes.insert(trace_hash);
        self.consumed_witness_bindings
            .insert((trace_hash, target_id, nonce));
        true
    }
}

/// Quórum bicameral: el peso heurístico nunca suple al testigo formal (`B60-01` / `FL-026`).
pub struct BicameralQuorum {
    required_heuristic_weight: u32,
    accumulated_weight: u32,
    formal_witness: Option<[u8; 32]>,
    expected_trace_hash: Option<[u8; 32]>,
    committed_weight: Option<u32>,
    vetoed_by_theorem: Option<u16>,
    witness_conflict: bool,
}

impl BicameralQuorum {
    /// Crea un quórum con el peso heurístico requerido.
    #[must_use]
    pub const fn new(required_heuristic_weight: u32) -> Self {
        Self {
            required_heuristic_weight,
            accumulated_weight: 0,
            formal_witness: None,
            expected_trace_hash: None,
            committed_weight: None,
            vetoed_by_theorem: None,
            witness_conflict: false,
        }
    }

    /// Crea un quórum vinculado criptográficamente al hash del artefacto ejecutado (`FL-026/H2` & `FL-018`).
    #[must_use]
    pub const fn with_expected_trace(
        required_heuristic_weight: u32,
        expected_trace_hash: [u8; 32],
    ) -> Self {
        Self {
            required_heuristic_weight,
            accumulated_weight: 0,
            formal_witness: None,
            expected_trace_hash: Some(expected_trace_hash),
            committed_weight: None,
            vetoed_by_theorem: None,
            witness_conflict: false,
        }
    }

    /// Ingiere un voto vinculando el testigo a un `target_id`, ` nonce` y `WitnessReplayLedger` (`FL-026/H2`).
    pub fn ingest_vote_bound(
        &mut self,
        vote: VoteKind,
        target_id: u64,
        nonce: u64,
        replay_ledger: &mut WitnessReplayLedger,
    ) -> ConsensusOutcome {
        if let VoteKind::FormalWitnessVerified { trace_hash } = vote {
            if !replay_ledger.try_consume(trace_hash, target_id, nonce) {
                self.witness_conflict = true;
                return ConsensusOutcome::AbortedByWitnessConflict;
            }
        }
        self.ingest_vote(vote)
    }

    /// Ingiere un voto y devuelve el estado resultante.
    pub fn ingest_vote(&mut self, vote: VoteKind) -> ConsensusOutcome {
        if self.witness_conflict {
            return ConsensusOutcome::AbortedByWitnessConflict;
        }
        if let Some(tid) = self.vetoed_by_theorem {
            return ConsensusOutcome::AbortedByFormalVeto { theorem_id: tid };
        }
        match vote {
            VoteKind::FormalRefutation { theorem_id } => {
                // FL-026/H1 & H3: una refutación sin prueba adjunta no puede tumbar un quórum
                // que ya posee testigo formal verificado o que ya alcanzó estado Committed.
                if self.committed_weight.is_some() || self.formal_witness.is_some() {
                    return self.evaluate();
                }
                self.vetoed_by_theorem = Some(theorem_id);
                ConsensusOutcome::AbortedByFormalVeto { theorem_id }
            }
            VoteKind::FormalWitnessVerified { trace_hash } => {
                // FL-026/H2: si el quórum está anclado a un artefacto, cualquier hash distinto aborta.
                if self
                    .expected_trace_hash
                    .is_some_and(|expected| expected != trace_hash)
                {
                    self.witness_conflict = true;
                    return ConsensusOutcome::AbortedByWitnessConflict;
                }
                if self.formal_witness.is_some_and(|first| first != trace_hash) {
                    self.witness_conflict = true;
                    return ConsensusOutcome::AbortedByWitnessConflict;
                }
                self.formal_witness = Some(trace_hash);
                self.try_latch_commit();
                self.evaluate()
            }
            VoteKind::HeuristicApprove { weight } => {
                // FL-026/H3: una vez Committed, el peso reportado es inmutable.
                if self.committed_weight.is_none() {
                    self.accumulated_weight = self.accumulated_weight.saturating_add(weight);
                    self.try_latch_commit();
                }
                self.evaluate()
            }
            VoteKind::HeuristicReject { .. } => self.evaluate(),
        }
    }

    #[inline]
    fn try_latch_commit(&mut self) {
        if self.committed_weight.is_none()
            && !self.witness_conflict
            && self.vetoed_by_theorem.is_none()
            && self.required_heuristic_weight > 0
            && self.formal_witness.is_some()
            && self.accumulated_weight >= self.required_heuristic_weight
        {
            self.committed_weight = Some(self.accumulated_weight);
        }
    }

    #[inline]
    fn evaluate(&self) -> ConsensusOutcome {
        if self.witness_conflict {
            return ConsensusOutcome::AbortedByWitnessConflict;
        }
        if let Some(tid) = self.vetoed_by_theorem {
            return ConsensusOutcome::AbortedByFormalVeto { theorem_id: tid };
        }
        if let (Some(hash), Some(weight)) = (self.formal_witness, self.committed_weight) {
            return ConsensusOutcome::Committed {
                trace_hash: hash,
                heuristic_weight: weight,
            };
        }
        ConsensusOutcome::Pending
    }
}

// ============================================================================
// FL-018: COMPOSITE SAFETY GATE (CONJUNCIÓN ESTRICTA DE INVARIANTES CRÍTICOS)
// ============================================================================

/// Atestación individual de un evaluador determinista registrada en CORTEX (`FL-018`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct EvaluatorAttestation {
    /// Identificador del control crítico (`0..64`).
    pub check_id: u8,
    /// Resultado binario verificable del evaluador sobre el artefacto.
    pub passed: bool,
    /// Hash BLAKE3 de la especificación/entrada del problema.
    pub input_hash: [u8; 32],
    /// Hash BLAKE3 del artefacto evaluado (`Hash(a_verified)`).
    pub artifact_hash: [u8; 32],
    /// Hash BLAKE3 de la política activa.
    pub policy_hash: [u8; 32],
    /// Época lógica en la que se emitió la evidencia.
    pub evidence_epoch: u64,
    /// Identificador del objetivo/entrega.
    pub target_id: u64,
    /// Nonce único de ejecución.
    pub nonce: u64,
    /// Digest canónico BLAKE3 que sella la tupla completa del evaluador.
    pub evaluator_digest: [u8; 32],
}

impl EvaluatorAttestation {
    /// Construye una atestación de evaluador sellando su digest BLAKE3 canónico.
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub fn new_canonical(
        check_id: u8,
        passed: bool,
        input_hash: [u8; 32],
        artifact_hash: [u8; 32],
        policy_hash: [u8; 32],
        evidence_epoch: u64,
        target_id: u64,
        nonce: u64,
    ) -> Self {
        let evaluator_digest = Self::compute_digest(
            check_id,
            passed,
            &input_hash,
            &artifact_hash,
            &policy_hash,
            evidence_epoch,
            target_id,
            nonce,
        );
        Self {
            check_id,
            passed,
            input_hash,
            artifact_hash,
            policy_hash,
            evidence_epoch,
            target_id,
            nonce,
            evaluator_digest,
        }
    }

    /// Calcula el digest BLAKE3 canónico con separación de dominio `B60:FL-018:EVAL:v1`.
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub fn compute_digest(
        check_id: u8,
        passed: bool,
        input_hash: &[u8; 32],
        artifact_hash: &[u8; 32],
        policy_hash: &[u8; 32],
        evidence_epoch: u64,
        target_id: u64,
        nonce: u64,
    ) -> [u8; 32] {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"B60:FL-018:EVAL:v1");
        hasher.update(&[check_id, u8::from(passed)]);
        hasher.update(input_hash);
        hasher.update(artifact_hash);
        hasher.update(policy_hash);
        hasher.update(&evidence_epoch.to_be_bytes());
        hasher.update(&target_id.to_be_bytes());
        hasher.update(&nonce.to_be_bytes());
        *hasher.finalize().as_bytes()
    }

    /// Verifica que el `evaluator_digest` coincida exactamente con el contenido de la atestación.
    #[must_use]
    pub fn verify_digest(&self) -> bool {
        let expected = Self::compute_digest(
            self.check_id,
            self.passed,
            &self.input_hash,
            &self.artifact_hash,
            &self.policy_hash,
            self.evidence_epoch,
            self.target_id,
            self.nonce,
        );
        self.evaluator_digest == expected
    }
}

/// Causa determinista de rechazo en la compuerta `FL-018`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CompositeRejectReason {
    /// La máscara de controles críticos obligatorios no puede ser vacía.
    ZeroCriticalMask,
    /// El umbral heurístico requerido no puede ser cero (`FL-026/H4`).
    ZeroHeuristicThreshold,
    /// Identificador de control crítico fuera de rango (`>= 64`).
    CheckIdOutOfRange {
        /// Identificador inválido recibido.
        check_id: u8,
    },
    /// El digest BLAKE3 de la atestación no coincide con sus campos.
    InvalidEvaluatorDigest {
        /// Identificador del control cuya firma/digest falló.
        check_id: u8,
    },
    /// `Hash(a_accepted) != Hash(a_verified)`: el artefacto fue mutado tras la verificación.
    ArtifactHashMismatch {
        /// Identificador del control afectado.
        check_id: u8,
    },
    /// El hash de la entrada evaluada no coincide con la entrada actual.
    InputHashMismatch {
        /// Identificador del control afectado.
        check_id: u8,
    },
    /// El hash de la política evaluada no coincide con la política activa.
    PolicyHashMismatch {
        /// Identificador del control afectado.
        check_id: u8,
    },
    /// La evidencia pertenece a otro `target_id`.
    TargetMismatch {
        /// Identificador del control afectado.
        check_id: u8,
    },
    /// La evidencia pertenece a otro `nonce`.
    NonceMismatch {
        /// Identificador del control afectado.
        check_id: u8,
    },
    /// Evidencia caducada respecto a la época de política activa.
    StaleEvidenceEpoch {
        /// Identificador del control afectado.
        check_id: u8,
        /// Época mínima requerida.
        required_epoch: u64,
        /// Época observada en la evidencia.
        observed_epoch: u64,
    },
    /// Uno de los controles críticos obligatorios falló (`VerifiedPass(c, a) == false`).
    CriticalCheckFailed {
        /// Identificador del control crítico incumplido.
        check_id: u8,
    },
    /// Faltan controles críticos obligatorios por verificar en la conjunción.
    IncompleteCriticalCoverage {
        /// Máscara de controles requeridos.
        required_mask: u64,
        /// Máscara de controles verificados en positivo.
        verified_mask: u64,
    },
    /// Peso heurístico insuficiente o fallo en el quórum bicameral subyacente.
    InsufficientHeuristicWeight {
        /// Peso requerido.
        required: u32,
        /// Peso acumulado.
        accumulated: u32,
    },
    /// Intento de reutilizar el conjunto de evidencias en otra aceptación (`Replay`).
    ReplayDetected,
}

/// Decisión terminal de la compuerta `FL-018: CompositeSafetyGate`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CompositeSafetyDecision {
    /// Aceptación conjunta certificada: todos los controles críticos superados sobre el mismo artefacto.
    Accepted {
        /// Hash BLAKE3 del artefacto aceptado (`Hash(a_accepted) == Hash(a_verified)`).
        artifact_hash: [u8; 32],
        /// Máscara de controles críticos verificados.
        verified_critical_mask: u64,
        /// Peso heurístico comprometido.
        heuristic_weight: u32,
        /// Digest conjunto BLAKE3 de la evidencia CORTEX que respalda el commit.
        joint_evidence_digest: [u8; 32],
    },
    /// Rechazo determinista fail-closed.
    Rejected(CompositeRejectReason),
}

/// Compuerta de Seguridad Compuesta (`FL-018`):
/// Garantiza `Accepted(a) => (forall c in CriticalChecks(a): VerifiedPass(c,a)) && Hash(a_accepted) == Hash(a_verified)`.
#[derive(Clone, Debug)]
pub struct CompositeSafetyGate {
    required_critical_mask: u64,
    required_heuristic_weight: u32,
    expected_input_hash: [u8; 32],
    candidate_artifact_hash: [u8; 32],
    active_policy_hash: [u8; 32],
    min_policy_epoch: u64,
    target_id: u64,
    nonce: u64,
}

impl CompositeSafetyGate {
    /// Crea una nueva instancia de `CompositeSafetyGate` vinculada al artefacto presentado y a la política activa.
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub const fn new(
        required_critical_mask: u64,
        required_heuristic_weight: u32,
        expected_input_hash: [u8; 32],
        candidate_artifact_hash: [u8; 32],
        active_policy_hash: [u8; 32],
        min_policy_epoch: u64,
        target_id: u64,
        nonce: u64,
    ) -> Self {
        Self {
            required_critical_mask,
            required_heuristic_weight,
            expected_input_hash,
            candidate_artifact_hash,
            active_policy_hash,
            min_policy_epoch,
            target_id,
            nonce,
        }
    }

    /// Evalúa conjuntamente todas las atestaciones de evaluadores y el peso heurístico,
    /// registrando el consumo atómico en `replay_ledger` solo si todas las invariantes se cumplen.
    pub fn evaluate_admission(
        &self,
        attestations: &[EvaluatorAttestation],
        heuristic_weight: u32,
        replay_ledger: &mut WitnessReplayLedger,
    ) -> CompositeSafetyDecision {
        if self.required_critical_mask == 0 {
            return CompositeSafetyDecision::Rejected(CompositeRejectReason::ZeroCriticalMask);
        }
        if self.required_heuristic_weight == 0 {
            return CompositeSafetyDecision::Rejected(
                CompositeRejectReason::ZeroHeuristicThreshold,
            );
        }

        let mut verified_mask: u64 = 0;
        let mut joint_hasher = blake3::Hasher::new();
        joint_hasher.update(b"B60:FL-018:JOINT_COMMIT:v1");
        joint_hasher.update(&self.candidate_artifact_hash);
        joint_hasher.update(&self.expected_input_hash);
        joint_hasher.update(&self.active_policy_hash);
        joint_hasher.update(&self.min_policy_epoch.to_be_bytes());
        joint_hasher.update(&self.target_id.to_be_bytes());
        joint_hasher.update(&self.nonce.to_be_bytes());

        for att in attestations {
            if att.check_id >= 64 {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::CheckIdOutOfRange {
                        check_id: att.check_id,
                    },
                );
            }
            if !att.verify_digest() {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::InvalidEvaluatorDigest {
                        check_id: att.check_id,
                    },
                );
            }
            if att.artifact_hash != self.candidate_artifact_hash {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::ArtifactHashMismatch {
                        check_id: att.check_id,
                    },
                );
            }
            if att.input_hash != self.expected_input_hash {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::InputHashMismatch {
                        check_id: att.check_id,
                    },
                );
            }
            if att.policy_hash != self.active_policy_hash {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::PolicyHashMismatch {
                        check_id: att.check_id,
                    },
                );
            }
            if att.target_id != self.target_id {
                return CompositeSafetyDecision::Rejected(CompositeRejectReason::TargetMismatch {
                    check_id: att.check_id,
                });
            }
            if att.nonce != self.nonce {
                return CompositeSafetyDecision::Rejected(CompositeRejectReason::NonceMismatch {
                    check_id: att.check_id,
                });
            }
            if att.evidence_epoch < self.min_policy_epoch {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::StaleEvidenceEpoch {
                        check_id: att.check_id,
                        required_epoch: self.min_policy_epoch,
                        observed_epoch: att.evidence_epoch,
                    },
                );
            }

            let bit = 1u64 << att.check_id;
            let is_critical = (self.required_critical_mask & bit) != 0;
            if is_critical && !att.passed {
                return CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::CriticalCheckFailed {
                        check_id: att.check_id,
                    },
                );
            }
            if att.passed {
                verified_mask |= bit;
            }
            joint_hasher.update(&att.evaluator_digest);
        }

        if (verified_mask & self.required_critical_mask) != self.required_critical_mask {
            return CompositeSafetyDecision::Rejected(
                CompositeRejectReason::IncompleteCriticalCoverage {
                    required_mask: self.required_critical_mask,
                    verified_mask,
                },
            );
        }

        let joint_evidence_digest = *joint_hasher.finalize().as_bytes();
        let mut quorum = BicameralQuorum::with_expected_trace(
            self.required_heuristic_weight,
            joint_evidence_digest,
        );
        quorum.ingest_vote(VoteKind::HeuristicApprove {
            weight: heuristic_weight,
        });
        let outcome = quorum.ingest_vote_bound(
            VoteKind::FormalWitnessVerified {
                trace_hash: joint_evidence_digest,
            },
            self.target_id,
            self.nonce,
            replay_ledger,
        );

        match outcome {
            ConsensusOutcome::Committed {
                heuristic_weight: committed_w,
                ..
            } => CompositeSafetyDecision::Accepted {
                artifact_hash: self.candidate_artifact_hash,
                verified_critical_mask: verified_mask & self.required_critical_mask,
                heuristic_weight: committed_w,
                joint_evidence_digest,
            },
            ConsensusOutcome::AbortedByWitnessConflict => {
                CompositeSafetyDecision::Rejected(CompositeRejectReason::ReplayDetected)
            }
            ConsensusOutcome::Pending | ConsensusOutcome::AbortedByFormalVeto { .. } => {
                CompositeSafetyDecision::Rejected(
                    CompositeRejectReason::InsufficientHeuristicWeight {
                        required: self.required_heuristic_weight,
                        accumulated: heuristic_weight,
                    },
                )
            }
        }
    }
}
