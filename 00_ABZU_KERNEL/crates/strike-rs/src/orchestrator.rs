// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! VECTOR B & C: Scheduler, Orchestrator & Attestor Interface
//! 
//! Orchestrates the ATMS, MasterLedger, and external LLMs (Oracles).
//! Encapsulates stochastic entropy ($S_{in}$) into `Justification::Conjecture`.

use crate::atms::{Atms, NodeId};
use crate::ledger::MasterLedger;
use crate::omega0::{Statement, JustifiedStatement, Justification, verify};
use async_trait::async_trait;

/// Vector C: La Interfaz de Atestador (Integración LLM)
/// The trait boundary for external stochastic generators.
#[async_trait]
pub trait Attestor: Send + Sync {
    /// Generates a heuristic justification (usually `Conjecture` or `ExogenousInjection`) for a goal statement.
    async fn query(&self, goal: &Statement) -> Justification;
}

/// Vector B: El Bucle de Eventos (Scheduler & Orchestrator)
pub struct Orchestrator {
    pub atms: Atms,
    pub ledger: MasterLedger,
    attestor: Box<dyn Attestor>,
}

impl Orchestrator {
    pub fn new(ledger: MasterLedger, attestor: Box<dyn Attestor>) -> Self {
        Self {
            atms: Atms::new(),
            ledger,
            attestor,
        }
    }

    /// Ignición: Convierte un intent en un Proof Search y lo asienta.
    pub async fn resolve_intent(&mut self, goal: &Statement, environment_id: &str) -> Result<NodeId, String> {
        // Delegación al Atestador para contener la entropía estocástica
        let justification = self.attestor.query(goal).await;
        
        let js = JustifiedStatement {
            statement: goal.clone(),
            justification,
        };

        // Cierre del Bucle: Verificar (⊨)
        if !verify(&js) {
            return Err("Causal-Determinist FATAL: Attestor provided an unverified justification".into());
        }

        // Persistencia (Vector A)
        let _id = self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| format!("Ledger Error: {}", e))?;

        // Runtime ATMS (Vector B)
        let node_id = self.atms.install(&js);
        
        Ok(node_id)
    }

    /// Inyecciones Exógenas: Hook para APIs y monitores externos.
    pub async fn inject_observation(
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
            return Err("Causal-Determinist FATAL: Observation violates obligations".into());
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
    #[async_trait]
    impl Attestor for DummyOracle {
        async fn query(&self, _goal: &Statement) -> Justification {
            Justification::Conjecture
        }
    }

    #[tokio::test]
    async fn test_orchestrator_resolve_intent() {
        let ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        let attestor = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, attestor);

        let goal = Statement {
            content: "P = NP".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        let node_id = orch.resolve_intent(&goal, "master_env").await.expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        
        // Assert it was installed as a conjecture (an assumption in ATMS)
        assert!(orch.atms.is_believed(node_id));
        assert!(orch.atms.assumption_of(node_id).is_some());
    }

    #[tokio::test]
    async fn test_orchestrator_inject_observation() {
        let ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        let attestor = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, attestor);

        let fact = Statement {
            content: "CPU Temp > 90C".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        let node_id = orch.inject_observation(&fact, "lm-sensors", 1720000000, "master_env").await.expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        
        // Assert it was installed as an observation (a premise in ATMS)
        assert!(orch.atms.is_believed(node_id));
        assert!(orch.atms.assumption_of(node_id).is_none());
    }
}

