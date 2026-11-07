//! NEMESIS WAVE 6 · FL-026 FORGED FORMAL AUTHORITY & FL-018 COMPOSITE SAFETY GATE.
//!
//! Verifies that `src/larsa.rs` enforces:
//! - `FL-026` (`H1`..`H4`): unproven refutation rejection once witness is present,
//!   target/nonce anti-replay via `WitnessReplayLedger`, expected artifact trace
//!   binding (`Hash(a_accepted) == Hash(a_verified)`), terminal immutable `Committed`
//!   state, and non-zero heuristic threshold.
//! - `FL-018` (`COMPOSITE-SAFETY`): conjunctive critical constraint verification
//!   across 29 PLE-equivalent tasks × 3 runs and 200 adversarial mutations with
//!   zero false-safe attestations.
use babylon60::larsa::{
    BicameralQuorum, CompositeRejectReason, CompositeSafetyDecision, CompositeSafetyGate,
    ConsensusOutcome, EvaluatorAttestation, VoteKind, WitnessReplayLedger,
};

const LEGIT_TRACE: [u8; 32] = [0x11; 32];

fn committed_quorum() -> BicameralQuorum {
    let mut q = BicameralQuorum::new(3);
    q.ingest_vote(VoteKind::FormalWitnessVerified { trace_hash: LEGIT_TRACE });
    let out = q.ingest_vote(VoteKind::HeuristicApprove { weight: 3 });
    assert!(matches!(out, ConsensusOutcome::Committed { .. }), "setup: {out:?}");
    q
}

/// Vector 1 (H1): a refutation with no proof behind it, built by an untrusted
/// actor, must not abort a legitimate pending operation that already holds a verified witness.
#[test]
fn fl026_v1_unproven_refutation_must_not_veto() {
    let mut q = BicameralQuorum::new(3);
    q.ingest_vote(VoteKind::FormalWitnessVerified { trace_hash: LEGIT_TRACE });
    // Forged: no theorem, no proof object, no verifier involved.
    let forged = q.ingest_vote(VoteKind::FormalRefutation { theorem_id: 401 });
    assert!(
        !matches!(forged, ConsensusOutcome::AbortedByFormalVeto { .. }),
        "unverified refutation accepted as veto (DoS vector): {forged:?}"
    );
}

/// Vector 2 (H2): one witness must not authorize two distinct targets.
/// Bound ingestion against `WitnessReplayLedger` rejects cross-target replay.
#[test]
fn fl026_v2_witness_replay_across_targets_must_not_commit() {
    let mut ledger = WitnessReplayLedger::new();
    let mut target_a = BicameralQuorum::with_expected_trace(1, LEGIT_TRACE);
    let mut target_b = BicameralQuorum::with_expected_trace(1, LEGIT_TRACE);
    let mut commits = 0;
    for (idx, q) in [&mut target_a, &mut target_b].into_iter().enumerate() {
        let target_id = (idx as u64) + 1;
        q.ingest_vote_bound(
            VoteKind::FormalWitnessVerified { trace_hash: LEGIT_TRACE },
            target_id,
            100,
            &mut ledger,
        );
        if matches!(
            q.ingest_vote(VoteKind::HeuristicApprove { weight: 1 }),
            ConsensusOutcome::Committed { .. }
        ) {
            commits += 1;
        }
    }
    assert!(commits <= 1, "same witness committed {commits} independent targets");
}

/// Vector 3 (H2): an arbitrary 32-byte value, never derived from the executed
/// artifact (`LEGIT_TRACE`), must not be accepted as a verified witness.
#[test]
fn fl026_v3_arbitrary_hash_must_not_count_as_witness() {
    let mut q = BicameralQuorum::with_expected_trace(1, LEGIT_TRACE);
    q.ingest_vote(VoteKind::FormalWitnessVerified { trace_hash: [0xEE; 32] });
    let out = q.ingest_vote(VoteKind::HeuristicApprove { weight: 1 });
    assert!(!matches!(out, ConsensusOutcome::Committed { .. }), "fabricated witness committed: {out:?}");
}

/// Vector 4a (H3): once Committed, a later veto must not rewrite the decision.
/// Otherwise the observable outcome depends on read timing (no linearization).
#[test]
fn fl026_v4a_commit_is_terminal_against_late_veto() {
    let mut q = committed_quorum();
    let late = q.ingest_vote(VoteKind::FormalRefutation { theorem_id: 909 });
    assert!(
        matches!(late, ConsensusOutcome::Committed { trace_hash, .. } if trace_hash == LEGIT_TRACE),
        "decision flipped after commit: {late:?}"
    );
}

