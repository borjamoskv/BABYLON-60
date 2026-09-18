//! Deterministic Constraint Evaluation Engine (Solver)
//! Evaluates IFC Model entities against PGOU/CTE Rulebook constraints

use crate::dsl::Rulebook;
use crate::ifc::IfcModel;
use serde::{Deserialize, Serialize};
use std::time::Instant;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Violation {
    pub code: String,
    pub title: String,
    pub description: String,
    pub measured: String,
    pub limit: String,
    pub legal_citation: String,
    pub file_path: String,
    pub line: u32,
    pub severity: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerificationResult {
    pub status: String,
    pub ifc_hash: String,
    pub pgou_hash: String,
    pub execution_time_ms: u64,
    pub violations: Vec<Violation>,
}

pub fn evaluate(
    model: &IfcModel,
    rulebook: &Rulebook,
    ifc_hash: String,
    pgou_hash: String,
    start_time: Instant,
) -> VerificationResult {
    let mut violations = Vec::new();
    let file_str = model.file_path.to_string_lossy().to_string();

    for rule in &rulebook.rules {
        let matching_entities = model.find_entities_by_type(&rule.target);

        for entity in matching_entities {
            // Check if entity has the target property
            let val_opt = entity
                .numeric_properties
                .iter()
                .find(|(k, _)| k.eq_ignore_ascii_case(&rule.property))
                .map(|(_, v)| *v);

            if let Some(val) = val_opt {
                let passed = rule.operator.evaluate(val, rule.threshold);
                if !passed {
                    let unit_str = rule.unit.as_deref().unwrap_or("");
                    let unit_suffix = if unit_str.is_empty() {
                        "".to_string()
                    } else {
                        format!(" {}", unit_str)
                    };

                    violations.push(Violation {
                        code: rule.code.clone(),
                        title: rule.title.clone(),
                        description: rule.description.clone(),
                        measured: format!("{}{}", format_val(val), unit_suffix).trim().to_string(),
                        limit: format!("{}{}", format_val(rule.threshold), unit_suffix).trim().to_string(),
                        legal_citation: rule.legal_citation.clone(),
                        file_path: file_str.clone(),
                        line: entity.line_number,
                        severity: rule.severity.clone(),
                    });
                }
            }
        }
    }

    let status = if violations.is_empty() { "SAT" } else { "UNSAT" };
    let execution_time_ms = start_time.elapsed().as_millis() as u64;

    VerificationResult {
        status: status.to_string(),
        ifc_hash,
        pgou_hash,
        execution_time_ms,
        violations,
    }
}

fn format_val(val: f64) -> String {
    if (val.fract()).abs() < 1e-6 {
        format!("{:.1}", val)
    } else {
        format!("{:.2}", val)
    }
}
