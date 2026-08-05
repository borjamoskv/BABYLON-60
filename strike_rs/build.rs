// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
fn main() {
    println!("cargo:rerun-if-changed=proto/c5_exergy.proto");
    
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile_protos(
            &["proto/c5_exergy.proto"],
            &["proto"]
        )
        .unwrap_or_else(|e| panic!("Failed to compile protos: {}", e));
}
