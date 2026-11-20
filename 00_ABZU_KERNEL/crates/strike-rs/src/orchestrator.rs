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
use crate::omega0::{Statement, JustifiedStatement, Justification, verify_with_nogoods};
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

        // Cierre del Bucle: Verificar (⊨) contra nogoods activos del ATMS
        let nogoods = self.atms.contradicted_statement_hashes();
        if let Some(existing_id) = self.atms.find_node_by_datum(&goal.content) {
            if !self.atms.contradiction_free(existing_id) {
                return Err("Causal-Determinist FATAL: Statement is refuted in ATMS nogoods".into());
            }
        }
        if !verify_with_nogoods(&js, &nogoods) {
            return Err("Causal-Determinist FATAL: Attestor provided an unverified justification".into());
        }

        // Runtime ATMS (Vector B) primero para verificar ausencia de contradicción antes de persistir
        let node_id = self.atms.install(&js);
        if !self.atms.contradiction_free(node_id) {
            return Err("Causal-Determinist FATAL: Installed node collapsed into ATMS contradiction".into());
        }

        // Persistencia (Vector A): las conjeturas se instalan como asunciones derribables en ATMS,
        // pero solo las afirmaciones con obligaciones descargadas se asientan como conocimiento firme si lo exigen.
        let _id = self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| format!("Ledger Error: {}", e))?;
        
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

        let nogoods = self.atms.contradicted_statement_hashes();
        if let Some(existing_id) = self.atms.find_node_by_datum(&statement.content) {
            if !self.atms.contradiction_free(existing_id) {
                return Err("Causal-Determinist FATAL: Observation is refuted in ATMS nogoods".into());
            }
        }
        if !verify_with_nogoods(&js, &nogoods) {
            return Err("Causal-Determinist FATAL: Observation violates obligations".into());
        }

        let node_id = self.atms.install(&js);
        if !self.atms.contradiction_free(node_id) {
            return Err("Causal-Determinist FATAL: Observation collapsed into ATMS contradiction".into());
        }

        let _id = self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| format!("Ledger Error: {}", e))?;
            
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

    #[tokio::test]
    async fn test_orchestrator_rejects_contradicted_and_unverified_obligations() {
        use crate::omega0::Obligation;

        let ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        let attestor = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, attestor);

        // 1. Conjecture cannot satisfy Obligation::Completeness or Obligation::Provenance
        let strict_goal = Statement {
            content: "Unverified Conjecture".into(),
            modality: Modality::Epistemic,
            obligations: vec![Obligation::Completeness],
        };
        assert!(orch.resolve_intent(&strict_goal, "master_env").await.is_err());

        // 2. Statement whose ATMS node was contradicted (nogood) must be rejected on re-resolution
        let c_goal = Statement {
            content: "Contradicted Hypothesis".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let nid = orch.resolve_intent(&c_goal, "master_env").await.expect("initial conjecture");
        orch.atms.contradict(&[nid]);
        assert!(!orch.atms.is_believed(nid));

        let re_attempt = Statement {
            content: "Contradicted Hypothesis".into(),
            modality: Modality::Epistemic,
            obligations: vec![Obligation::Contradiction],
        };
        assert!(orch.resolve_intent(&re_attempt, "master_env").await.is_err());
    }
}

