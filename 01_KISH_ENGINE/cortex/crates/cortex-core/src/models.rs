use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceRef {
    pub provider: String,
    pub conversation_id: Option<String>,
    pub message_id: Option<String>,
    pub source_uri: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEvent {
    pub event_id: String, // e.g. "mem_01892"
    pub source: SourceRef,
    pub timestamp: DateTime<Utc>,
    pub event_type: String, // e.g. "idea"

    pub raw_text: String,
    pub normalized_text: String,
    
    pub entities: Vec<String>,
    
    pub raw_hash: String, // sha3-256
    pub extractor_version: String,
    pub extraction_confidence: f32,
}

impl MemoryEvent {
    pub fn generate_id() -> String {
        format!("mem_{}", Uuid::new_v4().simple())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdeaThread {
    pub idea_id: String,
    pub core_concept: String,
    pub first_seen: DateTime<Utc>,
    pub last_seen: DateTime<Utc>,
    pub recurrence_count: u32,
    pub dormant_days: u32,
    pub events: Vec<String>, // list of event_ids
    pub score: f32,
}

impl IdeaThread {
    pub fn generate_id() -> String {
        format!("idea_{}", Uuid::new_v4().simple())
    }

    /// Compute score based on: 0.18N + 0.12R + 0.17C + 0.18U + 0.18T + 0.07E + 0.10S - D
    /// For this scaffolding MVP, we will simplify parameters mapping.
    #[allow(clippy::too_many_arguments)]
    pub fn compute_score(
        novelty: f32,     // N
        recurrence: f32,  // R
        cross_proj: f32,  // C
        unfinished: f32,  // U
        time_relev: f32,  // T
        evolution: f32,   // E
        surprise: f32,    // S
        decay: f32,       // D
    ) -> f32 {
        (0.18 * novelty) +
        (0.12 * recurrence) +
        (0.17 * cross_proj) +
        (0.18 * unfinished) +
        (0.18 * time_relev) +
        (0.07 * evolution) +
        (0.10 * surprise) - decay
    }
}

/// Model-derived interpretation or proposal (Ontology Law O1 & O2).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Inference {
    pub inference_id: String,
    pub derived_from_threads: Vec<String>,
    pub model_id: String,
    pub prompt_digest: String,
    pub generated_at: DateTime<Utc>,
    pub proposal_summary: String,
    pub confidence: f32,
}

impl Inference {
    pub fn generate_id() -> String {
        format!("inf_{}", Uuid::new_v4().simple())
    }
}

/// Contextual proposal crossing the trust boundary towards BABYLON.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProposalContext {
    pub proposal_id: String,
    pub inference_ref: String,
    pub suggested_action: String,
    pub justification: String,
    pub evaluated_risk: String,
}
