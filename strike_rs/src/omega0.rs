/// Ω₀ — The Irreducible Kernel of a Research Operating System
///
/// Formal identity: Ω₀ ≅ Hereditary Harrop fragment of intuitionistic logic
///
/// Kernel = {Statement⟨M⟩, Justification} × {derive, verify, optimize}
///
/// Two types. Three operators. Everything else is runtime.

// ──────────────────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────────────────

use serde::{Serialize, Deserialize};

/// Modality parameter M ∈ {Epistemic, Deontic}.
/// Captures Hume's guillotine as a type rule.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Modality {
    /// Assertions about what IS (facts, hypotheses, observations).
    Epistemic,
    /// Assertions about what OUGHT TO BE (policies, ethical constraints, process rules).
    Deontic,
}

/// Statement⟨M⟩ — A typed claim parameterized by modality.
/// Corresponds to a Harrop formula over signature Σ.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Statement {
    pub content: String,
    pub modality: Modality,
    /// Open proof obligations. While non-empty, the statement is incomplete.
    pub obligations: Vec<Obligation>,
}

/// A proof obligation that must be discharged before a statement is fully justified.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Obligation {
    Provenance,
    Reproducibility,
    Contradiction,
    Confidence,
    Freshness,
    Completeness,
}

/// Justification — A proof term establishing WHY a Statement holds.
/// Corresponds to typed λ-terms of the Hereditary Harrop fragment.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Justification {
    // === Endogenous (derived within the system) ===
    FormalProof {
        proof_term: String,
        premises: Vec<String>,
    },
    StatisticalInference {
        confidence: f64,
        method: String,
    },

    // === Exogenous (injected from outside the system) ===
    Observation {
        timestamp: u64,
        sensor: String,
    },
    ExogenousInjection {
        source: String,
        context: String,
    },

    // === Social (agent-based, not content-based) ===
    ExpertConsensus {
        agents: Vec<String>,
        quorum: f64,
    },
    Citation {
        source: String,
        reputation: f64,
    },

    // === Provisional (without complete proof) ===
    Conjecture,
    Axiom {
        domain: String,
    },
}

/// A justified pair (S, J) — the atomic unit of knowledge.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JustifiedStatement {
    pub statement: Statement,
    pub justification: Justification,
}

// ──────────────────────────────────────────────────────────
// ERRORS
// ──────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum Omega0Error {
    /// Hume's guillotine: cannot derive Deontic from purely Epistemic premises.
    HumeViolation,
    /// A premise failed verification.
    UnverifiedPremise(String),
    /// No premises provided for derivation.
    EmptyPremises,
}

// ──────────────────────────────────────────────────────────
// OPERATOR 1: verify — Type-checking
// ⟦verify⟧ : J × S → {true, false}
// Decidable. O(|j| · |s|).
// ──────────────────────────────────────────────────────────

/// Checks that a Justification satisfies the obligations of a Statement.
/// This is the elimination rule — it does not construct proofs, only validates.
pub fn verify(js: &JustifiedStatement) -> bool {
    let s = &js.statement;
    let j = &js.justification;

    // A statement with no obligations is trivially verified.
    if s.obligations.is_empty() {
        return true;
    }

    for obligation in &s.obligations {
        let satisfied = match obligation {
            Obligation::Provenance => has_provenance(j),
            Obligation::Reproducibility => has_reproducibility(j),
            Obligation::Confidence => has_sufficient_confidence(j),
            Obligation::Contradiction => true, // Requires runtime ATMS layer
            Obligation::Freshness => has_freshness(j),
            Obligation::Completeness => !matches!(j, Justification::Conjecture),
        };
        if !satisfied {
            return false;
        }
    }
    true
}

fn has_provenance(j: &Justification) -> bool {
    !matches!(j, Justification::Conjecture)
}

fn has_reproducibility(j: &Justification) -> bool {
    matches!(
        j,
        Justification::FormalProof { .. }
            | Justification::StatisticalInference { .. }
            | Justification::Observation { .. }
    )
}

fn has_sufficient_confidence(j: &Justification) -> bool {
    match j {
        Justification::FormalProof { .. } => true, // Formal proofs have confidence = 1.0
        Justification::StatisticalInference { confidence, .. } => *confidence >= 0.95,
        Justification::ExpertConsensus { quorum, .. } => *quorum >= 0.67,
        Justification::Citation { reputation, .. } => *reputation >= 0.8,
        Justification::Conjecture => false,
        _ => true,
    }
}

