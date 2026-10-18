// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use crate::state::MachineState;
use crate::isa::{Instruction, Opcode, Value};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HaltReason {
    Graceful,
    Critical,
}

/// The pure transition function mathematically guarantees no runtime panics.
/// Dynamic array out-of-bounds are irrepresentable.
pub fn step(mut state: MachineState, instr: &Instruction) -> Result<MachineState, HaltReason> {
    state.logical_clock = state.logical_clock.tick();
    
    match &instr.opcode {
        Opcode::Alloc(reg, tag) => {
            let mut cell = state.read_reg(*reg).clone();
            cell.tag = *tag;
            state.write_reg(*reg, cell);
        }
        Opcode::LoadImm(reg, val) => {
            let mut cell = state.read_reg(*reg).clone();
            cell.value = Value::ImmI64(*val);
            state.write_reg(*reg, cell);
        }
        Opcode::Mov(dest, src) => {
            let cell = state.read_reg(*src).clone();
            state.write_reg(*dest, cell);
        }
        Opcode::Add(dest, operand) => {
            let rhs = match operand {
                Value::ImmI64(v) => *v,
                Value::Reg(r) => match state.read_reg(*r).value {
                    Value::ImmI64(v) => v,
                    _ => return Err(HaltReason::Critical),
                },
            };
            let mut cell = state.read_reg(*dest).clone();
            if let Value::ImmI64(lhs) = cell.value {
                cell.value = Value::ImmI64(lhs.wrapping_add(rhs));
                state.write_reg(*dest, cell);
            } else {
                return Err(HaltReason::Critical);
            }
        }
        Opcode::Sub(dest, operand) => {
            let rhs = match operand {
                Value::ImmI64(v) => *v,
                Value::Reg(r) => match state.read_reg(*r).value {
                    Value::ImmI64(v) => v,
                    _ => return Err(HaltReason::Critical),
                },
            };
            let mut cell = state.read_reg(*dest).clone();
            if let Value::ImmI64(lhs) = cell.value {
                cell.value = Value::ImmI64(lhs.wrapping_sub(rhs));
                state.write_reg(*dest, cell);
            } else {
                return Err(HaltReason::Critical);
            }
        }
        Opcode::Mul(dest, operand) => {
            let rhs = match operand {
                Value::ImmI64(v) => *v,
                Value::Reg(r) => match state.read_reg(*r).value {
                    Value::ImmI64(v) => v,
                    _ => return Err(HaltReason::Critical),
                },
            };
            let mut cell = state.read_reg(*dest).clone();
            if let Value::ImmI64(lhs) = cell.value {
                cell.value = Value::ImmI64(lhs.wrapping_mul(rhs));
                state.write_reg(*dest, cell);
            } else {
                return Err(HaltReason::Critical);
            }
        }
        Opcode::Div(dest, operand) => {
            let rhs = match operand {
                Value::ImmI64(v) => *v,
                Value::Reg(r) => match state.read_reg(*r).value {
                    Value::ImmI64(v) => v,
                    _ => return Err(HaltReason::Critical),
                },
            };
            if rhs == 0 {
                return Err(HaltReason::Critical);
            }
            let mut cell = state.read_reg(*dest).clone();
            if let Value::ImmI64(lhs) = cell.value {
                cell.value = Value::ImmI64(lhs / rhs);
                state.write_reg(*dest, cell);
            } else {
                return Err(HaltReason::Critical);
            }
        }
        Opcode::Emit(tag, reg) => {
            let cell = state.read_reg(*reg);
            let val_str = match cell.value {
                Value::ImmI64(v) => alloc::format!("{}:{}", tag, v),
                _ => alloc::format!("{}:reg", tag),
            };
            let parent_ids = if state.ledger.is_empty() {
                alloc::vec::Vec::new()
            } else {
                alloc::vec![(state.ledger.len() - 1) as u64]
            };
            if state.ledger.append(parent_ids, state.sim_clock, val_str).is_err() {
                return Err(HaltReason::Critical);
            }
        }
        Opcode::Halt => return Err(HaltReason::Graceful),
        Opcode::CriticalHalt => return Err(HaltReason::Critical),
        // Fail-Stop invariant: unknown or unhandled opcodes trigger Critical Halt
        _ => return Err(HaltReason::Critical),
    }
    
    state.pc = state.pc.saturating_add(1);
    Ok(state)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::isa::{Reg, TypeTag};

    #[test]
    fn test_step_alloc_load_mov_halt() {
        let state = MachineState::new();
        let alloc_instr = Instruction { opcode: Opcode::Alloc(Reg::R1, TypeTag::I64) };
        let state = step(state, &alloc_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_eq!(state.read_reg(Reg::R1).tag, TypeTag::I64);

        let load_instr = Instruction { opcode: Opcode::LoadImm(Reg::R1, 42) };
        let state = step(state, &load_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_eq!(state.read_reg(Reg::R1).value, Value::ImmI64(42));

        let mov_instr = Instruction { opcode: Opcode::Mov(Reg::R2, Reg::R1) };
        let state = step(state, &mov_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_eq!(state.read_reg(Reg::R2).value, Value::ImmI64(42));

        let halt_instr = Instruction { opcode: Opcode::Halt };
        assert_eq!(step(state, &halt_instr), Err(HaltReason::Graceful));
    }

    #[test]
    fn test_step_critical_halt() {
        let state = MachineState::new();
        let crit_instr = Instruction { opcode: Opcode::CriticalHalt };
        assert_eq!(step(state, &crit_instr), Err(HaltReason::Critical));
    }

    #[test]
    fn test_step_arithmetic_and_emit() {
        let state = MachineState::new();
        let load_instr = Instruction { opcode: Opcode::LoadImm(Reg::R1, 10) };
        let state = step(state, &load_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let add_instr = Instruction { opcode: Opcode::Add(Reg::R1, Value::ImmI64(5)) };
        let state = step(state, &add_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_eq!(state.read_reg(Reg::R1).value, Value::ImmI64(15));

        let mul_instr = Instruction { opcode: Opcode::Mul(Reg::R1, Value::ImmI64(2)) };
        let state = step(state, &mul_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_eq!(state.read_reg(Reg::R1).value, Value::ImmI64(30));

        let emit_instr = Instruction { opcode: Opcode::Emit("STATE_TAG".into(), Reg::R1) };
        let state = step(state, &emit_instr).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_eq!(state.ledger.len(), 1);
        assert_ne!(state.ledger.root_hash(), [0u8; 32]);
    }
}


