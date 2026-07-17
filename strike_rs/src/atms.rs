use std::collections::{BTreeSet, HashMap, HashSet};
use crate::ledger::{MasterLedger, AtmsState};
use crate::omega0::{JustifiedStatement, Statement, derive, verify_with_nogoods, Omega0Error, hash_statement, Justification};

/// Environment es un conjunto ordenado de hashes de assumptions.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, serde::Serialize, serde::Deserialize)]
pub struct Environment {
    pub assumptions: BTreeSet<String>,
}

impl Environment {
    pub fn new(assumptions: BTreeSet<String>) -> Self {
        Self { assumptions }
    }

    pub fn is_subset_of(&self, other: &Environment) -> bool {
        self.assumptions.is_subset(&other.assumptions)
    }

    pub fn union(&self, other: &Environment) -> Self {
        let mut union = self.assumptions.clone();
        union.extend(other.assumptions.iter().cloned());
        Self::new(union)
    }
}

/// Justificación formal ATMS
#[derive(Debug, Clone)]
pub struct AtmsJustification {
    pub antecedents: Vec<String>,
}

/// Nodo formal del ATMS de de Kleer
#[derive(Debug, Clone)]
pub struct AtmsNode {
    pub statement_hash: String,
    pub statement: Statement,
    pub label: Vec<Environment>,
    pub justifications: Vec<AtmsJustification>,
}

