// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | SÍNTESIS TOPOLÓGICA (NIVEL 3 & 5 EN SILICIO)
// ============================================================================
//! Session Governance Buffer & Continual Epistemic Memory
//!
//! Enforces:
//! 1. O(1) Bounded capacity (Strict 12-item cap per section under Vía Negativa).
//! 2. Deterministic LFU eviction under AX-KDA-1..3.
//! 3. Hume's Guillotine gate: Epistemic facts cannot mutate into Deontic rules
//!    without operator biometric attestation.
//! 4. BLAKE3 state commitments for verifiable SCITT logging.

use std::collections::HashMap;

/// Modality of a learned item
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ItemModality {
    /// What IS: Empirical observation, build fact, benchmark
    EpistemicFact,
    /// What OUGHT TO BE: Normative rule, invariant, user preference
    DeonticRule,
}

/// An entry in the session governance memory
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GovernanceEntry {
    pub content: String,
    pub modality: ItemModality,
    pub version: u64,
    pub frequency: u64,
    pub has_biometric_attestation: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GovernanceError {
    CapacityExceeded,
    HumeGuillotineViolation,
    ItemNotFound,
}

/// Bounded memory buffer strictly enforcing the 12-item invariant (Vía Negativa)
#[derive(Debug, Clone)]
pub struct SessionGovernanceBuffer {
    max_capacity: usize,
    entries: HashMap<String, GovernanceEntry>,
}

impl Default for SessionGovernanceBuffer {
    fn default() -> Self {
        Self::new(12) // Canonical hard limit of 12 items
    }
}

impl SessionGovernanceBuffer {
    pub fn new(max_capacity: usize) -> Self {
        Self {
            max_capacity,
            entries: HashMap::with_capacity(max_capacity),
        }
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Read entry and increment its access frequency (AX-KDA-6)
    pub fn get(&mut self, key: &str) -> Option<&GovernanceEntry> {
        if let Some(entry) = self.entries.get_mut(key) {
            entry.frequency = entry.frequency.saturating_add(1);
        }
        self.entries.get(key)
    }

    /// Inserción tipada con compresión y respeto a la Guillotina de Hume
    pub fn insert(
        &mut self,
        key: &str,
        content: String,
        modality: ItemModality,
        has_biometric_attestation: bool,
    ) -> Result<(), GovernanceError> {
        // Hume's Guillotine Gate: Deontic rules REQUIRE biometric attestation
        if modality == ItemModality::DeonticRule && !has_biometric_attestation {
            return Err(GovernanceError::HumeGuillotineViolation);
        }

        // If key already exists: update in-place monotonically (AX-KDA-2)
        if let Some(entry) = self.entries.get_mut(key) {
            entry.content = content;
            entry.version = entry.version.saturating_add(1);
            entry.has_biometric_attestation = has_biometric_attestation;
            return Ok(());
        }

        // Capacity check: if at limit, evict least frequently used (AX-KDA-3)
        if self.entries.len() >= self.max_capacity {
            self.evict_lfu();
        }

        self.entries.insert(
            key.to_string(),
            GovernanceEntry {
                content,
                modality,
                version: 1,
                frequency: 1,
                has_biometric_attestation,
            },
        );

        Ok(())
    }

    /// Evicts the entry with lowest frequency, tie-broken deterministically by key (AX-KDA-3)
    fn evict_lfu(&mut self) {
        if let Some(min_key) = self
            .entries
            .iter()
            .min_by(|(k1, e1), (k2, e2)| {
                e1.frequency
                    .cmp(&e2.frequency)
                    .then_with(|| e1.version.cmp(&e2.version))
                    .then_with(|| k1.cmp(k2))
            })
            .map(|(k, _)| k.clone())
        {
            self.entries.remove(&min_key);
        }
    }

    /// Computes deterministic BLAKE3 digest of current state
    pub fn state_digest(&self) -> blake3::Hash {
        let mut hasher = blake3::Hasher::new();
        let mut sorted_keys: Vec<_> = self.entries.keys().collect();
        sorted_keys.sort();

        for k in sorted_keys {
            let entry = &self.entries[k];
            hasher.update(k.as_bytes());
            hasher.update(entry.content.as_bytes());
            hasher.update(&entry.version.to_le_bytes());
            hasher.update(&entry.frequency.to_le_bytes());
            hasher.update(&[match entry.modality {
                ItemModality::EpistemicFact => 0,
                ItemModality::DeonticRule => 1,
            }]);
            hasher.update(&[if entry.has_biometric_attestation { 1 } else { 0 }]);
        }

        hasher.finalize()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_governance_hume_guillotine_rejects_unattested_rule() {
        let mut buf = SessionGovernanceBuffer::new(12);
        let res = buf.insert(
            "rule_no_sleep",
            "Never sleep in agents".to_string(),
            ItemModality::DeonticRule,
            false, // Sin firma biométrica
        );
        assert_eq!(res, Err(GovernanceError::HumeGuillotineViolation));
        assert_eq!(buf.len(), 0);
    }

    #[test]
    fn test_governance_epistemic_fact_accepted_without_biometrics() {
        let mut buf = SessionGovernanceBuffer::new(12);
        let res = buf.insert(
            "fact_m3_pro",
            "Hardware is Apple Silicon M3 Pro 12 cores".to_string(),
            ItemModality::EpistemicFact,
            false,
        );
        assert!(res.is_ok());
        assert_eq!(buf.len(), 1);
    }

    #[test]
    fn test_governance_attested_deontic_rule_accepted() {
        let mut buf = SessionGovernanceBuffer::new(12);
        let res = buf.insert(
            "rule_bionic_cards",
            "Always emit Unicode cards for messaging".to_string(),
            ItemModality::DeonticRule,
            true, // Con atestación Touch ID
        );
        assert!(res.is_ok());
        assert_eq!(buf.len(), 1);
    }

    #[test]
    fn test_governance_bounded_capacity_and_lfu_eviction() {
        let mut buf = SessionGovernanceBuffer::new(3); // Mini capacity 3

        buf.insert("f1", "Fact 1".into(), ItemModality::EpistemicFact, false).unwrap();
        buf.insert("f2", "Fact 2".into(), ItemModality::EpistemicFact, false).unwrap();
        buf.insert("f3", "Fact 3".into(), ItemModality::EpistemicFact, false).unwrap();

        // Increment frequencies of f1 and f2
        buf.get("f1");
        buf.get("f1");
        buf.get("f2");

        // Inserting 4th item must evict f3 (frequency 1)
        buf.insert("f4", "Fact 4".into(), ItemModality::EpistemicFact, false).unwrap();

        assert_eq!(buf.len(), 3);
        assert!(buf.get("f3").is_none());
        assert!(buf.get("f1").is_some());
        assert!(buf.get("f2").is_some());
        assert!(buf.get("f4").is_some());
    }

    #[test]
    fn test_governance_blake3_state_digest_deterministic() {
        let mut buf1 = SessionGovernanceBuffer::new(12);
        let mut buf2 = SessionGovernanceBuffer::new(12);

        buf1.insert("alpha", "Data A".into(), ItemModality::EpistemicFact, false).unwrap();
        buf1.insert("beta", "Data B".into(), ItemModality::EpistemicFact, false).unwrap();

        // Insert in reverse order into buf2
        buf2.insert("beta", "Data B".into(), ItemModality::EpistemicFact, false).unwrap();
        buf2.insert("alpha", "Data A".into(), ItemModality::EpistemicFact, false).unwrap();

        assert_eq!(buf1.state_digest(), buf2.state_digest());
    }
}
