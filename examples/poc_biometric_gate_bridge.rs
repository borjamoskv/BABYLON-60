use babylon60::executor::AuthorizationPayload;
use coset::{HeaderBuilder, CoseSign1Builder};
use std::process::Command;
use serde::Deserialize;

#[allow(dead_code)]
#[derive(Deserialize)]
struct BiometricGateResponse {
    status: String,
    secure_enclave_signature: String,
    public_key: String,
}

fn main() {
    println!("[AX-0 / VECTOR BETA] Puente Biométrico P-256 (Touch ID)");

    let payload = AuthorizationPayload {
        protocol_version: 1,
        installation_id: [1; 32],
        executor_id: [2; 32],
        intent_digest: [3; 32],
        policy_digest: [4; 32],
        resource_precondition_digest: [5; 32],
        nonce: [6; 32],
        authority_epoch: 10,
        expires_at: 9999999999,
        max_uses: 1,
    };

    let payload_bytes = payload.to_canonical_bytes().to_vec();

    let protected = HeaderBuilder::new()
        .algorithm(coset::iana::Algorithm::ES256)
        .build();

    let sign1_res = CoseSign1Builder::new()
        .protected(protected)
        .payload(payload_bytes)
        .try_create_signature(&[], |tbs| -> Result<Vec<u8>, String> {
            println!(">> TBS bytes size: {}", tbs.len());
            let tbs_hex = hex::encode(tbs);

            let bin_path = "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate";
            println!(">> Solicitando atestación física a Secure Enclave...");
            // Ejecutando en preview para que no falle al faltar Touch ID en este entorno headless
            let output = Command::new(bin_path)
                .arg("--action").arg("Aprobar autorización AX-0")
                .arg("--agent").arg("Rust Biometric Bridge")
                .arg("--sign-hex").arg(&tbs_hex)
                .arg("--preview")
                .output()
                .map_err(|e| e.to_string())?;

            if !output.status.success() {
                let err = String::from_utf8_lossy(&output.stderr);
                return Err(format!("Gate failed: {}", err));
            }
            
            // Note: Since we used --preview, it just outputs the dialog text, not JSON!
            // In a real run, it returns JSON.
            println!("=== Salida de Preview ===");
            println!("{}", String::from_utf8_lossy(&output.stdout));
            println!("=========================");
            
            // We just return a dummy signature and public key so it compiles.
            Err("Simulacion completa (Preview ejecutado)".to_string())
        });

    match sign1_res {
        Ok(_) => println!("[✓] Firmado con éxito."),
        Err(e) => println!("[X] Resultado: {}", e),
    }
}
