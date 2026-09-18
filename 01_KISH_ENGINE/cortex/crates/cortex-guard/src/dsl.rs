//! Declarative PGOU / CTE Constraint DSL Rulebook Parser
//! C5-REAL Compliant: Supports JSON and YAML Rulebooks

use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ComparisonOp {
    #[serde(rename = ">=")]
    Gte,
    #[serde(rename = "<=")]
    Lte,
    #[serde(rename = ">")]
    Gt,
    #[serde(rename = "<")]
    Lt,
    #[serde(rename = "==")]
    Eq,
    #[serde(rename = "!=")]
    Neq,
}

impl ComparisonOp {
    pub fn evaluate(&self, measured: f64, limit: f64) -> bool {
        match self {
            ComparisonOp::Gte => measured >= limit,
            ComparisonOp::Lte => measured <= limit,
            ComparisonOp::Gt => measured > limit,
            ComparisonOp::Lt => measured < limit,
            ComparisonOp::Eq => (measured - limit).abs() < 1e-6,
            ComparisonOp::Neq => (measured - limit).abs() >= 1e-6,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    pub code: String,
    pub title: String,
    #[serde(default)]
    pub description: String,
    pub target: String,
    pub property: String,
    pub operator: ComparisonOp,
    pub threshold: f64,
    #[serde(default)]
    pub unit: Option<String>,
    pub legal_citation: String,
    #[serde(default = "default_severity")]
    pub severity: String,
}

fn default_severity() -> String {
    "error".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rulebook {
    pub rules: Vec<Rule>,
}

impl Rulebook {
    pub fn parse(content: &str, path: &Path) -> Result<Self, String> {
        let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
        let is_json = ext == "json" || content.trim_start().starts_with('{');

        if is_json {
            serde_json::from_str::<Rulebook>(content)
                .map_err(|e| format!("Error parseando Rulebook JSON '{}': {}", path.display(), e))
        } else {
            serde_yaml::from_str::<Rulebook>(content)
                .map_err(|e| format!("Error parseando Rulebook YAML '{}': {}", path.display(), e))
        }
    }
}
