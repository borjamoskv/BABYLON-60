use super::*;
use super::ipc::*;
use std::os::unix::net::UnixStream;

/// Software-only boundary regression: client time cannot revive an expired token.
#[test]
fn test_ipc_expired_authorization_cannot_use_client_clock() {
    let mut f = tests::fixture();
    f.intent.parameters = b"AUTHORIZED_EFFECT".to_vec();
    let mut resource = Vec::new();
    let mut payload = tests::payload(&f, 103);
    payload.resource_precondition_digest = ByteLogAdapter.compute_precondition(&resource).unwrap();
    payload.expires_at = 1;
    let expired = tests::sign(&f, payload.clone());
    payload.expires_at = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() + 3600;
    let valid = tests::sign(&f, payload);
    let executor = SovereignExecutor::new(
        tests::INST, tests::EXEC, 1,
        vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        DurableExecutionStore::open_in_memory_non_durable().unwrap(), ByteLogAdapter,
    );
    let mut server = IpcExecutorServer::new(executor);
    let (server_sock, client_sock) = UnixStream::pair().unwrap();
    let handle = std::thread::spawn(move || {
        server.handle_client(server_sock, &mut resource).unwrap();
        resource
    });
    let mut client = IpcExecutorClient::from_stream(client_sock);
    // Warmup followed by repeated hostile requests; no nonce may be consumed.
    client.ping().unwrap();
    for _ in 0..256 {
        assert_eq!(client.execute_action(&expired, &f.intent, &f.policy, 0),
                   Err(ExecutionError::AuthorizationExpired));
    }
    // A remote future timestamp must not reject a genuinely live authorization.
    assert_eq!(client.execute_action(&valid, &f.intent, &f.policy, u64::MAX).unwrap(),
               b"AUTHORIZED_EFFECT");
    assert!(matches!(client.execute_action(&valid, &f.intent, &f.policy, 0),
                     Err(ExecutionError::NonceAlreadyConsumed(_))));
    drop(client);
    assert_eq!(handle.join().unwrap(), vec![b"AUTHORIZED_EFFECT".to_vec()]);
}

#[test]
fn test_host_clock_rejects_pre_epoch() {
    let epoch = std::time::UNIX_EPOCH;
    assert_eq!(unix_seconds_from_host_time(epoch), Ok(0));
    assert_eq!(unix_seconds_from_host_time(epoch - std::time::Duration::from_secs(1)),
               Err(ExecutionError::ClockUnavailable));
}

#[test]
fn test_authorization_expiry_boundary_is_exclusive() {
    let f = tests::fixture();
    let mut payload = tests::payload(&f, 104);
    payload.expires_at = 100;
    let auth = tests::sign(&f, payload);
    let executor = tests::executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let pre = SyntheticEffectAdapter.compute_precondition(&f.resource).unwrap();
    assert_eq!(executor.verify_authorization(&auth, &f.intent, &f.policy, &pre, 99), Ok(()));
    assert_eq!(executor.verify_authorization(&auth, &f.intent, &f.policy, &pre, 100),
               Err(ExecutionError::AuthorizationExpired));
    assert_eq!(executor.verify_authorization(&auth, &f.intent, &f.policy, &pre, 101),
               Err(ExecutionError::AuthorizationExpired));
}

#[test]
fn test_host_clock_drives_reservation_dispatch_and_completion() {
    let f = tests::fixture();
    let before = unix_seconds_from_host_time(std::time::SystemTime::now()).unwrap();
    let mut payload = tests::payload(&f, 105);
    payload.expires_at = before + 3600;
    let nonce = payload.nonce;
    let auth = tests::sign(&f, payload);
    let mut executor = tests::executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut resource = f.resource.clone();
    executor.execute_action_with_host_clock(&auth, &f.intent, &f.policy, &mut resource).unwrap();
    let after = unix_seconds_from_host_time(std::time::SystemTime::now()).unwrap();
    let record = executor.store.get_record(&nonce).unwrap().unwrap();
    assert!((before..=after).contains(&record.created_at));
    assert_eq!(record.dispatched_at, Some(record.created_at));
    assert_eq!(record.completed_at, Some(record.created_at));
}

