//! C0201 / C0202: nothing may be certified as verified inference from a publicly
//! reproducible setup and a circuit that binds no model, input or output.
//!
//! The test forges a "valid" proof for an arbitrary payload hash without running any
//! inference, using only what is public in the source: the setup seed and the circuit.
use ark_bls12_381::{Bls12_381, Fr as BlsFr};
use ark_groth16::Groth16;
use ark_serialize::CanonicalSerialize;
use ark_snark::{CircuitSpecificSetupSNARK, SNARK};
use rand::SeedableRng;
use rand_chacha::ChaCha20Rng;
use std::ffi::CString;
use verifiable_inference_engine::{verify_inference_payload, verify_public_setup_relation_proof};

include!(concat!(env!("OUT_DIR"), "/inference_circuit.rs"));

#[test]
fn forged_proof_for_arbitrary_hash_is_not_certified() {
    // Public knowledge: the fixed setup seed from the library source.
    let mut setup_rng = ChaCha20Rng::seed_from_u64(0xC5C5C5C5C5C5C5C5u64);
    let empty = InferenceConstraint::<BlsFr> {
        weight: None,
        nonce: None,
        expected_hash: None,
    };
    let (pk, _vk) = Groth16::<Bls12_381>::setup(empty, &mut setup_rng).unwrap();

    // Attacker picks any "payload hash" and nonce; no model, input or output involved.
    let arbitrary_hash = BlsFr::from(0xDEADBEEFu64);
    let nonce = 7u64;
    let nonce_fr = BlsFr::from(nonce);
    let weight = arbitrary_hash * nonce_fr.inverse().unwrap();

    let circuit = InferenceConstraint::<BlsFr> {
        weight: Some(weight),
        nonce: Some(nonce_fr),
        expected_hash: Some(arbitrary_hash),
    };
    let mut prove_rng = ChaCha20Rng::seed_from_u64(1);
    let proof = Groth16::<Bls12_381>::prove(&pk, circuit, &mut prove_rng).unwrap();

    let mut proof_bytes = Vec::new();
    proof.serialize_compressed(&mut proof_bytes).unwrap();
    let mut hash_bytes = Vec::new();
    arbitrary_hash
        .serialize_compressed(&mut hash_bytes)
        .unwrap();

    let payload = CString::new(hex::encode(hash_bytes)).unwrap();
    let proof_hex = CString::new(hex::encode(proof_bytes)).unwrap();
    let certified = verify_inference_payload(payload.as_ptr(), nonce, proof_hex.as_ptr());
    assert!(
        !certified,
        "C0201/C0202: prueba fabricada sin inferencia certificada como inferencia verificada"
    );
    // The Groth16 math itself still holds for the demo relation; it just is not inference.
    assert!(verify_public_setup_relation_proof(
        payload.as_ptr(),
        nonce,
        proof_hex.as_ptr()
    ));
}
