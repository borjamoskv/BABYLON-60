use crate::receipt::Signer;
use std::env;
use std::process::{Command, Output, Stdio};
use std::sync::RwLock;
use base64ct::{Base64, Encoding};
use p256::ecdsa::signature::Verifier;
use p256::ecdsa::{Signature, VerifyingKey};
use p256::pkcs8::DecodePublicKey;

/// Enclave protegido por hardware (Apple Secure Enclave).
/// Enlaza con el daemon o script Swift de validación biométrica y atestación P-256.
pub struct AppleSecureEnclave {
    gate_path: String,
    public_key_bytes: RwLock<Option<Vec<u8>>>,
    pinned_public_key: Option<Vec<u8>>,
    configuration_error: Option<String>,
}

impl Default for AppleSecureEnclave {
    fn default() -> Self {
        Self::new()
    }
}

#[inline(never)]
fn constant_time_eq_slices(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut xor_acc: u8 = 0;
    for (x, y) in a.iter().zip(b.iter()) {
        xor_acc |= x ^ y;
    }
    core::hint::black_box(xor_acc) == 0
}

// Apple exports P-256 public keys as SEC1/X9.63 points. Keep SPKI DER support
// for existing pinned keys and callers of with_public_key_der.
fn parse_public_key(bytes: &[u8]) -> Result<VerifyingKey, String> {
    VerifyingKey::from_sec1_bytes(bytes)
        .or_else(|_| VerifyingKey::from_public_key_der(bytes))
        .map_err(|_| "Clave publica P-256 invalida: se requiere SEC1/X9.63 o SPKI DER".into())
}

fn same_public_key(expected: &[u8], actual: &VerifyingKey) -> Result<bool, String> {
    let expected = parse_public_key(expected)?.to_sec1_point(false);
    let actual = actual.to_sec1_point(false);
    Ok(constant_time_eq_slices(expected.as_bytes(), actual.as_bytes()))
}

fn decode_pinned_public_key(value: &str) -> Result<Vec<u8>, String> {
    // Validate each decoding before choosing it: a hexadecimal key may also be
    // syntactically valid Base64, but decode to an unrelated byte sequence.
    for decoded in [hex::decode(value).ok(), Base64::decode_vec(value).ok()]
        .into_iter()
        .flatten()
    {
        if parse_public_key(&decoded).is_ok() {
            return Ok(decoded);
        }
    }
    Err("BABYLON_ENCLAVE_PINNED_PUBKEY invalida: se requiere una clave P-256 en hex o Base64".into())
}

#[derive(serde::Deserialize)]
struct GateAttestation {
    status: String,
    causal_hash: String,
    success: Option<bool>,
    public_key: String,
    secure_enclave_signature: String,
}


fn causal_hash(payload: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    hex::encode(Sha256::digest(payload))
}

// A finite deadline covers the process and inherited pipes, without retries.
#[cfg(unix)]
fn run_gate_with_deadline(mut command: Command, limit: std::time::Duration) -> Result<Output, String> {
    use std::io::Read;
    use std::os::fd::AsRawFd;
    fn drain<R: Read>(pipe: &mut R, data: &mut Vec<u8>) -> Result<bool, String> {
        let mut buffer = [0u8; 4096];
        loop {
            match pipe.read(&mut buffer) {
                Ok(0) => return Ok(true),
                Ok(size) => {
                    if data.len() + size > 64 * 1024 {
                        return Err("Respuesta del gate biometrico demasiado grande".into());
                    }
                    data.extend_from_slice(&buffer[..size]);
                }
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => return Ok(false),
                Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
                Err(error) => return Err(error.to_string()),
            }
        }
    }
    command.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = command.spawn().map_err(|e| format!("Fallo al invocar gate biometrico: {e}"))?;
    let result = (|| {
        let mut stdout_pipe = child.stdout.take().ok_or("Gate sin stdout")?;
        let mut stderr_pipe = child.stderr.take().ok_or("Gate sin stderr")?;
        for fd in [stdout_pipe.as_raw_fd(), stderr_pipe.as_raw_fd()] {
            // SAFETY: both descriptors are owned live pipes.
            let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
            if flags < 0 || unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
                return Err(std::io::Error::last_os_error().to_string());
            }
        }
        let start = std::time::Instant::now();
        let mut stdout = Vec::new();
        let mut stderr = Vec::new();
        loop {
            let out_done = drain(&mut stdout_pipe, &mut stdout)?;
            let err_done = drain(&mut stderr_pipe, &mut stderr)?;
            if let Some(status) = child.try_wait().map_err(|e| e.to_string())? {
                if out_done && err_done { return Ok(Output { status, stdout, stderr }); }
            }
            if start.elapsed() >= limit {
                return Err("Plazo del gate biometrico agotado; operacion abortada".into());
            }
            std::thread::sleep(std::time::Duration::from_millis(10));
        }
    })();
    if result.is_err() {
        let _ = child.kill();
        let _ = child.wait();
    }
    result
}
#[cfg(not(unix))]
fn run_gate_with_deadline(_: Command, _: std::time::Duration) -> Result<Output, String> {
    Err("Gate biometrico no disponible en este anfitrion".into())
}

