//! Isolated tests: ephemeral software keys do not attest Secure Enclave hardware.
#![cfg(unix)]
use babylon60::acs_bridge::authenticated::*;
use babylon60::acs_bridge::*;
use babylon60::ontology::babylon::*;
use ed25519_dalek::{Signer, SigningKey};
use std::os::unix::fs::PermissionsExt;
use std::os::unix::net::UnixStream;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Lab(PathBuf);
impl Lab {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "acs-auth-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o700)).unwrap();
        Self(path)
    }
    fn ledger(&self) -> PathBuf {
        self.0.join("nonces")
    }
}
impl Drop for Lab {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

struct Setup {
    root: SigningKey,
    key: SigningKey,
}
impl Setup {
    fn new() -> Self {
        Self {
            root: SigningKey::generate(&mut rand::rngs::OsRng),
            key: SigningKey::generate(&mut rand::rngs::OsRng),
        }
    }
    fn raw(&self) -> BabylonAcsGuard {
        BabylonAcsGuard::new(
            Authority {
                authority_id: [1; 32],
                principal_type: PrincipalType::DelegatedRole,
                public_key: self.root.verifying_key().to_bytes(),
                active_epoch: 7,
            },
            Capability {
                capability_id: [2; 32],
                issuer_authority_id: [1; 32],
                target_resource: "file:///allowed".into(),
                allowed_effects: vec![EffectKind::FsRead, EffectKind::FsMutate],
                valid_until_epoch: 7,
                signature: vec![],
            },
            Policy {
                policy_id: "acs_scoped_read_v1".into(),
                version: "1".into(),
                predicate_digest: [3; 32],
                enforcement_mode: EnforcementMode::FailClosed,
            },
            // Deliberately fictitious descriptor: authenticated API must use the real socket instead.
            AcsTransportConfinement::AfUnixPeerVerified {
                socket_path: "/fictional".into(),
                peer_euid: 99999,
                peer_pid: 99999,
            },
            FailureDecisionPolicy::FailClosedAbort,
            100,
            10,
            true,
        )
        .unwrap()
    }
    fn root_key(&self) -> VerificationKey {
        VerificationKey::Ed25519(self.root.verifying_key().to_bytes())
    }
    fn key(&self) -> VerificationKey {
        VerificationKey::Ed25519(self.key.verifying_key().to_bytes())
    }
    fn provision(&self, store: DurableNonces) -> AuthenticatedAcsGuard {
        self.provision_key(
            store,
            self.key(),
            unsafe { libc::geteuid() },
            std::process::id(),
        )
    }
    fn provision_key(
        &self,
        store: DurableNonces,
        key: VerificationKey,
        uid: u32,
        pid: u32,
    ) -> AuthenticatedAcsGuard {
        let g = self.raw();
        let grant = self.root.sign(&provisioning_bytes(
            &g,
            &self.root_key(),
            &key,
            uid,
            pid,
            120,
        ));
        AuthenticatedAcsGuard::provision(
            g,
            self.root_key(),
            key,
            uid,
            pid,
            120,
            &grant.to_bytes(),
            store,
        )
        .unwrap()
    }
    fn call(&self, guard: &AuthenticatedAcsGuard) -> SignedCall {
        let mut c = unsigned_call();
        c.request.signature = self.key.sign(&guard.signing_bytes(&c)).to_bytes().to_vec();
        c
    }
}
fn unsigned_call() -> SignedCall {
    SignedCall {
        request: AcsToolCallRequest {
            acs_version: ACS_PROTOCOL_VERSION.into(),
            request_id: [4; 32],
            nonce: [5; 32],
            tool_name: "fs_read".into(),
            arguments: "file:///allowed/data".into(),
            target_uri: "file:///allowed/data".into(),
            client_logical_tick: 100,
            context_digest: [6; 32],
            signature: vec![],
        },
        epoch: 7,
        expires_at_tick: 110,
    }
}

#[test]
fn valid_ed25519_and_replay_after_reopen() {
    let lab = Lab::new();
    let s = Setup::new();
    let mut guard = s.provision(DurableNonces::create(lab.ledger()).unwrap());
    let call = s.call(&guard);
    let (socket, _peer) = UnixStream::pair().unwrap();
    assert_eq!(
        guard.evaluate(&socket, &call, 100, 7).unwrap().outcome,
        DecisionOutcome::Allow
    );
    drop(guard);
    let mut restarted = s.provision(DurableNonces::open(lab.ledger()).unwrap());
    assert_eq!(
        restarted.evaluate(&socket, &call, 100, 7).unwrap_err(),
        AcsBridgeError::NonceReplayDetected([5; 32])
    );
}

#[test]
fn complete_request_payload_is_bound() {
    let lab = Lab::new();
    let s = Setup::new();
    let store = DurableNonces::create(lab.ledger()).unwrap();
    let base = s.provision(store.clone());
    let call = s.call(&base);
    let mut variants = vec![];
    let mut c = call.clone();
    c.request.acs_version.push('x');
    variants.push(c);
    let mut c = call.clone();
    c.request.request_id[0] ^= 1;
    variants.push(c);
    let mut c = call.clone();
    c.request.nonce[0] ^= 1;
    variants.push(c);
    let mut c = call.clone();
    c.request.tool_name = "read_file".into();
    variants.push(c);
    let mut c = call.clone();
    c.request.arguments.push('x');
    variants.push(c);
    let mut c = call.clone();
    c.request.target_uri.push('x');
    variants.push(c);
    let mut c = call.clone();
    c.request.client_logical_tick += 1;
    variants.push(c);
    let mut c = call.clone();
    c.request.context_digest[0] ^= 1;
    variants.push(c);
    let mut c = call.clone();
    c.epoch += 1;
    variants.push(c);
    let mut c = call.clone();
    c.expires_at_tick += 1;
    variants.push(c);
    let mut c = call.clone();
    c.request.signature[0] ^= 1;
    variants.push(c);
    let (socket, _peer) = UnixStream::pair().unwrap();
    for c in variants {
        assert!(s
            .provision(store.clone())
            .evaluate(&socket, &c, 100, 7)
            .is_err());
    }
    assert!(s.provision(store).evaluate(&socket, &call, 100, 7).is_ok());
}

#[test]
fn grant_authority_policy_and_delegation_are_bound_to_root() {
    let lab = Lab::new();
    let s = Setup::new();
    let store = DurableNonces::create(lab.ledger()).unwrap();
    let raw = s.raw();
    let uid = unsafe { libc::geteuid() };
    let pid = std::process::id();
    let sig = s.root.sign(&provisioning_bytes(
        &raw,
        &s.root_key(),
        &s.key(),
        uid,
        pid,
        120,
    ));
    let mut variants = vec![];
    let mut g = raw.clone();
    g.authority.public_key[0] ^= 1;
    variants.push(g);
    let mut g = raw.clone();
    g.authority.active_epoch += 1;
    variants.push(g);
    let mut g = raw.clone();
    g.capability.target_resource = "file:///".into();
    variants.push(g);
    let mut g = raw.clone();
    g.capability.allowed_effects.push(EffectKind::FsDelete);
    variants.push(g);
    let mut g = raw.clone();
    g.policy.predicate_digest[0] ^= 1;
    variants.push(g);
    let mut g = raw.clone();
    g.policy.version.push('2');
    variants.push(g);
    for g in variants {
        assert!(AuthenticatedAcsGuard::provision(
            g,
            s.root_key(),
            s.key(),
            uid,
            pid,
            120,
            &sig.to_bytes(),
            store.clone()
        )
        .is_err());
    }
    let attacker = Setup::new();
    assert!(AuthenticatedAcsGuard::provision(
        raw.clone(),
        attacker.root_key(),
        s.key(),
        uid,
        pid,
        120,
        &sig.to_bytes(),
        store.clone()
    )
    .is_err());
    assert!(AuthenticatedAcsGuard::provision(
        raw,
        s.root_key(),
        attacker.key(),
        uid,
        pid,
        120,
        &sig.to_bytes(),
        store
    )
    .is_err());
}

#[test]
fn forged_signature_expiry_and_real_peer_credentials_reject() {
    let lab = Lab::new();
    let s = Setup::new();
    let store = DurableNonces::create(lab.ledger()).unwrap();
    let mut guard = s.provision(store.clone());
    let mut call = s.call(&guard);
    let (socket, _peer) = UnixStream::pair().unwrap();
    call.request.signature = Setup::new()
        .key
        .sign(&guard.signing_bytes(&call))
        .to_bytes()
        .to_vec();
    assert_eq!(
        guard.evaluate(&socket, &call, 100, 7).unwrap_err(),
        AcsBridgeError::InvalidSignature
    );
    let mut guard = s.provision(store.clone());
    let call = s.call(&guard);
    assert!(guard.evaluate(&socket, &call, 111, 7).is_err());
    let mut guard = s.provision_key(
        store,
        s.key(),
        unsafe { libc::geteuid() },
        std::process::id() + 1,
    );
    let call = s.call(&guard);
    assert!(matches!(
        guard.evaluate(&socket, &call, 100, 7),
        Err(AcsBridgeError::TransportViolation(_))
    ));
}

#[test]
fn scoped_destination_cannot_hide_different_argument_or_mutation() {
    let lab = Lab::new();
    let s = Setup::new();
    let store = DurableNonces::create(lab.ledger()).unwrap();
    let (socket, _peer) = UnixStream::pair().unwrap();
    let mut guard = s.provision(store.clone());
    let mut call = unsigned_call();
    call.request.arguments = "file:///secret".into();
    call.request.signature = s.key.sign(&guard.signing_bytes(&call)).to_bytes().to_vec();
    assert!(guard.evaluate(&socket, &call, 100, 7).is_err());
    let mut guard = s.provision(store);
    let mut call = unsigned_call();
    call.request.tool_name = "atomic_write".into();
    call.request.signature = s.key.sign(&guard.signing_bytes(&call)).to_bytes().to_vec();
    assert_eq!(
        guard.evaluate(&socket, &call, 100, 7).unwrap().outcome,
        DecisionOutcome::RequireApproval
    );
}

#[test]
fn storage_missing_removed_or_partial_fails_closed() {
    let lab = Lab::new();
    let s = Setup::new();
    assert!(DurableNonces::open(lab.ledger()).is_err());
    let mut guard = s.provision(DurableNonces::create(lab.ledger()).unwrap());
    let call = s.call(&guard);
    let (socket, _peer) = UnixStream::pair().unwrap();
    std::fs::remove_file(lab.ledger()).unwrap();
    assert!(matches!(
        guard.evaluate(&socket, &call, 100, 7),
        Err(AcsBridgeError::StorageFailure(_))
    ));
    assert!(DurableNonces::open(lab.ledger()).is_err());
    let store = DurableNonces::create(lab.ledger()).unwrap();
    drop(store);
    use std::io::Write;
    std::fs::OpenOptions::new()
        .append(true)
        .open(lab.ledger())
        .unwrap()
        .write_all(&[1])
        .unwrap();
    assert!(DurableNonces::open(lab.ledger()).is_err());
}

#[test]
fn concurrent_instances_only_authorize_once() {
    let lab = Lab::new();
    let s = Setup::new();
    let _store = DurableNonces::create(lab.ledger()).unwrap();
    let gate = std::sync::Arc::new(std::sync::Barrier::new(8));
    let handles: Vec<_> = (0..8)
        .map(|_| {
            let mut guard = s.provision(DurableNonces::open(lab.ledger()).unwrap());
            let call = s.call(&guard);
            let gate = gate.clone();
            std::thread::spawn(move || {
                let (socket, _peer) = UnixStream::pair().unwrap();
                gate.wait();
                guard.evaluate(&socket, &call, 100, 7).is_ok()
            })
        })
        .collect();
    assert_eq!(
        handles
            .into_iter()
            .filter(|h| h.thread().id() != std::thread::current().id())
            .map(|h| usize::from(h.join().unwrap()))
            .sum::<usize>(),
        1
    );
}

fn report() -> NemesisAutopsyReport {
    NemesisAutopsyReport::build(
        [1; 32],
        [2; 32],
        [3; 32],
        "policy-v1".into(),
        DivergencePoint {
            step_index: 4,
            expected_digest: [5; 32],
            observed_digest: [6; 32],
            description: "divergence".into(),
        },
        [7; 32],
        Vop1OutcomeState::Unknown {
            nonce: [8; 32],
            expected_post_digest: [9; 32],
        },
        vec!["reproduce".into()],
        &[],
    )
}
#[test]
fn forensic_all_fields_and_outcomes_are_signed() {
    let signer = SigningKey::generate(&mut rand::rngs::OsRng);
    let key = VerificationKey::Ed25519(signer.verifying_key().to_bytes());
    let mut r = report();
    r.cryptographic_attestation = signer
        .sign(&r.attestation_signing_bytes(&key))
        .to_bytes()
        .to_vec();
    assert!(r.verify_with_pinned_key(&key).is_ok());
    assert_eq!(r.cose_attestation(&key).unwrap()[0], 0xd2);
    let mut variants = vec![];
    let mut t = r.clone();
    t.incident_id[0] ^= 1;
    variants.push(t);
    let mut t = r.clone();
    t.principal_identity[0] ^= 1;
    variants.push(t);
    let mut t = r.clone();
    t.requested_effect_id[0] ^= 1;
    variants.push(t);
    let mut t = r.clone();
    t.policy_version.push('x');
    variants.push(t);
    let mut t = r.clone();
    t.first_divergence.step_index += 1;
    variants.push(t);
    let mut t = r.clone();
    t.first_divergence.expected_digest[0] ^= 1;
    variants.push(t);
    let mut t = r.clone();
    t.first_divergence.observed_digest[0] ^= 1;
    variants.push(t);
    let mut t = r.clone();
    t.first_divergence.description.push('x');
    variants.push(t);
    let mut t = r.clone();
    t.dispatch_evidence_digest[0] ^= 1;
    variants.push(t);
    let mut t = r.clone();
    t.observed_outcome = Vop1OutcomeState::Rejected {
        reason: "forged".into(),
    };
    variants.push(t);
    let mut t = r.clone();
    t.reproduction_steps.push("forged".into());
    variants.push(t);
    for t in variants {
        assert!(t.verify_with_pinned_key(&key).is_err());
    }
    assert!(r.verify_with_pinned_key(&Setup::new().key()).is_err());
    for outcome in [
        Vop1OutcomeState::Rejected {
            reason: "denied".into(),
        },
        Vop1OutcomeState::VerifiedSuccess {
            nonce: [1; 32],
            pre_state_digest: [2; 32],
            observed_post_digest: [3; 32],
            evidence_receipt_digest: [4; 32],
        },
    ] {
        let mut t = report();
        t.observed_outcome = outcome;
        t.cryptographic_attestation = signer
            .sign(&t.attestation_signing_bytes(&key))
            .to_bytes()
            .to_vec();
        assert!(t.verify_with_pinned_key(&key).is_ok());
    }
}

#[test]
fn p256_request_and_forensic_signature_verify() {
    let lab = Lab::new();
    let s = Setup::new();
    let signer = p256::ecdsa::SigningKey::random(&mut rand::rngs::OsRng);
    let key = VerificationKey::P256(
        signer
            .verifying_key()
            .to_encoded_point(false)
            .as_bytes()
            .to_vec(),
    );
    let mut guard = s.provision_key(
        DurableNonces::create(lab.ledger()).unwrap(),
        key.clone(),
        unsafe { libc::geteuid() },
        std::process::id(),
    );
    let mut call = unsigned_call();
    let sig: p256::ecdsa::Signature = signer.sign(&guard.signing_bytes(&call));
    call.request.signature = p256_der_to_cose_signature(sig.to_der().as_bytes()).unwrap();
    let (socket, _peer) = UnixStream::pair().unwrap();
    assert_eq!(
        guard.evaluate(&socket, &call, 100, 7).unwrap().outcome,
        DecisionOutcome::Allow
    );
    let mut r = report();
    let sig: p256::ecdsa::Signature = signer.sign(&r.attestation_signing_bytes(&key));
    r.cryptographic_attestation = sig.to_bytes().to_vec();
    assert!(r.verify_with_pinned_key(&key).is_ok());
    r.policy_version.push('x');
    assert!(r.verify_with_pinned_key(&key).is_err());
}

#[test]
fn acs_crash_child() {
    let Ok(path) = std::env::var("BABYLON_ACS_TEST_CRASH_STORE") else {
        return;
    };
    let s = Setup::new();
    let mut guard = s.provision(DurableNonces::open(path).unwrap());
    let call = s.call(&guard);
    let (socket, _peer) = UnixStream::pair().unwrap();
    assert!(guard.evaluate(&socket, &call, 100, 7).is_ok());
    // Kill after authorization, before Rust destructors or any simulated effect.
    unsafe {
        libc::kill(libc::getpid(), libc::SIGKILL);
    }
    panic!("SIGKILL unexpectedly returned");
}
#[test]
fn nonce_survives_sigkill_after_authorization() {
    let lab = Lab::new();
    let _store = DurableNonces::create(lab.ledger()).unwrap();
    let child = std::process::Command::new(std::env::current_exe().unwrap())
        .args(["--exact", "acs_crash_child", "--nocapture"])
        .env("BABYLON_ACS_TEST_CRASH_STORE", lab.ledger())
        .status()
        .unwrap();
    use std::os::unix::process::ExitStatusExt;
    assert_eq!(child.signal(), Some(libc::SIGKILL));
    let s = Setup::new();
    let mut restarted = s.provision(DurableNonces::open(lab.ledger()).unwrap());
    let call = s.call(&restarted);
    let (socket, _peer) = UnixStream::pair().unwrap();
    assert_eq!(
        restarted.evaluate(&socket, &call, 100, 7).unwrap_err(),
        AcsBridgeError::NonceReplayDetected([5; 32])
    );
}

#[test]
fn live_host_epoch_revokes_existing_grant() {
    let lab = Lab::new();
    let s = Setup::new();
    let mut guard = s.provision(DurableNonces::create(lab.ledger()).unwrap());
    let call = s.call(&guard);
    let (socket, _peer) = UnixStream::pair().unwrap();
    assert!(matches!(
        guard.evaluate(&socket, &call, 100, 8),
        Err(AcsBridgeError::InvalidRequest(_))
    ));
    assert!(matches!(
        guard.evaluate(&socket, &call, 100, 7),
        Err(AcsBridgeError::FailOpenProhibited { .. })
    ));
}

#[test]
#[cfg(feature = "halt-receipt")]
fn exported_cose_verifies_with_independent_coset_encoder() {
    use coset::TaggedCborSerializable;
    let signer = SigningKey::generate(&mut rand::rngs::OsRng);
    let key = VerificationKey::Ed25519(signer.verifying_key().to_bytes());
    let mut r = report();
    r.cryptographic_attestation = signer
        .sign(&r.attestation_signing_bytes(&key))
        .to_bytes()
        .to_vec();
    let cose = coset::CoseSign1::from_tagged_slice(&r.cose_attestation(&key).unwrap()).unwrap();
    assert_eq!(
        cose.payload.as_deref(),
        Some(r.canonical_payload().as_slice())
    );
    assert!(cose
        .verify_signature(&[], |sig, tbs| {
            signer
                .verifying_key()
                .verify_strict(tbs, &ed25519_dalek::Signature::from_slice(sig).unwrap())
        })
        .is_ok());
}

#[test]
fn lean_golden_vectors_match_runtime_encoder() {
    // Fixed SOFTWARE keys solely to keep cross-language wire fixtures reproducible.
    let s = Setup {
        root: SigningKey::from_bytes(&[0x11; 32]),
        key: SigningKey::from_bytes(&[0x22; 32]),
    };
    let raw = s.raw();
    let grant = provisioning_bytes(&raw, &s.root_key(), &s.key(), 501, 4242, 120);
    let lab = Lab::new();
    let guard = s.provision_key(
        DurableNonces::create(lab.ledger()).unwrap(),
        s.key(),
        501,
        4242,
    );
    let call = unsigned_call();
    let r = report();
    let vectors = [
        ("root", s.root.verifying_key().to_bytes().to_vec()),
        ("delegated", s.key.verifying_key().to_bytes().to_vec()),
        ("grant", grant),
        ("call", guard.payload(&call)),
        ("call_signing", guard.signing_bytes(&call)),
        ("forensic", r.canonical_payload()),
        ("forensic_signing", r.attestation_signing_bytes(&s.key())),
        (
            "cose_ed",
            cose_sign1(&s.key(), &r.canonical_payload(), &[0x33; 64]),
        ),
        (
            "cose_p256",
            cose_sign1(&VerificationKey::P256(vec![4; 65]), &[1, 2, 3], &[0x44; 64]),
        ),
    ];
    for (name, value) in vectors {
        let fixture = include_str!("acs_cbor_golden.txt")
            .lines()
            .find_map(|line| {
                line.split_once(' ')
                    .filter(|(key, _)| *key == name)
                    .map(|(_, value)| value)
            })
            .unwrap();
        assert_eq!(
            hex::encode(value),
            fixture,
            "Rust CBOR diverged from Lean fixture {name}"
        );
    }
}
