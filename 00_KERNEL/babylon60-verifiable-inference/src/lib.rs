// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use sha2::{Digest, Sha256};
use std::ffi::CStr;
use std::os::raw::c_char;

/// Motor de Verificación Causal-Determinist (Simulación LogUp/tlookup)
/// Asegura la colisión Bizantina (INV_BFT_04) en O(1) comparando el compromiso hash
/// generado a partir del payload estocástico y el nonce termodinámico.
#[no_mangle]
pub extern "C" fn verify_inference_payload(
    payload_hash: *const c_char,
    nonce: u64,
    proof_hash: *const c_char,
) -> bool {
    if payload_hash.is_null() || proof_hash.is_null() {
        return false;
    }

    let payload = unsafe { CStr::from_ptr(payload_hash) };
    let proof = unsafe { CStr::from_ptr(proof_hash) };

    if let (Ok(p_str), Ok(pr_str)) = (payload.to_str(), proof.to_str()) {
        let mut hasher = Sha256::new();
        hasher.update(p_str.as_bytes());
        hasher.update(&nonce.to_le_bytes());

        let result = format!("{:x}", hasher.finalize());
        return result == pr_str;
    }

    false
}
