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
}

impl DAGLedger {
    pub fn new() -> Self {
        Self {
            events: BTreeMap::new(),
            next_id: 0,
        }
    }

    pub fn append(&mut self, parents: Vec<EventId>, timestamp: SimulationClock, payload: String, hash: Hash) -> EventId {
        let id = self.next_id;
        self.next_id += 1;
        
        let event = Event {
            id,
            parents,
            timestamp,
            payload,
            signature: None,
            hash,
        };
        
        self.events.insert(id, event);
        id
    }

    pub fn get_event(&self, id: EventId) -> Option<&Event> {
        self.events.get(&id)
    }

    pub fn events(&self) -> impl Iterator<Item = &Event> {
        self.events.values()
    }
}
