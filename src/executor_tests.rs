use super::*;

pub(crate) const INST: [u8; 32] = [0x11; 32];
pub(crate) const EXEC: [u8; 32] = [0x22; 32];

#[test]
fn security_malformed_reservation_returns_error_without_panicking() {
    let mut store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    let auth = SignedAuthorization { cose_bytes: vec![0xff] };
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(||
        store.reserve_and_consume_nonce(&auth, false, 1000)));
    assert!(result.is_ok(), "untrusted COSE caused a panic");
    assert!(result.unwrap().is_err());
}

#[test]
fn security_cose_rejects_unprotected_authority_key_id() {
    use coset::{CborSerializable, CoseSign1Builder, HeaderBuilder};
    use ed25519_dalek::Signer as _;

    let f = fixture();
    let mut executor = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());

    for (nonce, protected_kid) in [(158, None), (159, Some(vec![0x99; 32]))] {
        let payload = payload(&f, nonce);
        let protected = HeaderBuilder::new()
            .algorithm(coset::iana::Algorithm::EdDSA)
            .key_id(protected_kid.unwrap_or_default())
            .build();
        let unprotected = HeaderBuilder::new().key_id(f.pk.clone()).build();
        let sign1 = CoseSign1Builder::new()
            .protected(protected)
            .unprotected(unprotected)
            .payload(payload.to_canonical_bytes().to_vec())
            .try_create_signature(&[], |data| Ok::<_, core::convert::Infallible>(
                f.sk.sign(data).to_bytes().to_vec(),
            ))
            .unwrap()
            .build();
        let auth = SignedAuthorization { cose_bytes: sign1.to_vec().unwrap() };
        let mut resource = f.resource.clone();
        assert_eq!(
            executor.execute_action(&auth, &f.intent, &f.policy, &mut resource, 1000),
            Err(ExecutionError::MalformedAuthorization("unsupported COSE header profile".into())),
        );
        assert_eq!(resource, f.resource);
        assert!(!executor.store.is_nonce_consumed(&payload.nonce, false).unwrap());
    }
}

#[test]
fn security_cose_rejects_unhandled_critical_headers() {
    use coset::{CborSerializable, CoseSign1Builder, HeaderBuilder, RegisteredLabel};
    use ed25519_dalek::Signer as _;

    let f = fixture();
    let mut executor = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());

    for (nonce, critical_header_is_protected) in [(160, true), (161, false)] {
        let payload = payload(&f, nonce);
        let critical = |header: HeaderBuilder| {
            header.add_critical_label(RegisteredLabel::Text("unhandled".into())).build()
        };
        let protected_builder = HeaderBuilder::new()
            .algorithm(coset::iana::Algorithm::EdDSA)
            .key_id(f.pk.clone());
        let (protected, unprotected) = if critical_header_is_protected {
            (critical(protected_builder), HeaderBuilder::new().build())
        } else {
            (protected_builder.build(), critical(HeaderBuilder::new()))
        };
        let sign1 = CoseSign1Builder::new()
            .protected(protected)
            .unprotected(unprotected)
            .payload(payload.to_canonical_bytes().to_vec())
            .try_create_signature(&[], |data| Ok::<_, core::convert::Infallible>(
                f.sk.sign(data).to_bytes().to_vec(),
            ))
            .unwrap()
            .build();
        let auth = SignedAuthorization { cose_bytes: sign1.to_vec().unwrap() };
        let mut resource = f.resource.clone();

        assert_eq!(
            executor.execute_action(&auth, &f.intent, &f.policy, &mut resource, 1000),
            Err(ExecutionError::MalformedAuthorization("unsupported COSE header profile".into())),
        );
        assert_eq!(resource, f.resource);
        assert!(!executor.store.is_nonce_consumed(&payload.nonce, false).unwrap());
    }
}

