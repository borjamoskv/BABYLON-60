// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use serde::{Serialize, Deserialize};
use kernel::ledger::DAGLedger;
use sha2::{Sha256, Digest};
use std::string::String;
use std::vec::Vec;

#[derive(Serialize, Deserialize, Debug)]
pub struct Manifest {
    pub version: String,
    pub timestamp: u64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CanonicalEvent {
    pub id: u64,
    pub parents: Vec<u64>,
    pub timestamp: u64,
    pub payload: String,
}

/// Serialize the DAG to a strictly canonical representation
pub fn serialize_canonical_dag(ledger: &DAGLedger) -> String {
    let mut canonical_events: Vec<CanonicalEvent> = ledger.events()
        .map(|e| CanonicalEvent {
            id: e.id,
            parents: e.parents.clone(),
            timestamp: e.timestamp.0,
            payload: e.payload.clone(),
        })
        .collect();
    
    // Sort topologically, using ID as tie-breaker (already satisfied if IDs are sequential)
    canonical_events.sort_by_key(|e| e.id);
    
    serde_json::to_string(&canonical_events).expect("Canonical serialization failed")
}

pub fn hash_canonical_dag(ledger: &DAGLedger) -> String {
    let canonical_str = serialize_canonical_dag(ledger);
    let mut hasher = Sha256::new();
    hasher.update(canonical_str.as_bytes());
    let result = hasher.finalize();
    format!("{:x}", result)
}
