use std::env;
use std::fs;
use std::path::Path;
use nul_zk::compile_nul_source;

fn main() {
    let source = r#"
circuit Polynomial {
    private a: Field,
    public c: Field,

    fn main() {
        // Evaluate c = 5 * a^2 + 2 * a + 1
        let a_sq = a * a;
        let term1 = a_sq * 5;
        let term2 = a * 2;
        let sum1 = term1 + term2;
        let temp = sum1 + 1;
        assert(temp == c);
    }
}
"#;

    let (_, arkworks_code) = compile_nul_source(source).expect("Failed to compile nul source");
    let out_dir = env::var_os("OUT_DIR").expect("BFT Fallback");
    let dest_path = Path::new(&out_dir).join("circuit.rs");
    fs::write(&dest_path, arkworks_code).expect("BFT Fallback");
    
    println!("cargo:rerun-if-changed=build.rs");
}
