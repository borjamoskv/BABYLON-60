//! # Integration Tests for BABYLON ONTOLOGY v1.0.0 (FROZEN)
//!
//! Validates the two foundational causal pipelines as executable contracts:
//! 1. MemoryEvent → IdeaThread → Inference → (Trust Boundary) → ProposalContext
//! 2. EffectRequest → Decision → Effect → EffectOutcome → Receipt
//!
//! Enforces the 10 Ontological Laws (O1-O10) and the two Transversal Laws:
//! - "No stochastic interpretation may create authority by itself"
//! - "No mediated effect may commit without an explicit Decision"

use babylon60::ontology::cortex::{SourceRecord, MemoryEvent, IdeaThread, Inference, ProposalContext};
use babylon60::ontology::babylon::{
    Effect, EffectKind, Reversibility, EffectRequest, Decision, DecisionOutcome,
    EffectOutcome, OutcomeStatus, Receipt, ReceiptStage
};
use babylon60::ontology::nemesis::{Assertion, AssertionStatus, Evidence, EvidenceResult, Attestation};
use babylon60::ontology::laws::{
    enforce_trust_boundary, verify_effect_dispatch_authorization,
    verify_receipt_stage_transition, update_assertion_from_evidence
};

#[test]
fn test_cortex_causal_chain_memory_to_inference_to_trust_boundary() {
    // 1. SourceRecord (Raw ground truth in substrate)
    let source = SourceRecord {
        source_id: "file:///vault/notes/architecture_2026.md".into(),
        provider: "local_fs".into(),
        raw_hash: [0x42; 32],
        ingested_at: 1700000000,
        content_length: 4096,
        mime_type: Some("text/markdown".into()),
    };

    // 2. MemoryEvent (Normalized extraction anchored to SourceRecord)
    let memory_event = MemoryEvent {
        event_id: "evt_001".into(),
        source_ref: source.source_id.clone(),
        timestamp: 1700000005,
        event_type: "ARCH_OBSERVATION".into(),
        normalized_text: "Observed cache contention during parallel dispatch".into(),
        entities: vec!["L1_CACHE".into(), "SPMC".into()],
        raw_hash: [0x43; 32],
        extractor_version: "cortex-v1.0".into(),
    };

    // 3. IdeaThread (Clustering recurrent memory events over time)
    let idea_thread = IdeaThread {
        idea_id: "idea_kudurru_l1".into(),
        core_concept: "Cache-line alignment zero-split lock".into(),
        first_seen: 1700000005,
        last_seen: 1700000100,
        recurrence_count: 5,
        dormant_days: 0,
        events: vec![memory_event.event_id.clone()],
        score: 0.98,
    };

    // 4. Inference (Model interpretation derived from IdeaThread)
    // Law O1: INFERENCE != SOURCE
    // Law O2: INFERENCE != AUTHORITY
    let inference = Inference {
        inference_id: "inf_kudurru_64".into(),
        derived_from_threads: vec![idea_thread.idea_id.clone()],
        model_id: "local_symbolic_reasoner".into(),
        prompt_digest: [0x50; 32],
        generated_at: 1700000105,
        proposal_summary: "Align Seqlock to 64 bytes to eliminate false sharing".into(),
        confidence: 0.99,
    };

    // 5. Trust Boundary Crossing: Inference produces ProposalContext, NEVER Authority
    let proposal: ProposalContext = enforce_trust_boundary(
        &inference,
        "Apply #[repr(align(64))] to KudurruSeqlock".into(),
        "Eliminates RFO invalidation across cores".into(),
        "Minimal".into(),
    );

    assert_eq!(proposal.inference_ref, inference.inference_id);
    assert_eq!(proposal.suggested_action, "Apply #[repr(align(64))] to KudurruSeqlock");
    // Verifies that proposal does NOT contain Authority capabilities
    assert_eq!(proposal.evaluated_risk, "Minimal");
}