impl AppleSecureEnclave {
    /// Crea una nueva instancia de `AppleSecureEnclave` resolviendo la ruta del gate biométrico.
    pub fn new() -> Self {
        let path = env::var("C5_BIOMETRIC_GATE_PATH").unwrap_or_else(|_| {
            let native_bin = "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate";
            if std::path::Path::new(native_bin).exists() {
                native_bin.into()
            } else {
                "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift".into()
            }
        });
        let (pinned, configuration_error) = match env::var("BABYLON_ENCLAVE_PINNED_PUBKEY") {
            Ok(value) => match decode_pinned_public_key(&value) {
                Ok(key) => (Some(key), None),
                Err(error) => (None, Some(error)),
            },
            Err(env::VarError::NotPresent) => (None, Some("Falta BABYLON_ENCLAVE_PINNED_PUBKEY: no se permite confianza inicial implícita".into())),
            Err(env::VarError::NotUnicode(_)) => (
                None,
                Some("BABYLON_ENCLAVE_PINNED_PUBKEY no es texto valido".into()),
            ),
        };
        Self {
            gate_path: path,
            public_key_bytes: RwLock::new(pinned.clone()),
            pinned_public_key: pinned,
            configuration_error,
        }
    }

    /// Fija una clave SPKI DER o SEC1/X9.63, preservando los bytes proporcionados.
    /// Conserva el nombre de la API para los consumidores existentes de SPKI DER.
    pub fn with_public_key_der(mut self, pubkey_der: Vec<u8>) -> Self {
        self.configuration_error = parse_public_key(&pubkey_der).err();
        self.pinned_public_key = Some(pubkey_der.clone());
        if let Ok(mut lock) = self.public_key_bytes.write() {
            *lock = Some(pubkey_der);
        }
        self
    }

    /// Valida la respuesta completa antes de registrar una clave o aceptar la firma.
    /// Es una operación local: no invoca el gate ni acredita hardware por sí sola.
    fn validate_gate_response(&self, payload: &[u8], stdout: &[u8]) -> Result<Vec<u8>, String> {
        if let Some(error) = &self.configuration_error {
            return Err(error.clone());
        }
        if payload.is_empty() {
            return Err("Payload de atestacion vacio".into());
        }
        let response: GateAttestation = serde_json::from_slice(stdout)
            .map_err(|_| "Respuesta del TEE invalida o incompleta".to_string())?;
        if response.status != "ATTESTED" || response.success == Some(false) || response.causal_hash != causal_hash(payload) {
            return Err("El gate no atestiguo el hash del payload solicitado".into());
        }
        let public_key = Base64::decode_vec(&response.public_key)
            .map_err(|_| "Clave publica del TEE con Base64 invalido".to_string())?;
        let verifying_key = parse_public_key(&public_key)?;
        let pinned = self.pinned_public_key.as_ref()
            .ok_or_else(|| "Falta clave de autoridad provisionada".to_string())?;
        if !same_public_key(pinned, &verifying_key)? {
            return Err("Clave publica del TEE rechazada: no coincide con la clave pineada".into());
        }
        let signature_der = Base64::decode_vec(&response.secure_enclave_signature)
            .map_err(|_| "Firma Secure Enclave con Base64 invalido".to_string())?;
        let signature = Signature::from_der(&signature_der)
            .map_err(|_| "Firma Secure Enclave con DER invalido".to_string())?;
        verifying_key.verify(payload, &signature)
            .map_err(|_| "Firma del TEE no verifica el payload solicitado".to_string())?;

        let mut registered = self.public_key_bytes.write()
            .map_err(|_| "Registro de clave publica del TEE no disponible".to_string())?;
        if let Some(existing) = registered.as_ref() {
            if !same_public_key(existing, &verifying_key)? {
                return Err("Clave publica del TEE mutada inesperadamente".into());
            }
        } else {
            *registered = Some(public_key);
        }
        // Preserve the Signer contract: fixed-width r || s, never ASN.1 DER.
        Ok(signature.to_bytes().to_vec())
    }
}

