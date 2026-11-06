//! # NEMESIS v2: Inyector de Perturbaciones Adversariales (Ring-0 / Ring-2)
//!
//! Genera perturbaciones distribuidas deterministas sobre la red:
//! - Particiones topológicas dinámicas (Aislado, Bipartición 2 vs 1).
//! - Reordenamiento no monótono de mensajes.
//! - Equivocation bizantina (emisión de votos dobles divergentes).
//! - Fallos y reinicios de nodos.

#![allow(missing_docs)]

use std::collections::BTreeSet;
use crate::larsa_pure::NodeId;

/// Matriz de conectividad entre nodos.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PartitionMatrix {
    /// Grupos o particiones disjuntas.
    partitions: Vec<BTreeSet<NodeId>>,
}

impl PartitionMatrix {
    /// Crea una red totalmente conectada (todos pueden comunicarse con todos).
    pub fn fully_connected(nodes: &[NodeId]) -> Self {
        let mut set = BTreeSet::new();
        for &n in nodes {
            set.insert(n);
        }
        Self {
            partitions: vec![set],
        }
    }

    /// Divide la red en dos particiones disjuntas (split-brain).
    pub fn split(group_a: &[NodeId], group_b: &[NodeId]) -> Self {
        let mut set_a = BTreeSet::new();
        for &n in group_a {
            set_a.insert(n);
        }
        let mut set_b = BTreeSet::new();
        for &n in group_b {
            set_b.insert(n);
        }
        Self {
            partitions: vec![set_a, set_b],
        }
    }

    /// Comprueba si dos nodos pueden comunicarse bajo la topología actual.
    pub fn can_communicate(&self, from: NodeId, to: NodeId) -> bool {
        if from == to {
            return true;
        }
        for partition in &self.partitions {
            if partition.contains(&from) && partition.contains(&to) {
                return true;
            }
        }
        false
    }
}

/// Tipo de fallo adversarial programable.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum AdversarialFault {
    /// Inyecta una partición de red en el tick lógico especificado.
    InjectPartition {
        at_tick: u64,
        matrix: PartitionMatrix,
    },
    /// Reordena o retrasa la entrega de mensajes a un nodo por `delay_ticks`.
    DelayDelivery {
        at_tick: u64,
        to_node: NodeId,
        delay_ticks: u64,
    },
    /// Simula la caída de un nodo en `at_tick`.
    CrashNode {
        at_tick: u64,
        node: NodeId,
    },
    /// Simula la recuperación de un nodo en `at_tick`.
    RecoverNode {
        at_tick: u64,
        node: NodeId,
    },
}

/// Plan determinista de fallos adversariales.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct FaultPlan {
    pub faults: Vec<AdversarialFault>,
}

impl FaultPlan {
    pub fn new() -> Self {
        Self { faults: Vec::new() }
    }

    pub fn add_fault(&mut self, fault: AdversarialFault) {
        self.faults.push(fault);
    }
}
