use std::collections::HashSet;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use crate::error::ExergyError;

/// High-Exergy Feature Payload isolated within a Markov Blanket.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FeaturePayload {
    pub raw_data: String,
    pub metadata: Vec<(String, String)>,
}

impl FeaturePayload {
    pub fn new(raw_data: impl Into<String>, metadata: Vec<(impl Into<String>, impl Into<String>)>) -> Self {
        Self {
            raw_data: raw_data.into(),
            metadata: metadata.into_iter().map(|(k, v)| (k.into(), v.into())).collect(),
        }
    }
}

/// Verification result for a Markov Blanket isolation test (MM-01).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MarkovBlanketResult {
    pub is_isolated: bool,
    pub information_leakage_bits: f64,
    pub content_hash: String,
    pub retained_features: Vec<String>,
    pub purged_noise_fields: Vec<String>,
}

/// Sovereign Markov Blanket Verifier (MM-01).
///
/// Ensures zero-anergy isolation of decision engines from contextual noise,
/// prompt biases, and external metadata leakage.
#[derive(Debug, Clone)]
pub struct MarkovBlanketVerifier {
    prohibited_noise_patterns: HashSet<String>,
    max_allowable_leakage_bits: f64,
}

impl MarkovBlanketVerifier {
    pub fn new(max_allowable_leakage_bits: f64) -> Self {
        let mut prohibited = HashSet::new();
        // Standard C5-REAL prohibited noise patterns for forensic/decisional isolation
        prohibited.insert("race".to_string());
        prohibited.insert("prior_record".to_string());
        prohibited.insert("suspect_name".to_string());
        prohibited.insert("media_hype".to_string());
        prohibited.insert("prompt_narrative_bias".to_string());
        prohibited.insert("prosecutor_theory".to_string());

        Self {
            prohibited_noise_patterns: prohibited,
            max_allowable_leakage_bits,
        }
    }

    pub fn add_prohibited_pattern(&mut self, pattern: impl Into<String>) {
        self.prohibited_noise_patterns.insert(pattern.into().to_lowercase());
    }

    pub fn verify_and_isolate(&self, payload: &FeaturePayload) -> Result<MarkovBlanketResult, ExergyError> {
        let mut purged = Vec::new();
        let mut retained = Vec::new();
        let mut leakage_bits = 0.0;

        for (key, val) in &payload.metadata {
            let key_lower = key.to_lowercase();
            let is_prohibited = self.prohibited_noise_patterns.iter().any(|p| key_lower.contains(p));

            if is_prohibited {
                purged.push(key.clone());
                // Shannon entropy contribution log2(N + 1) of leaked string length
                let val_len = val.len() as f64;
                leakage_bits += (val_len + 1.0).log2();
            } else {
                retained.push(format!("{}:{}", key, val));
            }
        }

        let is_isolated = leakage_bits <= self.max_allowable_leakage_bits;

        if !is_isolated {
            let leaked_fields = purged.join(", ");
            return Err(ExergyError::MarkovBlanketViolation {
                field: leaked_fields,
                leakage_bits,
                reason: format!(
                    "Information leakage of {:.4} bits exceeds maximum allowable threshold of {:.4} bits",
                    leakage_bits, self.max_allowable_leakage_bits
                ),
            });
        }

        // Hash isolated state (raw_data + retained metadata)
        let mut hasher = Sha256::new();
        hasher.update(payload.raw_data.as_bytes());
        for item in &retained {
            hasher.update(item.as_bytes());
        }
        let content_hash = hex::encode(hasher.finalize());

        Ok(MarkovBlanketResult {
            is_isolated,
            information_leakage_bits: leakage_bits,
            content_hash,
            retained_features: retained,
            purged_noise_fields: purged,
        })
    }
}