#[test]
fn test_ipc_errors_preserve_their_variants() {
    let errors = vec![
        ExecutionError::MalformedAuthorization("malformed".into()),
        ExecutionError::UnsupportedProtocolVersion(9),
        ExecutionError::UnsupportedMaxUses(2),
        ExecutionError::InvalidAuthorityKey("unadmitted".into()),
        ExecutionError::InvalidSignature("signature".into()),
        ExecutionError::InstallationMismatch,
        ExecutionError::ExecutorMismatch,
        ExecutionError::AuthorityEpochRevoked,
        ExecutionError::IntentDigestMismatch,
        ExecutionError::PolicyDigestMismatch,
        ExecutionError::PolicyActionMismatch,
        ExecutionError::PolicyAuthorityMismatch,
        ExecutionError::PolicyUsesExceeded,
        ExecutionError::PreconditionMismatch,
        ExecutionError::AuthorizationExpired,
        ExecutionError::ClockUnavailable,
        ExecutionError::NonceAlreadyConsumed("nonce".into()),
        ExecutionError::ExecutorPoisoned,
        ExecutionError::StorageError("storage".into()),
        ExecutionError::InvalidStateTransition("transition".into()),
        ExecutionError::EffectExecutionFailed("NonceAlreadyConsumed in adapter text".into()),
        ExecutionError::Interrupted(CrashPoint::AfterDispatchBeforeEffect),
    ];
    for error in errors {
        let response = IpcResponse::Err(error.clone());
        let bytes = serde_json::to_vec(&response).unwrap();
        match serde_json::from_slice::<IpcResponse>(&bytes).unwrap() {
            IpcResponse::Err(decoded) => assert_eq!(decoded, error),
            other => panic!("wrong error response: {other:?}"),
        }
    }
    assert!(serde_json::from_str::<IpcResponse>(
        r#"{"Err":{"Interrupted":"not-a-crash-point"}}"#).is_err());
    assert!(serde_json::from_str::<IpcResponse>(
        r#"{"Err":"NonceAlreadyConsumed(\"legacy payload\")"}"#).is_err());
}

#[test]
fn test_ipc_client_does_not_classify_adapter_error_text() {
    let f = tests::fixture();
    let auth = tests::sign(&f, tests::payload(&f, 106));
    let expected = ExecutionError::EffectExecutionFailed("NonceAlreadyConsumed".into());
    let response = expected.clone();
    let (mut server_sock, client_sock) = UnixStream::pair().unwrap();
    let handle = std::thread::spawn(move || {
        recv_frame::<_, IpcRequest>(&mut server_sock).unwrap();
        send_frame(&mut server_sock, &IpcResponse::Err(response)).unwrap();
    });
    let mut client = IpcExecutorClient::from_stream(client_sock);
    assert_eq!(client.execute_action(&auth, &f.intent, &f.policy, 0), Err(expected));
    drop(client);
    handle.join().unwrap();
}

#[test]
fn test_ipc_request_without_client_timestamp_is_accepted_and_checked() {
    let mut f = tests::fixture();
    f.intent.parameters = b"EXPIRED_EFFECT".to_vec();
    let mut resource = Vec::new();
    let mut payload = tests::payload(&f, 107);
    payload.resource_precondition_digest = ByteLogAdapter.compute_precondition(&resource).unwrap();
    payload.expires_at = 1;
    let request = IpcRequest::ExecuteAction {
        auth: tests::sign(&f, payload), intent: f.intent, policy: f.policy, timestamp: 0,
    };
    let mut wire = serde_json::to_value(request).unwrap();
    wire["ExecuteAction"].as_object_mut().unwrap().remove("timestamp");
    let executor = SovereignExecutor::new(
        tests::INST, tests::EXEC, 1,
        vec![AdmittedAuthority { public_key: f.pk, algorithm: AuthorityAlgorithm::Ed25519 }],
        DurableExecutionStore::open_in_memory_non_durable().unwrap(), ByteLogAdapter,
    );
    let mut server = IpcExecutorServer::new(executor);
    let (server_sock, mut client_sock) = UnixStream::pair().unwrap();
    let handle = std::thread::spawn(move || {
        server.handle_client(server_sock, &mut resource).unwrap();
        resource
    });
    send_frame(&mut client_sock, &wire).unwrap();
    match recv_frame::<_, IpcResponse>(&mut client_sock).unwrap() {
        IpcResponse::Err(error) => assert_eq!(error, ExecutionError::AuthorizationExpired),
        other => panic!("expired request was not rejected: {other:?}"),
    }
    drop(client_sock);
    assert!(handle.join().unwrap().is_empty());
}

struct ByteLogAdapter;
impl EffectAdapter for ByteLogAdapter {
    type Resource = Vec<Vec<u8>>;
    type Effect = Vec<u8>;
    type Output = Vec<u8>;
    type Error = SyntheticError;

    fn parse_intent(&self, intent: &ProposedIntent) -> Result<Self::Effect, Self::Error> {
        Ok(intent.parameters.clone())
    }

    fn compute_precondition(&self, r: &Self::Resource) -> Result<[u8; 32], Self::Error> {
        let mut h = CanonicalHasher::new(b"byte-log");
        for entry in r {
            h = h.field(entry);
        }
        Ok(h.finish())
    }

    fn apply_effect(
        &mut self,
        r: &mut Self::Resource,
        expected: &[u8; 32],
        _nonce: &[u8; 32],
        effect: &Self::Effect,
    ) -> Result<Self::Output, Self::Error> {
        if &self.compute_precondition(r)? != expected {
            return Err(SyntheticError::PreconditionMismatch);
        }
        r.push(effect.clone());
        Ok(effect.clone())
    }

    fn idempotency_contract(&self) -> IdempotencyContract {
        IdempotencyContract::NonIdempotentExplicitIntervention
    }
}

/// Escenario 1: Un worker EDIN desprivilegiado no puede ejecutar efectos protegidos sin clave admitida.
#[test]
pub fn test_scenario_1_edin_executes_directly_denied() {
    let f = tests::fixture();
    let rogue = ed25519_dalek::SigningKey::generate(&mut rand::rngs::OsRng);
    let p = tests::payload(&f, 100);
    let rogue_signer = crate::receipt::Ed25519Signer::from_signing_key(rogue);
    let unadmitted_auth = SignedAuthorization::new_cose(&p, &rogue_signer).unwrap();

    let (server_sock, client_sock) = UnixStream::pair().unwrap();
    let mut resource: Vec<Vec<u8>> = Vec::new();
    let store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    let executor = SovereignExecutor::new(
        tests::INST,
        tests::EXEC,
        1,
        vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        ByteLogAdapter,
    );

    let mut server = IpcExecutorServer::new(executor);
    let handle = std::thread::spawn(move || {
        server.handle_client(server_sock, &mut resource).unwrap();
        resource
    });

    let mut client = IpcExecutorClient::from_stream(client_sock);
    client.ping().unwrap();

    let res = client.execute_action(&unadmitted_auth, &f.intent, &f.policy, 1000);
    assert!(matches!(res, Err(ExecutionError::InvalidAuthorityKey(_))));

    drop(client);
    let final_resource = handle.join().unwrap();
    assert!(final_resource.is_empty(), "El recurso protegido no fue alterado");
}

/// Escenario 2: Un cliente IPC con autorización COSE válida ejecuta la mutación en el executor.
#[test]
pub fn test_scenario_2_valid_ipc_execution_succeeds() {
    let mut f = tests::fixture();
    f.intent.parameters = b"MUTATION_EFFECT".to_vec();
    let (server_sock, client_sock) = UnixStream::pair().unwrap();
    let mut resource: Vec<Vec<u8>> = Vec::new();
    let pre = ByteLogAdapter.compute_precondition(&resource).unwrap();
    
    let mut p = tests::payload(&f, 101);
    p.resource_precondition_digest = pre;
    let auth = tests::sign(&f, p);

    let store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    let executor = SovereignExecutor::new(
        tests::INST,
        tests::EXEC,
        1,
        vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        ByteLogAdapter,
    );

    let mut server = IpcExecutorServer::new(executor);
    let handle = std::thread::spawn(move || {
        server.handle_client(server_sock, &mut resource).unwrap();
        resource
    });

    let mut client = IpcExecutorClient::from_stream(client_sock);
    let res = client.execute_action(&auth, &f.intent, &f.policy, 1000);
    assert_eq!(res.unwrap(), b"MUTATION_EFFECT");

    drop(client);
    let final_resource = handle.join().unwrap();
    assert_eq!(final_resource, vec![b"MUTATION_EFFECT".to_vec()]);
}

/// Escenario 3: Replay de autorización vía IPC es rechazado con NonceAlreadyConsumed.
#[test]
pub fn test_scenario_3_replay_via_ipc_rejected() {
    let mut f = tests::fixture();
    f.intent.parameters = b"FIRST_CALL".to_vec();
    let (server_sock, client_sock) = UnixStream::pair().unwrap();
    let mut resource: Vec<Vec<u8>> = Vec::new();
    let pre = ByteLogAdapter.compute_precondition(&resource).unwrap();
    
    let mut p = tests::payload(&f, 102);
    p.resource_precondition_digest = pre;
    let auth = tests::sign(&f, p);

    let store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    let executor = SovereignExecutor::new(
        tests::INST,
        tests::EXEC,
        1,
        vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        ByteLogAdapter,
    );

    let mut server = IpcExecutorServer::new(executor);
    let handle = std::thread::spawn(move || {
        server.handle_client(server_sock, &mut resource).unwrap();
        resource
    });

    let mut client = IpcExecutorClient::from_stream(client_sock);
    let res1 = client.execute_action(&auth, &f.intent, &f.policy, 1000);
    assert_eq!(res1.unwrap(), b"FIRST_CALL");

    let res2 = client.execute_action(&auth, &f.intent, &f.policy, 1001);
    assert!(matches!(res2, Err(ExecutionError::NonceAlreadyConsumed(_))));

    drop(client);
    let final_resource = handle.join().unwrap();
    assert_eq!(final_resource.len(), 1);
}
