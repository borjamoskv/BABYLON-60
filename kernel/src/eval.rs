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
        let state = step(state, &alloc_instr).unwrap();
        assert_eq!(state.read_reg(Reg::R1).tag, TypeTag::I64);

        let load_instr = Instruction { opcode: Opcode::LoadImm(Reg::R1, 42) };
        let state = step(state, &load_instr).unwrap();
        assert_eq!(state.read_reg(Reg::R1).value, Value::ImmI64(42));

        let mov_instr = Instruction { opcode: Opcode::Mov(Reg::R2, Reg::R1) };
        let state = step(state, &mov_instr).unwrap();
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
}