#[test]
fn security_cose_rejects_missing_or_wrong_length_payload() {
    use coset::{CborSerializable, CoseSign1Builder, HeaderBuilder};

    let f = fixture();
    for payload_bytes in [None, Some(vec![0; AUTHORIZATION_PAYLOAD_CANONICAL_SIZE - 1])] {
        let protected = HeaderBuilder::new()
            .algorithm(coset::iana::Algorithm::EdDSA)
            .key_id(f.pk.clone())
            .build();
        let mut builder = CoseSign1Builder::new()
            .protected(protected)
            .signature(vec![0; 64]);
        if let Some(payload) = payload_bytes {
            builder = builder.payload(payload);
        }
        let auth = SignedAuthorization {
            cose_bytes: builder.build().to_vec().unwrap(),
        };
        assert!(auth.parse().is_err());
    }
}

#[test]
fn security_future_authority_epoch_cannot_execute() {
    let f = fixture();
    let mut p = payload(&f, 151);
    p.authority_epoch = 2;
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut resource = f.resource.clone();
    assert!(ex.execute_action(&sign(&f, p), &f.intent, &f.policy, &mut resource, 1000).is_err());
    assert_eq!(resource, f.resource);
}

#[test]
fn security_revoked_epoch_cannot_reach_effect() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 152));
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    ex.authority_epoch_gate.revoke_to(2).unwrap();
    let mut resource = f.resource.clone();

    assert_eq!(
        ex.execute_action(&auth, &f.intent, &f.policy, &mut resource, 1000),
        Err(ExecutionError::AuthorityEpochRevoked),
    );
    assert_eq!(resource, f.resource);
}

#[test]
fn authority_revocation_waits_for_effect_commit_and_then_advances() {
    use std::sync::mpsc;
    use std::time::Duration;

    let gate = Arc::new(AuthorityEpochGate::new(1));
    let mut current = 1;
    for _ in 0..32 {
        let effect_guard = gate.lock_for_effect(current).unwrap();
        let writer_gate = Arc::clone(&gate);
        let next = current + 1;
        let (started_tx, started_rx) = mpsc::channel();
        let (result_tx, result_rx) = mpsc::channel();
        let writer = std::thread::spawn(move || {
            started_tx.send(()).unwrap();
            result_tx.send(writer_gate.revoke_to(next)).unwrap();
        });

        started_rx.recv_timeout(Duration::from_secs(1)).unwrap();
        assert!(result_rx.recv_timeout(Duration::from_millis(20)).is_err(),
            "revocation must wait while a valid effect holds the commit gate");
        drop(effect_guard);
        result_rx.recv_timeout(Duration::from_secs(1)).unwrap().unwrap();
        writer.join().unwrap();

        assert_eq!(gate.current_epoch(), next);
        assert!(matches!(gate.lock_for_effect(current), Err(ExecutionError::AuthorityEpochRevoked)));
        current = next;
    }
    assert_eq!(
        gate.revoke_to(current),
        Err(ExecutionError::AuthorityEpochNotMonotonic { current, requested: current }),
    );
}

#[test]
fn security_reservation_identity_and_replay_history_are_immutable() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 152));
    let mut store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    store.reserve_and_consume_nonce(&auth, false, 1000).unwrap();
    for sql in ["UPDATE durable_reservations SET intent_digest=zeroblob(32)",
                "UPDATE durable_reservations SET authorization_blob=x'00'",
                "DELETE FROM durable_reservations"] {
        assert!(store.conn.execute_batch(sql).is_err(), "immutable history was modified: {sql}");
    }
    assert!(store.reserve_and_consume_nonce(&auth, false, 1001).is_err());
}

#[test]
fn security_reservation_transitions_cannot_rewind() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 154));
    let nonce = [154; 32];
    let mut store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    store.reserve_and_consume_nonce(&auth, false, 1000).unwrap();
    assert!(store.conn.execute_batch("UPDATE durable_reservations SET state='EXECUTED'").is_err());
    store.record_dispatch(&nonce, 1000).unwrap();
    assert!(store.conn.execute_batch("UPDATE durable_reservations SET state='RESERVED'").is_err());
    store.record_completion(&nonce, b"OK", 1000).unwrap();
    assert!(store.conn.execute_batch("UPDATE durable_reservations SET result_payload=x'00'").is_err());
    assert!(store.conn.execute_batch("UPDATE durable_reservations SET state='UNKNOWN'").is_err());
}

