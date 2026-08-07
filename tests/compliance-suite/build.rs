// C5-REAL EXERGY CERTIFIED
fn main() {
    println!("cargo:rerun-if-changed=c_src/verifiable_primitives.c");
    println!("cargo:rerun-if-changed=c_src/verifiable_primitives.h");

    cc::Build::new()
        .file("c_src/verifiable_primitives.c")
        .flag("-O3")
        .flag("-arch")
        .flag("arm64")
        .flag("-ffast-math")
        .warnings(false)
        .compile("verifiable_primitives");
}
