//! VECTOR D: SDK / Extracción (El Límite Físico)
//! 
//! Capa de I/O que transfiere un subgrafo verificado del ATMS (Hereditary Harrop)
//! hacia formatos de consumo biológico o sistémico (JSON, Markdown, Dashboards).
//! Publish no es lógica del Kernel, es un acto de cristalización física.

use crate::ledger::MasterLedger;
use crate::omega0::JustifiedStatement;

pub enum ExportFormat {
    Json,
    Markdown,
}

pub struct Publisher<'a> {
    ledger: &'a MasterLedger,
}

impl<'a> Publisher<'a> {
    pub fn new(ledger: &'a MasterLedger) -> Self {
        Self { ledger }
    }

    /// Extrae un subgrafo causal cronológicamente ordenado, garantizando su integridad criptográfica BFT.
    pub fn extract_subgraph(&self, environment_id: &str) -> Result<Vec<JustifiedStatement>, String> {
        // 1. Verificación BFT de la Cadena (Invariante Causal)
        self.ledger.verify_chain(environment_id)
            .map_err(|e| format!("C5-REAL FATAL: Ledger corruption detected: {}", e))?;

        // 2. Extraer log causal
        let assertions = self.ledger.get_all_assertions()
            .map_err(|e| format!("Ledger read error: {}", e))?;

        let mut subgraph = Vec::new();
        for (_, s_hash, j_hash, env) in assertions {
            if env == environment_id {
                let statement = self.ledger.get_statement(&s_hash)
                    .map_err(|e| format!("Missing Statement Hash {}: {}", s_hash, e))?;
                let justification = self.ledger.get_justification(&j_hash)
                    .map_err(|e| format!("Missing Justification Hash {}: {}", j_hash, e))?;
                
                subgraph.push(JustifiedStatement { statement, justification });
            }
        }
        
        Ok(subgraph)
    }

    /// Transducción: Compila el subgrafo BFT a un artefacto biológico o sistémico (JSON/Markdown).
    pub fn publish(&self, environment_id: &str, format: ExportFormat) -> Result<String, String> {
        let subgraph = self.extract_subgraph(environment_id)?;
        
        match format {
            ExportFormat::Json => {
                serde_json::to_string_pretty(&subgraph).map_err(|e| e.to_string())
            }
            ExportFormat::Markdown => {
                let mut out = format!("# C5-REAL KNOWLEDGE ARTIFACT\n");
                out.push_str(&format!("**Environment**: `{}`\n", environment_id));
                out.push_str("**Status**: VERIFIED & SECURED (BFT)\n\n");
                out.push_str("## CAUSAL SUBGRAPH\n");
                
                for js in subgraph {
                    out.push_str(&format!("- **Statement**: {} `[{:?}]`\n", js.statement.content, js.statement.modality));
                    
                    let just_str = serde_json::to_string(&js.justification).unwrap_or_else(|_| "[]".into());
                    out.push_str(&format!("  - **Justification**: `{}`\n", just_str));
                    out.push_str(&format!("  - **Obligations**: {:?}\n", js.statement.obligations));
                }
                Ok(out)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::{Modality, Statement, Justification};
    use crate::orchestrator::{Orchestrator, Oracle};

    struct DummyOracle;
    impl Oracle for DummyOracle {
        fn query(&self, _goal: &Statement) -> Justification {
            Justification::Conjecture
        }
    }

    #[test]
    fn test_publish_markdown() {
        let ledger = MasterLedger::new(":memory:").unwrap();
        let oracle = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, oracle);

        let goal = Statement {
            content: "Gravity bends time".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        // Inject into ATMS and Ledger
        orch.resolve_intent(&goal, "prod_env").unwrap();

        let publisher = Publisher::new(&orch.ledger);
        let markdown = publisher.publish("prod_env", ExportFormat::Markdown).unwrap();
        
        assert!(markdown.contains("# C5-REAL KNOWLEDGE ARTIFACT"));
        assert!(markdown.contains("prod_env"));
        assert!(markdown.contains("Gravity bends time"));
        assert!(markdown.contains("Conjecture"));
    }

    #[test]
    fn test_publish_json() {
        let ledger = MasterLedger::new(":memory:").unwrap();
        let oracle = Box::new(DummyOracle);
        let mut orch = Orchestrator::new(ledger, oracle);

        let goal = Statement {
            content: "Energy is conserved".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        orch.resolve_intent(&goal, "json_env").unwrap();

        let publisher = Publisher::new(&orch.ledger);
        let json = publisher.publish("json_env", ExportFormat::Json).unwrap();
        
        // Assert valid JSON
        let parsed: Vec<JustifiedStatement> = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.len(), 1);
        assert_eq!(parsed[0].statement.content, "Energy is conserved");
    }
}
