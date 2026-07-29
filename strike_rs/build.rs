fn main() {
    println!("cargo:rerun-if-changed=proto/c5_exergy.proto");
    
    tonic_build::configure()
        .build_server(true)
        .build_client(false)
        .compile_protos(
            &["proto/c5_exergy.proto"],
            &["proto"]
        )
        .unwrap_or_else(|e| panic!("Failed to compile protos: {}", e));
}