impl Signer for AppleSecureEnclave {
    fn algorithm(&self) -> coset::iana::Algorithm {
        coset::iana::Algorithm::ES256
    }

    fn sign(&self, to_sign: &[u8]) -> Result<Vec<u8>, String> {
        if let Some(error) = &self.configuration_error {
            return Err(error.clone());
        }
        if to_sign.is_empty() {
            return Err("Payload de atestacion vacio".into());
        }
        if self.pinned_public_key.is_none() {
            return Err("Falta clave de autoridad provisionada".into());
        }
        let payload_hash = causal_hash(to_sign);

        let mut cmd = if self.gate_path.ends_with(".swift") {
            let mut c = Command::new("swift");
            c.arg(&self.gate_path);
            c
        } else {
            Command::new(&self.gate_path)
        };

        cmd.arg("--causal-hash").arg(&payload_hash)
            .arg("--sign-hex").arg(hex::encode(to_sign))
            .arg("--action").arg("Firma Enclave C5-REAL")
            .arg("--agent").arg("BABYLON-60 KERNEL")
            .arg("--scope").arg("Ring-0 Secure Enclave");
        let output = run_gate_with_deadline(cmd, std::time::Duration::from_secs(45))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Rechazo Biometrico / Sandboxing: {}", stderr));
        }

        self.validate_gate_response(to_sign, &output.stdout)
    }

    /// Verificación criptográfica rigurosa P-256 ECDSA.
    /// Erradica el stub inseguro anterior `!signature.is_empty()`.
    fn verify(&self, payload: &[u8], signature: &[u8]) -> bool {
        if self.configuration_error.is_some() || signature.is_empty() || payload.is_empty() {
            return false;
        }

        // 1. Obtener la clave pública registrada
        let pubkey_bytes = match self.public_key_bytes.read() {
            Ok(lock) => match &*lock {
                Some(pk) => pk.clone(),
                None => return false, // Sin clave pública TEE registrada, rechazar fail-closed
            },
            Err(_) => return false,
        };

        // 2. Aceptar el punto SEC1/X9.63 de Apple y claves SPKI DER existentes.
        let verifying_key = match parse_public_key(&pubkey_bytes) {
            Ok(vk) => vk,
            Err(_) => return false,
        };

        // 3. Parsear firma de ancho fijo r || s (contrato Signer).
        let ecdsa_sig = match Signature::from_slice(signature) {
            Ok(sig) => sig,
            Err(_) => return false,
        };

        // ES256/COSE signs the original bytes, never their hex spelling.
        verifying_key.verify(payload, &ecdsa_sig).is_ok()
    }

    fn get_public_key(&self) -> Vec<u8> {
        match self.public_key_bytes.read() {
            Ok(lock) => lock.as_ref().and_then(|bytes| parse_public_key(bytes).ok())
                .map(|key| key.to_sec1_point(false).as_bytes().to_vec()).unwrap_or_default(),
            Err(_) => Vec::new(),
        }
    }
}

/// Intención canónica formal para autorización por hardware/biometría.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalIntent {
    /// Identificador único de la intención (32 bytes).
    pub intent_id: [u8; 32],
    /// Nombre de la acción propuesta.
    pub action_name: String,
    /// Digest SHA-256 de los parámetros canónicos.
    pub payload_digest: [u8; 32],
    /// Recurso sobre el que se solicita la acción.
    pub target_resource: String,
}

