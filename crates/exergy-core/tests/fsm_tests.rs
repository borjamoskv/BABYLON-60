use std::collections::HashSet;
use chrono::Utc;
use exergy_core::*;

#[test]
fn test_fsm_open_state_and_entropy_limit() {
    let mut fsm = ConversationFSM::new("chat-1".into(), "Test Chat".into(), "user-alice".into(), 3);

    assert_eq!(fsm.record_message().unwrap(), 1);
    assert_eq!(fsm.record_message().unwrap(), 2);
    assert_eq!(fsm.record_message().unwrap(), 3);

    // 4th message exceeds budget of 3
    let err = fsm.record_message();
    assert!(err.is_err());
    match err.unwrap_err() {
        ExergyError::EntropyLimitExceeded { budget, generated } => {
            assert_eq!(budget, 3);
            assert_eq!(generated, 4);
        }
        _ => panic!("Expected EntropyLimitExceeded error"),
    }
}

#[test]
fn test_fsm_decision_flow() {
    let mut fsm = ConversationFSM::new("chat-2".into(), "Dinner Plan".into(), "user-alice".into(), 10);
    fsm.add_participant("user-bob".into());

    let options = vec![
        DecisionOption {
            id: 1,
            label: "Restaurante A".into(),
            description: None,
        },
        DecisionOption {
            id: 2,
            label: "Restaurante B".into(),
            description: None,
        },
    ];

    let deadline = Utc::now() + chrono::Duration::hours(2);

    // Propose decision
    assert!(fsm
        .propose_decision("¿Dónde cenamos?".into(), options.clone(), deadline)
        .is_ok());

    // Cast votes
    assert!(fsm.cast_vote("user-alice".into(), 1).is_ok());
    assert!(fsm.cast_vote("user-bob".into(), 1).is_ok());

    // Invalid option vote fails
    assert!(fsm.cast_vote("user-alice".into(), 99).is_err());

    // Resolve decision
    let winner = fsm.resolve_decision(1).unwrap();
    assert_eq!(winner.id, 1);
    assert_eq!(winner.label, "Restaurante A");

    // Check state is Resolved
    match &fsm.state {
        ConversationState::Resolved { selected_option, participants_ack, .. } => {
            assert_eq!(selected_option.id, 1);
            assert_eq!(participants_ack.len(), 2);
        }
        _ => panic!("Expected Resolved state"),
    }
}

#[test]
fn test_causal_contract_integrity_and_signing() {
    let mut participants = HashSet::new();
    participants.insert("user-alice".to_string());
    participants.insert("user-bob".to_string());

    let mut contract = CausalContract::create(
        "contract-100".into(),
        "chat-2".into(),
        "Dinner Agreement".into(),
        "Restaurante A".into(),
        participants.clone(),
    );

    assert!(contract.verify_integrity().unwrap());
    assert!(!contract.is_fully_signed());

    // Alice signs
    assert!(contract.sign("user-alice".into(), "sig_proof_alice_123".into()).is_ok());
    assert!(!contract.is_fully_signed());

    // Bob signs
    assert!(contract.sign("user-bob".into(), "sig_proof_bob_456".into()).is_ok());
    assert!(contract.is_fully_signed());
}

#[test]
fn test_entropy_classification() {
    let high_exergy_text = "¿Confirmamos la reunión a las 18:00h en la oficina para decidir el presupuesto?";
    let metrics = analyze_text_entropy(high_exergy_text);
    let priority = metrics.classify_priority(false);

    assert_eq!(priority, PriorityLevel::HighExergy);

    let noise_text = "jaja lol nose jaja idkk whatever xd";
    let noise_metrics = analyze_text_entropy(noise_text);
    let noise_priority = noise_metrics.classify_priority(false);

    assert_eq!(noise_priority, PriorityLevel::LowExergyDigest);
}
