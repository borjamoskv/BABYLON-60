pub mod ast;
pub mod compiler;
pub mod parser;

use anyhow::Result;
pub use ast::Circuit;
pub use compiler::{generate_arkworks_rust, CompiledCircuit, Compiler, Gate};
pub use parser::parse_circuit;

/// Compiles a `.nul` circuit specification string into a `CompiledCircuit` IR and Arkworks Rust synthesizer code.
pub fn compile_nul_source(src: &str) -> Result<(CompiledCircuit, String)> {
    let circuit = parse_circuit(src)?;
    let compiler = Compiler::new();
    let compiled = compiler.compile(circuit);
    let arkworks_code = generate_arkworks_rust(&compiled);
    Ok((compiled, arkworks_code))
}