#[test]
fn security_expiry_after_dispatch_still_prevents_effect() {
    let f = fixture();
    let mut p = payload(&f, 155);
    p.expires_at = 1001;
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut resource = f.resource.clone();
    let mut times = [1000, 1000, 1002].into_iter();
    let result = ex.execute_with_clock(&sign(&f, p), &f.intent, &f.policy, &mut resource,
        &mut || Ok(times.next().expect("unexpected clock read")));
    assert_eq!(result, Err(ExecutionError::AuthorizationExpired));
    assert_eq!(resource, f.resource);
    assert!(ex.store.is_nonce_consumed(&[155; 32], false).unwrap());
}

#[test]
fn security_expiry_is_checked_after_acquiring_sqlite_write_lock() {
    struct Cleanup(std::path::PathBuf);
    impl Drop for Cleanup {
        fn drop(&mut self) { let _ = std::fs::remove_dir_all(&self.0); }
    }
    let f = fixture();
    let db = tmp_db("security_expiry");
    let _cleanup = Cleanup(std::path::Path::new(&db).parent().unwrap().to_owned());
    let mut ex = executor(&f, DurableExecutionStore::open(&db).unwrap());
    let mut p = payload(&f, 153);
    p.expires_at = unix_seconds_from_host_time(std::time::SystemTime::now()).unwrap() + 1;
    let auth = sign(&f, p);
    let blocker = rusqlite::Connection::open(&db).unwrap();
    blocker.execute_batch("BEGIN IMMEDIATE").unwrap();
    let release = std::thread::spawn(move || {
        std::thread::sleep(std::time::Duration::from_millis(2200));
        blocker.execute_batch("COMMIT").unwrap();
    });
    let mut resource = f.resource.clone();
    let result = ex.execute_action_with_host_clock(&auth, &f.intent, &f.policy, &mut resource);
    release.join().unwrap();
    assert_eq!(result, Err(ExecutionError::AuthorizationExpired));
    assert_eq!(resource, f.resource);
    assert!(!ex.store.is_nonce_consumed(&[153; 32], false).unwrap());
}

pub(crate) struct Fixture {
    pub(crate) sk: ed25519_dalek::SigningKey,
    pub(crate) pk: Vec<u8>,
    pub(crate) policy: SecurityPolicy,
    pub(crate) intent: ProposedIntent,
    pub(crate) resource: SyntheticResource,
}

pub(crate) fn fixture() -> Fixture {
    let sk = ed25519_dalek::SigningKey::generate(&mut rand::rngs::OsRng);
    let pk = sk.verifying_key().to_bytes().to_vec();
    Fixture {
        policy: SecurityPolicy {
            policy_id: [0xAA; 32],
            allowed_action: "ADD".into(),
            max_allowed_uses: 1,
            admitted_authority_key: pk.clone(),
        },
        intent: ProposedIntent {
            intent_id: [0xBB; 32],
            target_resource: "acct".into(),
            action_name: "ADD".into(),
            parameters: 250u64.to_be_bytes().to_vec(),
        },
        resource: SyntheticResource::new("acct", 1000),
        sk,
        pk,
    }
}

pub(crate) fn sign(f: &Fixture, payload: AuthorizationPayload) -> SignedAuthorization {
    let signer = crate::receipt::Ed25519Signer::from_signing_key(f.sk.clone());
    SignedAuthorization::new_cose(&payload, &signer).unwrap()
}

