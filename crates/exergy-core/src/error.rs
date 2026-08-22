use thiserror::Error;

#[derive(Error, Debug, PartialEq)]
pub enum ExergyError {
    #[error("Invalid state transition from {from} to {to}: {reason}")]
    InvalidStateTransition {
        from: String,
        to: String,
        reason: String,
    },

    #[error("Entropy limit exceeded: budget {budget}, generated {generated}")]
    EntropyLimitExceeded { budget: u32, generated: u32 },

    #[error("Invalid decision vote: option index {option_idx} out of bounds")]
    InvalidVoteOption { option_idx: usize },

    #[error("Missing contract signature for user {user_id}")]
    MissingSignature { user_id: String },

    #[error("Contract hash mismatch: expected {expected}, computed {computed}")]
    HashMismatch { expected: String, computed: String },

    #[error("Markov Blanket MM-01 violation on field '{field}': leakage {leakage_bits:.4} bits. Reason: {reason}")]
    MarkovBlanketViolation {
        field: String,
        leakage_bits: f64,
        reason: String,
    },
}

