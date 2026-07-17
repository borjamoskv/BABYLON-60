use crate::ledger::{MasterLedger, AtmsState};
use crate::omega0::{JustifiedStatement, Statement, derive, verify, Omega0Error};
use rusqlite::Result;

/// VECTOR A & B: ATMS Bridge (Assumption-Based Truth Maintenance System)
/// Conecta el cálculo formal Ω₀ (omega0.rs) con el Causal Ledger (ledger.rs).

pub struct AtmsRuntime {
    ledger: MasterLedger,
    state: AtmsState,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AtmsError {
    LedgerError(String),
    Omega0Error(Omega0Error),
    NogoodViolation, // Intentional assumption of a known Nogood
}

impl From<rusqlite::Error> for AtmsError {
    fn from(err: rusqlite::Error) -> Self {
        AtmsError::LedgerError(err.to_string())
    }
}

impl From<Omega0Error> for AtmsError {
    fn from(err: Omega0Error) -> Self {
        AtmsError::Omega0Error(err)
    }
}

impl AtmsRuntime {
    pub fn new(ledger: MasterLedger) -> Result<Self> {
        let state = ledger.replay_to_atms_state()?;
        Ok(Self { ledger, state })
    }

    /// Inyecta un `JustifiedStatement` en un entorno y lo asienta en el Master Ledger.
    pub fn assume(&mut self, js: &JustifiedStatement, environment_id: &str) -> std::result::Result<String, AtmsError> {
        if !verify(js) {
            return Err(AtmsError::Omega0Error(Omega0Error::UnverifiedPremise(js.statement.content.clone())));
        }

        let statement_hash = crate::ledger::MasterLedger::hash_statement(&js.statement); // Need to make hash_statement public

        // DDB Check: Evitar inyectar ruido entrópico ya marcado como Nogood
        if self.state.nogoods.contains(&statement_hash) {
            return Err(AtmsError::NogoodViolation);
        }

        let id = self.ledger.assert_knowledge(js, environment_id)?;
        
        self.state.environments.entry(environment_id.to_string())
            .or_default()
            .insert(statement_hash);

        Ok(id)
    }

    /// Deriva un nuevo statement usando Ω₀, y lo inyecta directamente al entorno.
    pub fn derive_and_assume(
        &mut self,
        premises: &[JustifiedStatement],
        goal: &Statement,
        environment_id: &str,
    ) -> std::result::Result<(JustifiedStatement, String), AtmsError> {
        // Ω₀ Proof Synthesis (Hereditary Harrop fragment + Hume's Rule)
        let derived = derive(premises, goal)?;

        // ATMS Bridge: asentar en disco y estado
        let id = self.assume(&derived, environment_id)?;

        Ok((derived, id))
    }

    /// Cierra el bucle DDB (Dependency-Directed Backtracking).
    /// Declara una contradicción (Nogood) y purga su presencia de todos los mundos posibles.
    pub fn declare_nogood(&mut self, statement_hash: &str, environment_id: &str) -> Result<String> {
        let taint = self.ledger.assert_nogood(statement_hash, environment_id)?;
        self.state.nogoods.insert(statement_hash.to_string());
        
        // Purga activa del estado in-memory
        for env in self.state.environments.values_mut() {
            env.remove(statement_hash);
        }

        Ok(taint)
    }

    pub fn state(&self) -> &AtmsState {
        &self.state
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::{Modality, Justification};

    #[test]
    fn test_atms_assume_and_derive() {
        let ledger = MasterLedger::new(":memory:").unwrap();
        let mut atms = AtmsRuntime::new(ledger).unwrap();

        let s1 = Statement {
            content: "Gravitational lensing is real".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js1 = JustifiedStatement { statement: s1.clone(), justification: Justification::Conjecture };

        atms.assume(&js1, "science_env").unwrap();

        let goal = Statement {
            content: "Light bends".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };

        let (derived, _) = atms.derive_and_assume(&[js1], &goal, "science_env").unwrap();
        assert_eq!(derived.statement.content, "Light bends");

        let state = atms.state();
        assert!(state.environments.get("science_env").is_some());
    }

    #[test]
    fn test_atms_nogood_ddb() {
        let ledger = MasterLedger::new(":memory:").unwrap();
        let mut atms = AtmsRuntime::new(ledger).unwrap();

        let s1 = Statement {
            content: "False fact".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js1 = JustifiedStatement { statement: s1.clone(), justification: Justification::Conjecture };
        
        let stmt_hash = crate::ledger::MasterLedger::hash_statement(&s1);

        atms.assume(&js1, "test_env").unwrap();
        assert!(atms.state().environments.get("test_env").unwrap().contains(&stmt_hash));

        // Inject Nogood
        atms.declare_nogood(&stmt_hash, "test_env").unwrap();

        // Should be purged from environment
        assert!(!atms.state().environments.get("test_env").unwrap().contains(&stmt_hash));
        
        // Re-assuming should fail fast with NogoodViolation
        assert_eq!(atms.assume(&js1, "test_env"), Err(AtmsError::NogoodViolation));
    }
}