pub(crate) fn payload(f: &Fixture, nonce: u8) -> AuthorizationPayload {
    AuthorizationPayload {
        protocol_version: PROTOCOL_VERSION,
        installation_id: INST,
        executor_id: EXEC,
        intent_digest: f.intent.compute_digest(),
        policy_digest: f.policy.compute_digest(),
        resource_precondition_digest: SyntheticEffectAdapter.compute_precondition(&f.resource).unwrap(),
        nonce: [nonce; 32],
        authority_epoch: 1,
        expires_at: 2_000_000_000,
        max_uses: 1,
    }
}

pub(crate) fn executor(f: &Fixture, store: DurableExecutionStore) -> SovereignExecutor<SyntheticEffectAdapter> {
    SovereignExecutor::new(
        INST,
        EXEC,
        1,
        vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        SyntheticEffectAdapter,
    )
}

pub(crate) fn tmp_db(tag: &str) -> String {
    let n = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
    let dir = std::env::temp_dir().join(format!("b60_exec_{}_{}_{}", tag, std::process::id(), n));
    std::fs::create_dir_all(&dir).unwrap();
    dir.join("ledger.sqlite").to_string_lossy().into_owned()
}

#[test]
fn canonical_payload_roundtrip_is_214_bytes() {
    let f = fixture();
    let p = payload(&f, 1);
    let b = p.to_canonical_bytes();
    assert_eq!(b.len(), 214);
    assert_eq!(AuthorizationPayload::from_canonical_bytes(&b).unwrap(), p);
    assert!(AuthorizationPayload::from_canonical_bytes(&b[..213]).is_err());
    let mut longer = b.to_vec();
    longer.push(0);
    assert!(AuthorizationPayload::from_canonical_bytes(&longer).is_err());
}

#[test]
fn digest_is_unambiguous_under_field_shift() {
    let a = ProposedIntent { intent_id: [0; 32], target_resource: "ab".into(), action_name: "c".into(), parameters: vec![] };
    let b = ProposedIntent { intent_id: [0; 32], target_resource: "a".into(), action_name: "bc".into(), parameters: vec![] };
    assert_ne!(a.compute_digest(), b.compute_digest());
}

#[test]
fn unadmitted_key_cannot_authorize() {
    // Un proponente que fabrica y firma su propia autorización posee una clave,
    // no autoridad: la clave no está admitida.
    let f = fixture();
    let rogue = ed25519_dalek::SigningKey::generate(&mut rand::rngs::OsRng);
    let p = payload(&f, 1);
    let rogue_signer = crate::receipt::Ed25519Signer::from_signing_key(rogue);
    let auth = SignedAuthorization::new_cose(&p, &rogue_signer).unwrap();
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut r = f.resource.clone();
    let res = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000);
    assert!(matches!(res, Err(ExecutionError::InvalidAuthorityKey(_))));
    assert_eq!(r, f.resource, "resource must be untouched");
}

#[test]
fn replay_rejected_after_reopening_file_ledger() {
    let f = fixture();
    let db = tmp_db("replay");
    let auth = sign(&f, payload(&f, 2));
    let mut r = f.resource.clone();
    {
        let mut ex = executor(&f, DurableExecutionStore::open(&db).unwrap());
        assert_eq!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000).unwrap(), 1250);
    } // conexión cerrada
    let mut ex = executor(&f, DurableExecutionStore::open(&db).unwrap());
    ex.store.reconcile_on_startup().unwrap();
    let res = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1001);
    assert!(matches!(res, Err(ExecutionError::NonceAlreadyConsumed(_))));
    assert_eq!(r.state_counter, 1250);
}

#[test]
fn tampered_intent_or_policy_rejected() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 3));
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut r = f.resource.clone();

    let mut ti = f.intent.clone();
    ti.parameters = 999_999u64.to_be_bytes().to_vec();
    assert_eq!(ex.execute_action(&auth, &ti, &f.policy, &mut r, 1000), Err(ExecutionError::IntentDigestMismatch));

    let mut tp = f.policy.clone();
    tp.allowed_action = "DROP".into();
    assert_eq!(ex.execute_action(&auth, &f.intent, &tp, &mut r, 1000), Err(ExecutionError::PolicyDigestMismatch));
}

