//! Tests de verificación en silicio para FL-007 (AdmissionController) y FL-008 (ScopedHandle).
//! Verifica Little's Law, backpressure determinista y anti-confused deputy.

#![cfg(feature = "cortex-persist")]

use std::time::Duration;
use babylon60::admission::AdmissionController;
use babylon60::capability::ScopedHandle;
use babylon60::ontology::babylon::RejectReason;

#[test]
fn test_fl007_admission_bounded_capacity() {
    let controller = AdmissionController::new(
        3,                                   // max_queue_depth
        Duration::from_millis(100),          // max_latency_budget
        Duration::from_millis(20),           // estimated_service_time_per_item
    );

    assert_eq!(controller.current_depth(), 0);

    // Admit slot 1, 2, 3
    assert!(controller.try_admit().is_ok());
    assert_eq!(controller.current_depth(), 1);

    assert!(controller.try_admit().is_ok());
    assert_eq!(controller.current_depth(), 2);

    assert!(controller.try_admit().is_ok());
    assert_eq!(controller.current_depth(), 3);

    // Slot 4 debe ser rechazado por max_queue_depth
    let err = controller.try_admit();
    assert!(err.is_err());
    assert_eq!(controller.current_depth(), 3);

    // Liberar 1 slot y admitir de nuevo
    controller.release();
    assert_eq!(controller.current_depth(), 2);
    assert!(controller.try_admit().is_ok());
    assert_eq!(controller.current_depth(), 3);
}

#[test]
fn test_fl007_admission_latency_budget_exhaustion() {
    // Presupuesto de latencia pequeño que se agota antes del max_queue_depth
    let controller = AdmissionController::new(
        100,                                 // max_queue_depth muy alto
        Duration::from_millis(50),           // max_latency_budget 50ms
        Duration::from_millis(30),           // 30ms por item -> a partir de 2 items = 60ms > 50ms
    );

    assert!(controller.try_admit().is_ok()); // current=1, next expected = 30ms <= 50ms
    assert!(controller.try_admit().is_ok()); // current=2, next expected = 60ms > 50ms -> RECHAZA
    assert!(controller.try_admit().is_err()); // slot 3 rechazado por latency budget
}

#[test]
fn test_fl008_scoped_handle_anti_confused_deputy() {
    let temp_dir = std::env::temp_dir();
    let legitimate_parent = [0x42u8; 32];
    let attacker_deputy = [0x66u8; 32];

    let handle = ScopedHandle::new(&temp_dir, legitimate_parent)
        .expect("Failed to create ScopedHandle on temp_dir");

    // Reclamación legítima por el padre causal exacto
    assert!(handle.verify_causal_parent(&legitimate_parent).is_ok());

    // Intento de usurpación / Confused Deputy
    let result = handle.verify_causal_parent(&attacker_deputy);
    assert_eq!(result, Err(RejectReason::ConfusedDeputyAttempt));
}

