// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use ark_bls12_381::{Bls12_381, Fr as BlsFr};
use ark_groth16::{Groth16, Proof, VerifyingKey};
use ark_serialize::CanonicalDeserialize;
use ark_snark::{CircuitSpecificSetupSNARK, SNARK};
use rand_chacha::ChaCha20Rng;
use rand::SeedableRng;
use std::ffi::CStr;
use std::os::raw::c_char;
use std::sync::OnceLock;

// Incluir el circuito transpilado de nul-zk
include!(concat!(env!("OUT_DIR"), "/inference_circuit.rs"));

/// Clave de verificación de DEMOSTRACIÓN. Sale de un setup con semilla fija y pública, por lo
/// que cualquiera puede reproducirlo: no es un setup confiable (C0202). Solo la usa
/// `verify_public_setup_relation_proof`. `None` si el setup falla, sin pánico en FFI.
static VK: OnceLock<Option<VerifyingKey<Bls12_381>>> = OnceLock::new();

fn get_verifying_key() -> Option<&'static VerifyingKey<Bls12_381>> {
    VK.get_or_init(|| {
        let mut rng = ChaCha20Rng::seed_from_u64(0xC5C5C5C5C5C5C5C5u64); // Invariante Determinista
        let empty_circuit = InferenceConstraint::<BlsFr> {
            weight: None,
            nonce: None,
            expected_hash: None,
        };
        Groth16::<Bls12_381>::setup(empty_circuit, &mut rng)
            .ok()
            .map(|(_, vk)| vk)
    })
    .as_ref()
}

/// Convierte un string hexadecimal a un elemento del campo Fr (BLS12-381)
fn hex_to_fr(hex_str: &str) -> Option<BlsFr> {
    let clean_hex = hex_str.trim_start_matches("0x");
    let bytes = hex::decode(clean_hex).ok()?;
    BlsFr::deserialize_compressed(&*bytes).ok()
}

/// Punto de entrada FFI para "verificación de inferencia". BLOQUEADO (C0201, C0202).
///
/// Devuelve siempre `false`. Motivos, ambos verificados con una prueba fabricada:
/// - C0201: el circuito solo expresa `weight * nonce == expected_hash`. No liga modelo, entrada
///   ni salida, ni demuestra que se evaluó una inferencia: cualquiera elige
///   `weight = expected_hash / nonce`.
/// - C0202: la clave de verificación sale de un setup con semilla fija y pública, así que no
///   es un parámetro confiable.
///
/// Hasta que exista un circuito que ligue la inferencia y parámetros de una ceremonia
/// confiable, esta capacidad no certifica nada.
#[no_mangle]
#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub extern "C" fn verify_inference_payload(
    _payload_hash: *const c_char,
    _nonce: u64,
    _proof_hash: *const c_char,
) -> bool {
    false
}

/// Solo demostración: verifica una prueba Groth16 de la relación `weight * nonce == expected_hash`
/// contra el setup de semilla pública. NO es verificación de inferencia ni usa un setup
/// confiable; no debe usarse para certificar nada. No se exporta por FFI.
///
/// public_inputs:
/// - nonce
/// - payload_hash: expected_hash del circuito
///
/// proof_hash: prueba Groth16 serializada en hexadecimal
#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub fn verify_public_setup_relation_proof(
    payload_hash: *const c_char,
    nonce: u64,
    proof_hash: *const c_char,
) -> bool {
    if payload_hash.is_null() || proof_hash.is_null() {
        return false;
    }

    let payload_c = unsafe { CStr::from_ptr(payload_hash) };
    let proof_c = unsafe { CStr::from_ptr(proof_hash) };

    if let (Ok(p_str), Ok(pr_str)) = (payload_c.to_str(), proof_c.to_str()) {
        
        // 1. Deserialización estricta de la Prueba ZK
        let proof_bytes = match hex::decode(pr_str) {
            Ok(b) => b,
            Err(_) => return false,
        };
        
        let proof = match Proof::<Bls12_381>::deserialize_compressed(&*proof_bytes) {
            Ok(p) => p,
            Err(_) => return false, // Prueba corrupta o adulterada
        };

        // 2. Parseo topológico de los Inputs Públicos (El Mapa Causal)
        let expected_hash_fr = match hex_to_fr(p_str) {
            Some(fr) => fr,
            None => return false,
        };
        let nonce_fr = BlsFr::from(nonce);

        // 3. Verificación ZK con VK Determinista (Cero-Anergía O(1))
        // IMPORTANTE: El orden de los public inputs en Groth16 depende del compilador.
        // nul-zk ordena los public inputs según aparecen en AST.
        // En InferenceConstraint: 
        // public nonce: Field
        // public expected_hash: Field
        let public_inputs = vec![nonce_fr, expected_hash_fr];
        
        let Some(vk) = get_verifying_key() else {
            return false;
        };
        return Groth16::<Bls12_381>::verify(vk, &public_inputs, &proof).unwrap_or(false);
    }

    false
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::CString;

    #[test]
    fn deterministic_verifying_key_initializes_and_ffi_rejects_invalid_inputs_without_panic() {
        assert!(get_verifying_key().is_some());
        assert!(!verify_inference_payload(std::ptr::null(), 1, std::ptr::null()));

        let bad_payload = CString::new("deadbeef").expect("cstr");
        let bad_proof = CString::new("00").expect("cstr");
        assert!(!verify_inference_payload(
            bad_payload.as_ptr(),
            42,
            bad_proof.as_ptr(),
        ));
    }
}