#[test]
fn policy_binding_enforced_even_with_valid_signature() {
    let mut f = fixture();
    // La autoridad firma correctamente una intención cuya acción la política no permite.
    f.intent.action_name = "DELETE".into();
    let auth = sign(&f, payload(&f, 4));
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut r = f.resource.clone();
    assert_eq!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::PolicyActionMismatch));
}

#[test]
fn security_authorization_is_expired_at_exclusive_boundary() {
    let f = fixture();
    let mut p = payload(&f, 156);
    p.expires_at = 1000;
    let auth = sign(&f, p);
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut resource = f.resource.clone();
    let result = ex.execute_action(&auth, &f.intent, &f.policy, &mut resource, 1000);
    assert_eq!(result, Err(ExecutionError::AuthorizationExpired));
    assert_eq!(resource, f.resource);
    assert!(!ex.store.is_nonce_consumed(&[156; 32], false).unwrap());
}

#[test]
fn unsupported_profile_parameters_rejected() {
    let f = fixture();
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut r = f.resource.clone();
    let mut p = payload(&f, 5);
    p.max_uses = 2;
    assert_eq!(ex.execute_action(&sign(&f, p), &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::UnsupportedMaxUses(2)));
    let mut p = payload(&f, 6);
    p.protocol_version = 4;
    assert_eq!(ex.execute_action(&sign(&f, p), &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::UnsupportedProtocolVersion(4)));
    let p = payload(&f, 7);
    assert_eq!(ex.execute_action(&sign(&f, p), &f.intent, &f.policy, &mut r, 2_000_000_001), Err(ExecutionError::AuthorizationExpired));
}

#[test]
fn algorithm_is_pinned_per_key() {
    let f = fixture();
    struct FakeP256Signer(Vec<u8>);
    impl crate::receipt::Signer for FakeP256Signer {
        fn get_public_key(&self) -> Vec<u8> { self.0.clone() }
        fn algorithm(&self) -> coset::iana::Algorithm { coset::iana::Algorithm::ES256 }
        fn sign(&self, _data: &[u8]) -> Result<Vec<u8>, alloc::string::String> { Ok(vec![0; 64]) }
        fn verify(&self, _payload: &[u8], _signature: &[u8]) -> bool { false }
    }
    let p = payload(&f, 8);
    let signer = FakeP256Signer(f.pk.clone());
    let auth = SignedAuthorization::new_cose(&p, &signer).unwrap();
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut r = f.resource.clone();
    assert!(matches!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::InvalidAuthorityKey(_))));
}

#[test]
fn substituted_resource_rejected() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 9));
    let mut r = f.resource.clone();
    r.state_counter = 5000;
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    assert_eq!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::PreconditionMismatch));
    assert!(!ex.store.is_nonce_consumed(&auth.parse().unwrap().0.nonce, false).unwrap(), "rejected before reservation");
}

#[test]
fn interrupted_after_dispatch_becomes_unknown_on_reopen() {
    let f = fixture();
    let db = tmp_db("unknown");
    let auth = sign(&f, payload(&f, 10));
    let mut r = f.resource.clone();
    {
        let mut ex = executor(&f, DurableExecutionStore::open(&db).unwrap())
            .with_crash(CrashPoint::AfterDispatchBeforeEffect, CrashAction::ReturnError);
        assert_eq!(
            ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000),
            Err(ExecutionError::Interrupted(CrashPoint::AfterDispatchBeforeEffect))
        );
    }
    let mut store = DurableExecutionStore::open(&db).unwrap();
    assert_eq!(store.reconcile_on_startup().unwrap(), vec![auth.parse().unwrap().0.nonce]);
    assert_eq!(store.get_record(&auth.parse().unwrap().0.nonce).unwrap().unwrap().state, ReservationState::Unknown);
    let mut ex = executor(&f, store);
    assert!(matches!(
        ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1002),
        Err(ExecutionError::NonceAlreadyConsumed(_))
    ));
}

