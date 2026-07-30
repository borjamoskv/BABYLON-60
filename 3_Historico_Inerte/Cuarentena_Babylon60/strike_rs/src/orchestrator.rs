// C5-REAL EXERGY CERTIFIED
//! VECTOR B & C: Scheduler, Orchestrator & Oracle Interface
//!
//! Orchestrates the ATMS, MasterLedger, and external LLMs (Oracles).
//! Encapsulates stochastic entropy ($S_{in}$) into `Justification::Conjecture`.

use crate::atms::{Atms, NodeId};
use crate::ledger::MasterLedger;
use crate::omega0::{Statement, JustifiedStatement, Justification, verify};

/// Vector C: La Interfaz de Oráculo (Integración LLM)
/// The trait boundary for external stochastic generators.
pub trait Oracle {
    /// Generates a heuristic justification (usually `Conjecture`) for a goal statement.
    fn query(&self, goal: &Statement) -> Justification;
}

/// Vector B: El Bucle de Eventos (Scheduler & Orchestrator)
pub struct Orchestrator {
    pub atms: Atms,
    pub ledger: MasterLedger,
    oracle: Box<dyn Oracle>,
}

impl Orchestrator {
    pub fn new(ledger: MasterLedger, oracle: Box<dyn Oracle>) -> Self {
        Self {
            atms: Atms::new(),
            ledger,
            oracle,
        }
    }

    /// Ignición: Convierte un intent en un Proof Search y lo asienta.
    pub fn resolve_intent(&mut self, goal: &Statement, environment_id: &str) -> Result<NodeId, String> {
        // Delegación al Oráculo para contener la entropía estocástica
        let justification = self.oracle.query(goal);

        let js = JustifiedStatement {
            statement: goal.clone(),
            justification,
        };

        // Cierre del Bucle: Verificar (⊨)
        if !verify(&js) {
            return Err("C5-REAL FATAL: Oracle provided an unverified justification".into());
        }

        // Persistencia (Vector A)
        let _id = self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| format!("Ledger Error: {}", e))?;

        // Runtime ATMS (Vector B)
        let node_id = self.atms.install(&js);

        Ok(node_id)
    }

    /// Inyecciones Exógenas: Hook para APIs y monitores externos.
    pub fn inject_observation(
        &mut self,
        statement: &Statement,
        sensor: &str,
        timestamp: u64,
        environment_id: &str
    ) -> Result<NodeId, String> {
        let js = JustifiedStatement {
            statement: statement.clone(),
            justification: Justification::Observation {
                timestamp,
                sensor: sensor.to_string(),
            },
        };

        if !verify(&js) {
            return Err("C5-REAL FATAL: Observation violates obligations".into());
        }

        let _id = self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| format!("Ledger Error: {}", e))?;

        let node_id = self.atms.install(&js);

        Ok(node_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::Modality;

    struct DummyOracle;
    impl Oracle for DummyOracle {
        fn query(&self, _goal: &Statement) -> Justification {
            Justification::Conjecture
        }
    }

    #[test]
    fn test_orchestrator_resolve_intent() {
        let ledger = MasterLedger::new(":memory:").unwrap();
        let oracle = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, oracle);

        let goal = Statement {
            content: "P = NP".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        let node_id = orch.resolve_intent(&goal, "master_env").unwrap();

        // Assert it was installed as a conjecture (an assumption in ATMS)
        assert!(orch.atms.is_believed(node_id));
        assert!(orch.atms.assumption_of(node_id).is_some());
    }

    #[test]
    fn test_orchestrator_inject_observation() {
        let ledger = MasterLedger::new(":memory:").unwrap();
        let oracle = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, oracle);

        let fact = Statement {
            content: "CPU Temp > 90C".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        let node_id = orch.inject_observation(&fact, "lm-sensors", 1720000000, "master_env").unwrap();

        // Assert it was installed as an observation (a premise in ATMS)
        assert!(orch.atms.is_believed(node_id));
        assert!(orch.atms.assumption_of(node_id).is_none());
    }
}
