// LARSA bicameral — quórum determinista con veto formal estricto (B60-01).

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
    /// Refutación formal: veto terminal e irreversible.
    FormalRefutation {
        /// Teorema refutado.
        theorem_id: u16,
    },
}

/// Resultado del quórum.
#[derive(Debug, PartialEq, Eq)]
pub enum ConsensusOutcome {
    /// Aún sin testigo formal o sin peso suficiente.
    Pending,
    /// Conflicting witnesses permanently invalidate this quorum instance.
    AbortedByWitnessConflict,
    /// Commit: testigo formal presente y peso heurístico suficiente.
    Committed {
        /// Hash de la traza certificada.
        trace_hash: [u8; 32],
        /// Peso heurístico acumulado.
        heuristic_weight: u32,
    },
    /// Abortado por veto formal (estado terminal).
    AbortedByFormalVeto {
        /// Teorema que originó el veto.
        theorem_id: u16,
    },
}

/// Quórum bicameral: el peso heurístico nunca suple al testigo formal.
pub struct BicameralQuorum {
    required_heuristic_weight: u32,
    accumulated_weight: u32,
    formal_witness: Option<[u8; 32]>,
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
            vetoed_by_theorem: None,
            witness_conflict: false,
        }
    }

    /// Ingiere un voto y devuelve el estado resultante.
    pub fn ingest_vote(&mut self, vote: VoteKind) -> ConsensusOutcome {
        if self.witness_conflict { return ConsensusOutcome::AbortedByWitnessConflict; }
        if let Some(tid) = self.vetoed_by_theorem {
            return ConsensusOutcome::AbortedByFormalVeto { theorem_id: tid };
        }
        match vote {
            VoteKind::FormalRefutation { theorem_id } => {
                self.vetoed_by_theorem = Some(theorem_id);
                ConsensusOutcome::AbortedByFormalVeto { theorem_id }
            }
            VoteKind::FormalWitnessVerified { trace_hash } => {
                if self.formal_witness.is_some_and(|first| first != trace_hash) {
                    self.witness_conflict = true;
                    return ConsensusOutcome::AbortedByWitnessConflict;
                }
                self.formal_witness = Some(trace_hash);
                self.evaluate()
            }
            VoteKind::HeuristicApprove { weight } => {
                self.accumulated_weight = self.accumulated_weight.saturating_add(weight);
                self.evaluate()
            }
            VoteKind::HeuristicReject { .. } => self.evaluate(),
        }
    }

    #[inline]
    fn evaluate(&self) -> ConsensusOutcome {
        if self.witness_conflict { return ConsensusOutcome::AbortedByWitnessConflict; }
        if let Some(tid) = self.vetoed_by_theorem {
            return ConsensusOutcome::AbortedByFormalVeto { theorem_id: tid };
        }
        if let Some(hash) = self.formal_witness {
            if self.accumulated_weight >= self.required_heuristic_weight {
                return ConsensusOutcome::Committed {
                    trace_hash: hash,
                    heuristic_weight: self.accumulated_weight,
                };
            }
        }
        ConsensusOutcome::Pending
    }
}
