//! # NEMESIS v2: Motor de Replay Causal y Delta-Debugging (Ring-0 / Ring-2)
//!
//! Registra, reproduce y minimiza trazas adversariales:
//! - Empaquetado de séxtupla causal: `(Seed, CommitSHA, ToolchainHash, BinaryBLAKE3, FaultPlan, TraceLog)`.
//! - Minimizador de traza (Delta-Debugging) para aislar el contraejemplo irreducible.

#![allow(missing_docs)]

use crate::larsa_pure::LogicalEvent;
use crate::nemesis_v2::faults::AdversarialFault;

/// Registro sellado de una traza con metadatos de reproducibilidad bit a bit.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CausalEvidenceBundle {
    pub seed: u64,
    pub commit_sha: String,
    pub toolchain_version: String,
    pub binary_blake3: [u8; 32],
    pub fault_plan: Vec<AdversarialFault>,
    pub events: Vec<(u64, LogicalEvent)>,
}

impl CausalEvidenceBundle {
    pub fn new(
        seed: u64,
        commit_sha: &str,
        toolchain_version: &str,
        binary_blake3: [u8; 32],
        fault_plan: Vec<AdversarialFault>,
        events: Vec<(u64, LogicalEvent)>,
    ) -> Self {
        Self {
            seed,
            commit_sha: commit_sha.to_string(),
            toolchain_version: toolchain_version.to_string(),
            binary_blake3,
            fault_plan,
            events,
        }
    }
}

/// Minimizador de trazas por Delta-Debugging.
pub struct DeltaDebugger;

impl DeltaDebugger {
    /// Reduce una secuencia de eventos a su subconjunto mínimo reproducible que
    /// preserve la violación bajo el predicado evaluador `test_fn`.
    pub fn minimize<F>(events: &[(u64, LogicalEvent)], test_fn: F) -> Vec<(u64, LogicalEvent)>
    where
        F: Fn(&[(u64, LogicalEvent)]) -> bool,
    {
        if events.is_empty() || !test_fn(events) {
            return events.to_vec();
        }

        let mut current = events.to_vec();

        // Poda secuencial de un solo elemento (1-minimal delta debugging)
        let mut i = 0;
        while i < current.len() {
            let mut candidate = current.clone();
            candidate.remove(i);

            if test_fn(&candidate) {
                // El subconjunto más pequeño todavía dispara la violación
                current = candidate;
            } else {
                // Este evento es necesario para causar el fallo
                i += 1;
            }
        }

        current
    }
}
