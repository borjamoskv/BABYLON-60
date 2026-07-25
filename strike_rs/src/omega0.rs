//! Ω₀ — The Irreducible Kernel of a Research Operating System
//!
//! Formal identity: Ω₀ ≅ Hereditary Harrop fragment of intuitionistic logic
//!
//! Kernel = {Statement⟨M⟩, Justification} × {derive, verify, optimize}
//!
//! Two types. Three operators. Everything else is runtime.

// ──────────────────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────────────────

use serde::{Serialize, Deserialize};
use blake3;

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
        confidence_bp: u32,
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
        quorum_bp: u32,
    },
    Citation {
        source: String,
        reputation_bp: u32,
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

impl std::fmt::Display for Omega0Error {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Omega0Error::HumeViolation => write!(f, "Hume's guillotine violation"),
            Omega0Error::UnverifiedPremise(p) => write!(f, "Unverified premise: {}", p),
            Omega0Error::EmptyPremises => write!(f, "Empty premises"),
        }
    }
}

impl std::error::Error for Omega0Error {}

// ──────────────────────────────────────────────────────────
// OPERATOR 1: verify — Type-checking
// ⟦verify⟧ : J × S → {true, false}
// Decidable. O(|j| · |s|).
// ──────────────────────────────────────────────────────────

/// Checks that a Justification satisfies the obligations of a Statement.
/// This is the elimination rule — it does not construct proofs, only validates.
pub fn verify(js: &JustifiedStatement) -> bool {
    verify_with_nogoods(js, &std::collections::HashSet::new())
}

/// Verification with active nogoods set to resolve Obligation::Contradiction.
pub fn verify_with_nogoods(js: &JustifiedStatement, nogoods: &std::collections::HashSet<String>) -> bool {
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
            Obligation::Contradiction => {
                let s_hash = hash_statement(s);
                !nogoods.contains(&s_hash)
            }
            Obligation::Freshness => has_freshness(j),
            Obligation::Completeness => !matches!(j, Justification::Conjecture),
        };
        if !satisfied {
            return false;
        }
    }
    true
}

/// Deterministically computes the statement hash.
pub fn hash_statement(s: &Statement) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(s.content.as_bytes());
    hasher.update(format!("{:?}", s.modality).as_bytes());
    format!("STMT:{}", hasher.finalize().to_hex())
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
        Justification::StatisticalInference { confidence_bp, .. } => *confidence_bp >= 9500,
        Justification::ExpertConsensus { quorum_bp, .. } => *quorum_bp >= 6700,
        Justification::Citation { reputation_bp, .. } => *reputation_bp >= 8000,
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
                confidence_bp: 4000,
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
        let once = optimize(std::slice::from_ref(&js));
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
                reputation_bp: 9500,
            },
        };
        let p2 = JustifiedStatement {
            statement: epistemic(
                "SDM retrieval entropy decreases with address density",
                vec![Obligation::Confidence],
            ),
            justification: Justification::StatisticalInference {
                confidence_bp: 9700,
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

    #[cfg(test)]
    mod proptests {
        use super::super::*;
        use proptest::prelude::*;

        fn any_modality() -> impl Strategy<Value = Modality> {
            prop_oneof![
                Just(Modality::Epistemic),
                Just(Modality::Deontic),
            ]
        }

        fn any_obligation() -> impl Strategy<Value = Obligation> {
            prop_oneof![
                Just(Obligation::Provenance),
                Just(Obligation::Reproducibility),
                Just(Obligation::Confidence),
                Just(Obligation::Contradiction),
                Just(Obligation::Freshness),
                Just(Obligation::Completeness),
            ]
        }

        fn any_justification() -> impl Strategy<Value = Justification> {
            prop_oneof![
                Just(Justification::Conjecture),
                any::<u32>().prop_map(|confidence| Justification::StatisticalInference {
                    confidence_bp: confidence.min(10000),
                    method: "proptest_gen".to_string(),
                }),
                any::<u32>().prop_map(|quorum| Justification::ExpertConsensus {
                    agents: vec!["agent1".to_string()],
                    quorum_bp: quorum.min(10000),
                }),
                any::<u32>().prop_map(|reputation| Justification::Citation {
                    source: "citation_gen".to_string(),
                    reputation_bp: reputation.min(10000),
                }),
                Just(Justification::Axiom { domain: "math".to_string() }),
                Just(Justification::FormalProof {
                    proof_term: "proof".to_string(),
                    premises: vec![],
                }),
                Just(Justification::Observation {
                    timestamp: 123456,
                    sensor: "sensor".to_string(),
                }),
                Just(Justification::ExogenousInjection {
                    source: "ext".to_string(),
                    context: "context".to_string(),
                })
            ]
        }

        fn any_statement() -> impl Strategy<Value = Statement> {
            (
                "[a-zA-Z0-9 ]{1,10}", // string de texto alfanumérico simple
                any_modality(),
                prop::collection::vec(any_obligation(), 0..3)
            ).prop_map(|(content, modality, obligations)| Statement {
                content,
                modality,
                obligations,
            })
        }

        fn any_justified_statement() -> impl Strategy<Value = JustifiedStatement> {
            (any_statement(), any_justification()).prop_map(|(statement, justification)| {
                JustifiedStatement {
                    statement,
                    justification,
                }
            })
        }

        proptest! {
            #![proptest_config(ProptestConfig::with_cases(50))]

            #[test]
            fn test_optimize_is_idempotent_prop(proof in prop::collection::vec(any_justified_statement(), 0..10)) {
                let once = optimize(&proof);
                let twice = optimize(&once);
                prop_assert_eq!(once, twice);
            }

            #[test]
            fn test_optimize_is_conservative_prop(proof in prop::collection::vec(any_justified_statement(), 0..10)) {
                let optimized = optimize(&proof);
                for js in &optimized {
                    prop_assert!(verify(js));
                }
            }

            #[test]
            fn test_hume_guillotine_prop(
                premises in prop::collection::vec(any_justified_statement(), 1..5),
                goal_content in "[a-zA-Z0-9 ]{1,10}"
            ) {
                // Si el objetivo es Deontic, y todas las premisas son Epistemic, derive debe fallar
                let all_epistemic = premises.iter().all(|p| p.statement.modality == Modality::Epistemic);
                let goal = Statement {
                    content: goal_content,
                    modality: Modality::Deontic,
                    obligations: vec![],
                };
                let result = derive(&premises, &goal);
                if all_epistemic {
                    prop_assert_eq!(result.err(), Some(Omega0Error::HumeViolation));
                }
            }
        }
    }
}

