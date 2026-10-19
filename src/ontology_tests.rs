use super::cortex::*;
use super::babylon::*;
use super::nemesis::*;
use super::laws::*;

#[test]
fn test_o1_source_distinct_from_inference() {
    let src = SourceRecord {
        source_id: "file:///corpus/doc1.md".into(),
        provider: "local_fs".into(),
        raw_hash: [0xaa; 32],
        ingested_at: 1000,
        content_length: 512,
        mime_type: Some("text/markdown".into()),
    };
    assert_eq!(src.raw_hash, [0xaa; 32]);
}

#[test]
fn test_o2_inference_cannot_become_authority_trust_boundary() {
    let inf = Inference {
        inference_id: "inf_001".into(),
        derived_from_threads: vec!["idea_alpha".into()],
        model_id: "claude-3-7-sonnet".into(),
        prompt_digest: [0x11; 32],
        generated_at: 1010,
        proposal_summary: "Delete stale cache files".into(),
        confidence: 0.95,
    };

    // CORTEX crossing trust boundary yields ProposalContext, never Authority
    let prop = enforce_trust_boundary(
        &inf,
        "Purge /tmp/cache".into(),
        "Reclaim 4GB".into(),
        "Low".into(),
    );

    assert_eq!(prop.inference_ref, "inf_001");
    assert_eq!(prop.proposal_id, "prop_inf_001");
}

#[test]
fn test_o4_o5_request_decision_effect_demarcation() {
    let req_id = [0x42; 32];
    let effect = Effect {
        effect_id: [0x55; 32],
        effect_kind: EffectKind::FsDelete,
        reversibility: Reversibility::Irreversible,
        target_resource: "file:///tmp/cache".into(),
    };

    let req = EffectRequest {
        request_id: req_id,
        authority_id: [0x01; 32],
        capability_id: [0x02; 32],
        resource_uri: "file:///tmp/cache".into(),
        proposed_effect: effect,
        context_digest: [0x03; 32],
        requested_epoch: 1,
        requested_at: 2000,
    };

    // Decision Deny must block dispatch
    let decision_deny = Decision {
        decision_id: [0x99; 32],
        request_id: req_id,
        outcome: DecisionOutcome::Deny,
        evaluated_tuple_digest: [0xee; 32],
        matched_policies: vec!["pol_no_delete".into()],
        reason: "Policy forbids deletion".into(),
        decided_epoch: 1,
        decided_at: 2001,
    };

    let err = verify_effect_dispatch_authorization(&req, &decision_deny);
    assert!(matches!(err, Err(OntologicalViolation::EffectWithoutApproval { .. })));

    // Decision Allow authorizes dispatch
    let decision_allow = Decision {
        decision_id: [0x88; 32],
        request_id: req_id,
        outcome: DecisionOutcome::Allow,
        evaluated_tuple_digest: [0xdd; 32],
        matched_policies: vec!["pol_allow_tmp".into()],
        reason: "Target in tmp allowed".into(),
        decided_epoch: 1,
        decided_at: 2002,
    };

    assert!(verify_effect_dispatch_authorization(&req, &decision_allow).is_ok());
}

#[test]
fn test_o7_receipt_lifecycle_stages() {
    assert!(verify_receipt_stage_transition(ReceiptStage::Requested, ReceiptStage::Authorized).is_ok());
    assert!(verify_receipt_stage_transition(ReceiptStage::Authorized, ReceiptStage::Dispatched).is_ok());
    assert!(verify_receipt_stage_transition(ReceiptStage::Dispatched, ReceiptStage::Observed).is_ok());
    assert!(verify_receipt_stage_transition(ReceiptStage::Observed, ReceiptStage::Committed).is_ok());

    // Skip is forbidden (e.g. Requested directly to Committed)
    let invalid = verify_receipt_stage_transition(ReceiptStage::Requested, ReceiptStage::Committed);
    assert!(matches!(invalid, Err(OntologicalViolation::InvalidReceiptStageTransition { .. })));

    // Regression is forbidden (e.g. Dispatched back to Requested)
    let regr = verify_receipt_stage_transition(ReceiptStage::Dispatched, ReceiptStage::Requested);
    assert!(matches!(regr, Err(OntologicalViolation::InvalidReceiptStageTransition { .. })));
}

