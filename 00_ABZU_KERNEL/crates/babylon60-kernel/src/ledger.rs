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

/// Canonical cryptographic event hash using BLAKE3 with domain separation.
/// Eradicates the non-cryptographic FNV-1a pseudo-256b implementation.
pub fn compute_event_hash(
    id: EventId,
    parents: &[EventId],
    timestamp: u64,
    payload: &str,
    parent_hashes: &[Hash],
) -> Hash {
    let mut hasher = blake3::Hasher::new();
    // Domain separation tag for BABYLON-60 Ledger Events
    hasher.update(b"BABYLON60_LEDGER_EVENT_V1\0");
    hasher.update(&id.to_le_bytes());
    hasher.update(&timestamp.to_le_bytes());
    hasher.update(&(parents.len() as u64).to_le_bytes());
    for &p in parents {
        hasher.update(&p.to_le_bytes());
    }
    hasher.update(&(payload.len() as u64).to_le_bytes());
    hasher.update(payload.as_bytes());
    hasher.update(&(parent_hashes.len() as u64).to_le_bytes());
    for ph in parent_hashes {
        hasher.update(ph);
    }
    *hasher.finalize().as_bytes()
}

/// Legacy FNV-1a 64-bit derivation retained strictly for empirical collision falsification benchmarks.
#[cfg(test)]
pub fn compute_event_hash_legacy_fnv1a(
    id: EventId,
    parents: &[EventId],
    timestamp: u64,
    payload: &str,
    parent_hashes: &[Hash],
) -> Hash {
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


impl Default for DAGLedger {
    fn default() -> Self {
        Self::new()
    }
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

        // Update Merkle-causal cumulative root hash via cryptographic BLAKE3
        let mut root_hasher = blake3::Hasher::new();
        root_hasher.update(b"BABYLON60_CUMULATIVE_ROOT_V1\0");
        root_hasher.update(&self.cumulative_hash);
        root_hasher.update(&hash);
        self.cumulative_hash = *root_hasher.finalize().as_bytes();


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
        let id1 = l1.append(vec![], clock, "payload_alpha".into()).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        let id2 = l2.append(vec![], clock, "payload_beta".into()).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

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

    #[test]
    fn test_falsify_legacy_fnv1a_collision_attack() {
        // FALSACIÓN EMPÍRICA: Demostración de colisión trivial en FNV-1a.
        // En FNV-1a legado, no existía separación de longitud entre payload y parent_hashes,
        // permitiendo forjar una colisión idéntica de 32 bytes entre dos eventos semánticamente disjuntos.
        let payload_32b = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
        let parent_hash_32b: Hash = [b'A'; 32];

        // Evento 1: Payload de 32 bytes 'A', sin parent hashes
        let fnv_h1 = compute_event_hash_legacy_fnv1a(0, &[], 100, payload_32b, &[]);
        // Evento 2: Payload vacío, con un parent hash de 32 bytes 'A'
        let fnv_h2 = compute_event_hash_legacy_fnv1a(0, &[], 100, "", &[parent_hash_32b]);

        // Falsación demostrada: FNV-1a colisiona al 100% (los 32 bytes coinciden exactamente)
        assert_eq!(fnv_h1, fnv_h2, "FNV-1a colisiona trivialmente ante desplazamiento de límites");

        // BLAKE3 con domain separation y longitud canónica previene completamente esta colisión
        let b3_h1 = compute_event_hash(0, &[], 100, payload_32b, &[]);
        let b3_h2 = compute_event_hash(0, &[], 100, "", &[parent_hash_32b]);

        assert_ne!(b3_h1, b3_h2, "BLAKE3 erradica la colisión con 256 bits de resistencia criptográfica");
    }

    #[test]
    fn test_blake3_avalanche_and_domain_separation() {
        let h1 = compute_event_hash(0, &[], 100, "transaction_1", &[]);
        let h2 = compute_event_hash(0, &[], 100, "transaction_2", &[]);

        // Avalanche effect: un solo cambio en el payload debe alterar drásticamente el hash
        let mut diff_bits = 0;
        for (b1, b2) in h1.iter().zip(h2.iter()) {
            diff_bits += (b1 ^ b2).count_ones();
        }

        // Para un hash criptográfico de 256 bits, la distancia de Hamming esperada es ~128 bits
        assert!(diff_bits > 80 && diff_bits < 180, "Avalanche defectuoso: diff_bits = {}", diff_bits);
    }
}


