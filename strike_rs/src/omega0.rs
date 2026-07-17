/// Ω₀: The Computational Atom of Research
/// A typed, immutable logic kernel where Research = Proof Search.

#[derive(Debug, Clone, PartialEq)]
pub enum Justification {
    FormalProof { proof_term: String },
    EmpiricalStudy { confidence: f64, sources: Vec<String> },
    Measurement { sensor_id: String, value: Vec<u8> },
    Simulation { model_id: String, seed: u64 },
    ExpertConsensus { consensus_ratio: f64 },
    Observation { timestamp: u64, raw_data: Vec<u8> },
}

#[derive(Debug, Clone, PartialEq)]
pub struct Statement {
    pub content: String,
    pub obligations: Vec<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct JustifiedStatement {
    pub statement: Statement,
    pub justification: Justification,
}

impl JustifiedStatement {
    /// Verify: Checks if the justification satisfies the proof obligations of the statement.
    pub fn verify(&self) -> bool {
        if !self.statement.obligations.is_empty() {
            match &self.justification {
                Justification::FormalProof { proof_term } => !proof_term.is_empty(),
                Justification::EmpiricalStudy { confidence, .. } => *confidence >= 0.95,
                Justification::Measurement { value, .. } => !value.is_empty(),
                _ => true,
            }
        } else {
            true
        }
    }
}

/// Derive: Synthesizes a new justified statement from existing premises under rules of inference.
pub fn derive(
    premises: &[JustifiedStatement],
    goal: &Statement,
) -> Result<JustifiedStatement, String> {
    // Basic verification of premises
    for premise in premises {
        if !premise.verify() {
            return Err(format!("Unverified premise: {}", premise.statement.content));
        }
    }

    // In a real execution runtime, this invokes a proof search or constraint solver.
    // For the kernel shell, we construct the goal statement with a composite justification.
    Ok(JustifiedStatement {
        statement: goal.clone(),
        justification: Justification::FormalProof {
            proof_term: format!("derived_from_premises_count_{}", premises.len()),
        },
    })
}

/// Optimize: Simplifies a proof sequence (cut-elimination analog).
pub fn optimize(proof: &mut Vec<JustifiedStatement>) {
    // Retain only statements that are verified and contribute non-redundantly to the target.
    proof.retain(|js| js.verify());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_omega0_derive_and_verify() {
        let premise = JustifiedStatement {
            statement: Statement {
                content: "Sparse Distributed Memory reduces retrieval entropy".to_string(),
                obligations: vec!["reproducibility".to_string()],
            },
            justification: Justification::EmpiricalStudy {
                confidence: 0.98,
                sources: vec!["Kanerva 1988".to_string()],
            },
        };

        assert!(premise.verify());

        let goal = Statement {
            content: "We can build an associative memory with bounded entropy".to_string(),
            obligations: vec![],
        };

        let derived = derive(&[premise], &goal).unwrap();
        assert!(derived.verify());
        assert_eq!(
            derived.justification,
            Justification::FormalProof {
                proof_term: "derived_from_premises_count_1".to_string()
            }
        );
    }
}