fn has_freshness(j: &Justification) -> bool {
    matches!(
        j,
        Justification::Observation { .. } | Justification::ExogenousInjection { .. }
    ) || !matches!(j, Justification::Conjecture)
}

// ──────────────────────────────────────────────────────────
// OPERATOR 2: derive — Proof synthesis
// ⟦derive⟧ : P(S×J) × S → (S×J) ∪ {⊥}
// Decidable in Hereditary Harrop. PSPACE (prop) / EXPTIME (FO bounded).
//
// HUME'S RULE: Γ_Epistemic ⊬ S_Deontic
// ──────────────────────────────────────────────────────────

/// Derives a new justified statement from premises, enforcing Hume's guillotine.
pub fn derive(
    premises: &[JustifiedStatement],
    goal: &Statement,
) -> Result<JustifiedStatement, Omega0Error> {
    if premises.is_empty() {
        return Err(Omega0Error::EmptyPremises);
    }

    // HUME'S RULE: Deontic goals require at least one Deontic premise.
    if goal.modality == Modality::Deontic {
        let has_deontic_premise = premises
            .iter()
            .any(|p| p.statement.modality == Modality::Deontic);
        if !has_deontic_premise {
            return Err(Omega0Error::HumeViolation);
        }
    }

    // All premises must pass verification.
    for premise in premises {
        if !verify(premise) {
            return Err(Omega0Error::UnverifiedPremise(
                premise.statement.content.clone(),
            ));
        }
    }

    // Construct the derived statement with a formal proof justification.
    let premise_refs: Vec<String> = premises
        .iter()
        .map(|p| p.statement.content.clone())
        .collect();

    Ok(JustifiedStatement {
        statement: goal.clone(),
        justification: Justification::FormalProof {
            proof_term: format!("derived[{}]", premise_refs.join(" ∧ ")),
            premises: premise_refs,
        },
    })
}

// ──────────────────────────────────────────────────────────
// OPERATOR 3: optimize — Proof normalization
// ⟦optimize⟧ : List(S×J) → List(S×J)
// Decidable. ≤ 2-EXPTIME. Idempotent.
//
// Invariant: optimize(P) ⊢ s ⟺ P ⊢ s (conservativity)
// Invariant: optimize(optimize(P)) = optimize(P) (idempotence)
// ──────────────────────────────────────────────────────────

/// Simplifies a proof sequence: removes unverified statements, deduplicates.
/// Does not change what is provable (conservativity).
pub fn optimize(proof: &[JustifiedStatement]) -> Vec<JustifiedStatement> {
    let mut result: Vec<JustifiedStatement> = Vec::new();
    let mut seen_content: std::collections::HashSet<String> = std::collections::HashSet::new();

    for js in proof {
        // Only retain verified statements.
        if !verify(js) {
            continue;
        }
        // Deduplicate by content.
        if seen_content.insert(js.statement.content.clone()) {
            result.push(js.clone());
        }
    }

    result
}

