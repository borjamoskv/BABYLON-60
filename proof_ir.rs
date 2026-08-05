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

    /// Extractor: Lean 4
    pub fn emit_lean(&self) -> String {
        let mut lean_code = String::from("-- BABYLON-60 Auto-Generated Lean 4 Proof Obligations\n\n");
        for lemma in &self.lemmas {
            lean_code.push_str(&format!("lemma {} :\n", lemma.name));
            for hyp in &lemma.hypothesis {
                lean_code.push_str(&format!("  {} \\to\n", hyp));
            }
            lean_code.push_str(&format!("  {} := by\n  sorry\n\n", lemma.conclusion));
        }
        lean_code
    }

    /// Extractor: Coq
    pub fn emit_coq(&self) -> String {
        let mut coq_code = String::from("(* BABYLON-60 Auto-Generated Coq Proof Obligations *)\n\n");
        for lemma in &self.lemmas {
            coq_code.push_str(&format!("Lemma {} :\n", lemma.name));
            for hyp in &lemma.hypothesis {
                coq_code.push_str(&format!("  {} ->\n", hyp));
            }
            coq_code.push_str(&format!("  {}.\nProof.\n  Admitted.\n\n", lemma.conclusion));
        }
        coq_code
    }
}
