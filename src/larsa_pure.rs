//! # Máquina de Estados Pura LARSA (Ring-0 / Ring-2)
//!
//! Formalización determinista libre de E/S y efectos colaterales de la máquina de consenso
//! multirréplica LARSA. Modela transiciones puras:
//! `δ: S × E -> S × P(A)`

#![allow(missing_docs)]

use std::collections::BTreeMap;
use crate::larsa::VoteKind;

/// Identificador de réplica o nodo en la red.
pub type NodeId = u32;

/// Época lógica del consenso.
pub type Epoch = u64;

/// Identificador de vista dentro de una época.
pub type ViewId = u32;

/// Clave de firma o identificación de voto emitida por un nodo.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct VoteRecordKey {
    pub epoch: Epoch,
    pub view: ViewId,
    pub voter: NodeId,
}

/// Registro inmutable de un voto emitido.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct VoteRecord {
    pub kind: VoteKind,
    pub payload_hash: Option<[u8; 32]>,
}

/// Estado del nodo en el quórum.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum NodeStatus {
    /// Activo y con derecho a voto.
    Active,
    /// Expulsado por equivocación o comportamiento bizantino.
    EvictedByEquivocation,
    /// Desconectado o caído.
    Offline,
}

/// Estado de la época en la máquina pura.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum EpochStatus {
    /// En progreso.
    InProgress,
    /// Bloque confirmado con consenso válido.
    Committed {
        trace_hash: [u8; 32],
        heuristic_weight: u32,
    },
    /// Abortado permanentemente por veto formal.
    Vetoed {
        theorem_id: u16,
    },
    /// Abortado por conflicto irreconciliable de testigos formales.
    WitnessConflict,
}

/// Estado global inmutable de la máquina pura LARSA.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LarsaPureState {
    /// Nodos configurados y su estado actual.
    pub nodes: BTreeMap<NodeId, NodeStatus>,
    /// Peso heurístico asignado a cada nodo.
    pub node_weights: BTreeMap<NodeId, u32>,
    /// Peso heurístico total requerido para commit.
    pub required_heuristic_weight: u32,
    /// Época actual.
    pub current_epoch: Epoch,
    /// Vista actual.
    pub current_view: ViewId,
    /// Estado por época.
    pub epoch_statuses: BTreeMap<Epoch, EpochStatus>,
    /// Votos registrados por (Epoch, View, Voter).
    pub votes: BTreeMap<VoteRecordKey, VoteRecord>,
    /// Testigo formal aceptado por época.
    pub formal_witnesses: BTreeMap<Epoch, [u8; 32]>,
    /// Veto formal por época.
    pub vetoes: BTreeMap<Epoch, u16>,
    /// Acumulador de peso heurístico por época.
    pub accumulated_weights: BTreeMap<Epoch, u32>,
}

/// Evento lógico entrante (estrictamente puro).
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum LogicalEvent {
    /// Inicia una nueva época de consenso.
    StartEpoch { epoch: Epoch },
    /// Voto recibido de un nodo.
    VoteReceived {
        epoch: Epoch,
        view: ViewId,
        voter: NodeId,
        kind: VoteKind,
    },
    /// Avance de vista por timeout lógico.
    ViewTimeout { epoch: Epoch, view: ViewId },
    /// Marca un nodo como desconectado.
    NodeOffline { node: NodeId },
    /// Restaura un nodo a estado activo (si no está expulsado por equivocación).
    NodeRecovered { node: NodeId },
}

/// Efecto declarativo emitido por la transición.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DeclarativeEffect {
    /// Notifica que un bloque ha sido committed.
    NotifyCommit {
        epoch: Epoch,
        trace_hash: [u8; 32],
        heuristic_weight: u32,
    },
    /// Notifica un aborto terminal por veto formal.
    NotifyVeto {
        epoch: Epoch,
        theorem_id: u16,
    },
    /// Expulsión inmediata de un nodo por comportamiento bizantino.
    EvictNode {
        node: NodeId,
        epoch: Epoch,
        view: ViewId,
    },
    /// Solicitud de cambio de vista ante timeout.
    RequestViewChange {
        epoch: Epoch,
        next_view: ViewId,
    },
}

impl LarsaPureState {
    /// Inicializa una máquina de estados pura con un conjunto de nodos y pesos.
    pub fn new(nodes: BTreeMap<NodeId, u32>, required_weight: u32) -> Self {
        let mut node_statuses = BTreeMap::new();
        let mut node_weights = BTreeMap::new();
        for (&id, &weight) in &nodes {
            node_statuses.insert(id, NodeStatus::Active);
            node_weights.insert(id, weight);
        }

        Self {
            nodes: node_statuses,
            node_weights,
            required_heuristic_weight: required_weight,
            current_epoch: 0,
            current_view: 0,
            epoch_statuses: BTreeMap::new(),
            votes: BTreeMap::new(),
            formal_witnesses: BTreeMap::new(),
            vetoes: BTreeMap::new(),
            accumulated_weights: BTreeMap::new(),
        }
    }

    /// Cuenta los nodos actualmente activos.
    pub fn active_nodes_count(&self) -> usize {
        self.nodes.values().filter(|&&s| s == NodeStatus::Active).count()
    }

    /// Comprueba si el quórum tiene al menos 2/3 de nodos activos.
    pub fn has_supermajority(&self) -> bool {
        let total = self.nodes.len();
        if total == 0 {
            return false;
        }
        let active = self.active_nodes_count();
        // Condición 2/3: active * 3 >= total * 2
        active.saturating_mul(3) >= total.saturating_mul(2)
    }
}