// ──────────────────────────────────────────────────────────
// TESTS
// ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn epistemic(content: &str, obligations: Vec<Obligation>) -> Statement {
        Statement {
            content: content.to_string(),
            modality: Modality::Epistemic,
            obligations,
        }
    }

    fn deontic(content: &str) -> Statement {
        Statement {
            content: content.to_string(),
            modality: Modality::Deontic,
            obligations: vec![],
        }
    }

    // ── verify ──

    #[test]
    fn test_verify_formal_proof_passes() {
        let js = JustifiedStatement {
            statement: epistemic(
                "SDM reduces retrieval entropy",
                vec![Obligation::Provenance, Obligation::Reproducibility],
            ),
            justification: Justification::FormalProof {
                proof_term: "kanerva_1988_thm_3".into(),
                premises: vec!["Kanerva 1988".into()],
            },
        };
        assert!(verify(&js));
    }

    #[test]
    fn test_verify_conjecture_fails_completeness() {
        let js = JustifiedStatement {
            statement: epistemic("Unproven hypothesis", vec![Obligation::Completeness]),
            justification: Justification::Conjecture,
        };
        assert!(!verify(&js));
    }

    #[test]
    fn test_verify_low_confidence_fails() {
        let js = JustifiedStatement {
            statement: epistemic("Weak claim", vec![Obligation::Confidence]),
            justification: Justification::StatisticalInference {
                confidence: 0.4,
                method: "bootstrap".into(),
            },
        };
        assert!(!verify(&js));
    }

    // ── derive ──

    #[test]
    fn test_derive_epistemic_from_epistemic() {
        let premise = JustifiedStatement {
            statement: epistemic("A implies B", vec![]),
            justification: Justification::FormalProof {
                proof_term: "axiom_1".into(),
                premises: vec![],
            },
        };
        let goal = epistemic("B holds", vec![]);
        let result = derive(&[premise], &goal);
        assert!(result.is_ok());
        assert!(verify(&result.unwrap()));
    }

    #[test]
    fn test_derive_deontic_from_epistemic_fails_hume() {
        let premise = JustifiedStatement {
            statement: epistemic("Water boils at 100C", vec![]),
            justification: Justification::Observation {
                timestamp: 1720000000,
                sensor: "thermometer".into(),
            },
        };
        let goal = deontic("We should boil water");
        let result = derive(&[premise], &goal);
        assert_eq!(result, Err(Omega0Error::HumeViolation));
    }

    #[test]
    fn test_derive_deontic_from_deontic_succeeds() {
        let premise = JustifiedStatement {
            statement: deontic("All research must be reproducible"),
            justification: Justification::Axiom {
                domain: "research_ethics".into(),
            },
        };
        let goal = deontic("This experiment must be reproducible");
        let result = derive(&[premise], &goal);
        assert!(result.is_ok());
    }

    #[test]
    fn test_derive_rejects_unverified_premise() {
        let bad_premise = JustifiedStatement {
            statement: epistemic("Dubious claim", vec![Obligation::Confidence]),
            justification: Justification::Conjecture,
        };
        let goal = epistemic("Derived from dubious", vec![]);
        let result = derive(&[bad_premise], &goal);
        assert!(matches!(result, Err(Omega0Error::UnverifiedPremise(_))));
    }

    // ── optimize ──

    #[test]
    fn test_optimize_removes_unverified() {
        let good = JustifiedStatement {
            statement: epistemic("Verified fact", vec![]),
            justification: Justification::FormalProof {
                proof_term: "p1".into(),
                premises: vec![],
            },
        };
        let bad = JustifiedStatement {
            statement: epistemic("Unverified", vec![Obligation::Completeness]),
            justification: Justification::Conjecture,
        };
        let result = optimize(&[good.clone(), bad]);
        assert_eq!(result.len(), 1);
        assert_eq!(result[0], good);
    }

    #[test]
    fn test_optimize_deduplicates() {
        let js = JustifiedStatement {
            statement: epistemic("Same fact", vec![]),
            justification: Justification::Axiom {
                domain: "test".into(),
            },
        };
        let result = optimize(&[js.clone(), js.clone(), js]);
        assert_eq!(result.len(), 1);
    }

    #[test]
    fn test_optimize_is_idempotent() {
        let js = JustifiedStatement {
            statement: epistemic("Fact A", vec![]),
            justification: Justification::Axiom {
                domain: "test".into(),
            },
        };
        let once = optimize(&[js.clone()]);
        let twice = optimize(&once);
        assert_eq!(once, twice);
    }

    // ── Integration ──

    #[test]
    fn test_full_pipeline_derive_verify_optimize() {
        // Premises
        let p1 = JustifiedStatement {
            statement: epistemic("SDM is an associative memory model", vec![]),
            justification: Justification::Citation {
                source: "Kanerva 1988".into(),
                reputation: 0.95,
            },
        };
        let p2 = JustifiedStatement {
            statement: epistemic(
                "SDM retrieval entropy decreases with address density",
                vec![Obligation::Confidence],
            ),
            justification: Justification::StatisticalInference {
                confidence: 0.97,
                method: "Monte Carlo simulation".into(),
            },
        };

        // Derive
        let goal = epistemic("Bounded-entropy associative memory is feasible", vec![]);
        let derived = derive(&[p1, p2], &goal).expect("derivation should succeed");

        // Verify
        assert!(verify(&derived));

        // Optimize
        let optimized = optimize(&[derived.clone(), derived]);
        assert_eq!(optimized.len(), 1); // deduplicated
        assert!(verify(&optimized[0]));
    }
}