#[test]
fn test_fl008_mcp_broker_10000_adversarial_trials() {
    use babylon60::capability::{McpCapabilityBroker, McpToolDef, sha256_digest};
    use babylon60::ontology::babylon::EffectKind;

    let mut broker = McpCapabilityBroker::new();
    let server_a = [0xAAu8; 32];
    let server_b = [0xBBu8; 32];

    broker.register_server(server_a, true, 1);
    broker.register_server(server_b, false, 1); // Server B disabled

    let read_tool = McpToolDef {
        name: "read_fixture".to_string(),
        code_hash: sha256_digest(b"v1_read_fixture_impl"),
        allowed_effects: vec![EffectKind::FsRead],
        target_resource_scope: "fixtures/safe/".to_string(),
    };

    let mutate_tool = McpToolDef {
        name: "mutate_fixture".to_string(),
        code_hash: sha256_digest(b"v1_mutate_fixture_impl"),
        allowed_effects: vec![EffectKind::FsMutate],
        target_resource_scope: "fixtures/writable/".to_string(),
    };

    let delete_tool = McpToolDef {
        name: "delete_fixture".to_string(),
        code_hash: sha256_digest(b"v1_delete_fixture_impl"),
        allowed_effects: vec![EffectKind::FsDelete],
        target_resource_scope: "fixtures/deletable/".to_string(),
    };

    broker.register_tool(&server_a, read_tool).unwrap();
    broker.register_tool(&server_a, mutate_tool).unwrap();
    broker.register_tool(&server_a, delete_tool).unwrap();

    let legitimate_args = b"target=fixtures/safe/file1.txt";
    let token = broker.request_capability(
        &server_a,
        "read_fixture",
        &sha256_digest(b"v1_read_fixture_impl"),
        legitimate_args,
        "fixtures/safe/file1.txt",
        EffectKind::FsRead,
        10,
    ).expect("Legitimate capability issuance must succeed");

    // Acceptance Metrics
    let mut unauthorized_effects = 0usize;
    let mut capability_escalations = 0usize;
    let mut stale_token_acceptances = 0usize;
    let mut tool_identity_confusions = 0usize;
    let mut configuration_drifts = 0usize;
    let mut valid_commits = 0usize;

    // Run 10,000 adversarial trial iterations partitioned over 5 vectors:
    // 0: Disabled server activation exploit (2,000 attempts)
    // 1: Tool substitution / code hash tampering (2,000 attempts)
    // 2: Capability escalation (READ -> WRITE/DELETE) (2,000 attempts)
    // 3: Stale token acceptance / revocation bypass (2,000 attempts)
    // 4: Configuration drift / argument poisoning (2,000 attempts)
    for i in 0..10_000 {
        match i % 5 {
            0 => {
                // Escenario 1: Ejecución contra servidor deshabilitado
                let res = broker.commit_execution(
                    &token,
                    &server_b, // disabled server
                    "read_fixture",
                    &sha256_digest(b"v1_read_fixture_impl"),
                    legitimate_args,
                    "fixtures/safe/file1.txt",
                    EffectKind::FsRead,
                    1,
                );
                match res {
                    Ok(_) => unauthorized_effects += 1,
                    Err(RejectReason::ServerDisabled) | Err(RejectReason::ConfusedDeputyAttempt) => {},
                    Err(_) => unauthorized_effects += 1,
                }
            }
            1 => {
                // Escenario 2: Sustitución de herramienta / falsificación de hash
                let fake_hash = sha256_digest(format!("malicious_payload_{}", i).as_bytes());
                let res = broker.commit_execution(
                    &token,
                    &server_a,
                    "read_fixture",
                    &fake_hash,
                    legitimate_args,
                    "fixtures/safe/file1.txt",
                    EffectKind::FsRead,
                    1,
                );
                match res {
                    Ok(_) => tool_identity_confusions += 1,
                    Err(RejectReason::ToolIdentityMismatch) => {},
                    Err(_) => tool_identity_confusions += 1,
                }
            }
            2 => {
                // Escenario 3: Escalada de capacidades no concedidas (Read -> Write/Delete)
                let escalated_effect = if i % 2 == 0 { EffectKind::FsMutate } else { EffectKind::FsDelete };
                let res = broker.commit_execution(
                    &token,
                    &server_a,
                    "read_fixture",
                    &sha256_digest(b"v1_read_fixture_impl"),
                    legitimate_args,
                    "fixtures/safe/file1.txt",
                    escalated_effect,
                    1,
                );
                match res {
                    Ok(_) => capability_escalations += 1,
                    Err(RejectReason::CapabilityEscalation) => {},
                    Err(_) => capability_escalations += 1,
                }
            }
            3 => {
                // Escenario 4: Reutilización de token caducado o revocado en t_commit
                let expired_t_commit = 999;
                let res = broker.commit_execution(
                    &token,
                    &server_a,
                    "read_fixture",
                    &sha256_digest(b"v1_read_fixture_impl"),
                    legitimate_args,
                    "fixtures/safe/file1.txt",
                    EffectKind::FsRead,
                    expired_t_commit,
                );
                match res {
                    Ok(_) => stale_token_acceptances += 1,
                    Err(RejectReason::StaleCapability) => {},
                    Err(_) => stale_token_acceptances += 1,
                }
            }
            4 => {
                // Escenario 5: Drift de argumentos / envenenamiento de recurso entre validación y commit
                let poisoned_args = format!("target=fixtures/safe/secret_{}.txt", i).into_bytes();
                let res = broker.commit_execution(
                    &token,
                    &server_a,
                    "read_fixture",
                    &sha256_digest(b"v1_read_fixture_impl"),
                    &poisoned_args,
                    "fixtures/safe/file1.txt",
                    EffectKind::FsRead,
                    1,
                );
                match res {
                    Ok(_) => configuration_drifts += 1,
                    Err(RejectReason::ConfigurationDrift) => {},
                    Err(_) => configuration_drifts += 1,
                }
            }
            _ => unreachable!(),
        }
    }

    // Comprobación de Control Positivo: un commit legítimo dentro del contrato exacto
    let happy_commit = broker.commit_execution(
        &token,
        &server_a,
        "read_fixture",
        &sha256_digest(b"v1_read_fixture_impl"),
        legitimate_args,
        "fixtures/safe/file1.txt",
        EffectKind::FsRead,
        1,
    );
    assert!(happy_commit.is_ok());
    valid_commits += 1;

    // Aserción formal de los criterios FL-008 / ACCEPTANCE
    assert_eq!(unauthorized_effects, 0, "FL-008 Violation: unauthorized effects committed");
    assert_eq!(capability_escalations, 0, "FL-008 Violation: capability escalations committed");
    assert_eq!(stale_token_acceptances, 0, "FL-008 Violation: stale token accepted");
    assert_eq!(tool_identity_confusions, 0, "FL-008 Violation: tool identity confusion accepted");
    assert_eq!(configuration_drifts, 0, "FL-008 Violation: configuration drift accepted");
    assert_eq!(valid_commits, 1, "Control positivo debe producir evidencia criptográfica válida");
}

