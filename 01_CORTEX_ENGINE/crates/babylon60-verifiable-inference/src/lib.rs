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

/// Llave de Verificación Determinista. Se genera de manera perezosa (Lazy)
/// usando una semilla termodinámica fija para asegurar que el Prover y Verifier
/// deriven el mismo Setup sin necesidad de serializar llaves masivas.
static VK: OnceLock<VerifyingKey<Bls12_381>> = OnceLock::new();

fn get_verifying_key() -> &'static VerifyingKey<Bls12_381> {
    VK.get_or_init(|| {
        let mut rng = ChaCha20Rng::seed_from_u64(0xC5C5C5C5C5C5C5C5u64); // Invariante Determinista
        let empty_circuit = InferenceConstraint::<BlsFr> {
            weight: None,
            nonce: None,
            expected_hash: None,
        };
        let (_, vk) = Groth16::<Bls12_381>::setup(empty_circuit, &mut rng)
            .expect("Fallo fatal en el Trusted Setup determinista");
        vk
    })
}

/// Convierte un string hexadecimal a un elemento del campo Fr (BLS12-381)
fn hex_to_fr(hex_str: &str) -> Option<BlsFr> {
    let clean_hex = hex_str.trim_start_matches("0x");
    let bytes = hex::decode(clean_hex).ok()?;
    BlsFr::deserialize_compressed(&*bytes).ok()
}

/// Motor de Verificación Causal-Determinist (Groth16 / ZK-SNARK)
/// La simulación Sha256 (LogUp/tlookup) ha sido PURGADA bajo el Framework C5-REAL.
///
/// public_inputs:
/// - nonce: El nonce termodinámico
/// - payload_hash: expected_hash del circuito
/// 
/// proof_hash: El string hexadecimal representando la prueba Groth16 serializada
#[no_mangle]
#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub extern "C" fn verify_inference_payload(
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
        
        let vk = get_verifying_key();
        return Groth16::<Bls12_381>::verify(vk, &public_inputs, &proof).unwrap_or(false);
    }

    false
}
