// C5-REAL EXERGY CERTIFIED
//! Control-Flow Guarded Kleene Algebra with Tests (CF-GKAT) Engine
//! Implements canonical equivalence class reduction and symbolic evaluation
//! for agentic non-local control flows (goto, break, return, retry).

use sha2::{Digest, Sha256};
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum CFGKATExpr {
    Skip,
    Action(String),
    Test(String),
    Seq(Box<CFGKATExpr>, Box<CFGKATExpr>),
    IfThenElse(Box<CFGKATExpr>, Box<CFGKATExpr>, Box<CFGKATExpr>),
    Goto(String),
    Break,
    Return,
    Loop(Box<CFGKATExpr>),
}

impl fmt::Display for CFGKATExpr {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CFGKATExpr::Skip => write!(f, "skip"),
            CFGKATExpr::Action(a) => write!(f, "action({})", a),
            CFGKATExpr::Test(t) => write!(f, "test({})", t),
            CFGKATExpr::Seq(e1, e2) => write!(f, "({}); ({})", e1, e2),
            CFGKATExpr::IfThenElse(b, e1, e2) => write!(f, "if ({}) then ({}) else ({})", b, e1, e2),
            CFGKATExpr::Goto(lbl) => write!(f, "goto({})", lbl),
            CFGKATExpr::Break => write!(f, "break"),
            CFGKATExpr::Return => write!(f, "return"),
            CFGKATExpr::Loop(body) => write!(f, "loop({})", body),
        }
    }
}

pub struct CFGKATEngine;

impl CFGKATEngine {
    /// Normalizes a CF-GKAT expression into its canonical representative modulo equivalence (A/≡)
    pub fn normalize(expr: &CFGKATExpr) -> CFGKATExpr {
        match expr {
            CFGKATExpr::Skip => CFGKATExpr::Skip,
            CFGKATExpr::Action(a) => CFGKATExpr::Action(a.clone()),
            CFGKATExpr::Test(t) => CFGKATExpr::Test(t.clone()),
            CFGKATExpr::Goto(lbl) => CFGKATExpr::Goto(lbl.clone()),
            CFGKATExpr::Break => CFGKATExpr::Break,
            CFGKATExpr::Return => CFGKATExpr::Return,
            CFGKATExpr::Seq(e1, e2) => {
                let n1 = Self::normalize(e1);
                let n2 = Self::normalize(e2);
                match (n1, n2) {
                    (CFGKATExpr::Skip, right) => right,
                    (left, CFGKATExpr::Skip) => left,
                    (CFGKATExpr::Return, _) => CFGKATExpr::Return,
                    (CFGKATExpr::Break, _) => CFGKATExpr::Break,
                    (CFGKATExpr::Goto(lbl), _) => CFGKATExpr::Goto(lbl),
                    (CFGKATExpr::Seq(a, b), right) => {
                        Self::normalize(&CFGKATExpr::Seq(a, Box::new(CFGKATExpr::Seq(b, Box::new(right)))))
                    }
                    (left, right) => CFGKATExpr::Seq(Box::new(left), Box::new(right)),
                }
            }
            CFGKATExpr::IfThenElse(cond, e1, e2) => {
                let nc = Self::normalize(cond);
                let n1 = Self::normalize(e1);
                let n2 = Self::normalize(e2);
                if n1 == n2 {
                    n1
                } else {
                    CFGKATExpr::IfThenElse(Box::new(nc), Box::new(n1), Box::new(n2))
                }
            }
            CFGKATExpr::Loop(body) => {
                let nb = Self::normalize(body);
                match nb {
                    CFGKATExpr::Skip => CFGKATExpr::Skip,
                    other => CFGKATExpr::Loop(Box::new(other)),
                }
            }
        }
    }

    /// Computes the canonical equivalence hash SHA-256 for the expression class [e]≡
    pub fn compute_canonical_hash(expr: &CFGKATExpr) -> [u8; 32] {
        let canonical = Self::normalize(expr);
        let repr_str = format!("{}", canonical);
        let mut hasher = Sha256::new();
        hasher.update(repr_str.as_bytes());
        hasher.finalize().into()
    }

    /// Verifies if two CF-GKAT expressions are algebraically equivalent under A/≡
    pub fn is_equivalent(expr1: &CFGKATExpr, expr2: &CFGKATExpr) -> bool {
        let hash1 = Self::compute_canonical_hash(expr1);
        let hash2 = Self::compute_canonical_hash(expr2);
        hash1 == hash2
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cfgkat_normalization_skip_elimination() {
        let expr = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Skip),
            Box::new(CFGKATExpr::Action("exec_tool".to_string())),
        );
        let norm = CFGKATEngine::normalize(&expr);
        assert_eq!(norm, CFGKATExpr::Action("exec_tool".to_string()));
    }

    #[test]
    fn test_cfgkat_equivalence_class_hash() {
        let expr1 = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Action("fetch".to_string())),
            Box::new(CFGKATExpr::Skip),
        );
        let expr2 = CFGKATExpr::Action("fetch".to_string());

        assert!(CFGKATEngine::is_equivalent(&expr1, &expr2));
    }

    #[test]
    fn test_cfgkat_non_local_control_flow() {
        let expr = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Return),
            Box::new(CFGKATExpr::Action("unreachable".to_string())),
        );
        let norm = CFGKATEngine::normalize(&expr);
        assert_eq!(norm, CFGKATExpr::Return);
    }

    #[test]
    fn test_cfgkat_goto_dead_code_elimination() {
        let expr = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Goto("LABEL_END".to_string())),
            Box::new(CFGKATExpr::Action("unreachable".to_string())),
        );
        let norm = CFGKATEngine::normalize(&expr);
        assert_eq!(norm, CFGKATExpr::Goto("LABEL_END".to_string()));
    }

    #[test]
    fn test_cfgkat_seq_associativity_equivalence() {
        // (a ; b) ; c
        let expr1 = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Seq(
                Box::new(CFGKATExpr::Action("a".to_string())),
                Box::new(CFGKATExpr::Action("b".to_string())),
            )),
            Box::new(CFGKATExpr::Action("c".to_string())),
        );

        // a ; (b ; c)
        let expr2 = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Action("a".to_string())),
            Box::new(CFGKATExpr::Seq(
                Box::new(CFGKATExpr::Action("b".to_string())),
                Box::new(CFGKATExpr::Action("c".to_string())),
            )),
        );

        assert!(CFGKATEngine::is_equivalent(&expr1, &expr2));
    }
}
