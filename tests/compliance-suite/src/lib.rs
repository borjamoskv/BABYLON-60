// C5-REAL EXERGY CERTIFIED
//! Verifiable Inference Suite Engine Library
//!
//! Provides Rust FFI bindings for C SIMD 10-primitives engine, ZK-SNARK circuit provers
//! (BN254 R1CS & LogUp fractional lookup argument), CF-GKAT algebraic verifier,
//! WASM Sandbox envelope, SCITT RFC 9942 COSE receipt emitter, and FOCUS budget controller.

pub mod cf_gkat;
pub mod ffi;
pub mod focus_budget;
pub mod scitt_receipt;
pub mod wasm_sandbox;
pub mod zk_snark;

pub use cf_gkat::*;
pub use ffi::*;
pub use focus_budget::*;
pub use scitt_receipt::*;
pub use wasm_sandbox::*;
pub use zk_snark::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_teff_end_to_end_pipeline() {
        // 1. Plan in CF-GKAT
        let expr = CFGKATExpr::Seq(
            Box::new(CFGKATExpr::Test("b_valid".to_string())),
            Box::new(CFGKATExpr::Action("exec_tool_a".to_string())),
        );
        let norm_expr = CFGKATEngine::normalize(&expr);
        let canonical_hash = CFGKATEngine::compute_canonical_hash(&norm_expr);
        assert_ne!(canonical_hash, [0u8; 32]);

        // 2. FOCUS Budget Check
        let controller = FOCUSBudgetController::new(FOCUSBudgetLimits::default());
        let tracker = FOCUSUsageTracker {
            current_tokens: 500,
            current_usd_micros: 1_000,
            current_wall_clock_ms: 50,
            current_tool_calls: 1,
            current_landauer_nats: 0.0,
        };
        let verdict = controller.evaluate_admission(&tracker, 100, 100);
        assert_eq!(verdict, AdmissionVerdict::Admitted);

        // 3. Execute inside WASM Sandbox Envelope
        let runner = WASMSandboxRunner::new(WASMSandboxConfig::default());
        let exec_result = runner.execute_tool("exec_tool_a", b"param=1", |payload| !payload.is_empty());
        assert!(exec_result.success);

        // 4. Emit SCITT RFC 9942 Receipt
        let emitter = SCITTReceiptEmitter::new();
        let payload = SCITTPayload {
            model_id: "claude-3-5-sonnet-20260802".to_string(),
            prompt_digest: [1u8; 32],
            artifact_digest: canonical_hash,
            sandbox_image_digest: [3u8; 32],
            output_digest: exec_result.output_state_hash,
            execution_cost_micros: 100,
            wall_clock_ms: exec_result.wall_clock_ms,
            contractual_cap_usd: 10_000,
            declared_scope_digest: [0u8; 32],
        };

        let receipt = emitter.generate_receipt(&payload);
        assert!(SCITTReceiptEmitter::verify_receipt(&receipt));
    }
}
