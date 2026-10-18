//! REOPEN IDEA Package contract and serialization.
//! Blueprint §10: Frozen snapshot containing sources, inference synthesis, open questions, and next_action.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt::Write;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceCitation {
    pub source_digest: String,
    pub content_digest: String,
    pub exact_excerpt: String,
    pub locator: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SynthesisPayload {
    pub inference_text: String,
    pub model_id: String,
    pub classification: String, // Must be "INFERENCE"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NextActionPayload {
    pub target_goal: String,
    pub proposed_destination: String,
    pub preconditions: Vec<String>,
    pub termination_criteria: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReopenPackage {
    pub schema_version: String,
    pub project_title: String,
    pub cycle_id: String,
    pub thread_revision_id: String,
    pub first_observed_utc: String,
    pub reopened_at_utc: String,
    pub reopening_rationale: String,
    pub sources: Vec<SourceCitation>,
    pub synthesis: SynthesisPayload,
    pub bias_warning_acknowledged: bool,
    pub open_questions: Vec<String>,
    pub next_action: NextActionPayload,
    pub package_sha3_256: Option<String>,
}

#[inline]
fn bytes_to_hex(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        write!(s, "{:02x}", b).unwrap();
    }
    s
}

impl ReopenPackage {
    /// Computes the deterministic SHA3-256 seal of the package and embeds it.
    pub fn seal(&mut self) -> Result<String, serde_json::Error> {
        self.package_sha3_256 = None;
        let serialized = serde_json::to_vec(&self)?;
        let mut hasher = Sha256::new();
        hasher.update(&serialized);
        let digest = format!("sha3-256:{}", bytes_to_hex(&hasher.finalize()));
        self.package_sha3_256 = Some(digest.clone());
        Ok(digest)
    }

    /// Exports to human-readable Markdown following Blueprint §10.
    pub fn to_markdown(&self) -> String {
        let mut md = String::new();
        md.push_str(&format!("PROJECT: {}\n", self.project_title));
        md.push_str(&format!("ORIGIN: {}\n", self.first_observed_utc));
        md.push_str(&format!("WHY REOPENED: {}\n\n", self.reopening_rationale));
        
        md.push_str("ORIGINAL SOURCES:\n");
        for s in &self.sources {
            md.push_str(&format!("- [{}] ({}): \"{}\"\n", s.source_digest, s.locator, s.exact_excerpt));
        }
        md.push_str("\nCURRENT SYNTHESIS (INFERENCE):\n");
        md.push_str("> [!WARNING] Interpretación generada por un modelo: puede contener errores y sesgos. Consulta las fuentes enlazadas.\n");
        md.push_str(&format!("{}\n\n", self.synthesis.inference_text));

        md.push_str("OPEN QUESTIONS (INFERENCE):\n");
        for q in &self.open_questions {
            md.push_str(&format!("- {}\n", q));
        }
        md.push_str("\nNEXT_ACTION:\n");
        md.push_str(&format!("- Goal: {}\n", self.next_action.target_goal));
        md.push_str(&format!("- Destination: {}\n", self.next_action.proposed_destination));
        md.push_str(&format!("- Criteria: {}\n", self.next_action.termination_criteria));

        if let Some(ref h) = self.package_sha3_256 {
            md.push_str(&format!("\nSEAL: {}\n", h));
        }
        md
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_package_sealing_and_markdown() {
        let mut pkg = ReopenPackage {
            schema_version: "1.0.0".into(),
            project_title: "Thermodynamic Memory Archaeology".into(),
            cycle_id: "cyc_001".into(),
            thread_revision_id: "rev_001".into(),
            first_observed_utc: "2024-01-01T00:00:00Z".into(),
            reopened_at_utc: "2026-10-03T12:00:00Z".into(),
            reopening_rationale: "Operator identified forgotten Landauer bound architecture".into(),
            sources: vec![SourceCitation {
                source_digest: "sha3-256:abcd".into(),
                content_digest: "sha3-256:1234".into(),
                exact_excerpt: "Irreversible bit erasure requires kT ln 2".into(),
                locator: "line:42".into(),
            }],
            synthesis: SynthesisPayload {
                inference_text: "We can implement zero-torn seqlock based on Landauer limits.".into(),
                model_id: "gemini-3.8-flash".into(),
                classification: "INFERENCE".into(),
            },
            bias_warning_acknowledged: true,
            open_questions: vec!["Does APFS support atomic renameat2?".into()],
            next_action: NextActionPayload {
                target_goal: "Verify atomic quarantine in APFS".into(),
                proposed_destination: "tests/secure_fs_apfs.rs".into(),
                preconditions: vec!["macOS ARM64 host available".into()],
                termination_criteria: "Zero TOCTOU leaks observed".into(),
            },
            package_sha3_256: None,
        };

        let digest = pkg.seal().unwrap();
        assert!(digest.starts_with("sha3-256:"));
        assert_eq!(pkg.package_sha3_256.as_ref().unwrap(), &digest);

        let md = pkg.to_markdown();
        assert!(md.contains("PROJECT: Thermodynamic Memory Archaeology"));
        assert!(md.contains("CURRENT SYNTHESIS (INFERENCE):"));
        assert!(md.contains("[!WARNING]"));
    }
}
