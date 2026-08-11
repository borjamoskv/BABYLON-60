// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use alloc::vec::Vec;
use alloc::string::String;
use alloc::collections::BTreeMap;
use crate::scheduler::time::SimulationClock;

pub type Hash = [u8; 32];
pub type EventId = u64;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Event {
    pub id: EventId,
    pub parents: Vec<EventId>,
    pub timestamp: SimulationClock,
    pub payload: String,
    pub signature: Option<String>,
    pub hash: Hash,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DAGLedger {
    events: BTreeMap<EventId, Event>,
    next_id: EventId,
    cumulative_hash: Hash,
}

fn compute_event_hash(id: EventId, parents: &[EventId], timestamp: u64, payload: &str, parent_hashes: &[Hash]) -> Hash {
    let mut h = [0u8; 32];
    let mut state = 0xcbf29ce484222325u64;
    let prime = 0x100000001b3u64;
    
    let mix_u64 = |s: &mut u64, val: u64| {
        for byte in val.to_le_bytes() {
            *s ^= byte as u64;
            *s = s.wrapping_mul(prime);
        }
    };

    mix_u64(&mut state, id);
    mix_u64(&mut state, timestamp);
    for &p in parents {
        mix_u64(&mut state, p);
    }
    for byte in payload.as_bytes() {
        state ^= *byte as u64;
        state = state.wrapping_mul(prime);
    }
    for ph in parent_hashes {
        for byte in ph {
            state ^= *byte as u64;
            state = state.wrapping_mul(prime);
        }
    }

    for i in 0..4 {
        mix_u64(&mut state, i as u64);
        h[i * 8..(i + 1) * 8].copy_from_slice(&state.to_le_bytes());
    }
    h
}

impl DAGLedger {
    pub fn new() -> Self {
        Self {
            events: BTreeMap::new(),
            next_id: 0,
            cumulative_hash: [0u8; 32],
        }
    }

    pub fn append(&mut self, parents: Vec<EventId>, timestamp: SimulationClock, payload: String) -> Result<EventId, &'static str> {
        let id = self.next_id;

        // Invariant: Parent Existence Guard
        let mut parent_hashes = Vec::new();
        for &p in &parents {
            if p >= id {
                return Err("SelfLoopOrFutureParentDetected");
            }
            match self.events.get(&p) {
                Some(parent_evt) => parent_hashes.push(parent_evt.hash),
                None => return Err("ParentNotFound"),
            }
        }

        let hash = compute_event_hash(id, &parents, timestamp.0, &payload, &parent_hashes);

        let event = Event {
            id,
            parents,
            timestamp,
            payload,
            signature: None,
            hash,
        };

        // Update Merkle-causal cumulative root hash
        for i in 0..32 {
            self.cumulative_hash[i] ^= hash[i];
            self.cumulative_hash[i] = self.cumulative_hash[i].rotate_left(1);
        }

        self.events.insert(id, event);
        self.next_id += 1;
        Ok(id)
    }

    pub fn get_event(&self, id: EventId) -> Option<&Event> {
        self.events.get(&id)
    }

    pub fn events(&self) -> impl Iterator<Item = &Event> {
        self.events.values()
    }

    pub fn len(&self) -> usize {
        self.events.len()
    }

    pub fn is_empty(&self) -> bool {
        self.events.is_empty()
    }

    pub fn root_hash(&self) -> Hash {
        self.cumulative_hash
    }

    /// Verifies the causal integrity of the entire event ledger.
    pub fn verify_chain(&self) -> bool {
        for (&id, event) in &self.events {
            let mut parent_hashes = Vec::new();
            for &p in &event.parents {
                match self.events.get(&p) {
                    Some(parent_evt) => parent_hashes.push(parent_evt.hash),
                    None => return false,
                }
            }
            let expected_hash = compute_event_hash(
                id,
                &event.parents,
                event.timestamp.0,
                &event.payload,
                &parent_hashes,
            );
            if expected_hash != event.hash {
                return false;
            }
        }
        true
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use alloc::vec;

    #[test]
    fn test_dag_ledger_tamper_evident_hashes() {
        let mut l1 = DAGLedger::new();
        let mut l2 = DAGLedger::new();

        let clock = SimulationClock::new(100);
        let id1 = l1.append(vec![], clock, "payload_alpha".into()).unwrap();
        let id2 = l2.append(vec![], clock, "payload_beta".into()).unwrap();

        assert_eq!(id1, id2);
        assert_ne!(l1.root_hash(), l2.root_hash());
    }

    #[test]
    fn test_dag_ledger_rejects_nonexistent_parents() {
        let mut ledger = DAGLedger::new();
        let clock = SimulationClock::new(100);
        assert!(ledger.append(vec![999], clock, "orphan".into()).is_err());
    }

    #[test]
    fn test_dag_ledger_rejects_self_loop() {
        let mut ledger = DAGLedger::new();
        let clock = SimulationClock::new(100);
        assert!(ledger.append(vec![0], clock, "self_loop".into()).is_err());
    }
}

