use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, PartialOrd)]
pub struct ExergyRatio(pub f64);

impl ExergyRatio {
    pub fn new(val: f64) -> Self {
        Self(val.clamp(0.0, 1.0))
    }

    pub fn is_high_exergy(&self) -> bool {
        self.0 >= 0.70
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum PriorityLevel {
    /// High exergy: Action required, decision pending, direct question
    HighExergy,
    /// Medium exergy: Deterministic status update, resolution notice
    MediumExergy,
    /// Low exergy / Noise: Social chatter, uncompressed raw audio
    LowExergyDigest,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageEntropyMetrics {
    pub total_words: usize,
    pub actionable_verbs_count: usize,
    pub question_count: usize,
    pub noise_ratio: f64,
}

impl MessageEntropyMetrics {
    pub fn compute_exergy_ratio(&self) -> ExergyRatio {
        if self.total_words == 0 {
            return ExergyRatio::new(1.0);
        }

        // Informational work density: actionable tokens + questions vs filler tokens
        let structured_signal = (self.actionable_verbs_count * 2 + self.question_count * 3) as f64;
        let density = structured_signal / (self.total_words as f64);
        
        let exergy = (density * (1.0 - self.noise_ratio)).clamp(0.0, 1.0);
        ExergyRatio::new(exergy)
    }

    pub fn classify_priority(&self, has_pending_decision: bool) -> PriorityLevel {
        let exergy = self.compute_exergy_ratio();

        if has_pending_decision || self.question_count > 0 || exergy.is_high_exergy() {
            PriorityLevel::HighExergy
        } else if exergy.0 > 0.35 {
            PriorityLevel::MediumExergy
        } else {
            PriorityLevel::LowExergyDigest
        }
    }
}

/// Simple heuristic entropy analyzer for plain text strings
pub fn analyze_text_entropy(text: &str) -> MessageEntropyMetrics {
    let words: Vec<&str> = text.split_whitespace().collect();
    let total_words = words.len();
    if total_words == 0 {
        return MessageEntropyMetrics {
            total_words: 0,
            actionable_verbs_count: 0,
            question_count: 0,
            noise_ratio: 0.0,
        };
    }

    let question_count = text.matches('?').count() + text.matches("¿").count();

    // High exergy keywords (Spanish & English actionable verbs/terms)
    let action_keywords = [
        "votar", "decidir", "confirmar", "reunión", "hora", "lugar", "llegar", "fecha",
        "reserva", "precio", "acuerdo", "tarea", "hacer", "si", "no",
        "vote", "decide", "confirm", "meeting", "time", "location", "agree", "todo", "done"
    ];

    let actionable_verbs_count = words
        .iter()
        .filter(|w| action_keywords.iter().any(|k| w.to_lowercase().contains(k)))
        .count();

    // Filler/Noise keywords
    let filler_keywords = ["jaja", "lol", "jajaja", "jeje", "xd", "bueno", "nose", "idk", "whatever"];
    let filler_count = words
        .iter()
        .filter(|w| filler_keywords.iter().any(|k| w.to_lowercase().contains(k)))
        .count();

    let noise_ratio = (filler_count as f64 / total_words as f64).clamp(0.0, 1.0);

    MessageEntropyMetrics {
        total_words,
        actionable_verbs_count,
        question_count,
        noise_ratio,
    }
}