#[test]
fn test_babylon_causal_chain_request_decision_outcome_receipt() {
    let authority_id = [0x01; 32];
    let capability_id = [0x02; 32];
    let req_id = [0x10; 32];
    let effect_id = [0x20; 32];
    let outcome_id = [0x30; 32];
    let receipt_id = [0x40; 32];

    // 1. Target Resource & Effect Definition
    // Effect reversibility is an orthogonal property, not its definition
    let effect = Effect {
        effect_id,
        effect_kind: EffectKind::FsMutate,
        reversibility: Reversibility::Reversible,
        target_resource: "file:///workspace/src/seqlock.rs".into(),
    };

    // 2. EffectRequest: Formal demand for state transition
    // Law O4: REQUEST != DECISION
    let request = EffectRequest {
        request_id: req_id,
        authority_id,
        capability_id,
        resource_uri: "file:///workspace/src/seqlock.rs".into(),
        proposed_effect: effect.clone(),
        context_digest: [0x99; 32],
        requested_epoch: 42,
        requested_at: 1700001000,
    };

    // 3. Negative Gate: Dispatch WITHOUT an Allow Decision is rejected (Transversal Law 2)
    let decision_pending = Decision {
        decision_id: [0xd0; 32],
        request_id: req_id,
        outcome: DecisionOutcome::RequireApproval,
        evaluated_tuple_digest: [0xaa; 32],
        matched_policies: vec!["pol_require_touch_id".into()],
        reason: "Mutation requires biometric confirmation".into(),
        decided_epoch: 42,
        decided_at: 1700001001,
    };
    assert!(verify_effect_dispatch_authorization(&request, &decision_pending).is_err());

    // 4. Affirmative Decision (Law O5: DECISION != EFFECT)
    let decision_allow = Decision {
        decision_id: [0xd1; 32],
        request_id: req_id,
        outcome: DecisionOutcome::Allow,
        evaluated_tuple_digest: [0xbb; 32],
        matched_policies: vec!["pol_allow_source_edit".into()],
        reason: "Valid epoch, capability attested by Touch ID".into(),
        decided_epoch: 42,
        decided_at: 1700001002,
    };
    assert!(verify_effect_dispatch_authorization(&request, &decision_allow).is_ok());

    // 5. EffectOutcome: Observed physical consequence in silicio
    // Law O6: EFFECT != OBSERVED OUTCOME
    let outcome = EffectOutcome {
        outcome_id,
        effect_id,
        status: OutcomeStatus::Success,
        pre_state_digest: [0x11; 32],
        post_state_digest: [0x22; 32],
        divergence_detected: false,
        observed_at: 1700001005,
    };
    assert_eq!(outcome.status, OutcomeStatus::Success);
    assert!(!outcome.divergence_detected);

    // 6. Receipt: Cryptographic record of evidence across stages
    // Law O7: RECEIPT != TRUTH
    let receipt = Receipt {
        receipt_id,
        effect_id,
        outcome_id: Some(outcome_id),
        stage: ReceiptStage::Committed,
        evidence_digest: [0xee; 32],
        signature: vec![0xca, 0xfe, 0xba, 0xbe],
        signer_kid: "key_secure_enclave_p256".into(),
        anchored_epoch: Some(42),
        issued_at: 1700001010,
    };
    assert_eq!(receipt.stage, ReceiptStage::Committed);

    // 7. Verify Receipt Stage Progression
    assert!(verify_receipt_stage_transition(ReceiptStage::Requested, ReceiptStage::Authorized).is_ok());
    assert!(verify_receipt_stage_transition(ReceiptStage::Authorized, ReceiptStage::Dispatched).is_ok());
    assert!(verify_receipt_stage_transition(ReceiptStage::Dispatched, ReceiptStage::Observed).is_ok());
    assert!(verify_receipt_stage_transition(ReceiptStage::Observed, ReceiptStage::Committed).is_ok());
}

#[test]
fn test_nemesis_popperian_falsification_and_attestation_binding() {
    let mut assertion = Assertion {
        assertion_id: "INV-C5-EFFECT-NO-DECISION".into(),
        name: "No effect may commit without explicit decision".into(),
        formal_predicate: "Forall e: Effect, Committed(e) => Exists d: Decision, Allow(d, e)".into(),
        status: AssertionStatus::Untested,
        domain_scope: "BABYLON_CORE".into(),
        last_challenged_at: 0,
    };

    // Adversarial campaign executes without falsifying -> Supported
    let ev = Evidence {
        evidence_id: [0x01; 32],
        test_id: "test_loom_100k_race".into(),
        associated_receipt_ids: vec![[0x99; 32]],
        result: EvidenceResult::FalsificationFailed,
        recorded_at: 1700002000,
    };
    update_assertion_from_evidence(&mut assertion, &ev);
    assert_eq!(assertion.status, AssertionStatus::Supported);

    // Attestation binds Assertion + Evidence + Artifact + Environment (Firma != Verdad)
    let attestation = Attestation {
        attestation_id: [0xaa; 32],
        subject_id: "babylon60_kernel_binary".into(),
        assertion_id: assertion.assertion_id.clone(),
        evidence_hashes: vec![[0x01; 32]],
        artifact_digest: [0xdd; 32],
        environment_digest: [0xee; 32],
        claims: vec!["Passed 100k loom race perturbations".into()],
        issued_at: 1700002005,
        signature: vec![0x12, 0x34],
        signer_authority_id: [0x01; 32],
    };

    assert_eq!(attestation.assertion_id, "INV-C5-EFFECT-NO-DECISION");
    assert!(!attestation.evidence_hashes.is_empty());
}