#[test]
fn corrupted_signature_rejected() {
    let f = fixture();
    let mut auth = sign(&f, payload(&f, 11));
    let len = auth.cose_bytes.len();
    auth.cose_bytes[len - 2] ^= 0xFF;
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    let mut r = f.resource.clone();
    assert!(matches!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::InvalidSignature(_))));
}

#[test]
fn storage_failure_is_fail_closed() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 12));
    let store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    store.conn.execute("DROP TABLE durable_reservations", []).unwrap();
    let mut ex = executor(&f, store);
    let mut r = f.resource.clone();
    assert!(matches!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::StorageError(_))));
    assert_eq!(r, f.resource);
}

#[test]
fn poisoned_executor_admits_nothing() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 13));
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    ex.poison();
    let mut r = f.resource.clone();
    assert_eq!(ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000), Err(ExecutionError::ExecutorPoisoned));
}

#[test]
fn test_authorization_with_p256() {
    let mut f = fixture();
    let p256_signer = crate::receipt::P256Signer::new();
    let pub_key = crate::receipt::Signer::get_public_key(&p256_signer);
    
    // Update the policy first so that payload() captures the correct digest!
    f.policy.admitted_authority_key = pub_key.clone();
    
    let p = payload(&f, 42);
    let auth = SignedAuthorization::new_cose(&p, &p256_signer).expect("failed to sign P-256");
    
    let mut ex = executor(&f, DurableExecutionStore::open_in_memory_non_durable().unwrap());
    // We override the default admitted authority in the executor with our new one
    ex.admitted_authorities = vec![AdmittedAuthority {
        public_key: pub_key.clone(),
        algorithm: AuthorityAlgorithm::P256,
    }];
    
    let mut r = f.resource.clone();
    let res = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000);
    assert!(res.is_ok(), "P-256 authorization should succeed, got {:?}", res.err());
}

#[test]
fn reserved_entry_stays_blocked_against_replay() {
    let f = fixture();
    let auth = sign(&f, payload(&f, 50));
    let store = DurableExecutionStore::open_in_memory_non_durable().unwrap();
    
    // Simular que una ejecución previa falló justo después del reserve
    // Insertamos manualmente el estado RESERVED.
    let p = &auth.parse().unwrap().0;
    store.conn.execute(
        "INSERT INTO durable_reservations
             (nonce, intent_digest, policy_digest, precondition_digest, authorization_blob, state, created_at)
         VALUES (?1, ?2, ?3, ?4, ?5, 'RESERVED', ?6)",
        rusqlite::params![
            &p.nonce[..],
            &p.intent_digest[..],
            &p.policy_digest[..],
            &p.resource_precondition_digest[..],
            auth.archive_blob(),
            1000_i64
        ],
    ).unwrap();
    
    // Ahora instanciamos el executor e intentamos ejecutar
    let mut ex = executor(&f, store);
    let mut r = f.resource.clone();
    
    let res = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000);
    assert!(matches!(res, Err(ExecutionError::NonceAlreadyConsumed(_))));
    assert_eq!(r, f.resource, "resource must be untouched");
}

// -- Adaptador VerifiableIdempotent para Test --
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdempotentResource {
    pub state_counter: u64,
    pub processed_nonces: std::collections::HashSet<[u8; 32]>,
}

#[derive(Debug, Default)]
pub struct IdempotentAdapter;

impl EffectAdapter for IdempotentAdapter {
    type Resource = IdempotentResource;
    type Effect = u64;
    type Output = u64;
    type Error = SyntheticError;
    
    fn parse_intent(&self, intent: &ProposedIntent) -> Result<Self::Effect, Self::Error> {
        if intent.parameters.len() != 8 {
            return Err(SyntheticError::Overflow);
        }
        let mut buf = [0u8; 8];
        buf.copy_from_slice(&intent.parameters);
        Ok(u64::from_be_bytes(buf))
    }