pub struct AtmsRuntime {
    ledger: MasterLedger,
    nodes: HashMap<String, AtmsNode>,
    assumptions: HashSet<String>,
    nogoods: Vec<Environment>,
    // Mapeo de entornos de string a sus asunciones base
    env_to_assumptions: HashMap<String, BTreeSet<String>>,
    // Cache de compatibilidad de AtmsState
    compat_state: AtmsState,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AtmsError {
    LedgerError(String),
    Omega0Error(Omega0Error),
    NogoodViolation,
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
    pub fn new(ledger: MasterLedger) -> Result<Self, rusqlite::Error> {
        let mut runtime = Self {
            ledger,
            nodes: HashMap::new(),
            assumptions: HashSet::new(),
            nogoods: Vec::new(),
            env_to_assumptions: HashMap::new(),
            compat_state: AtmsState {
                environments: HashMap::new(),
                nogoods: HashSet::new(),
            },
        };

        runtime.replay_from_ledger()?;
        Ok(runtime)
    }

    /// Reconstruye el ATMS leyendo secuencialmente los datos del Master Ledger
    fn replay_from_ledger(&mut self) -> Result<(), rusqlite::Error> {
        let assertions = self.ledger.get_all_assertions()?;
        let mut replayed_assertions = Vec::new();

        for (_id, stmt_hash, just_hash, env_id) in assertions {
            let stmt = self.ledger.get_statement(&stmt_hash)?;
            let just = self.ledger.get_justification(&just_hash)?;
            let js = JustifiedStatement {
                statement: stmt,
                justification: just,
            };
            replayed_assertions.push((js, env_id));
        }

        // Bucle de inserción en memoria
        for (js, env_id) in replayed_assertions {
            self.insert_in_memory(&js, &env_id);
        }

        // Leemos el log de nogoods de la DB
        let mut stmt = self.ledger.conn.prepare(
            "SELECT nogood_hash, environment_id FROM atms_nogoods_log"
        )?;
        let mut rows = stmt.query([])?;
        let mut nogoods_from_db = Vec::new();
        while let Some(row) = rows.next()? {
            let ng_hash: String = row.get(0)?;
            let env_id: String = row.get(1)?;
            nogoods_from_db.push((ng_hash, env_id));
        }
        drop(rows);
        drop(stmt);

        for (ng_hash, env_id) in nogoods_from_db {
            self.declare_nogood_in_memory(&ng_hash, &env_id);
        }

        self.recompute_compat_state();
        Ok(())
    }

    fn insert_in_memory(&mut self, js: &JustifiedStatement, environment_id: &str) {
        let stmt_hash = hash_statement(&js.statement);

        // Si es una asunción (conjetura, axioma, etc.), la registramos
        let is_assumption = matches!(
            js.justification,
            Justification::Conjecture | Justification::Axiom { .. }
        );

        if is_assumption {
            self.assumptions.insert(stmt_hash.clone());
            self.env_to_assumptions.entry(environment_id.to_string())
                .or_default()
                .insert(stmt_hash.clone());
        }

        // Separamos el préstamo inmutable de self.nodes para obtener antecedentes antes de mutar self.nodes
        let antecedents: Vec<String> = if let Justification::FormalProof { premises, .. } = &js.justification {
            premises.iter().map(|p| {
                self.nodes.values()
                    .find(|n| n.statement.content == *p)
                    .map(|n| n.statement_hash.clone())
                    .unwrap_or_else(|| {
                        hash_statement(&Statement {
                            content: p.clone(),
                            modality: crate::omega0::Modality::Epistemic,
                            obligations: vec![],
                        })
                    })
            }).collect()
        } else {
            Vec::new()
        };

        let node = self.nodes.entry(stmt_hash.clone()).or_insert_with(|| AtmsNode {
            statement_hash: stmt_hash.clone(),
            statement: js.statement.clone(),
            label: Vec::new(),
            justifications: Vec::new(),
        });

        if let Justification::FormalProof { .. } = &js.justification {
            node.justifications.push(AtmsJustification { antecedents });
        }

        // Propagamos la etiqueta en el ATMS
        self.propagate_label(&stmt_hash);
    }

    /// Inyecta un `JustifiedStatement` en un entorno y lo asienta en el Master Ledger.
    pub fn assume(&mut self, js: &JustifiedStatement, environment_id: &str) -> std::result::Result<String, AtmsError> {
        let stmt_hash = hash_statement(&js.statement);

        // DDB Check: Evitar inyectar si viola un Nogood del entorno activo
        let current_env_assumptions = self.env_to_assumptions.get(environment_id).cloned().unwrap_or_default();
        let mut test_env = current_env_assumptions.clone();
        test_env.insert(stmt_hash.clone());
        let test_env_struct = Environment::new(test_env);

        if self.is_inconsistent(&test_env_struct) {
            return Err(AtmsError::NogoodViolation);
        }

        let nogoods_hashes: HashSet<String> = self.compat_state.nogoods.clone();
        if !verify_with_nogoods(js, &nogoods_hashes) {
            return Err(AtmsError::Omega0Error(Omega0Error::UnverifiedPremise(js.statement.content.clone())));
        }

        // Persistimos en base de datos
        let id = self.ledger.assert_knowledge(js, environment_id)?;

        // Insertamos en memoria
        self.insert_in_memory(js, environment_id);

        self.recompute_compat_state();
        Ok(id)
    }

    /// Deriva un nuevo statement usando Ω₀, y lo inyecta directamente al entorno.
    pub fn derive_and_assume(
        &mut self,
        premises: &[JustifiedStatement],
        goal: &Statement,
        environment_id: &str,
    ) -> std::result::Result<(JustifiedStatement, String), AtmsError> {
        let derived = derive(premises, goal)?;
        let id = self.assume(&derived, environment_id)?;
        Ok((derived, id))
    }

    fn declare_nogood_in_memory(&mut self, statement_hash: &str, _environment_id: &str) {
        let mut new_nogoods = Vec::new();
        if let Some(node) = self.nodes.get(statement_hash) {
            if node.label.is_empty() {
                let mut base = BTreeSet::new();
                base.insert(statement_hash.to_string());
                new_nogoods.push(Environment::new(base));
            } else {
                new_nogoods.extend(node.label.clone());
            }
        } else {
            let mut base = BTreeSet::new();
            base.insert(statement_hash.to_string());
            new_nogoods.push(Environment::new(base));
        }

        for ng in new_nogoods {
            self.register_nogood(ng);
        }
    }

    /// Cierra el bucle DDB (Dependency-Directed Backtracking).
    /// Declara una contradicción (Nogood) y purga su presencia de todos los mundos posibles.
    pub fn declare_nogood(&mut self, statement_hash: &str, environment_id: &str) -> Result<String, rusqlite::Error> {
        let taint = self.ledger.assert_nogood(statement_hash, environment_id)?;
        self.declare_nogood_in_memory(statement_hash, environment_id);
        self.recompute_compat_state();
        Ok(taint)
    }

    /// Recomputa el AtmsState de compatibilidad
    fn recompute_compat_state(&mut self) {
        let mut compat_nogoods = HashSet::new();
        for ng in &self.nogoods {
            if ng.assumptions.len() == 1 {
                compat_nogoods.insert(ng.assumptions.iter().next().unwrap().clone());
            }
        }
        
        let mut environments = HashMap::new();
        for (env_id, assumptions) in &self.env_to_assumptions {
            let env_struct = Environment::new(assumptions.clone());
            let mut supported_stmts = HashSet::new();

            for node in self.nodes.values() {
                let is_supported = node.label.iter().any(|label_env| label_env.is_subset_of(&env_struct));
                if is_supported && !compat_nogoods.contains(&node.statement_hash) {
                    supported_stmts.insert(node.statement_hash.clone());
                }
            }
            environments.insert(env_id.clone(), supported_stmts);
        }

        self.compat_state = AtmsState {
            environments,
            nogoods: compat_nogoods,
        };
    }

    fn propagate_label(&mut self, target_hash: &str) {
        let mut new_label: Vec<Environment> = Vec::new();

        if self.assumptions.contains(target_hash) {
            let mut base = BTreeSet::new();
            base.insert(target_hash.to_string());
            new_label.push(Environment::new(base));
        }

        let justifications = if let Some(node) = self.nodes.get(target_hash) {
            node.justifications.clone()
        } else {
            return;
        };

        for just in &justifications {
            let mut just_label = vec![Environment::new(BTreeSet::new())];
            let mut antecedents_exist = true;

            for ant in &just.antecedents {
                if let Some(ant_node) = self.nodes.get(ant) {
                    let mut temp = Vec::new();
                    for e_ant in &ant_node.label {
                        for e_j in &just_label {
                            let combined = e_j.union(e_ant);
                            if !self.is_inconsistent(&combined) {
                                temp.push(combined);
                            }
                        }
                    }
                    just_label = temp;
                } else {
                    antecedents_exist = false;
                    break;
                }
            }

            if antecedents_exist {
                new_label.extend(just_label);
            }
        }

        let minimized = self.minimize_label(new_label);

        let label_changed = if let Some(node) = self.nodes.get_mut(target_hash) {
            if node.label != minimized {
                node.label = minimized;
                true
            } else {
                false
            }
        } else {
            false
        };

        if label_changed {
            if target_hash == "CONTRADICTION" || self.is_contradiction_node(target_hash) {
                let conflicts = self.nodes.get(target_hash).unwrap().label.clone();
                for conflict in conflicts {
                    self.register_nogood(conflict);
                }
            } else {
                let dependents: Vec<String> = self.nodes.values()
                    .filter(|n| n.justifications.iter().any(|j| j.antecedents.contains(&target_hash.to_string())))
                    .map(|n| n.statement_hash.clone())
                    .collect();

                for dep in dependents {
                    self.propagate_label(&dep);
                }
            }
        }
    }

    fn minimize_label(&self, label: Vec<Environment>) -> Vec<Environment> {
        let mut result: Vec<Environment> = Vec::new();
        for env in label {
            if self.is_inconsistent(&env) {
                continue;
            }
            if result.iter().any(|existing| existing.is_subset_of(&env)) {
                continue;
            }
            result.retain(|existing| !env.is_subset_of(existing));
            result.push(env);
        }
        result.sort();
        result
    }

    fn is_inconsistent(&self, env: &Environment) -> bool {
        self.nogoods.iter().any(|nogood| nogood.is_subset_of(env))
    }

    fn is_contradiction_node(&self, hash: &str) -> bool {
        if let Some(node) = self.nodes.get(hash) {
            node.statement.obligations.contains(&crate::omega0::Obligation::Contradiction)
        } else {
            false
        }
    }

    fn register_nogood(&mut self, env: Environment) {
        if !self.nogoods.contains(&env) {
            self.nogoods.push(env);

            let mut minimized_nogoods: Vec<Environment> = Vec::new();
            for ng in &self.nogoods {
                if minimized_nogoods.iter().any(|existing| existing.is_subset_of(ng)) {
                    continue;
                }
                minimized_nogoods.retain(|existing| !ng.is_subset_of(existing));
                minimized_nogoods.push(ng.clone());
            }
            self.nogoods = minimized_nogoods;

            let current_nogoods = &self.nogoods;
            let nodes = &mut self.nodes;
            for node in nodes.values_mut() {
                node.label.retain(|e| !current_nogoods.iter().any(|nogood| nogood.is_subset_of(e)));
            }
        }
    }

    pub fn state(&self) -> &AtmsState {
        &self.compat_state
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
        
        let stmt_hash = hash_statement(&s1);

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

