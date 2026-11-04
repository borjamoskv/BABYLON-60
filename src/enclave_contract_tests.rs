//! Software-only protocol regression tests. No Secure Enclave invocation.
use super::*;
use crate::executor::{
    AuthorizationPayload, ExecutionError, SignedAuthorization, PROTOCOL_VERSION,
};
use p256::ecdsa::{signature::Signer as _, SigningKey};
use p256::pkcs8::EncodePublicKey;

fn key() -> SigningKey {
    SigningKey::from_bytes((&[7u8; 32]).into()).unwrap()
}
fn enclave(pin: Vec<u8>) -> AppleSecureEnclave {
    AppleSecureEnclave {
        gate_path: String::new(),
        public_key_bytes: RwLock::new(Some(pin.clone())),
        pinned_public_key: Some(pin),
        configuration_error: None,
    }
}
fn payload() -> AuthorizationPayload {
    AuthorizationPayload {
        protocol_version: PROTOCOL_VERSION,
        installation_id: [1; 32],
        executor_id: [2; 32],
        intent_digest: [3; 32],
        policy_digest: [4; 32],
        resource_precondition_digest: [5; 32],
        nonce: [6; 32],
        authority_epoch: 1,
        expires_at: 100,
        max_uses: 1,
    }
}
fn response(key: &SigningKey, data: &[u8]) -> Vec<u8> {
    let signature: Signature = key.sign(data);
    serde_json::to_vec(&serde_json::json!({
        "status": "ATTESTED", "causal_hash": causal_hash(data),
        "test_source": "SOFTWARE_ONLY",
        "public_key": Base64::encode_string(key.verifying_key().to_encoded_point(false).as_bytes()),
        "secure_enclave_signature": Base64::encode_string(signature.to_der().as_bytes()),
    }))
    .unwrap()
}
struct SoftwareGate {
    gate: AppleSecureEnclave,
    key: SigningKey,
}
impl Signer for SoftwareGate {
    fn sign(&self, data: &[u8]) -> Result<Vec<u8>, String> {
        self.gate
            .validate_gate_response(data, &response(&self.key, data))
    }
    fn verify(&self, data: &[u8], sig: &[u8]) -> bool {
        self.gate.verify(data, sig)
    }
    fn get_public_key(&self) -> Vec<u8> {
        self.gate.get_public_key()
    }
    fn algorithm(&self) -> coset::iana::Algorithm {
        coset::iana::Algorithm::ES256
    }
}
#[test]
fn raw_payload_cose_roundtrip_accepts_sec1_and_spki_pins() {
    let key = key();
    for pin in [
        key.verifying_key()
            .to_encoded_point(false)
            .as_bytes()
            .to_vec(),
        key.verifying_key()
            .to_public_key_der()
            .unwrap()
            .as_bytes()
            .to_vec(),
    ] {
        let signer = SoftwareGate {
            gate: enclave(pin),
            key: key.clone(),
        };
        let authorization = SignedAuthorization::new_cose(&payload(), &signer).unwrap();
        assert_eq!(authorization.parse().unwrap().0, payload());
        authorization.verify_signature().unwrap();
    }
}
#[test]
fn status_hash_and_signature_are_bound_to_the_requested_bytes() {
    let key = key();
    let pin = key
        .verifying_key()
        .to_encoded_point(false)
        .as_bytes()
        .to_vec();
    let data = b"software contract";
    let valid: serde_json::Value = serde_json::from_slice(&response(&key, data)).unwrap();
    for (field, value) in [
        ("status", "PREVIEW".to_string()),
        ("causal_hash", "00".repeat(32)),
    ] {
        let mut bad = valid.clone();
        bad[field] = value.into();
        assert!(enclave(pin.clone())
            .validate_gate_response(data, &serde_json::to_vec(&bad).unwrap())
            .is_err());
    }
    let mut contradictory = valid.clone();
    contradictory["success"] = false.into();
    assert!(enclave(pin.clone())
        .validate_gate_response(data, &serde_json::to_vec(&contradictory).unwrap())
        .is_err());
    let signature: Signature = key.sign(hex::encode(data).as_bytes());
    let mut bad = valid;
    bad["secure_enclave_signature"] = Base64::encode_string(signature.to_der().as_bytes()).into();
    assert!(enclave(pin)
        .validate_gate_response(data, &serde_json::to_vec(&bad).unwrap())
        .is_err());
}
#[test]
fn missing_key_fails_before_requesting_a_signature() {
    struct Keyless;
    impl Signer for Keyless {
        fn sign(&self, _: &[u8]) -> Result<Vec<u8>, String> {
            panic!("must reject before signing")
        }
        fn verify(&self, _: &[u8], _: &[u8]) -> bool {
            false
        }
        fn get_public_key(&self) -> Vec<u8> {
            Vec::new()
        }
    }
    assert!(matches!(
        SignedAuthorization::new_cose(&payload(), &Keyless),
        Err(ExecutionError::InvalidAuthorityKey(_))
    ));
}
#[cfg(unix)]
#[test]
fn deadline_includes_child_and_inherited_pipes() {
    for script in ["exec sleep 5", "sleep 0.3 & exit 0"] {
        let mut command = Command::new("sh");
        command.args(["-c", script]);
        let result = run_gate_with_deadline(command, std::time::Duration::from_millis(20));
        assert!(result.unwrap_err().contains("Plazo"));
    }
}
#[cfg(unix)]
#[test]
fn oversized_response_is_bounded_and_rejected() {
    let mut command = Command::new("sh");
    command.args(["-c", "exec dd if=/dev/zero bs=4096 count=32 2>/dev/null"]);
    assert!(
        run_gate_with_deadline(command, std::time::Duration::from_secs(2))
            .unwrap_err()
            .contains("demasiado grande")
    );
}
#[test]
#[ignore = "requires compiled SOFTWARE_ONLY Swift fixture; no hardware attestation"]
fn swift_response_round_trips_through_rust_cose() {
    let key = key();
    let mut signer = enclave(
        key.verifying_key()
            .to_encoded_point(false)
            .as_bytes()
            .to_vec(),
    );
    signer.gate_path =
        std::env::var("B60_SWIFT_SOFTWARE_FIXTURE").expect("compile software Swift fixture");
    let authorization = SignedAuthorization::new_cose(&payload(), &signer).unwrap();
    assert_eq!(authorization.parse().unwrap().0, payload());
    authorization.verify_signature().unwrap();
}
