// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use alloc::string::String;

/// Minimal strictly verifiable register set.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Reg {
    R1,
    R2,
    R3,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TypeTag {
    I64,
    F60,
    Time,
    Unallocated,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Value {
    ImmI64(i64),
    Reg(Reg),
}

/// 25 Opcodes Maximum. Minimal ISA for Formal Proofs.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Opcode {
    /// Memory / Registers
    Alloc(Reg, TypeTag),
    LoadImm(Reg, i64),
    Mov(Reg, Reg),
    
    /// Math (Strict bounds checked)
    Add(Reg, Value),
    Sub(Reg, Value),
    Mul(Reg, Value),
    Div(Reg, Value),
    
    /// Causal Control
    Fork(String),
    Await(String),
    After(Reg, String),
    
    /// Ledger Mutation
    Emit(String, Reg),
    
    /// Termination
    Halt,
    CriticalHalt,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Instruction {
    pub opcode: Opcode,
}
