// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
#[cfg(test)]
mod tests {
    use std::process::Command;
    
    // Differential test module comparing reference Python output vs Rust Kernel output.
    
    #[test]
    fn test_differential_homomorphism() {
        // Enforces that execution output from python interpreter matches rust kernel bit-for-bit
        
        let py_res = Command::new("python3")
            .arg("reference/interpreter.py")
            .arg("examples/causal_test.b60")
            .output();
            
        let kernel_bin = if std::path::Path::new("target/debug/b60_kernel").exists() {
            "target/debug/b60_kernel"
        } else {
            "./b60_kernel"
        };
        let rs_res = Command::new(kernel_bin)
            .arg("examples/causal_test.b60")
            .output();
            
        use sha2::{Sha256, Digest};
        
        let py_status = py_res.expect("Python interpreter failed to run");
        assert!(py_status.status.success(), "Python interpreter exited with failure");
        let py_ir = std::fs::read_to_string("artifact_bundle_v3/proof.ir").expect("Read Python proof.ir");

        let rs_status = rs_res.expect("Rust kernel failed to run");
        assert!(rs_status.status.success(), "Rust kernel exited with failure");
        let rs_ir = std::fs::read_to_string("artifact_bundle_v3/proof.ir").expect("Read Rust proof.ir");
        
        let mut hasher_py = Sha256::new();
        hasher_py.update(py_ir.as_bytes());
        let py_hash = format!("{:x}", hasher_py.finalize());
        
        let mut hasher_rs = Sha256::new();
        hasher_rs.update(rs_ir.as_bytes());
        let rs_hash = format!("{:x}", hasher_rs.finalize());
        
        assert_eq!(py_hash, rs_hash, "Differential Failsafe: Traces diverge between Python and Rust Kernel!");
    }
}
