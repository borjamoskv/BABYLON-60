// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use crate::ast::{AST, Stmt};
use proof_ir::{AbstractState, Invariant, ProofIR, ProofObligation};
use std::collections::BTreeMap;
use std::string::String;
use std::vec::Vec;

pub fn generate_proof_ir() -> ProofIR {
    let default_ast = AST {
        statements: vec![
            Stmt::LetAlloc("manifest_slot".to_string(), "SharedManifest64".to_string()),
            Stmt::AssignField("manifest_slot".to_string(), "seqlock_seq".to_string(), 2),
            Stmt::Free("manifest_slot".to_string()),
        ],
    };
    generate_proof_ir_for_ast(&default_ast)
}

pub fn generate_proof_ir_for_ast(ast: &AST) -> ProofIR {
    let mut variables = Vec::new();
    let mut alloc_counts: BTreeMap<String, usize> = BTreeMap::new();
    let mut free_counts: BTreeMap<String, usize> = BTreeMap::new();

    for stmt in &ast.statements {
        match stmt {
            Stmt::LetAlloc(var, struct_name) => {
                variables.push((var.clone(), struct_name.clone()));
                *alloc_counts.entry(var.clone()).or_insert(0) += 1;
            }
            Stmt::AssignField(_, _, _) => {}
            Stmt::Free(var) => {
                *free_counts.entry(var.clone()).or_insert(0) += 1;
            }
        }
    }

    let mut invariants = Vec::new();
    let mut obligations = Vec::new();

    for (var, &allocs) in &alloc_counts {
        let frees = *free_counts.get(var).unwrap_or(&0);
        invariants.push(Invariant {
            name: format!("affine_linear_{var}"),
            condition: format!("alloc_{var} == 1 && free_{var} == 1"),
        });
        obligations.push(ProofObligation {
            name: format!("affine_balance_{var}"),
            hypotheses: vec![
                format!("def alloc_{var} : Nat := {allocs}"),
                format!("def free_{var} : Nat := {frees}"),
            ],
            goal: format!("alloc_{var} = 1 ∧ free_{var} = 1"),
        });
    }

    ProofIR {
        state: AbstractState { variables },
        invariants,
        obligations,
    }
}

/// Emite un certificado Lean 4 Core constructivo (0 axiomas) verificando la
/// aniquilación afín 1:1 (LetAlloc == Free == 1) sobre el AST de `.b60`.
pub fn emit_constructive_lean4_proof(ast: &AST, module_name: &str) -> String {
    let ir = generate_proof_ir_for_ast(ast);
    let mut lean = String::new();
    lean.push_str("import Init\n\n");
    lean.push_str("set_option warningAsError true\n\n");
    lean.push_str(&format!("namespace B60.StaticProofs.{module_name}\n\n"));

    for ob in &ir.obligations {
        for hyp in &ob.hypotheses {
            lean.push_str(hyp);
            lean.push('\n');
        }
        lean.push_str(&format!(
            "\ntheorem {} : {} := by\n  decide\n\n",
            ob.name, ob.goal
        ));
        lean.push_str(&format!(
            "/-- info: 'B60.StaticProofs.{module_name}.{}' does not depend on any axioms -/\n",
            ob.name
        ));
        lean.push_str("#guard_msgs in\n");
        lean.push_str(&format!("#print axioms {}\n\n", ob.name));
    }

    lean.push_str(&format!("end B60.StaticProofs.{module_name}\n"));
    lean
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command;

    #[test]
    fn test_static_proofs_non_empty_and_lean4_zero_axiom() {
        let ir = generate_proof_ir();
        assert!(!ir.state.variables.is_empty());
        assert!(!ir.invariants.is_empty());
        assert!(!ir.obligations.is_empty());

        let ast = AST {
            statements: vec![
                Stmt::LetAlloc("kudurru".to_string(), "SharedManifest64".to_string()),
                Stmt::AssignField("kudurru".to_string(), "seq".to_string(), 60),
                Stmt::Free("kudurru".to_string()),
            ],
        };
        let lean_src = emit_constructive_lean4_proof(&ast, "KudurruAffine");
        assert!(lean_src.contains("theorem affine_balance_kudurru"));
        assert!(!lean_src.contains("axiom "));

        if Command::new("lean").arg("--version").output().is_ok() {
            let tmp = std::env::temp_dir()
                .join(format!("b60_static_proof_{}.lean", std::process::id()));
            std::fs::write(&tmp, &lean_src).unwrap();
            let status = Command::new("lean").arg(&tmp).status().unwrap();
            let _ = std::fs::remove_file(&tmp);
            assert!(status.success(), "Constructive static proof must compile in Lean 4 with 0 axioms");
        }
    }
}