/// Vector 4b (H3): the committed record must be immutable; extra approvals
/// must not change the reported heuristic weight.
#[test]
fn fl026_v4b_committed_payload_is_immutable() {
    let mut q = committed_quorum();
    let again = q.ingest_vote(VoteKind::HeuristicApprove { weight: 1_000 });
    assert_eq!(
        again,
        ConsensusOutcome::Committed { trace_hash: LEGIT_TRACE, heuristic_weight: 3 },
        "committed record mutated after decision"
    );
}

/// H4: a zero heuristic threshold lets a lone witness commit. Either reject
/// the configuration or declare it explicitly; silent acceptance fails here.
#[test]
fn fl026_h4_zero_threshold_must_not_commit_on_witness_alone() {
    let mut q = BicameralQuorum::new(0);
    let out = q.ingest_vote(VoteKind::FormalWitnessVerified { trace_hash: LEGIT_TRACE });
    assert!(!matches!(out, ConsensusOutcome::Committed { .. }), "witness alone committed: {out:?}");
}

/// FL-018: 91% of constraints satisfied (10 of 11 critical checks passed, 1 critical failed)
/// must NEVER produce `Accepted`.
#[test]
fn fl018_composite_safety_gate_rejects_partial_91_percent_compliance() {
    let required_mask: u64 = (1u64 << 11) - 1; // 11 critical engineering checks (bits 0..10)
    let input_hash = [0xA1; 32];
    let artifact_hash = [0xB2; 32];
    let policy_hash = [0xC3; 32];
    let epoch = 10;
    let target_id = 42;
    let nonce = 7001;

    let gate = CompositeSafetyGate::new(
        required_mask,
        10,
        input_hash,
        artifact_hash,
        policy_hash,
        epoch,
        target_id,
        nonce,
    );

    // 10 of 11 pass (90.9% ~ 91%), check #10 fails.
    let attestations: Vec<EvaluatorAttestation> = (0..11u8)
        .map(|cid| {
            EvaluatorAttestation::new_canonical(
                cid,
                cid != 10,
                input_hash,
                artifact_hash,
                policy_hash,
                epoch,
                target_id,
                nonce,
            )
        })
        .collect();

    let mut ledger = WitnessReplayLedger::new();
    let decision = gate.evaluate_admission(&attestations, 100, &mut ledger);
    assert_eq!(
        decision,
        CompositeSafetyDecision::Rejected(CompositeRejectReason::CriticalCheckFailed {
            check_id: 10
        })
    );
}

