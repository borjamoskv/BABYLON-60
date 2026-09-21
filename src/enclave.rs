use crate::receipt::Signer;
use std::env;
use std::process::Command;

/// Enclave protegido por hardware (Apple Secure Enclave).
/// Enlaza con el daemon o script Swift de validación biométrica.
pub struct AppleSecureEnclave {
    gate_path: String,
}

impl Default for AppleSecureEnclave {
    fn default() -> Self {
        Self::new()
    }
}

impl AppleSecureEnclave {
    /// Crea una nueva instancia de `AppleSecureEnclave` resolviendo la ruta del gate biométrico.
    pub fn new() -> Self {
        let path = env::var("C5_BIOMETRIC_GATE_PATH")
            .unwrap_or_else(|_| "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift".into());
        Self { gate_path: path }
    }
}

impl Signer for AppleSecureEnclave {
    fn sign(&self, to_sign: &[u8]) -> Result<Vec<u8>, String> {
        let payload_hash = hex::encode(to_sign);

        let output = match Command::new("swift")
            .arg(&self.gate_path)
            .arg("--causal-hash")
            .arg(&payload_hash)
            .arg("--message")
            .arg("Firma Enclave C5-REAL")
            .output() {
                Ok(out) => out,
                Err(e) => return Err(format!("Fallo al invocar gate biometrico: {}", e)),
            };

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Rechazo Biometrico / Sandboxing: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        
        let sig_marker = "\"secure_enclave_signature\": \"";
        if let Some(start_idx) = stdout.find(sig_marker) {
            let substr = &stdout[start_idx + sig_marker.len()..];
            if let Some(end_idx) = substr.find("\"") {
                let base64_sig = &substr[..end_idx];
                return Ok(base64_sig.as_bytes().to_vec());
            }
        }
        
        Err(String::from("El TEE no devolvio una firma valida"))
    }

    fn verify(&self, _payload: &[u8], signature: &[u8]) -> bool {
        !signature.is_empty()
    }

    fn get_public_key(&self) -> Vec<u8> {
        Vec::new()
    }
}
