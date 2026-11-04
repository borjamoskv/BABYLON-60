// =====================================================================
// BABYLON-60: Causal-Determinist Proof Intermediate Representation (IR)
// =====================================================================
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct ProofState {
    pub logical_tick: u64,
    pub memory_snapshot: HashMap<usize, i128>,
}

#[derive(Debug, Clone)]
pub struct ProofTransition {
    pub event_id: String,
    pub pre_state: ProofState,
    pub post_state: ProofState,
}

#[derive(Debug, Clone)]
pub struct ProofInvariant {
    pub description: String,
    pub condition: String,
}

#[derive(Debug, Clone)]
pub struct ProofLemma {
    pub name: String,
    pub hypothesis: Vec<String>,
    pub conclusion: String,
}

#[derive(Debug, Clone)]
pub struct ProofObligation {
    pub lemma_ref: String,
    pub verification_target: String, // e.g. "Lean4", "Coq"
}

#[derive(Debug, Clone)]
pub struct ProofWitness {
    pub causal_hash: String,
    pub trigger_event: String,
}

/// The absolute bridge between determinism and formal logic.
/// Never depends on a specific solver.
#[derive(Debug, Clone)]
pub struct ProofIR {
    pub states: Vec<ProofState>,
    pub transitions: Vec<ProofTransition>,
    pub invariants: Vec<ProofInvariant>,
    pub lemmas: Vec<ProofLemma>,
    pub obligations: Vec<ProofObligation>,
    pub witnesses: Vec<ProofWitness>,
}

impl ProofIR {
    pub fn new() -> Self {
        Self {
            states: Vec::new(),
            transitions: Vec::new(),
            invariants: Vec::new(),
            lemmas: Vec::new(),
            obligations: Vec::new(),
            witnesses: Vec::new(),
        }
    }

    /// Extractor: Lean 4 Constructivo (Cero `sorry`, `warningAsError true`, auditoría `#print axioms`)
    pub fn emit_lean(&self) -> String {
        let mut lean_code = String::from(
            "-- BABYLON-60 Auto-Generated Lean 4 Constructive Proof Obligations\nset_option warningAsError true\n\n",
        );
        for (idx, lemma) in self.lemmas.iter().enumerate() {
            lean_code.push_str(&format!("theorem {} ", lemma.name));
            for (h_idx, hyp) in lemma.hypothesis.iter().enumerate() {
                lean_code.push_str(&format!("(h{} : {}) ", h_idx + 1, hyp));
            }
            lean_code.push_str(&format!(": {} := by\n  decide\n\n", lemma.conclusion));
            lean_code.push_str(&format!(
                "/-- info: '{}' does not depend on any axioms -/\n#guard_msgs in\n#print axioms {}\n\n",
                lemma.name, lemma.name
            ));
            let _ = idx;
        }
        lean_code
    }

    /// Extractor: Coq Constructivo
    pub fn emit_coq(&self) -> String {
        let mut coq_code = String::from("(* BABYLON-60 Auto-Generated Coq Proof Obligations *)\n\n");
        for lemma in &self.lemmas {
            coq_code.push_str(&format!("Theorem {} :\n", lemma.name));
            for hyp in &lemma.hypothesis {
                coq_code.push_str(&format!("  {} ->\n", hyp));
            }
            coq_code.push_str(&format!("  {}.\nProof.\n  reflexivity.\nQed.\n\n", lemma.conclusion));
        }
        coq_code
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn emit_lean_produces_constructive_theorem_without_sorry() {
        let mut ir = ProofIR::new();
        ir.lemmas.push(ProofLemma {
            name: "tick_monotonicity_check".to_string(),
            hypothesis: vec!["1 < 2".to_string()],
            conclusion: "1 + 1 = 2".to_string(),
        });

        let code = ir.emit_lean();
        assert!(code.contains("set_option warningAsError true"));
        assert!(code.contains("theorem tick_monotonicity_check (h1 : 1 < 2) : 1 + 1 = 2 := by"));
        assert!(code.contains("decide"));
        assert!(code.contains("#guard_msgs in\n#print axioms tick_monotonicity_check"));
        assert!(!code.contains("sorry"));
    }
}

