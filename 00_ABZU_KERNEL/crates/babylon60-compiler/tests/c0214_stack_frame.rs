//! C0214: stack slots must never fall outside the reserved frame.
use babylon60_compiler::backend_x86::X86Backend;
use babylon60_compiler::ir::{BasicBlock, BlockId, IrOp, Reg, Terminator};

fn program(registers: usize) -> Vec<BasicBlock> {
    let mut instructions: Vec<IrOp> = (0..registers)
        .map(|n| IrOp::ConstInt {
            dest: Reg(n),
            val: n as i64,
        })
        .collect();
    // A call pushes a return address just below rsp: any slot there gets clobbered.
    instructions.push(IrOp::Alloc {
        dest: Reg(registers),
        size: 8,
    });
    vec![BasicBlock {
        id: BlockId(0),
        instructions,
        terminator: Terminator::Return,
    }]
}

fn reserved_frame(asm: &str) -> usize {
    let line = asm
        .lines()
        .find(|l| l.trim_start().starts_with("sub rsp,"))
        .expect("prologue");
    line.trim()
        .trim_start_matches("sub rsp,")
        .trim()
        .parse()
        .expect("frame size")
}

fn deepest_slot(asm: &str) -> usize {
    asm.match_indices("[rbp - ")
        .map(|(at, pat)| {
            let rest = &asm[at + pat.len()..];
            rest[..rest.find(']').unwrap()].parse::<usize>().unwrap()
        })
        .max()
        .expect("at least one slot")
}

#[test]
fn slots_stay_inside_the_reserved_frame() {
    for registers in [1, 30, 31, 32, 40, 200] {
        let asm = X86Backend::new()
            .compile(&program(registers))
            .expect("fits the kernel stack");
        let (frame, deepest) = (reserved_frame(&asm), deepest_slot(&asm));
        assert!(
            deepest <= frame,
            "C0214: {registers} registros: slot [rbp - {deepest}] fuera del marco de {frame} bytes"
        );
        assert_eq!(
            frame % 16,
            0,
            "el marco debe conservar la alineación de 16 bytes"
        );
    }
}

#[test]
fn frame_larger_than_the_kernel_stack_is_rejected() {
    // 3000 slots need ~24 KB, more than the 16 KB kernel stack.
    assert!(X86Backend::new().compile(&program(3000)).is_err());
}
