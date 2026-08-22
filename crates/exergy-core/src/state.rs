use std::collections::{HashMap, HashSet};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::error::ExergyError;

pub type UserId = String;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DecisionOption {
    pub id: usize,
    pub label: String,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ActionItem {
    pub id: String,
    pub assignee: UserId,
    pub description: String,
    pub due_at: Option<DateTime<Utc>>,
    pub completed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExergyCrystal {
    pub summary_bullets: Vec<String>,
    pub key_decisions: Vec<String>,
    pub action_items: Vec<ActionItem>,
    pub raw_content_hash: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ConversationState {
    /// Open channel for free-form interaction under an entropy budget
    Open {
        entropy_budget: u32,
        messages_count: u32,
    },

    /// State machine detected an unresolved decision needing convergence
    DecisionPending {
        question: String,
        options: Vec<DecisionOption>,
        votes: HashMap<UserId, usize>, // UserId -> Option ID
        deadline: DateTime<Utc>,
    },

    /// Decision has collapsed into an immutable causal resolution
    Resolved {
        selected_option: DecisionOption,
        participants_ack: HashSet<UserId>,
        resolved_at: DateTime<Utc>,
    },

    /// Read-only archived state containing the final Exergy Crystal
    Archived {
        crystal: ExergyCrystal,
        archived_at: DateTime<Utc>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConversationFSM {
    pub id: String,
    pub title: String,
    pub state: ConversationState,
    pub participants: HashSet<UserId>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl ConversationFSM {
    pub fn new(id: String, title: String, creator: UserId, entropy_budget: u32) -> Self {
        let now = Utc::now();
        let mut participants = HashSet::new();
        participants.insert(creator);

        Self {
            id,
            title,
            state: ConversationState::Open {
                entropy_budget,
                messages_count: 0,
            },
            participants,
            created_at: now,
            updated_at: now,
        }
    }

    pub fn add_participant(&mut self, user_id: UserId) {
        self.participants.insert(user_id);
        self.updated_at = Utc::now();
    }

    /// Record a new message in Open state, incrementing entropy count
    pub fn record_message(&mut self) -> Result<u32, ExergyError> {
        match &mut self.state {
            ConversationState::Open {
                entropy_budget,
                messages_count,
            } => {
                if *messages_count >= *entropy_budget {
                    return Err(ExergyError::EntropyLimitExceeded {
                        budget: *entropy_budget,
                        generated: *messages_count + 1,
                    });
                }
                *messages_count += 1;
                self.updated_at = Utc::now();
                Ok(*messages_count)
            }
            other => Err(ExergyError::InvalidStateTransition {
                from: format!("{:?}", other),
                to: "Open(message)".into(),
                reason: "Cannot record raw messages outside Open state".into(),
            }),
        }
    }

    /// Transition from Open to DecisionPending
    pub fn propose_decision(
        &mut self,
        question: String,
        options: Vec<DecisionOption>,
        deadline: DateTime<Utc>,
    ) -> Result<(), ExergyError> {
        match &self.state {
            ConversationState::Open { .. } => {
                self.state = ConversationState::DecisionPending {
                    question,
                    options,
                    votes: HashMap::new(),
                    deadline,
                };
                self.updated_at = Utc::now();
                Ok(())
            }
            other => Err(ExergyError::InvalidStateTransition {
                from: format!("{:?}", other),
                to: "DecisionPending".into(),
                reason: "Can only propose decision from Open state".into(),
            }),
        }
    }

    /// Cast a vote in DecisionPending state
    pub fn cast_vote(&mut self, user_id: UserId, option_id: usize) -> Result<(), ExergyError> {
        if !self.participants.contains(&user_id) {
            self.participants.insert(user_id.clone());
        }

        match &mut self.state {
            ConversationState::DecisionPending { options, votes, .. } => {
                if !options.iter().any(|o| o.id == option_id) {
                    return Err(ExergyError::InvalidVoteOption {
                        option_idx: option_id,
                    });
                }
                votes.insert(user_id, option_id);
                self.updated_at = Utc::now();
                Ok(())
            }
            other => Err(ExergyError::InvalidStateTransition {
                from: format!("{:?}", other),
                to: "Vote".into(),
                reason: "Voting only allowed in DecisionPending state".into(),
            }),
        }
    }

    /// Collapse DecisionPending into Resolved when consensus or deadline is reached
    pub fn resolve_decision(&mut self, winning_option_id: usize) -> Result<DecisionOption, ExergyError> {
        match &self.state {
            ConversationState::DecisionPending { options, votes, .. } => {
                let winning = options
                    .iter()
                    .find(|o| o.id == winning_option_id)
                    .cloned()
                    .ok_or(ExergyError::InvalidVoteOption {
                        option_idx: winning_option_id,
                    })?;

                let acks: HashSet<UserId> = votes.keys().cloned().collect();

                self.state = ConversationState::Resolved {
                    selected_option: winning.clone(),
                    participants_ack: acks,
                    resolved_at: Utc::now(),
                };
                self.updated_at = Utc::now();
                Ok(winning)
            }
            other => Err(ExergyError::InvalidStateTransition {
                from: format!("{:?}", other),
                to: "Resolved".into(),
                reason: "Can only resolve from DecisionPending state".into(),
            }),
        }
    }

    /// Archive the conversation into a permanent Exergy Crystal
    pub fn archive(&mut self, crystal: ExergyCrystal) -> Result<(), ExergyError> {
        self.state = ConversationState::Archived {
            crystal,
            archived_at: Utc::now(),
        };
        self.updated_at = Utc::now();
        Ok(())
    }
}
