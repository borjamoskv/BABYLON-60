//! Regression probes for trust boundaries; real Lean checks require a prepared workspace.
use babylon60::larsa::{BicameralQuorum, ConsensusOutcome, VoteKind};
use babylon60::aot_oracle::OracleVerdict;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

#[test]
fn security_conflicting_witnesses_never_commit_another_trace() {
    for threshold in [1, 3] {
        for committed_first in [false, true] {
            let mut quorum = BicameralQuorum::new(threshold);
            quorum.ingest_vote(VoteKind::FormalWitnessVerified { trace_hash: [1; 32] });
            if committed_first {
                assert!(matches!(quorum.ingest_vote(VoteKind::HeuristicApprove { weight: threshold }),
                    ConsensusOutcome::Committed { trace_hash, .. } if trace_hash == [1; 32]));
            }
            let conflict = quorum.ingest_vote(VoteKind::FormalWitnessVerified { trace_hash: [2; 32] });
            assert!(!matches!(conflict, ConsensusOutcome::Committed { .. }), "conflicting witness committed: {conflict:?}");
            for _ in 0..16 {
                assert!(!matches!(quorum.ingest_vote(VoteKind::HeuristicApprove { weight: u32::MAX }),
                    ConsensusOutcome::Committed { .. }));
            }
        }
    }
}

static SERIAL: Mutex<()> = Mutex::new(());
static CALLS: AtomicUsize = AtomicUsize::new(0);
static SWAP: Mutex<Option<std::path::PathBuf>> = Mutex::new(None);

extern "C" fn monotonic_callback(data: *const u8, len: usize) -> u32 {
    CALLS.fetch_add(1, Ordering::SeqCst);
    let bytes = unsafe { std::slice::from_raw_parts(data, len) };
    let monotonic = bytes.as_chunks::<8>().0.iter().map(|b| u64::from_le_bytes(*b) >> 32)
        .collect::<Vec<_>>().windows(2).all(|w| w[0] <= w[1]);
    if let Some(path) = SWAP.lock().unwrap().as_ref() {
        // This replacement passes Lean's stale-read rule but fails Z3 monotonicity.
        let alternate: Vec<u8> = [(1u64 << 32), (2u64 << 32) | 1, 2]
            .into_iter().flat_map(u64::to_le_bytes).collect();
        std::fs::write(path, alternate).unwrap();
    }
    if monotonic { 0 } else { 2 }
}

#[test]
fn security_missing_trace_never_becomes_an_empty_valid_callback() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    babylon60::ffi_oracle::b60_register_z3_callback(monotonic_callback);
    CALLS.store(0, Ordering::SeqCst);
    let missing = std::env::temp_dir().join(format!("b60_security_missing_{}", std::process::id()));
    assert!(!missing.exists());
    assert_eq!(babylon60::z3_oracle::Z3FirewallClient::verify_causality(missing), OracleVerdict::SystemFailure);
    assert_eq!(CALLS.load(Ordering::SeqCst), 0);
}

#[test]
fn security_both_oracles_verify_the_same_snapshot() {
    let _serial = SERIAL.lock().unwrap_or_else(|p| p.into_inner());
    babylon60::ffi_oracle::b60_register_z3_callback(monotonic_callback);
    let path = std::env::temp_dir().join(format!("b60_security_swap_{}.bin", std::process::id()));
    // One odd read: monotonic under Z3, invalid under Lean.
    std::fs::write(&path, ((1u64 << 32) | 2).to_le_bytes()).unwrap();
    *SWAP.lock().unwrap() = Some(path.clone());
    let result = babylon60::larsa_bft::LarsaTriadConsensus::new().evaluate_trace(&path);
    *SWAP.lock().unwrap() = None;
    std::fs::remove_file(path).unwrap();
    assert_eq!(result.to_ffi_code(), babylon60::manifest::POISONED,
        "two proofs of different inputs must never authorize one request");
}

#[test]
#[ignore = "requires a prepared BABYLON_LEAN_TEST_WORKSPACE"]
fn security_invalid_trace_record_must_fail_lean_compilation() {
    use babylon60::lean_emitter::TraceRecord;
    let workspace = std::env::var("BABYLON_LEAN_TEST_WORKSPACE").unwrap();
    let mut record = TraceRecord { step_id: 419, agent_id: 1, seq_start: 0, seq_end: 0,
        kernel_epoch: 1, lease_epoch: 2, formal_witness_ok: true, formal_veto: false,
        heuristic_weight: 3, quorum_threshold: 3 };
    let path = std::env::temp_dir().join(format!("b60_security_record_{}.lean", std::process::id()));
    for valid in [true, false] {
        record.formal_veto = !valid;
        std::fs::write(&path, format!("import BabylonTrace\n{}", record.emit_lean4_def())).unwrap();
        let result = std::process::Command::new("lake").args(["env", "lean"])
            .arg(&path).current_dir(&workspace).output().unwrap();
        std::fs::remove_file(&path).unwrap();
        assert_eq!(result.status.success(), valid, "{}", String::from_utf8_lossy(&result.stdout));
    }
}