/// Atestación criptográfica emitida tras autorización de hardware.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Attestation {
    /// Clave pública de la autoridad en formato DER.
    pub public_key: Vec<u8>,
    /// Firma ASN.1 DER sobre la intención canónica.
    pub signature_der: Vec<u8>,
    /// Algoritmo criptográfico utilizado (ej. ES256 / P-256).
    pub algorithm: coset::iana::Algorithm,
    /// Timestamp Unix de la atestación.
    pub timestamp_epoch_s: u64,
}

/// Trait formal de Autoridad de Hardware (AX-0).
/// Desacopla la autenticación biométrica (Touch ID / LocalAuthentication)
/// del firmado de la clave protegida en Secure Enclave.
pub trait HardwareAuthority {
    /// Autoriza una intención canónica solicitando interacción de hardware y firma.
    fn authorize(&self, intent: &CanonicalIntent) -> Result<Attestation, String>;
}

impl HardwareAuthority for AppleSecureEnclave {
    fn authorize(&self, intent: &CanonicalIntent) -> Result<Attestation, String> {
        let sig = self.sign(&intent.payload_digest)?;
        let sig = Signature::from_slice(&sig).map_err(|_| "Invalid fixed-width signature".to_string())?
            .to_der().as_bytes().to_vec();
        let pk = self.get_public_key();
        Ok(Attestation {
            public_key: pk,
            signature_der: sig,
            algorithm: self.algorithm(),
            timestamp_epoch_s: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use p256::ecdsa::SigningKey;
    use p256::pkcs8::EncodePublicKey;
    use p256::elliptic_curve::Generate;
    use p256::ecdsa::signature::Signer as P256Signer;

    #[test]
    fn test_enclave_rejects_empty_or_bogus_signature() {
        let enclave = AppleSecureEnclave::new();
        let payload = b"PAYLOAD_TEST";

        // Rechaza firma vacía
        assert!(!enclave.verify(payload, b""));
        // Rechaza firma con basura sin clave pública
        assert!(!enclave.verify(payload, b"non_empty_garbage_signature"));
    }

    #[test]
    fn test_enclave_cryptographic_verification_p256() {
        // Generar un par de claves P-256 genuino para verificar la lógica de firma/verificación
        let signing_key = SigningKey::generate();
        let verifying_key = signing_key.verifying_key();
        let pubkey_der = verifying_key.to_public_key_der().unwrap().as_bytes().to_vec();

        let enclave = AppleSecureEnclave::new().with_public_key_der(pubkey_der.clone());
        assert_eq!(enclave.get_public_key(), verifying_key.to_sec1_point(false).as_bytes());

        let payload = b"ATTESTATION_CRITICAL_TRANSACTION";
        // Sign the original message bytes.

        // Generar firma DER legítima
        let sig: Signature = signing_key.sign(payload);
        let sig_der = sig.to_bytes().to_vec();

        // 1. Verificación exitosa de firma legítima
        assert!(enclave.verify(payload, &sig_der), "La firma criptográfica P-256 válida debe verificar");

        // 2. Rechazo ante alteración del payload
        let tampered_payload = b"ATTESTATION_CRITICAL_TRANSACTION_MUTATED";
        assert!(!enclave.verify(tampered_payload, &sig_der), "Payload alterado debe fallar verificación");

        // 3. Rechazo ante firma corrupta
        let mut corrupt_sig = sig_der.clone();
        if let Some(byte) = corrupt_sig.last_mut() {
            *byte ^= 0xFF;
        }
        assert!(!enclave.verify(payload, &corrupt_sig), "Firma corrupta debe fallar verificación");

        // 4. Reject the legacy signature over the hex spelling.
        let raw_sig: Signature = signing_key.sign(hex::encode(payload).as_bytes());
        let raw_sig_der = raw_sig.to_bytes().to_vec();
        assert!(!enclave.verify(payload, &raw_sig_der), "Firma sobre payload crudo sin hex canonical debe ser rechazada");
    }

    #[test]
    fn test_enclave_algorithm_is_es256() {
        let enclave = AppleSecureEnclave::new();
        assert_eq!(enclave.algorithm(), coset::iana::Algorithm::ES256);
    }

    // [FRENTE-007/053] This test uses an in-memory software key pair as a stand-in for the
    // Apple Secure Enclave. It validates the *contract* of HardwareAuthority, NOT physical
    // silicon attestation. Real biometric attest is tested only on physical Apple Silicon
    // hardware via `cargo test --features test_real_enclave`.
    // Gated behind `cfg(test_mock_hardware)` to prevent CI from treating software-signed
    // receipts as proof of physical enclave operations.
    #[cfg(feature = "test_mock_hardware")]
    #[test]
    fn test_hardware_authority_contract() {
        // Mock HardwareAuthority to test the interface contract
        struct MockHardwareAuthority {
            signing_key: SigningKey,
            pubkey_der: Vec<u8>,
        }

        impl HardwareAuthority for MockHardwareAuthority {
            fn authorize(&self, intent: &CanonicalIntent) -> Result<Attestation, String> {
                let payload_hex = hex::encode(intent.payload_digest);
                let sig: Signature = self.signing_key.sign(payload_hex.as_bytes());
                Ok(Attestation {
                    public_key: self.pubkey_der.clone(),
                    signature_der: sig.to_bytes().to_vec(),
                    algorithm: coset::iana::Algorithm::ES256,
                    timestamp_epoch_s: 1727950000,
                })
            }
        }

        let signing_key = SigningKey::generate();
        let verifying_key = signing_key.verifying_key();
        let pubkey_der = verifying_key.to_public_key_der().unwrap().as_bytes().to_vec();

        let authority = MockHardwareAuthority {
            signing_key,
            pubkey_der: pubkey_der.clone(),
        };

        let intent = CanonicalIntent {
            intent_id: [1u8; 32],
            action_name: "PURGE_CORRUPT_LEDGER_BLOCK".into(),
            payload_digest: [0x5A; 32],
            target_resource: "00_ABZU_KERNEL/ledger".into(),
        };

        let attestation = authority.authorize(&intent).expect("Authorization must succeed");
        assert_eq!(attestation.public_key, pubkey_der);
        assert_eq!(attestation.algorithm, coset::iana::Algorithm::ES256);

        // Verify attestation signature
        let vk = VerifyingKey::from_public_key_der(&attestation.public_key).unwrap();
        let sig = Signature::from_slice(&attestation.signature_der)
            .or_else(|_| Signature::from_der(&attestation.signature_der))
            .unwrap();
        let payload_hex = hex::encode(intent.payload_digest);
        assert!(vk.verify(payload_hex.as_bytes(), &sig).is_ok());

        // Tampering payload digest must fail verification
        let tampered_hex = hex::encode([0xFF; 32]);
        assert!(vk.verify(tampered_hex.as_bytes(), &sig).is_err());
    }
}


#[cfg(test)]
mod gate_response_tests {
    use super::*;
    use p256::ecdsa::{SigningKey, signature::Signer as _};
    use p256::pkcs8::EncodePublicKey;

    // Software-only fixtures. No process, biometric gate, or hardware key is used.
    fn key(seed: u8) -> SigningKey {
        SigningKey::from_bytes((&[seed; 32]).into()).unwrap()
    }

    fn enclave(pinned: Option<Vec<u8>>) -> AppleSecureEnclave {
        AppleSecureEnclave {
            gate_path: String::new(),
            public_key_bytes: RwLock::new(pinned.clone()),
            pinned_public_key: pinned,
            configuration_error: None,
        }
    }

    fn response(key: &SigningKey, payload: &[u8], spki: bool) -> Vec<u8> {
        let public_key = if spki {
            key.verifying_key().to_public_key_der().unwrap().as_bytes().to_vec()
        } else {
            key.verifying_key().to_sec1_point(false).as_bytes().to_vec()
        };
        let signature: Signature = key.sign(payload);
        serde_json::to_vec(&serde_json::json!({
            "status": "ATTESTED",
            "causal_hash": causal_hash(payload),
            "public_key": Base64::encode_string(&public_key),
            "secure_enclave_signature": Base64::encode_string(signature.to_der().as_bytes()),
        })).unwrap()
    }

    #[test]
    fn equivalent_sec1_and_spki_pins_expose_canonical_sec1_for_cose() {
        let key = key(7);
        let payload = b"software compatibility only";
        for pin_spki in [false, true] {
            let pin = if pin_spki {
                key.verifying_key().to_public_key_der().unwrap().as_bytes().to_vec()
            } else {
                key.verifying_key().to_sec1_point(false).as_bytes().to_vec()
            };
            for response_spki in [false, true] {
                let enclave = enclave(Some(pin.clone()));
                let signature = enclave.validate_gate_response(payload, &response(&key, payload, response_spki)).unwrap();
                assert_eq!(signature.len(), 64);
                assert!(enclave.verify(payload, &signature));
                assert_eq!(enclave.get_public_key(), key.verifying_key().to_sec1_point(false).as_bytes());
            }
        }
    }

    #[test]
    fn invalid_response_never_registers_a_public_key() {
        let key = key(7);
        let payload = b"software response validation";
        let valid = response(&key, payload, false);
        let parsed: serde_json::Value = serde_json::from_slice(&valid).unwrap();
        let cases = [
            b"not JSON".to_vec(),
            serde_json::to_vec(&serde_json::json!({"public_key": parsed["public_key"]})).unwrap(),
            serde_json::to_vec(&serde_json::json!({"secure_enclave_signature": parsed["secure_enclave_signature"]})).unwrap(),
            serde_json::to_vec(&serde_json::json!({"public_key": "@@@", "secure_enclave_signature": parsed["secure_enclave_signature"]})).unwrap(),
            serde_json::to_vec(&serde_json::json!({"public_key": Base64::encode_string(&[0u8; 65]), "secure_enclave_signature": parsed["secure_enclave_signature"]})).unwrap(),
            serde_json::to_vec(&serde_json::json!({"public_key": parsed["public_key"], "secure_enclave_signature": "@@@"})).unwrap(),
            serde_json::to_vec(&serde_json::json!({"public_key": parsed["public_key"], "secure_enclave_signature": Base64::encode_string(&[0u8; 64])})).unwrap(),
            response(&key, b"different payload", false),
        ];
        for mut invalid in cases {
            if let Ok(mut json) = serde_json::from_slice::<serde_json::Value>(&invalid) {
                if json.get("status").is_none() { json["status"] = "ATTESTED".into(); }
                if json.get("causal_hash").is_none() { json["causal_hash"] = causal_hash(payload).into(); }
                invalid = serde_json::to_vec(&json).unwrap();
            }
            let enclave = enclave(None);
            assert!(enclave.validate_gate_response(payload, &invalid).is_err());
            assert!(enclave.get_public_key().is_empty());
        }
        let enclave = enclave(None);
        assert!(enclave.validate_gate_response(b"", &valid).is_err());
        assert!(enclave.get_public_key().is_empty());
    }

    #[test]
    fn pin_mismatch_and_later_key_rotation_fail_closed() {
        let original = key(7);
        let replacement = key(8);
        let payload = b"software pin integrity";
        let pin = original.verifying_key().to_sec1_point(false).as_bytes().to_vec();
        let pinned = enclave(Some(pin.clone()));
        assert!(pinned.validate_gate_response(payload, &response(&replacement, payload, true)).is_err());
        assert_eq!(pinned.get_public_key(), pin);
        let unprovisioned = enclave(None);
        assert!(unprovisioned.validate_gate_response(payload, &response(&original, payload, false)).is_err());
        assert!(unprovisioned.get_public_key().is_empty());
    }

    #[test]
    fn pin_decoding_validates_hex_and_base64_and_rejects_invalid_configuration_before_gate() {
        let key = key(7);
        for bytes in [
            key.verifying_key().to_sec1_point(false).as_bytes().to_vec(),
            key.verifying_key().to_public_key_der().unwrap().as_bytes().to_vec(),
        ] {
            assert_eq!(decode_pinned_public_key(&hex::encode(&bytes)).unwrap(), bytes);
            assert_eq!(decode_pinned_public_key(&Base64::encode_string(&bytes)).unwrap(), bytes);
        }
        for invalid in ["", "@@@", "deadbeef"] {
            assert!(decode_pinned_public_key(invalid).is_err());
        }
        let mut invalid = enclave(None);
        invalid.configuration_error = Some("invalid software pin fixture".into());
        // The empty gate path cannot launch a process; the exact config error
        // proves rejection happened before attempting to execute the gate.
        assert_eq!(invalid.sign(b"payload").unwrap_err(), "invalid software pin fixture");
        assert!(!invalid.verify(b"payload", &[1u8; 64]));
    }

    #[test]
    fn software_response_stress_after_warmup() {
        let key = key(7);
        let payload = b"software stress, no hardware attestation";
        let sec1 = response(&key, payload, false);
        let spki = response(&key, payload, true);
        let enclave = enclave(Some(key.verifying_key().to_sec1_point(false).as_bytes().to_vec()));
        for _ in 0..64 {
            enclave.validate_gate_response(payload, &sec1).unwrap();
        }
        let original = enclave.get_public_key();
        for i in 0..512 {
            let response = if i % 2 == 0 { &sec1 } else { &spki };
            let signature = enclave.validate_gate_response(payload, response).unwrap();
            assert_eq!(signature.len(), 64);
            assert!(enclave.verify(payload, &signature));
            assert!(!enclave.verify(b"tampered", &signature));
            assert_eq!(enclave.get_public_key(), original);
        }
    }
}

#[cfg(test)]
#[path = "enclave_contract_tests.rs"]
mod contract_regression_tests;

#[cfg(test)]
mod p1_cose_regression {
    use super::*;
    use crate::executor::{AuthorizationPayload, SignedAuthorization, PROTOCOL_VERSION};
    use coset::{CoseSign1Builder, HeaderBuilder};
    use p256::ecdsa::{SigningKey, signature::Signer as _};
    use p256::pkcs8::EncodePublicKey;
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn apple_adapter_cose_round_trip_with_software_helper() {
        // Software-only process fixture: exercises the real adapter, not Touch ID.
        let key = SigningKey::from_bytes((&[19u8; 32]).into()).unwrap();
        let public = key.verifying_key().to_sec1_point(false).as_bytes().to_vec();
        let payload = AuthorizationPayload {
            protocol_version: PROTOCOL_VERSION, installation_id: [1; 32], executor_id: [2; 32],
            intent_digest: [3; 32], policy_digest: [4; 32], resource_precondition_digest: [5; 32],
            nonce: [6; 32], authority_epoch: 1, expires_at: 1200, max_uses: 1,
        };
        let mut signing_bytes = Vec::new();
        CoseSign1Builder::new()
            .protected(HeaderBuilder::new().algorithm(coset::iana::Algorithm::ES256).key_id(public.clone()).build())
            .payload(payload.to_canonical_bytes().to_vec())
            .create_signature(&[], |data| { signing_bytes = data.to_vec(); Vec::new() }).build();
        let signature: Signature = key.sign(&signing_bytes);
        use sha2::{Digest, Sha256};
        let response = serde_json::json!({
            "status": "ATTESTED", "causal_hash": hex::encode(Sha256::digest(&signing_bytes)),
            "public_key": Base64::encode_string(&public),
            "secure_enclave_signature": Base64::encode_string(signature.to_der().as_bytes()),
        }).to_string();
        let dir = std::env::temp_dir().join(format!("babylon-p1-cose-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let helper = dir.join("software-helper");
        std::fs::write(&helper, format!(
            "#!/bin/sh\nraw=''\nhash=''\nwhile [ \"$#\" -gt 0 ]; do\ncase \"$1\" in\n--sign-hex) raw=\"$2\"; shift;;\n--causal-hash) hash=\"$2\"; shift;;\nesac\nshift\ndone\n[ \"$raw\" = '{}' ] && [ \"$hash\" = '{}' ] || exit 1\nprintf '%s' '{}'\n",
            hex::encode(&signing_bytes), hex::encode(Sha256::digest(&signing_bytes)), response,
        )).unwrap();
        std::fs::set_permissions(&helper, std::fs::Permissions::from_mode(0o700)).unwrap();
        for pin in [public.clone(), key.verifying_key().to_public_key_der().unwrap().as_bytes().to_vec()] {
            let enclave = AppleSecureEnclave {
                gate_path: helper.to_string_lossy().into_owned(),
                public_key_bytes: RwLock::new(Some(pin.clone())), pinned_public_key: Some(pin),
                configuration_error: None,
            };
            let auth = SignedAuthorization::new_cose(&payload, &enclave)
                .expect("Apple adapter must sign raw COSE Sig_structure bytes");
            assert!(auth.verify_signature().is_ok());
            assert_eq!(auth.parse().unwrap().1, public);
            let mut changed = auth;
            let last = changed.cose_bytes.len() - 1;
            changed.cose_bytes[last] ^= 1;
            assert!(changed.verify_signature().is_err());
        }
        std::fs::remove_dir_all(dir).unwrap();
    }
}
