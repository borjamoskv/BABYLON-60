use nul_zk::{compile_nul_source, Gate};

#[test]
fn test_multiplier_circuit_compilation() {
    let source = r#"
circuit Multiplier {
    private a: Field,
    private b: Field,
    public c: Field,

    fn main() {
        let temp = a * b;
        assert(temp == c);
    }
}
"#;

    let (compiled, arkworks_code) = compile_nul_source(source).expect("Should compile circuit successfully");

    assert_eq!(compiled.name, "Multiplier");
    assert_eq!(compiled.public_inputs, vec!["c"]);
    assert_eq!(compiled.private_inputs, vec!["a", "b"]);

    // Expect 2 gates: Mul (a * b -> temp) and AssertEq (temp == c)
    assert_eq!(compiled.gates.len(), 2);
    match &compiled.gates[0] {
        Gate::Mul { out, lhs, rhs } => {
            assert_eq!(lhs, "a");
            assert_eq!(rhs, "b");
            assert_eq!(out, "v0");
        }
        _ => panic!("Expected Mul gate as first gate"),
    }

    match &compiled.gates[1] {
        Gate::AssertEq { lhs, rhs } => {
            assert_eq!(lhs, "v0");
            assert_eq!(rhs, "c");
        }
        _ => panic!("Expected AssertEq gate as second gate"),
    }

    // Verify generated Arkworks Rust code structure
    assert!(arkworks_code.contains("pub struct Multiplier<F: Field>"));
    assert!(arkworks_code.contains("impl<F: Field> ConstraintSynthesizer<F> for Multiplier<F>"));
    assert!(arkworks_code.contains("cs.new_input_variable"));
    assert!(arkworks_code.contains("cs.new_witness_variable"));
    assert!(arkworks_code.contains("cs.enforce_constraint"));
}
