#[cfg(test)]
mod tests {
    use std::process::Command;
    
    // Differential test module comparing reference Python output vs Rust Kernel output.
    
    #[test]
    fn test_differential_homomorphism() {
        // Enforces that execution output from python interpreter matches rust kernel bit-for-bit
        
        let py_res = Command::new("python3")
            .arg("reference/interpreter.py")
            .arg("causal_test.b60")
            .output();
            
        let rs_res = Command::new("./b60_kernel")
            .arg("causal_test.b60")
            .output();
            
        use sha2::{Sha256, Digest};
        
        let py_output = py_res.expect("Python interpreter failed to run");
        let rs_output = rs_res.expect("Rust kernel failed to run");
        
        let mut hasher_py = Sha256::new();
        hasher_py.update(&py_output.stdout);
        let py_hash = format!("{:x}", hasher_py.finalize());
        
        let mut hasher_rs = Sha256::new();
        hasher_rs.update(&rs_output.stdout);
        let rs_hash = format!("{:x}", hasher_rs.finalize());
        
        assert_eq!(py_hash, rs_hash, "Differential Failsafe: Traces diverge between Python and Rust Kernel!");
    }
}
