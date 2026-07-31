// C5-REAL EXERGY CERTIFIED
//! Verifiable Inference Suite Engine Library
//!
//! Provides Rust FFI bindings for C SIMD 10-primitives engine and ZK-SNARK circuit provers
//! (BN254 R1CS & LogUp fractional lookup argument).

pub mod ffi;
pub mod zk_snark;

pub use ffi::{
    create_bn254_r1cs_proof, primitive_results_t, prove_and_verify_zk_logup,
    run_verifiable_primitives, verify_bn254_r1cs_proof,
};
pub use zk_snark::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ffi_run_verifiable_primitives() {
        let input_a = vec![1.0f32, 2.0f32, 3.0f32, 4.0f32];
        let input_b = vec![0.5f32, 1.5f32, 2.5f32, 3.5f32];
        let mut results = primitive_results_t {
            pi_inv: 0.0,
            pi_entr: 0.0,
            pi_zk: 0.0,
            pi_causal: 0.0,
            pi_ll: 0.0,
            pi_st: 0.0,
            pi_pmi: 0.0,
            pi_landauer: 0.0,
            pi_kl: 0.0,
            pi_dedup: 0,
        };

        unsafe {
            let res = run_verifiable_primitives(
                input_a.as_ptr(),
                input_b.as_ptr(),
                input_a.len(),
                &mut results,
            );
            assert_eq!(res, 0);
        }

        assert!(results.pi_inv > 0.0);
        assert!(results.pi_entr > 0.0);
        assert!(results.pi_landauer > 0.0);
    }

    #[test]
    fn test_ffi_prove_and_verify_zk_logup() {
        // Construct binary witness payload:
        // Table: [10, 20, 30]
        // Lookups: [20, 10, 20]
        let mut payload = Vec::new();
        // Table count = 3
        payload.extend_from_slice(&(3u32).to_le_bytes());
        payload.extend_from_slice(&(10u64).to_le_bytes());
        payload.extend_from_slice(&(20u64).to_le_bytes());
        payload.extend_from_slice(&(30u64).to_le_bytes());

        // Lookups count = 3
        payload.extend_from_slice(&(3u32).to_le_bytes());
        payload.extend_from_slice(&(20u64).to_le_bytes());
        payload.extend_from_slice(&(10u64).to_le_bytes());
        payload.extend_from_slice(&(20u64).to_le_bytes());

        unsafe {
            let res = prove_and_verify_zk_logup(payload.as_ptr(), payload.len());
            assert_eq!(res, 0);
        }
    }

    #[test]
    fn test_ffi_r1cs_proof_lifecycle() {
        // Witness: w = [1, 15, 3, 5] (where 3 * 5 = 15)
        let mut payload = Vec::new();
        payload.extend_from_slice(&(4u32).to_le_bytes()); // num_vars
        payload.extend_from_slice(&(2u32).to_le_bytes()); // num_pub
        payload.extend_from_slice(&(4u32).to_le_bytes()); // num_witness

        payload.extend_from_slice(&(1u64).to_le_bytes());  // w[0] = 1
        payload.extend_from_slice(&(15u64).to_le_bytes()); // w[1] = 15
        payload.extend_from_slice(&(3u64).to_le_bytes());  // w[2] = 3
        payload.extend_from_slice(&(5u64).to_le_bytes());  // w[3] = 5

        let mut proof_buf = vec![0u8; 2048];
        let mut out_len = 0usize;

        unsafe {
            let create_res = create_bn254_r1cs_proof(
                payload.as_ptr(),
                payload.len(),
                proof_buf.as_mut_ptr(),
                proof_buf.len(),
                &mut out_len,
            );
            assert_eq!(create_res, 0);
            assert!(out_len > 0);

            let verify_res = verify_bn254_r1cs_proof(
                proof_buf.as_ptr(),
                out_len,
                std::ptr::null(),
                0,
            );
            assert_eq!(verify_res, 0);
        }
    }
}
