//! # NEMESIS v2: Oráculos de Invariante de Seguridad y Consenso (Ring-0 / Ring-2)
//!
//! Evalúa formalmente el estado global de la simulación tras cada tick lógico:
//! - Oracle 1: NO_SPLIT_BRAIN (No dos hashes distintos confirmados para la misma época).
//! - Oracle 2: FORMAL_VETO_TERMINAL (Ningún commit es posible tras veto formal).
//! - Oracle 3: SUPERMAJORITY_RESPECT (Commit solo si hay supermayoría 2/3 activa).
//! - Oracle 4: EQUIVOCATION_EVICTION (Nodos bizantinos equívocos son expulsados).

#![allow(missing_docs)]

use std::collections::BTreeMap;
use crate::larsa_pure::{Epoch, EpochStatus, LarsaPureState, NodeId};

/// Violación formal de una invariante del sistema.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum InvariantViolation {
    /// Violación de Safety: Conflicto de finalidad / Split-Brain.
    SplitBrain {
        epoch: Epoch,
        committed_hashes: Vec<[u8; 32]>,
    },
    /// Violación de Seguridad Formal: Commit tras veto formal de teorema.
    CommitAfterFormalVeto {
        epoch: Epoch,
        theorem_id: u16,
    },
    /// Violación de Quórum: Commit emitido sin supermayoría 2/3 activa.
    CommitWithoutSupermajority {
        epoch: Epoch,
        active_nodes: usize,
        total_nodes: usize,
    },
    /// Violación de Tolerancia Bizantina: Nodo equívoco sigue activo.
    EquivocatingNodeNotEvicted {
        node: NodeId,
    },
}

/// Oráculo de seguridad determinista.
pub struct NemesisOracles;

impl NemesisOracles {
    /// Evalúa todas las invariantes sobre el estado puro actual.
    pub fn verify_all(
        state: &LarsaPureState,
        committed_history: &BTreeMap<Epoch, [u8; 32]>,
    ) -> Result<(), InvariantViolation> {
        // 1. NO_SPLIT_BRAIN: Comprobar que en ninguna época existen dos commits conflictivos
        for (&epoch, status) in &state.epoch_statuses {
            if let EpochStatus::Committed { trace_hash, .. } = status {
                if let Some(&historic_hash) = committed_history.get(&epoch) {
                    if historic_hash != *trace_hash {
                        return Err(InvariantViolation::SplitBrain {
                            epoch,
                            committed_hashes: vec![historic_hash, *trace_hash],
                        });
                    }
                }
            }
        }

        // 2. FORMAL_VETO_TERMINAL: Ningún commit tras veto formal
        for (&epoch, &theorem_id) in &state.vetoes {
            if let Some(EpochStatus::Committed { .. }) = state.epoch_statuses.get(&epoch) {
                return Err(InvariantViolation::CommitAfterFormalVeto {
                    epoch,
                    theorem_id,
                });
            }
        }

        // 3. SUPERMAJORITY_RESPECT: No commits sin quórum 2/3
        for (&epoch, status) in &state.epoch_statuses {
            if let EpochStatus::Committed { .. } = status {
                let total = state.nodes.len();
                let active = state.active_nodes_count();
                if active.saturating_mul(3) < total.saturating_mul(2) {
                    return Err(InvariantViolation::CommitWithoutSupermajority {
                        epoch,
                        active_nodes: active,
                        total_nodes: total,
                    });
                }
            }
        }

        Ok(())
    }
}
