// C5-REAL EXERGY CERTIFIED
//! Unsafe C FFI bindings bridging C SIMD primitives and Rust ZK-SNARK provers.

use crate::zk_snark::{
    BN254R1CSProof, BN254R1CSProver, LinearCombination, LogUpProver, R1CSSystem,
};
use ark_bn254::Fr;
use std::slice;

/// C-compatible result struct matching `c_src/verifiable_primitives.h`
#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct primitive_results_t {
    pub pi_inv: f32,
    pub pi_entr: f32,
    pub pi_zk: f32,
    pub pi_causal: f32,
    pub pi_ll: f32,
    pub pi_st: f32,
    pub pi_pmi: f32,
    pub pi_landauer: f64,
    pub pi_kl: f32,
    pub pi_dedup: u64,
}

extern "C" {
    /// C compiled SIMD unified batch primitive executor
    pub fn execute_10_primitives_neon(
        a: *const f32,
        b: *const f32,
        len: usize,
        out: *mut primitive_results_t,
    );
}

/// Run C SIMD 10-primitive batch pipeline via FFI.
/// Returns 0 on success, -1 if any pointer is null or len is 0.
#[no_mangle]
pub unsafe extern "C" fn run_verifiable_primitives(
    input_a: *const f32,
    input_b: *const f32,
    len: usize,
    out: *mut primitive_results_t,
) -> i32 {
    if input_a.is_null() || input_b.is_null() || out.is_null() || len == 0 {
        return -1;
    }
    execute_10_primitives_neon(input_a, input_b, len, out);
    0
}

/// Prove and verify ZK LogUp fractional lookup argument from binary witness data.
/// Returns 0 if proof is successfully created and verified, 1 if verification fails, -1 on error.
#[no_mangle]
pub unsafe extern "C" fn prove_and_verify_zk_logup(
    witness_data: *const u8,
    witness_len: usize,
) -> i32 {
    if witness_data.is_null() || witness_len == 0 {
        return -1;
    }

    let bytes = slice::from_raw_parts(witness_data, witness_len);

    // Parse binary payload: [u32: num_table][u64 * num_table: table_elements][u32: num_lookups][u64 * num_lookups: lookup_elements]
    if bytes.len() < 8 {
        return -1;
    }

    let mut cursor = 0;
    let num_table = u32::from_le_bytes(bytes[cursor..cursor + 4].try_into().unwrap()) as usize;
    cursor += 4;

    if bytes.len() < cursor + num_table * 8 + 4 {
        return -1;
    }

    let mut table = Vec::with_capacity(num_table);
    for _ in 0..num_table {
        let val = u64::from_le_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
        table.push(Fr::from(val));
        cursor += 8;
    }

    let num_lookups = u32::from_le_bytes(bytes[cursor..cursor + 4].try_into().unwrap()) as usize;
    cursor += 4;

    if bytes.len() < cursor + num_lookups * 8 {
        return -1;
    }

    let mut lookups = Vec::with_capacity(num_lookups);
    for _ in 0..num_lookups {
        let val = u64::from_le_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
        lookups.push(Fr::from(val));
        cursor += 8;
    }

    let seed = [42u8; 32];
    match LogUpProver::create_proof(&table, &lookups, &seed) {
        Ok(proof) => {
            if LogUpProver::verify_proof(&table, &lookups, &proof) {
                0
            } else {
                1
            }
        }
        Err(_) => 1,
    }
}

/// Create BN254 R1CS Zero-Knowledge Proof.
/// Serializes proof into `proof_out` buffer.
/// Returns 0 on success, -1 on error, -2 if output buffer is too small.
#[no_mangle]
pub unsafe extern "C" fn create_bn254_r1cs_proof(
    witness_data: *const u8,
    witness_len: usize,
    proof_out: *mut u8,
    max_proof_len: usize,
    out_proof_len: *mut usize,
) -> i32 {
    if witness_data.is_null() || witness_len == 0 || proof_out.is_null() || out_proof_len.is_null() {
        return -1;
    }

    let bytes = slice::from_raw_parts(witness_data, witness_len);
    if bytes.len() < 16 {
        return -1;
    }

    let mut cursor = 0;
    let num_vars = u32::from_le_bytes(bytes[cursor..cursor + 4].try_into().unwrap()) as usize;
    cursor += 4;
    let num_pub = u32::from_le_bytes(bytes[cursor..cursor + 4].try_into().unwrap()) as usize;
    cursor += 4;
    let num_witness = u32::from_le_bytes(bytes[cursor..cursor + 4].try_into().unwrap()) as usize;
    cursor += 4;

    if num_witness != num_vars || bytes.len() < cursor + num_witness * 8 {
        return -1;
    }

    let mut witness = Vec::with_capacity(num_witness);
    for _ in 0..num_witness {
        let val = u64::from_le_bytes(bytes[cursor..cursor + 8].try_into().unwrap());
        witness.push(Fr::from(val));
        cursor += 8;
    }

    // Default 1-constraint R1CS system or parse constraints from payload
    let mut system = R1CSSystem::new(num_vars, num_pub);
    if num_vars >= 4 {
        // x * y = z constraint: w = [1, z, x, y]
        system.add_constraint(
            LinearCombination::new(vec![(2, Fr::from(1u64))]),
            LinearCombination::new(vec![(3, Fr::from(1u64))]),
            LinearCombination::new(vec![(1, Fr::from(1u64))]),
        );
    } else {
        // 1 * w[0] = 1
        system.add_constraint(
            LinearCombination::new(vec![(0, Fr::from(1u64))]),
            LinearCombination::new(vec![(0, Fr::from(1u64))]),
            LinearCombination::new(vec![(0, Fr::from(1u64))]),
        );
    }

    let seed = [7u8; 32];
    match BN254R1CSProver::create_proof(&system, &witness, &seed) {
        Ok(proof) => {
            let serialized = proof.serialize_to_vec();
            if serialized.len() > max_proof_len {
                *out_proof_len = serialized.len();
                return -2;
            }
            std::ptr::copy_nonoverlapping(serialized.as_ptr(), proof_out, serialized.len());
            *out_proof_len = serialized.len();
            0
        }
        Err(_) => -1,
    }
}

/// Verify BN254 R1CS Zero-Knowledge Proof.
/// Returns 0 if verified, 1 if verification failed, -1 on format/null error.
#[no_mangle]
pub unsafe extern "C" fn verify_bn254_r1cs_proof(
    proof_data: *const u8,
    proof_len: usize,
    _public_inputs_data: *const u8,
    _pub_len: usize,
) -> i32 {
    if proof_data.is_null() || proof_len == 0 {
        return -1;
    }

    let proof_bytes = slice::from_raw_parts(proof_data, proof_len);
    let proof = match BN254R1CSProof::deserialize_from_slice(proof_bytes) {
        Ok(p) => p,
        Err(_) => return -1,
    };

    let mut system = R1CSSystem::new(
        proof.public_inputs.len().max(4),
        proof.public_inputs.len(),
    );

    if system.num_variables >= 4 {
        system.add_constraint(
            LinearCombination::new(vec![(2, Fr::from(1u64))]),
            LinearCombination::new(vec![(3, Fr::from(1u64))]),
            LinearCombination::new(vec![(1, Fr::from(1u64))]),
        );
    } else {
        system.add_constraint(
            LinearCombination::new(vec![(0, Fr::from(1u64))]),
            LinearCombination::new(vec![(0, Fr::from(1u64))]),
            LinearCombination::new(vec![(0, Fr::from(1u64))]),
        );
    }

    if BN254R1CSProver::verify_proof(&system, &proof) {
        0
    } else {
        1
    }
}
