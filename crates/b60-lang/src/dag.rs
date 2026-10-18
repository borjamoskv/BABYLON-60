// ============================================================================
// B60 CAUSAL DAG COMPILER & TOPOLOGICAL PIPELINE EXECUTOR
// Framework: C5-REAL | Teorema 16: Acotamiento de Acción en Grafos Causal-Conexos
// ============================================================================

use std::collections::{HashMap, HashSet, VecDeque};
use crate::fisher::FisherSimplex;

#[derive(Debug, Clone)]
pub struct CausalNode {
    pub id: u32,
    pub label: String,
    pub exergy_cost: u64,
    pub belief_coords: Vec<f64>,
    pub lamport_ts: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum CausalParadoxError {
    CyclicAnomaly { cycle_nodes: Vec<u32> },
    TemporalInversion { from_id: u32, to_id: u32, from_ts: u64, to_ts: u64 },
    InvalidBeliefSimplex { node_id: u32, reason: String },
    UnknownNodeId(u32),
}

#[derive(Debug, Clone)]
pub struct ExecutionStage {
    pub stage_index: usize,
    pub parallel_node_ids: Vec<u32>,
    pub stage_exergy_budget: u64,
}

#[derive(Debug, Clone)]
pub struct CompiledCausalPlan {
    pub topological_order: Vec<u32>,
    pub execution_stages: Vec<ExecutionStage>,
    pub total_exergy_cost: u64,
    pub cumulative_fisher_action: f64,
}

pub struct CausalDag {
    pub nodes: HashMap<u32, CausalNode>,
    pub adj: HashMap<u32, Vec<u32>>,
    pub in_degree: HashMap<u32, usize>,
}

impl Default for CausalDag {
    fn default() -> Self {
        Self::new()
    }
}

impl CausalDag {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            adj: HashMap::new(),
            in_degree: HashMap::new(),
        }
    }

    pub fn add_node(&mut self, node: CausalNode) -> Result<(), CausalParadoxError> {
        // Validar que las coordenadas pertenezcan al símplex (suma aprox 1.0, elementos > 0)
        let sum: f64 = node.belief_coords.iter().sum();
        if !node.belief_coords.is_empty() && ((sum - 1.0).abs() > 1e-4 || node.belief_coords.iter().any(|&c| c < 0.0)) {
            return Err(CausalParadoxError::InvalidBeliefSimplex {
                node_id: node.id,
                reason: format!("Las coordenadas de creencia no suman 1.0 (suma = {})", sum),
            });
        }

        let id = node.id;
        self.nodes.insert(id, node);
        self.adj.entry(id).or_default();
        self.in_degree.entry(id).or_insert(0);
        Ok(())
    }

    pub fn add_edge(&mut self, from_id: u32, to_id: u32) -> Result<(), CausalParadoxError> {
        if !self.nodes.contains_key(&from_id) {
            return Err(CausalParadoxError::UnknownNodeId(from_id));
        }
        if !self.nodes.contains_key(&to_id) {
            return Err(CausalParadoxError::UnknownNodeId(to_id));
        }

        // Invariante de Cono de Luz Causal: Lamport(from) < Lamport(to)
        let from_ts = self.nodes[&from_id].lamport_ts;
        let to_ts = self.nodes[&to_id].lamport_ts;
        if from_ts >= to_ts {
            return Err(CausalParadoxError::TemporalInversion {
                from_id,
                to_id,
                from_ts,
                to_ts,
            });
        }

        self.adj.entry(from_id).or_default().push(to_id);
        *self.in_degree.entry(to_id).or_insert(0) += 1;
        Ok(())
    }

    /// Compila y optimiza el DAG causal generando ordenamiento topológico y ondas de paralelismo
    pub fn compile(&self) -> Result<CompiledCausalPlan, CausalParadoxError> {
        let mut in_deg = self.in_degree.clone();
        let mut queue = VecDeque::new();

        for (&id, &deg) in &in_deg {
            if deg == 0 {
                queue.push_back(id);
            }
        }

        let mut topological_order = Vec::new();
        let mut execution_stages = Vec::new();
        let mut stage_idx = 0;

        while !queue.is_empty() {
            let stage_size = queue.len();
            let mut current_parallel_nodes = Vec::new();
            let mut stage_budget = 0u64;

            for _ in 0..stage_size {
                let Some(u) = queue.pop_front() else { break; };
                topological_order.push(u);
                current_parallel_nodes.push(u);
                if let Some(node) = self.nodes.get(&u) {
                    stage_budget += node.exergy_cost;
                }

                if let Some(neighbors) = self.adj.get(&u) {
                    for &v in neighbors {
                        if let Some(deg) = in_deg.get_mut(&v) {
                            *deg = deg.saturating_sub(1);
                            if *deg == 0 {
                                queue.push_back(v);
                            }
                        }
                    }
                }
            }

            execution_stages.push(ExecutionStage {
                stage_index: stage_idx,
                parallel_node_ids: current_parallel_nodes,
                stage_exergy_budget: stage_budget,
            });
            stage_idx += 1;
        }

        // Detección de ciclo causal
        if topological_order.len() != self.nodes.len() {
            let visited: HashSet<u32> = topological_order.into_iter().collect();
            let mut cycle_nodes: Vec<u32> = self.nodes.keys().filter(|k| !visited.contains(k)).cloned().collect();
            cycle_nodes.sort();
            return Err(CausalParadoxError::CyclicAnomaly { cycle_nodes });
        }

        // Cálculo de Acción Cinética de Fisher acumulada a través de las dependencias causales
        let mut cumulative_action = 0.0;
        let mut total_exergy = 0u64;

        for node in self.nodes.values() {
            total_exergy += node.exergy_cost;
        }

        for (&from_id, neighbors) in &self.adj {
            let Some(from_node) = self.nodes.get(&from_id) else { continue; };
            let p = &from_node.belief_coords;
            let from_t = from_node.lamport_ts;

            for &to_id in neighbors {
                let Some(to_node) = self.nodes.get(&to_id) else { continue; };
                let q = &to_node.belief_coords;
                let to_t = to_node.lamport_ts;
                let delta_t = if to_t > from_t { (to_t - from_t) as f64 } else { 1.0 };

                if !p.is_empty() && !q.is_empty() && p.len() == q.len() {
                    let action = FisherSimplex::kinetic_action(p, q, delta_t);
                    cumulative_action += action;
                }
            }
        }

        Ok(CompiledCausalPlan {
            topological_order,
            execution_stages,
            total_exergy_cost: total_exergy,
            cumulative_fisher_action: cumulative_action,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_causal_dag_compilation() {
        let mut dag = CausalDag::new();

        dag.add_node(CausalNode {
            id: 1,
            label: "root_observation".to_string(),
            exergy_cost: 100,
            belief_coords: vec![0.5, 0.5],
            lamport_ts: 1,
        }).expect("BFT Fallback");

        dag.add_node(CausalNode {
            id: 2,
            label: "branch_a".to_string(),
            exergy_cost: 200,
            belief_coords: vec![0.6, 0.4],
            lamport_ts: 2,
        }).expect("BFT Fallback");

        dag.add_node(CausalNode {
            id: 3,
            label: "branch_b".to_string(),
            exergy_cost: 300,
            belief_coords: vec![0.4, 0.6],
            lamport_ts: 2,
        }).expect("BFT Fallback");

        dag.add_node(CausalNode {
            id: 4,
            label: "join_consensus".to_string(),
            exergy_cost: 150,
            belief_coords: vec![0.5, 0.5],
            lamport_ts: 3,
        }).expect("BFT Fallback");

        dag.add_edge(1, 2).expect("BFT Fallback");
        dag.add_edge(1, 3).expect("BFT Fallback");
        dag.add_edge(2, 4).expect("BFT Fallback");
        dag.add_edge(3, 4).expect("BFT Fallback");

        let plan = dag.compile().expect("BFT Fallback");
        assert_eq!(plan.topological_order.len(), 4);
        assert_eq!(plan.execution_stages.len(), 3); // Onda 0: [1], Onda 1: [2, 3], Onda 2: [4]
        assert_eq!(plan.execution_stages[0].parallel_node_ids, vec![1]);
        assert_eq!(plan.execution_stages[1].parallel_node_ids.len(), 2);
        assert_eq!(plan.execution_stages[2].parallel_node_ids, vec![4]);
        assert_eq!(plan.total_exergy_cost, 750);
        assert!(plan.cumulative_fisher_action > 0.0);
    }

    #[test]
    fn test_temporal_inversion_rejection() {
        let mut dag = CausalDag::new();

        dag.add_node(CausalNode {
            id: 1,
            label: "future_event".to_string(),
            exergy_cost: 10,
            belief_coords: vec![0.5, 0.5],
            lamport_ts: 10,
        }).expect("BFT Fallback");

        dag.add_node(CausalNode {
            id: 2,
            label: "past_event".to_string(),
            exergy_cost: 10,
            belief_coords: vec![0.5, 0.5],
            lamport_ts: 5,
        }).expect("BFT Fallback");

        // Intentar conectar del futuro (ts=10) al pasado (ts=5)
        let res = dag.add_edge(1, 2);
        assert!(matches!(res, Err(CausalParadoxError::TemporalInversion { .. })));
    }
}
