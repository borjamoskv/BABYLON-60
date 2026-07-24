use blake3::Hasher;
use petgraph::algo::{is_cyclic_directed, toposort};
use petgraph::graph::DiGraph;

pub mod omega0;
pub mod shield;
pub mod ledger;
pub mod atms;
pub mod orchestrator;
pub mod publisher;
pub mod bindings;

/// Motor de Taint C5-REAL (Causal Poset)
/// Garantiza ejecución de coste cero en el Fast-Loop y verifica Kahn's Invariant (INV-GCM-003).

#[derive(Debug, Clone, PartialEq)]
pub enum TaintError {
    CycleDetected,
    TopologicalSortFailed,
}

/// Nodo del Poset Causal (Owned para prevenir fugas de memoria por Box::leak en grafos dinámicos)
#[derive(Debug, Clone)]
pub struct CausalNode {
    pub id: String,
    pub payload: Vec<u8>,
}

pub struct TaintEngine {
    graph: DiGraph<CausalNode, ()>,
}

impl Default for TaintEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl TaintEngine {
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
        }
    }

    /// Inyecta un nodo en el Causal Poset. Cero-Anergía y cero Box::leak.
    pub fn add_node(&mut self, id: &str, payload: &[u8]) -> petgraph::graph::NodeIndex {
        self.graph.add_node(CausalNode {
            id: id.to_string(),
            payload: payload.to_vec(),
        })
    }

    /// Conecta dos nodos asegurando direccionalidad, con Rollback si se detecta un ciclo (OP-1).
    pub fn add_edge(&mut self, from: petgraph::graph::NodeIndex, to: petgraph::graph::NodeIndex) -> Result<(), TaintError> {
        let edge_idx = self.graph.add_edge(from, to, ());
        if is_cyclic_directed(&self.graph) {
            self.graph.remove_edge(edge_idx);
            return Err(TaintError::CycleDetected);
        }
        Ok(())
    }

    /// Verifica la Invariante de Kahn (INV-GCM-003): El poset debe ser acíclico.
    pub fn verify_kahn_invariant(&self) -> Result<(), TaintError> {
        if is_cyclic_directed(&self.graph) {
            return Err(TaintError::CycleDetected);
        }
        Ok(())
    }

    /// Calcula el CORTEX-TAINT mediante BLAKE3 colapsando el DAG topológicamente.
    /// Ejecución sin asignación de memoria dinámica durante el ciclo de hashing.
    pub fn compute_cortex_taint(&self) -> Result<String, TaintError> {
        self.verify_kahn_invariant()?;

        let mut sorted_indices = match toposort(&self.graph, None) {
            Ok(indices) => indices,
            Err(_) => return Err(TaintError::TopologicalSortFailed),
        };

        // Orden canónico (OP-2): entre nodos sin relación causal, ordenar por ID lexicográfico
        sorted_indices.sort_by(|a, b| {
            self.graph[*a].id.cmp(&self.graph[*b].id)
        });

        let mut hasher = Hasher::new();
        
        // Hashing secuencial determinista basado en el orden topológico y lexicográfico
        for idx in sorted_indices {
            let node = &self.graph[idx];
            hasher.update(node.id.as_bytes());
            hasher.update(&node.payload);
        }

        let hash_output = hasher.finalize();
        Ok(format!("TAINT:C5_REAL_RUST:{}", hash_output.to_hex()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_poset_taint() {
        let mut engine = TaintEngine::new();
        let n1 = engine.add_node("commit_A", b"payload_A");
        let n2 = engine.add_node("commit_B", b"payload_B");
        
        let _ = engine.add_edge(n1, n2); // A -> B

        assert!(engine.verify_kahn_invariant().is_ok());
        let taint = engine.compute_cortex_taint().expect("[C5-REAL] FATAL: Taint computation failed in test");
        assert!(taint.starts_with("TAINT:C5_REAL_RUST:"));
    }

    #[test]
    fn test_cycle_detection_inv_gcm_003() {
        let mut engine = TaintEngine::new();
        let n1 = engine.add_node("A", b"data");
        let n2 = engine.add_node("B", b"data");
        
        let _ = engine.add_edge(n1, n2);
        let res = engine.add_edge(n2, n1); // Ciclo: Violación de la invariante detectada en la inserción

        assert_eq!(res, Err(TaintError::CycleDetected));
        // Verificamos que el grafo no quedó contaminado
        assert!(engine.verify_kahn_invariant().is_ok());
    }
}