#[test]
fn test_o8_popperian_falsification_evidence() {
    let mut assertion = Assertion {
        assertion_id: "NEM-I1-AUTH".into(),
        name: "Effect Authorization Invariant".into(),
        formal_predicate: "Not(Authorized) => Not(Effected)".into(),
        status: AssertionStatus::Untested,
        domain_scope: "SecureFS".into(),
        last_challenged_at: 0,
    };

    // Evidence showing test held (falsification failed) -> Supported
    let ev_passed = Evidence {
        evidence_id: [0x01; 32],
        test_id: "test_loom_race_1".into(),
        associated_receipt_ids: vec![[0xaa; 32]],
        result: EvidenceResult::FalsificationFailed,
        recorded_at: 5000,
    };
    update_assertion_from_evidence(&mut assertion, &ev_passed);
    assert_eq!(assertion.status, AssertionStatus::Supported);
    assert_eq!(assertion.last_challenged_at, 5000);

    // Counterexample found -> Falsified
    let ev_counterexample = Evidence {
        evidence_id: [0x02; 32],
        test_id: "test_loom_race_2".into(),
        associated_receipt_ids: vec![[0xbb; 32]],
        result: EvidenceResult::FalsificationSuccessful,
        recorded_at: 6000,
    };
    update_assertion_from_evidence(&mut assertion, &ev_counterexample);
    assert_eq!(assertion.status, AssertionStatus::Falsified);
    assert_eq!(assertion.last_challenged_at, 6000);
}

#[test]
fn test_transversal_no_effect_commit_without_decision() {
    let req_id = [0x77; 32];
    let effect = Effect {
        effect_id: [0x88; 32],
        effect_kind: EffectKind::NetTransmit,
        reversibility: Reversibility::Reversible,
        target_resource: "net://gateway/tx".into(),
    };
    let req = EffectRequest {
        request_id: req_id,
        authority_id: [0x01; 32],
        capability_id: [0x02; 32],
        resource_uri: "net://gateway/tx".into(),
        proposed_effect: effect,
        context_digest: [0x00; 32],
        requested_epoch: 1,
        requested_at: 100,
    };
    // Without an explicit Decision outcome == Allow, effect cannot commit
    let pending_decision = Decision {
        decision_id: [0x99; 32],
        request_id: req_id,
        outcome: DecisionOutcome::RequireApproval,
        evaluated_tuple_digest: [0x11; 32],
        matched_policies: vec!["require_biometric".into()],
        reason: "Awaiting touch id".into(),
        decided_epoch: 1,
        decided_at: 101,
    };
    assert!(verify_effect_dispatch_authorization(&req, &pending_decision).is_err());
}

#[test]
fn test_effect_state_8_phase_progression_and_terminal_absorption() {
    let mut rec = EffectLifecycleRecord::new([0x42; 32], 1000, 5000);
    assert_eq!(rec.state, EffectState::Requested);
    assert!(!rec.state.is_terminal());

    // 1 -> 2: Validated
    rec.transition(EffectState::Validated, 1010).unwrap();
    // 2 -> 3: Authorized
    rec.transition(EffectState::Authorized, 1020).unwrap();
    // 3 -> 4: Admitted
    rec.transition(EffectState::Admitted, 1030).unwrap();
    // 4 -> 5: Durable
    rec.transition(EffectState::Durable, 1040).unwrap();
    assert!(rec.state.is_durable());
    assert_eq!(rec.durable_at, Some(1040));

    // 5 -> 6: Executing
    rec.transition(EffectState::Executing, 1050).unwrap();
    // 6 -> 7: Executed
    rec.transition(EffectState::Executed, 1080).unwrap();
    // 7 -> 8: Verified (Terminal Success)
    rec.transition(EffectState::Verified, 1100).unwrap();
    assert!(rec.state.is_terminal());
    assert_eq!(rec.terminal_at, Some(1100));

    // Terminal state is absorbing: cannot transition further
    assert!(rec.transition(EffectState::Requested, 1200).is_err());
    assert!(rec.transition(EffectState::Durable, 1200).is_err());

    // Bounded liveness holds (1100 - 1040 = 60 ms <= 5000 ms)
    assert!(rec.check_bounded_liveness(1200).is_ok());
}