#[test]
fn test_fl008_scope_rejects_prefix_confusion_and_path_traversal() {
    use babylon60::capability::{McpCapabilityBroker, McpToolDef, sha256_digest};
    use babylon60::ontology::babylon::EffectKind;

    let mut broker = McpCapabilityBroker::new();
    let server = [0xABu8; 32];
    let code_hash = sha256_digest(b"read-tool-v1");
    broker.register_server(server, true, 1);
    broker.register_tool(&server, McpToolDef {
        name: "read".to_string(),
        code_hash,
        allowed_effects: vec![EffectKind::FsRead],
        target_resource_scope: "fixtures/safe/".to_string(),
    }).unwrap();

    let args = b"document";
    let good = "fixtures/safe/document.txt";
    let token = broker.request_capability(
        &server, "read", &code_hash, args, good, EffectKind::FsRead, 5,
    ).expect("valid child resource must be in scope");
    assert!(broker.commit_execution(
        &token, &server, "read", &code_hash, args, good, EffectKind::FsRead, 1,
    ).is_ok());

    for bad in [
        "fixtures/safe-evil/passwords",
        "fixtures/safe/../secrets",
        "fixtures/safe/%2e%2e/secrets",
        "fixtures/safe\\..\\secrets",
        "fixtures/safe//secrets",
    ] {
        assert!(broker.request_capability(
            &server, "read", &code_hash, args, bad, EffectKind::FsRead, 5,
        ).is_err(), "escaped scope accepted: {}", bad);
        assert!(broker.commit_execution(
            &token, &server, "read", &code_hash, args, bad, EffectKind::FsRead, 1,
        ).is_err(), "scope drift accepted: {}", bad);
    }
}

