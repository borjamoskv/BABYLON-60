#![cfg(feature = "larsa-bft")]

use babylon60::larsa_bft::{
    LarsaTriadConsensus, LarsaVertex, QuorumHealth, TraceVerdict, VertexState,
};
use babylon60::manifest::RUNNING;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

static TRACE_ID: AtomicU64 = AtomicU64::new(0);

struct TraceFile {
    directory: PathBuf,
    path: PathBuf,
}

impl TraceFile {
    fn new(events: &[u64]) -> Self {
        let directory = std::env::temp_dir().join(format!(
            "babylon-bft-test-{}-{}",
            std::process::id(),
            TRACE_ID.fetch_add(1, Ordering::Relaxed),
        ));
        fs::create_dir(&directory).unwrap();
        let path = directory.join("trace.bin");
        let bytes: Vec<u8> = events
            .iter()
            .flat_map(|event| event.to_le_bytes())
            .collect();
        fs::write(&path, bytes).unwrap();
        Self { directory, path }
    }
}

impl Drop for TraceFile {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
        let _ = fs::remove_dir(&self.directory);
    }
}

fn pack_event(thread_id: u32, seq: u32, action: u8) -> u64 {
    (action as u64) | ((thread_id as u64) << 8) | ((seq as u64) << 32)
}

#[test]
fn test_bft_aot_oracle_integration() {
    let valid_trace = TraceFile::new(&[
        pack_event(1, 1, 0),
        pack_event(1, 2, 1),
        pack_event(1, 3, 0),
        pack_event(1, 4, 1),
    ]);
    let healthy = LarsaTriadConsensus::new();
    assert_eq!(
        healthy.evaluate_trace(&valid_trace.path),
        TraceVerdict::Validated
    );
    assert_eq!(healthy.active_count(), 3);

    // The rejected call remains rejected while the quorum can validate a later request.
    let bad_state_trace = TraceFile::new(&[pack_event(1, 1, 0), pack_event(1, 2, 0)]);
    let state_rejected = LarsaTriadConsensus::new();
    assert_eq!(
        state_rejected.evaluate_trace(&bad_state_trace.path),
        TraceVerdict::TraceRejected
    );
    assert_eq!(
        state_rejected.get_state(LarsaVertex::Beta),
        VertexState::Fallen
    );
    assert_eq!(
        state_rejected.get_state(LarsaVertex::Gamma),
        VertexState::Active
    );
    assert_eq!(state_rejected.active_count(), 2);
    assert_eq!(state_rejected.evaluate_quorum(), RUNNING);
    assert_eq!(state_rejected.quorum_health(), QuorumHealth::Degraded);
    assert_eq!(
        state_rejected.evaluate_trace(&valid_trace.path),
        TraceVerdict::Validated
    );

    // Independent instance: a Z3 rejection must veto before Lean is consulted.
    let bad_time_trace = TraceFile::new(&[pack_event(1, 5, 0), pack_event(1, 2, 1)]);
    let time_rejected = LarsaTriadConsensus::new();
    assert_eq!(
        time_rejected.evaluate_trace(&bad_time_trace.path),
        TraceVerdict::TraceRejected
    );
    assert_eq!(
        time_rejected.get_state(LarsaVertex::Gamma),
        VertexState::Fallen
    );
    assert_eq!(
        time_rejected.get_state(LarsaVertex::Beta),
        VertexState::Active
    );
    assert_eq!(time_rejected.active_count(), 2);
    assert_eq!(time_rejected.evaluate_quorum(), RUNNING);
    assert_eq!(time_rejected.quorum_health(), QuorumHealth::Degraded);
    assert_eq!(
        time_rejected.evaluate_trace(&valid_trace.path),
        TraceVerdict::Validated
    );
}

#[test]
fn missing_trace_rejects_without_halting_remaining_quorum() {
    let trace = TraceFile::new(&[]);
    fs::remove_file(&trace.path).unwrap();
    let triad = LarsaTriadConsensus::new();
    assert_eq!(
        triad.evaluate_trace(&trace.path),
        TraceVerdict::TraceRejected
    );
    assert_eq!(triad.quorum_health(), QuorumHealth::Degraded);
    assert_eq!(triad.get_state(LarsaVertex::Beta), VertexState::Active);
}
