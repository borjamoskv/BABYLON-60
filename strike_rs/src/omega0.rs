

use serde::{Serialize, Deserialize};
use blake3;

pub enum Modality {
    Epistemic,
    Deontic,
}

pub struct Statement {
    pub content: String,
    pub modality: Modality,
    pub obligations: Vec<Obligation>,
}

pub enum Obligation {
    Provenance,
    Reproducibility,
    Contradiction,
    Confidence,
    Freshness,
    Completeness,
}

pub enum Justification {
    FormalProof {
        proof_term: String,
        premises: Vec<String>,
    },
    StatisticalInference {
        confidence: f64,
        method: String,
    },

    Observation {
        timestamp: u64,
        sensor: String,
    },
    ExogenousInjection {
        source: String,
        context: String,
    },

    ExpertConsensus {
        agents: Vec<String>,
        quorum: f64,
    },
    Citation {
        source: String,
        reputation: f64,
    },

    Conjecture,
    Axiom {
        domain: String,
    },
}

pub struct JustifiedStatement {
    pub statement: Statement,
    pub justification: Justification,
}


pub enum Omega0Error {
    HumeViolation,
    UnverifiedPremise(String),
    EmptyPremises,
}


pub fn verify(js: &JustifiedStatement) -> bool {
    verify_with_nogoods(js, &std::collections::HashSet::new())
}

pub fn verify_with_nogoods(js: &JustifiedStatement, nogoods: &std::collections::HashSet<String>) -> bool {
    let s = &js.statement;
    let j = &js.justification;

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


pub fn derive(
    premises: &[JustifiedStatement],
    goal: &Statement,
) -> Result<JustifiedStatement, Omega0Error> {
    if premises.is_empty() {
        return Err(Omega0Error::EmptyPremises);
    }

    if goal.modality == Modality::Deontic {
        let has_deontic_premise = premises
            .iter()
            .any(|p| p.statement.modality == Modality::Deontic);
        if !has_deontic_premise {
            return Err(Omega0Error::HumeViolation);
        }
    }

    for premise in premises {
        if !verify(premise) {
            return Err(Omega0Error::UnverifiedPremise(
                premise.statement.content.clone(),
            ));
        }
    }

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


pub fn optimize(proof: &[JustifiedStatement]) -> Vec<JustifiedStatement> {
    let mut result: Vec<JustifiedStatement> = Vec::new();
    let mut seen_content: std::collections::HashSet<String> = std::collections::HashSet::new();

    for js in proof {
        if !verify(js) {
            continue;
        }
        if seen_content.insert(js.statement.content.clone()) {
            result.push(js.clone());
        }
    }

    result
}


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

    fn test_verify_conjecture_fails_completeness() {
        let js = JustifiedStatement {
            statement: epistemic("Unproven hypothesis", vec![Obligation::Completeness]),
            justification: Justification::Conjecture,
        };
        assert!(!verify(&js));
    }

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

    fn test_derive_rejects_unverified_premise() {
        let bad_premise = JustifiedStatement {
            statement: epistemic("Dubious claim", vec![Obligation::Confidence]),
            justification: Justification::Conjecture,
        };
        let goal = epistemic("Derived from dubious", vec![]);
        let result = derive(&[bad_premise], &goal);
        assert!(matches!(result, Err(Omega0Error::UnverifiedPremise(_))));
    }


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


    fn test_full_pipeline_derive_verify_optimize() {
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

        let goal = epistemic("Bounded-entropy associative memory is feasible", vec![]);
        let derived = derive(&[p1, p2], &goal).expect("derivation should succeed");

        assert!(verify(&derived));

        let optimized = optimize(&[derived.clone(), derived]);
        assert_eq!(optimized.len(), 1); // deduplicated
        assert!(verify(&optimized[0]));
    }

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
                any::<f64>().prop_map(|confidence| Justification::StatisticalInference {
                    confidence: confidence.abs().min(1.0),
                    method: "proptest_gen".to_string(),
                }),
                any::<f64>().prop_map(|quorum| Justification::ExpertConsensus {
                    agents: vec!["agent1".to_string()],
                    quorum: quorum.abs().min(1.0),
                }),
                any::<f64>().prop_map(|reputation| Justification::Citation {
                    source: "citation_gen".to_string(),
                    reputation: reputation.abs().min(1.0),
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

            fn test_optimize_is_idempotent_prop(proof in prop::collection::vec(any_justified_statement(), 0..10)) {
                let once = optimize(&proof);
                let twice = optimize(&once);
                prop_assert_eq!(once, twice);
            }

            fn test_optimize_is_conservative_prop(proof in prop::collection::vec(any_justified_statement(), 0..10)) {
                let optimized = optimize(&proof);
                for js in &optimized {
                    prop_assert!(verify(js));
                }
            }

            fn test_hume_guillotine_prop(
                premises in prop::collection::vec(any_justified_statement(), 1..5),
                goal_content in "[a-zA-Z0-9 ]{1,10}"
            ) {
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

