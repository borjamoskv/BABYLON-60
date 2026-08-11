// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use crate::ast::AST;
use kernel::isa::{Instruction, Opcode, Reg};
use std::vec::Vec;

pub fn parse(source: &str) -> AST {
    let mut instructions = Vec::new();
    for line in source.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with("//") {
            continue;
        }
        let parts: Vec<&str> = trimmed.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }
        match parts[0].to_uppercase().as_str() {
            "HALT" => instructions.push(Instruction { opcode: Opcode::Halt }),
            "CRITICAL_HALT" => instructions.push(Instruction { opcode: Opcode::CriticalHalt }),
            "FORK" => {
                let label = parts.get(1).unwrap_or(&"default").to_string();
                instructions.push(Instruction { opcode: Opcode::Fork(label) });
            }
            "LOADIMM" => {
                let val = parts.get(1).and_then(|s| s.parse::<i64>().ok()).unwrap_or(0);
                instructions.push(Instruction { opcode: Opcode::LoadImm(Reg::R1, val) });
            }
            _ => {}
        }
    }
    AST { instructions }
}
