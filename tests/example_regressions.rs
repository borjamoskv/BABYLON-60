// Include the examples so `cargo test --workspace` discovers their unit tests.
// Their demonstration mains are not executed by this harness.
#[allow(dead_code)]
#[path = "../examples/poc_bifurcation_5_lifetimes.rs"]
mod lifetimes;

#[allow(dead_code)]
#[path = "../examples/poc_bifurcation_6_parser.rs"]
mod parser;

#[allow(dead_code)]
#[path = "../examples/navier_stokes_larsa_oracle.rs"]
mod oracle;

#[allow(dead_code)]
#[path = "../examples/poc_lean4_emitter.rs"]
mod lean_emitter;

#[test]
fn reallocating_a_borrowed_owner_cannot_authorize_write_or_free() {
    use lifetimes::{BorrowChecker, IrOp, Reg};
    let mut checker = BorrowChecker::new();
    let result = checker.check(&[
        IrOp::Alloc { dest: Reg(0) },
        IrOp::BorrowShared {
            dest: Reg(1),
            src: Reg(0),
        },
        IrOp::Alloc { dest: Reg(0) },
        IrOp::Write { dest: Reg(0) },
        IrOp::Free { ptr: Reg(0) },
    ]);
    assert!(result.is_err(), "live borrow was erased by Alloc");
    assert!(checker.reference_map.contains_key(&Reg(1)));
    assert!(checker.states.contains_key(&Reg(0)));
}

#[test]
fn borrow_destinations_cannot_overwrite_owners_or_live_references() {
    use lifetimes::{BorrowChecker, BorrowError, IrOp, Reg};
    for dest in [Reg(0), Reg(1)] {
        for op in [
            IrOp::BorrowShared { dest, src: Reg(2) },
            IrOp::BorrowMut { dest, src: Reg(2) },
            IrOp::Alloc { dest },
        ] {
            let mut checker = BorrowChecker::new();
            checker
                .check(&[
                    IrOp::Alloc { dest: Reg(0) },
                    IrOp::Alloc { dest: Reg(2) },
                    IrOp::BorrowShared {
                        dest: Reg(1),
                        src: Reg(0),
                    },
                ])
                .unwrap();
            let before = (checker.states.clone(), checker.reference_map.clone());
            assert_eq!(
                checker.check(&[op]),
                Err(BorrowError::RegisterAlreadyInUse(dest))
            );
            assert_eq!((checker.states, checker.reference_map), before);
        }
    }
}

#[test]
fn released_registers_can_be_reused() {
    use lifetimes::{BorrowChecker, IrOp, Reg};
    assert_eq!(
        BorrowChecker::new().check(&[
            IrOp::Alloc { dest: Reg(0) },
            IrOp::BorrowMut {
                dest: Reg(1),
                src: Reg(0)
            },
            IrOp::EndBorrow { ptr: Reg(1) },
            IrOp::Alloc { dest: Reg(1) },
            IrOp::Free { ptr: Reg(0) },
            IrOp::Alloc { dest: Reg(0) },
        ]),
        Ok(())
    );
}

#[test]
fn unknown_characters_cannot_hide_the_remaining_program() {
    for source in [
        "@ free sensor;",
        "let sensor = alloc Sensor; @ free sensor;",
        "free sensor; @",
    ] {
        assert_eq!(
            parser::Lexer::new(source).tokenize(),
            Err(parser::LexError::UnexpectedCharacter('@'))
        );
    }
}

#[test]
fn lexical_integer_overflow_is_an_error() {
    assert!(matches!(
        parser::Lexer::new("9223372036854775808").tokenize(),
        Err(parser::LexError::IntegerOutOfRange(_))
    ));
}

#[test]
fn valid_program_keeps_its_free_statement() {
    let tokens =
        parser::Lexer::new("let sensor = alloc Sensor; sensor.temperature = 42; free sensor;")
            .tokenize()
            .unwrap();
    let ast = parser::Parser::new(tokens).parse();
    assert_eq!(ast.len(), 3);
    assert!(matches!(&ast[2], parser::Stmt::Free(name) if name == "sensor"));
}