/// FL-018: 29 PLE-equivalent tasks × 3 runs (87 valid runs) + 200 controlled adversarial mutations
/// (50 post-verification artifact mutations, 50 stale evidence epochs, 50 isolated critical check
/// failures, 50 cross-version/nonce/digest mutations).
#[test]
fn fl018_composite_safety_gate_200_adversarial_mutations_zero_false_safe() {
    let mut ledger = WitnessReplayLedger::new();
    let required_mask: u64 = 0b1111_1111; // 8 mandatory critical checks per deliverable
    let policy_hash = [0x55; 32];
    let active_epoch = 40u64;

    let mut valid_accepted = 0usize;
    let valid_total = 29usize * 3usize;

    for task_idx in 0..29u64 {
        for run_idx in 0..3u64 {
            let nonce = 1_000 + task_idx * 10 + run_idx;
            let mut input_hash = [0u8; 32];
            input_hash[0] = task_idx as u8;
            let mut artifact_hash = [0u8; 32];
            artifact_hash[0] = task_idx as u8;
            artifact_hash[1] = (run_idx + 1) as u8;

            let gate = CompositeSafetyGate::new(
                required_mask,
                3,
                input_hash,
                artifact_hash,
                policy_hash,
                active_epoch,
                task_idx + 1,
                nonce,
            );
            let atts: Vec<EvaluatorAttestation> = (0..8u8)
                .map(|cid| {
                    EvaluatorAttestation::new_canonical(
                        cid,
                        true,
                        input_hash,
                        artifact_hash,
                        policy_hash,
                        active_epoch,
                        task_idx + 1,
                        nonce,
                    )
                })
                .collect();

            if let CompositeSafetyDecision::Accepted {
                artifact_hash: accepted_hash,
                verified_critical_mask,
                ..
            } = gate.evaluate_admission(&atts, 3, &mut ledger)
            {
                assert_eq!(accepted_hash, artifact_hash);
                assert_eq!(verified_critical_mask, required_mask);
                valid_accepted += 1;
            }
        }
    }

    assert_eq!(valid_accepted, valid_total, "100% of valid deliverables must be accepted");

    let mut false_safe_attestations_c = 0usize;
    let mut artifact_hash_mismatches_accepted = 0usize;
    let mut stale_evidence_acceptance = 0usize;
    let mut unauthorized_commits_c = 0usize;

    for mut_idx in 0..200u64 {
        let nonce = 50_000 + mut_idx;
        let target_id = 900 + mut_idx;
        let input_hash = [0x22; 32];
        let verified_artifact_hash = [0x33; 32];
        let mut presented_artifact_hash = verified_artifact_hash;

        let category = mut_idx % 4;
        if category == 0 {
            // Category 0 (50 mutations): Artifact altered after verification
            presented_artifact_hash[0] ^= ((mut_idx / 4) as u8).wrapping_add(1);
        }

        let gate = CompositeSafetyGate::new(
            required_mask,
            3,
            input_hash,
            presented_artifact_hash,
            policy_hash,
            active_epoch,
            target_id,
            nonce,
        );

        let atts: Vec<EvaluatorAttestation> = (0..8u8)
            .map(|cid| {
                let failing_cid = ((mut_idx / 4) % 8) as u8;
                let passed = if category == 2 && cid == failing_cid {
                    // Category 2 (50 mutations): Isolated critical constraint violation
                    false
                } else {
                    true
                };
                let ev_epoch = if category == 1 && cid == failing_cid {
                    // Category 1 (50 mutations): Stale evidence from prior policy epoch
                    active_epoch - 1
                } else {
                    active_epoch
                };
                let ev_target = if category == 3 && cid == failing_cid {
                    // Category 3 (50 mutations): Evidence belonging to another version/target
                    target_id + 10_000
                } else {
                    target_id
                };

                EvaluatorAttestation::new_canonical(
                    cid,
                    passed,
                    input_hash,
                    verified_artifact_hash,
                    policy_hash,
                    ev_epoch,
                    ev_target,
                    nonce,
                )
            })
            .collect();

        let decision = gate.evaluate_admission(&atts, 3, &mut ledger);
        if matches!(decision, CompositeSafetyDecision::Accepted { .. }) {
            false_safe_attestations_c += 1;
            match category {
                0 => artifact_hash_mismatches_accepted += 1,
                1 => stale_evidence_acceptance += 1,
                _ => unauthorized_commits_c += 1,
            }
        }
    }

    assert_eq!(false_safe_attestations_c, 0);
    assert_eq!(artifact_hash_mismatches_accepted, 0);
    assert_eq!(stale_evidence_acceptance, 0);
    assert_eq!(unauthorized_commits_c, 0);
}

/// FL-018 / B60-06..09: verifica la emisión determinista de `CompositeTraceRecord` hacia Lean 4 (`BitVec 64`).
#[test]
fn fl018_lean4_composite_trace_emitter_roundtrip() {
    use babylon60::lean_emitter::CompositeTraceRecord;

    let record = CompositeTraceRecord {
        step_id: 18,
        required_critical_mask: 0x7FF,
        verified_critical_mask: 0x7FF,
        accepted_artifact_hash_u64: 0xCAFE_BABE_0000_0001,
        verified_artifact_hash_u64: 0xCAFE_BABE_0000_0001,
        min_policy_epoch: 40,
        evidence_epoch: 40,
        heuristic_weight: 10,
        quorum_threshold: 3,
    };

    let lean_code = record.emit_lean4_composite_def();
    assert!(lean_code.contains("def composite_step_18 : B60.Ledger.CompositeGateState"));
    assert!(lean_code.contains("requiredCriticalMask := 2047#64"));
    assert!(lean_code.contains("verifiedCriticalMask := 2047#64"));
    assert!(lean_code.contains("theorem composite_step_18_valid : B60.Ledger.ValidCompositeAcceptance composite_step_18 := by decide"));
    assert!(lean_code.contains("#print axioms composite_step_18_valid"));
}
