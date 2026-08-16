// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
fn main() {
    println!("cargo:rerun-if-changed=proto/c5_exergy.proto");

    // protoc vendored (protoc-bin-vendored): los runners CI no instalan protobuf.
    // prost-build honra la env var PROTOC antes de buscar en PATH — build hermético
    // cross-platform (ubuntu/macos/windows) sin pasos apt/brew/choco por OS.
    // SAFETY: el build script es single-threaded en este punto y la variable se fija
    // antes de cualquier lectura concurrente del entorno.
    unsafe {
        std::env::set_var(
            "PROTOC",
            protoc_bin_vendored::protoc_bin_path().expect("vendored protoc"),
        );
    }

    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile_protos(
            &["proto/c5_exergy.proto"],
            &["proto"]
        )
        .unwrap_or_else(|e| panic!("Failed to compile protos: {}", e));
}