/// Función pura de transición: δ(S, E) -> (S', Vec<Effect>)
pub fn step(mut state: LarsaPureState, event: LogicalEvent) -> (LarsaPureState, Vec<DeclarativeEffect>) {
    let mut effects = Vec::new();

    match event {
        LogicalEvent::StartEpoch { epoch } => {
            if epoch >= state.current_epoch {
                state.current_epoch = epoch;
                state.current_view = 0;
                state.epoch_statuses.entry(epoch).or_insert(EpochStatus::InProgress);
                state.accumulated_weights.entry(epoch).or_insert(0);
            }
        }

        LogicalEvent::NodeOffline { node } => {
            if let Some(status) = state.nodes.get_mut(&node) {
                if *status != NodeStatus::EvictedByEquivocation {
                    *status = NodeStatus::Offline;
                }
            }
        }

        LogicalEvent::NodeRecovered { node } => {
            if let Some(status) = state.nodes.get_mut(&node) {
                if *status != NodeStatus::EvictedByEquivocation {
                    *status = NodeStatus::Active;
                }
            }
        }

        LogicalEvent::ViewTimeout { epoch, view } => {
            if epoch == state.current_epoch && view == state.current_view {
                let next_view = view.saturating_add(1);
                state.current_view = next_view;
                effects.push(DeclarativeEffect::RequestViewChange { epoch, next_view });
            }
        }

        LogicalEvent::VoteReceived { epoch, view, voter, kind } => {
            // Verificar si el nodo existe y está autorizado
            let voter_status = match state.nodes.get(&voter) {
                Some(&s) => s,
                None => return (state, effects), // Voto de nodo desconocido ignorado
            };

            // Nodos expulsados u offline no pueden votar
            if voter_status != NodeStatus::Active {
                return (state, effects);
            }

            // Comprobar si la época existe y no está terminada (Committed o Vetoed)
            let status = match state.epoch_statuses.get_mut(&epoch) {
                Some(s) => s,
                None => return (state, effects), // Votos sobre épocas no iniciadas formalmente son descartados
            };
            match status {
                EpochStatus::Committed { .. } | EpochStatus::Vetoed { .. } | EpochStatus::WitnessConflict => {
                    return (state, effects); // No procesar votos sobre épocas ya decididas
                }
                EpochStatus::InProgress => {}
            }

            // Clave del voto
            let key = VoteRecordKey { epoch, view, voter };

            // DETECCIÓN DE EQUIVOCATION (Mismo nodo emite voto diferente en misma (epoch, view))
            let payload_hash = match kind {
                VoteKind::FormalWitnessVerified { trace_hash } => Some(trace_hash),
                _ => None,
            };

            if let Some(existing_vote) = state.votes.get(&key) {
                if existing_vote.kind != kind || existing_vote.payload_hash != payload_hash {
                    // EQUIVOCATION DETECTADA: Evicción en O(1)
                    if let Some(s) = state.nodes.get_mut(&voter) {
                        *s = NodeStatus::EvictedByEquivocation;
                    }
                    effects.push(DeclarativeEffect::EvictNode { node: voter, epoch, view });
                    return (state, effects);
                }
                // Voto duplicado idéntico: idempotent no-op
                return (state, effects);
            }

            // Registrar voto
            state.votes.insert(key, VoteRecord { kind, payload_hash });

            // Procesar tipo de voto
            match kind {
                VoteKind::FormalRefutation { theorem_id } => {
                    state.vetoes.insert(epoch, theorem_id);
                    state.epoch_statuses.insert(epoch, EpochStatus::Vetoed { theorem_id });
                    effects.push(DeclarativeEffect::NotifyVeto { epoch, theorem_id });
                    return (state, effects);
                }

                VoteKind::FormalWitnessVerified { trace_hash } => {
                    if let Some(&first_hash) = state.formal_witnesses.get(&epoch) {
                        if first_hash != trace_hash {
                            // Conflicto permanente de testigos formales
                            state.epoch_statuses.insert(epoch, EpochStatus::WitnessConflict);
                            return (state, effects);
                        }
                    } else {
                        state.formal_witnesses.insert(epoch, trace_hash);
                    }
                }

                VoteKind::HeuristicApprove { weight } => {
                    let configured_weight = state.node_weights.get(&voter).copied().unwrap_or(0);
                    let effective_weight = core::cmp::min(weight, configured_weight);
                    let current = state.accumulated_weights.entry(epoch).or_insert(0);
                    *current = current.saturating_add(effective_weight);
                }

                VoteKind::HeuristicReject { .. } => {
                    // Rechazo no suma peso heurístico
                }
            }

            // Evaluar condición de commit
            let has_veto = state.vetoes.contains_key(&epoch);
            if !has_veto {
                let witness = state.formal_witnesses.get(&epoch).copied();
                let acc_weight = state.accumulated_weights.get(&epoch).copied().unwrap_or(0);

                if let Some(trace_hash) = witness {
                    if acc_weight >= state.required_heuristic_weight && state.has_supermajority() {
                        let outcome = EpochStatus::Committed {
                            trace_hash,
                            heuristic_weight: acc_weight,
                        };
                        state.epoch_statuses.insert(epoch, outcome);
                        effects.push(DeclarativeEffect::NotifyCommit {
                            epoch,
                            trace_hash,
                            heuristic_weight: acc_weight,
                        });
                    }
                }
            }
        }
    }

    (state, effects)
}
