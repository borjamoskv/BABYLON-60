use std::env;
use std::fs;
use std::path::Path;
use nul_zk::compile_nul_source;

fn main() {
    let source = r#"
circuit InferenceConstraint {
    private weight: Field,
    public nonce: Field,
    public expected_hash: Field,

    fn main() {
        let temp = weight * nonce;
        assert(temp == expected_hash);
    }
}
"#;

    let (_, arkworks_code) = compile_nul_source(source).expect("Failed to compile nul source");
    let out_dir = env::var_os("OUT_DIR").expect("BFT Fallback");
    let dest_path = Path::new(&out_dir).join("inference_circuit.rs");
    fs::write(&dest_path, arkworks_code).expect("BFT Fallback");
    
    println!("cargo:rerun-if-changed=build.rs");
}
