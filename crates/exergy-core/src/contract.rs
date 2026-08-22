use std::collections::HashSet;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::error::ExergyError;
use crate::state::UserId;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContractSignature {
    pub user_id: UserId,
    pub signed_at: DateTime<Utc>,
    pub signature_proof: String, // Mock/hex signature proof
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CausalContract {
    pub contract_id: String,
    pub conversation_id: String,
    pub title: String,
    pub resolved_decision: String,
    pub participants: HashSet<UserId>,
    pub signatures: Vec<ContractSignature>,
    pub content_hash: String,
    pub created_at: DateTime<Utc>,
}

impl CausalContract {
    pub fn create(
        contract_id: String,
        conversation_id: String,
        title: String,
        resolved_decision: String,
        participants: HashSet<UserId>,
    ) -> Self {
        let created_at = Utc::now();
        let hash = Self::compute_hash(&contract_id, &conversation_id, &resolved_decision, &created_at);

        Self {
            contract_id,
            conversation_id,
            title,
            resolved_decision,
            participants,
            signatures: Vec::new(),
            content_hash: hash,
            created_at,
        }
    }

    pub fn compute_hash(
        contract_id: &str,
        conversation_id: &str,
        resolved_decision: &str,
        created_at: &DateTime<Utc>,
    ) -> String {
        let mut hasher = Sha256::new();
        hasher.update(contract_id.as_bytes());
        hasher.update(conversation_id.as_bytes());
        hasher.update(resolved_decision.as_bytes());
        hasher.update(created_at.to_rfc3339().as_bytes());
        hex::encode(hasher.finalize())
    }

    pub fn sign(&mut self, user_id: UserId, signature_proof: String) -> Result<(), ExergyError> {
        if !self.participants.contains(&user_id) {
            return Err(ExergyError::MissingSignature {
                user_id: format!("User {} is not a participant in contract {}", user_id, self.contract_id),
            });
        }

        let sig = ContractSignature {
            user_id,
            signed_at: Utc::now(),
            signature_proof,
        };

        self.signatures.push(sig);
        Ok(())
    }

    pub fn verify_integrity(&self) -> Result<bool, ExergyError> {
        let computed = Self::compute_hash(
            &self.contract_id,
            &self.conversation_id,
            &self.resolved_decision,
            &self.created_at,
        );

        if computed != self.content_hash {
            return Err(ExergyError::HashMismatch {
                expected: self.content_hash.clone(),
                computed,
            });
        }

        Ok(true)
    }

    pub fn is_fully_signed(&self) -> bool {
        let signed_users: HashSet<UserId> = self.signatures.iter().map(|s| s.user_id.clone()).collect();
        self.participants.is_subset(&signed_users)
    }
}
