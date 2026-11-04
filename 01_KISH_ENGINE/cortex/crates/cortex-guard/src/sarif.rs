//! SARIF v2.1.0 Exporter for GitHub Code Scanning
//! Compliant with OASIS Standard SARIF v2.1.0

use crate::eval::VerificationResult;
use serde::Serialize;

#[derive(Serialize)]
pub struct SarifReport {
    #[serde(rename = "$schema")]
    pub schema: String,
    pub version: String,
    pub runs: Vec<SarifRun>,
}

#[derive(Serialize)]
pub struct SarifRun {
    pub tool: SarifTool,
    pub results: Vec<SarifResult>,
}

#[derive(Serialize)]
pub struct SarifTool {
    pub driver: SarifDriver,
}

#[derive(Serialize)]
pub struct SarifDriver {
    pub name: String,
    pub version: String,
    pub rules: Vec<SarifRule>,
}

#[derive(Serialize)]
pub struct SarifRule {
    pub id: String,
    pub name: String,
    pub short_description: SarifText,
}

#[derive(Serialize)]
pub struct SarifResult {
    pub rule_id: String,
    pub level: String,
    pub message: SarifText,
    pub locations: Vec<SarifLocation>,
}

#[derive(Serialize)]
pub struct SarifText {
    pub text: String,
}

#[derive(Serialize)]
pub struct SarifLocation {
    pub physical_location: SarifPhysicalLocation,
}

#[derive(Serialize)]
pub struct SarifPhysicalLocation {
    pub artifact_location: SarifArtifactLocation,
    pub region: SarifRegion,
}

#[derive(Serialize)]
pub struct SarifArtifactLocation {
    pub uri: String,
}

#[derive(Serialize)]
pub struct SarifRegion {
    pub start_line: u32,
}

pub fn generate_sarif(result: &VerificationResult) -> SarifReport {
    let mut rules_map = std::collections::HashMap::new();

    for v in &result.violations {
        rules_map.entry(v.code.clone()).or_insert_with(|| SarifRule {
            id: v.code.clone(),
            name: v.title.clone(),
            short_description: SarifText {
                text: v.legal_citation.clone(),
            },
        });
    }

    let rules: Vec<SarifRule> = rules_map.into_values().collect();

    let results: Vec<SarifResult> = result
        .violations
        .iter()
        .map(|v| SarifResult {
            rule_id: v.code.clone(),
            level: v.severity.clone(),
            message: SarifText {
                text: format!(
                    "{} — Medido: {}, Límite: {}. Evidencia Legal: {}",
                    v.title, v.measured, v.limit, v.legal_citation
                ),
            },
            locations: vec![SarifLocation {
                physical_location: SarifPhysicalLocation {
                    artifact_location: SarifArtifactLocation {
                        uri: v.file_path.clone(),
                    },
                    region: SarifRegion {
                        start_line: v.line,
                    },
                },
            }],
        })
        .collect();

    SarifReport {
        schema: "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json".to_string(),
        version: "2.1.0".to_string(),
        runs: vec![SarifRun {
            tool: SarifTool {
                driver: SarifDriver {
                    name: "cortex-guard".to_string(),
                    version: "1.0.0".to_string(),
                    rules,
                },
            },
            results,
        }],
    }
}
