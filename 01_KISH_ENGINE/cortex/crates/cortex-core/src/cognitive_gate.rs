//! Cognitive Validation Gate (INV_C5_CLAIMS_AND_COGNITIVE_GATE §6.3).
//! Enforces fail-closed rejection if >= 2 participants perceive absolute/magic security.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SurveyResponse {
    pub participant_id: String,
    pub distinguishes_functions: bool, // Correctly separates past (CORTEX), future (BABYLON), proof (NEMESIS)
    pub believes_absolute_security: bool, // Infers magic/absolute invulnerability
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GateVerdict {
    Pass { correct_count: usize, absolute_security_count: usize },
    FailClosedVeto { absolute_security_count: usize },
    InsufficientDistinction { correct_count: usize },
}

pub fn evaluate_cognitive_gate(responses: &[SurveyResponse]) -> Result<GateVerdict, &'static str> {
    if responses.len() != 10 {
        return Err("Panel must consist of exactly 10 participants");
    }

    let absolute_security_count = responses.iter().filter(|r| r.believes_absolute_security).count();
    let correct_count = responses.iter().filter(|r| r.distinguishes_functions).count();

    // FAIL-CLOSED VETO: If >= 2 participants infer absolute security, gate fails immediately
    if absolute_security_count >= 2 {
        return Ok(GateVerdict::FailClosedVeto { absolute_security_count });
    }

    if correct_count >= 8 {
        return Ok(GateVerdict::Pass { correct_count, absolute_security_count });
    }

    Ok(GateVerdict::InsufficientDistinction { correct_count })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gate_fail_closed_veto() {
        // 9 people distinguish functions, but 2 believe in absolute security => FAIL_CLOSED
        let mut responses = Vec::new();
        for i in 0..8 {
            responses.push(SurveyResponse {
                participant_id: format!("p_{}", i),
                distinguishes_functions: true,
                believes_absolute_security: false,
            });
        }
        for i in 8..10 {
            responses.push(SurveyResponse {
                participant_id: format!("p_{}", i),
                distinguishes_functions: true,
                believes_absolute_security: true,
            });
        }

        let verdict = evaluate_cognitive_gate(&responses).unwrap();
        assert_eq!(verdict, GateVerdict::FailClosedVeto { absolute_security_count: 2 });
    }

    #[test]
    fn test_gate_pass() {
        // 8 people distinguish functions, only 1 believes in absolute security => PASS
        let mut responses = Vec::new();
        for i in 0..8 {
            responses.push(SurveyResponse {
                participant_id: format!("p_{}", i),
                distinguishes_functions: true,
                believes_absolute_security: false,
            });
        }
        responses.push(SurveyResponse {
            participant_id: "p_8".into(),
            distinguishes_functions: false,
            believes_absolute_security: true,
        });
        responses.push(SurveyResponse {
            participant_id: "p_9".into(),
            distinguishes_functions: false,
            believes_absolute_security: false,
        });

        let verdict = evaluate_cognitive_gate(&responses).unwrap();
        assert_eq!(verdict, GateVerdict::Pass { correct_count: 8, absolute_security_count: 1 });
    }
}