    fn compute_precondition(&self, _r: &Self::Resource) -> Result<[u8; 32], Self::Error> {
        // Precondición estable (no cambia tras mutar)
        Ok(CanonicalHasher::new(b"stable_precondition").finish())
    }
    
    fn apply_effect(
        &mut self,
        r: &mut Self::Resource,
        _expected: &[u8; 32],
        nonce: &[u8; 32],
        delta: &u64,
    ) -> Result<u64, SyntheticError> {
        // Idempotencia por clave (nonce)
        if r.processed_nonces.contains(nonce) {
            return Ok(r.state_counter); // Ya procesado, no hacer nada
        }
        r.state_counter += delta;
        r.processed_nonces.insert(*nonce);
        Ok(r.state_counter)
    }
    
    fn idempotency_contract(&self) -> IdempotencyContract {
        IdempotencyContract::VerifiableIdempotent
    }
}

#[test]
fn verifiable_idempotent_adapter_allows_unknown_retry() {
    let mut f = fixture();
    f.intent.parameters = 50u64.to_be_bytes().to_vec();
    let db = tmp_db("idempotent");
    let mut r = IdempotentResource { state_counter: 100, processed_nonces: std::collections::HashSet::new() };
    let mut p = payload(&f, 10);
    p.resource_precondition_digest = IdempotentAdapter.compute_precondition(&r).unwrap();
    let auth = sign(&f, p);
    
    {
        // Instanciar executor pero inyectarle un IdempotentAdapter
        let mut ex = SovereignExecutor {
            installation_id: INST,
            executor_id: EXEC,
            authority_epoch_gate: Arc::new(AuthorityEpochGate::new(1)),
            is_poisoned: std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false)),
            admitted_authorities: vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
            store: DurableExecutionStore::open(&db).unwrap(),
            adapter: IdempotentAdapter,
            crash_point: CrashPoint::AfterDispatchBeforeEffect,
            crash_action: CrashAction::ReturnError,
        };
        
        // Va a crashear en AfterDispatchBeforeEffect (estado DISPATCHED)
        let res = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 1000);
        assert_eq!(res, Err(ExecutionError::Interrupted(CrashPoint::AfterDispatchBeforeEffect)));
    }
    
    // El recurso mutante NO se modificó (crasheó antes)
    assert_eq!(r.state_counter, 100);
    
    // Al reiniciar, reconcile convierte DISPATCHED a UNKNOWN
    let mut ex = SovereignExecutor {
        installation_id: INST,
        executor_id: EXEC,
        authority_epoch_gate: Arc::new(AuthorityEpochGate::new(1)),
        is_poisoned: std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false)),
        admitted_authorities: vec![AdmittedAuthority { public_key: f.pk.clone(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store: DurableExecutionStore::open(&db).unwrap(),
        adapter: IdempotentAdapter,
        crash_point: CrashPoint::None,
        crash_action: CrashAction::ReturnError,
    };
    
    let unknowns = ex.store.reconcile_on_startup().unwrap();
    assert_eq!(unknowns.len(), 1);
    
    // Ahora reintentamos EXACTAMENTE el mismo payload (mismo nonce)
    // Como el adapter es VerifiableIdempotent, debe permitirlo!
    let res = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 2000);
    assert!(res.is_ok(), "Debe reanudar una ejecución UNKNOWN porque es VerifiableIdempotent, error: {:?}", res.err());
    
    // El efecto se aplicó (100 + 50)
    assert_eq!(r.state_counter, 150);
    
    // Si lo ejecutamos de nuevo (otra vez), el Adapter deduplicará pero el executor nos frenará!
    // Wait, si el executor nos frena, es porque el estado es EXECUTED.
    // is_nonce_consumed returna true si state NO ES (RESERVED o UNKNOWN). EXECUTED entra en ese caso.
    let res2 = ex.execute_action(&auth, &f.intent, &f.policy, &mut r, 3000);
    assert!(matches!(res2, Err(ExecutionError::NonceAlreadyConsumed(_))));
    
    // El mutante sigue con 150
    assert_eq!(r.state_counter, 150);
}
