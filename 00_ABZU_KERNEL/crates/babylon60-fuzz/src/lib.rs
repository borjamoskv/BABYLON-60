//! Real robustness fuzz harnesses for BABYLON-60.
//! These drive the ACTUAL compiler parser and kernel evaluator (not stand-ins),
//! so libFuzzer / proptest inputs exercise real code paths.
use compiler::parser::parse;
use kernel::eval::step;
use kernel::state::MachineState;

/// Parse arbitrary bytes as source and return how many instructions were
/// recognized. Must never panic for any input (robustness invariant).
pub fn fuzz_parse_instruction(data: &[u8]) -> usize {
    let src = String::from_utf8_lossy(data);
    match parse(&src) {
        Ok(ast) => ast.instructions.len(),
        Err(_) => 0,
    }
}

/// Parse then drive the evaluator over the resulting program. Returns true when
/// execution reaches a terminal state (completion or a HaltReason) without
/// panicking — the property a fuzzer asserts.
pub fn fuzz_eval_step(data: &[u8]) -> bool {
    let src = String::from_utf8_lossy(data);
    let ast = match parse(&src) {
        Ok(ast) => ast,
        Err(_) => return true,
    };
    let mut state = MachineState::new();
    for instr in &ast.instructions {
        match step(state, instr) {
            Ok(next) => state = next,
            Err(_halt) => return true,
        }
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn parses_real_opcodes() {
        // Exercises the real parser: HALT, LOADIMM, FORK -> 3 instructions.
        assert_eq!(fuzz_parse_instruction(b"HALT\nLOADIMM 5\nFORK label"), 3);
    }

    proptest! {
        #[test]
        fn parse_and_eval_never_panic(data in proptest::collection::vec(any::<u8>(), 0..512)) {
            // Core fuzz invariant: no arbitrary byte string may panic the
            // parser or the evaluator.
            let _ = fuzz_parse_instruction(&data);
            prop_assert!(fuzz_eval_step(&data));
        }
    }
}