#[test]
fn test_bounded_liveness_contract_timeout_detection() {
    let mut rec = EffectLifecycleRecord::new([0x99; 32], 1000, 2000); // 2 second limit
    rec.transition(EffectState::Validated, 1010).unwrap();
    rec.transition(EffectState::Authorized, 1020).unwrap();
    rec.transition(EffectState::Admitted, 1030).unwrap();
    rec.transition(EffectState::Durable, 1040).unwrap();
    rec.transition(EffectState::Executing, 1050).unwrap();

    // Still executing at 1040 + 3000 ms = 4040 ms -> Timeout!
    let res = rec.check_bounded_liveness(4040);
    assert!(matches!(res, Err(FailureReason::ExecutionTimeout { elapsed_ms: 3000, limit_ms: 2000 })));

    // Fail to terminal state Failed(CrashBeforeCompletion)
    rec.transition(EffectState::Failed(FailureReason::CrashBeforeCompletion), 4050).unwrap();
    assert!(rec.state.is_terminal());
}

#[test]
fn test_o11_machine_inference_neq_prediction_error() {
    let inf = Inference {
        inference_id: "inf_alpha".into(),
        derived_from_threads: vec!["thread_1".into()],
        model_id: "stochastic_llm_v1".into(),
        prompt_digest: [0x11; 32],
        generated_at: 1000,
        proposal_summary: "Reindex corpus".into(),
        confidence: 0.92,
    };

    // Self-evaluation is forbidden (Law O11)
    assert!(verify_prediction_error_evaluation(&inf, false).is_err());
    // Human operator or objective empirical evaluation is allowed
    assert!(verify_prediction_error_evaluation(&inf, true).is_ok());
}

#[test]
fn test_o12_traceability_neq_authorization() {
    let receipt = Receipt {
        receipt_id: [0x55; 32],
        effect_id: [0x22; 32],
        outcome_id: Some([0x44; 32]),
        stage: ReceiptStage::Committed,
        evidence_digest: [0xaa; 32],
        signature: vec![0xbb; 64],
        signer_kid: "kid_enclave_01".into(),
        anchored_epoch: Some(1),
        issued_at: 2000,
    };

    // Without an explicit Allow Decision, ledger trace does not constitute authorization
    assert!(verify_traceability_not_authorization(&receipt, None).is_err());

    let dec_allow = Decision {
        decision_id: [0x33; 32],
        request_id: [0x11; 32],
        outcome: DecisionOutcome::Allow,
        evaluated_tuple_digest: [0x77; 32],
        matched_policies: vec!["pol_ok".into()],
        reason: "Authorized".into(),
        decided_epoch: 1,
        decided_at: 1999,
    };
    assert!(verify_traceability_not_authorization(&receipt, Some(&dec_allow)).is_ok());
}

#[test]
fn test_o13_client_clock_neq_system_time() {
    let system_ts = 1700000000;
    // Acceptable skew (e.g. 5 seconds)
    assert!(verify_system_clock_authority(system_ts + 3, system_ts, 5).is_ok());
    assert!(verify_system_clock_authority(system_ts - 2, system_ts, 5).is_ok());

    // Clock skew exceeded (e.g. 30 seconds drift attempt) -> Rejected
    assert!(verify_system_clock_authority(system_ts + 30, system_ts, 5).is_err());
    assert!(verify_system_clock_authority(system_ts - 30, system_ts, 5).is_err());
}

#[test]
fn test_o14_interface_authorization_neq_environment_confinement() {
    let dec_allow = Decision {
        decision_id: [0x33; 32],
        request_id: [0x11; 32],
        outcome: DecisionOutcome::Allow,
        evaluated_tuple_digest: [0x77; 32],
        matched_policies: vec!["pol_allow".into()],
        reason: "Allowed at UI".into(),
        decided_epoch: 1,
        decided_at: 100,
    };

    // Interface authorization without kernel OS-level confinement -> Rejected
    assert!(verify_environment_confinement(&dec_allow, "file:///etc/hosts", false).is_err());

    // With active kernel confinement -> Allowed
    assert!(verify_environment_confinement(&dec_allow, "file:///workspace/output.txt", true).is_ok());
}
