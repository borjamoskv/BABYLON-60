// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use proof_ir::{AbstractState, Invariant, ProofIR, ProofObligation};
use crate::ir::{BasicBlock, IrOp};
use std::string::String;
use std::vec::Vec;

/// Genera ProofIR base (canónico / punto fijo)
pub fn generate_proof_ir() -> ProofIR {
    generate_proof_ir_from_blocks(&[])
}

/// Extrae y formaliza ProofIR desde la secuencia de bloques básicos del compilador
pub fn generate_proof_ir_from_blocks(blocks: &[BasicBlock]) -> ProofIR {
    let mut variables = Vec::new();
    let mut has_hardware_session = false;
    let mut has_heap_alloc = false;

    for block in blocks {
        for op in &block.instructions {
            match op {
                IrOp::Alloc { dest, size } => {
                    has_heap_alloc = true;
                    variables.push((
                        format!("reg_{}", dest.0),
                        format!("AffineHeapPointer(size={})", size),
                    ));
                }
                IrOp::HardwareAcquire { dest, peripheral_id } => {
                    has_hardware_session = true;
                    variables.push((
                        format!("reg_{}", dest.0),
                        format!("HardwareSessionState::Configured(peripheral={})", peripheral_id),
                    ));
                }
                _ => {}
            }
        }
    }

    let mut invariants = Vec::new();
    let mut obligations = Vec::new();

    // Invariante universal C5: Prevención de Double-Free
    invariants.push(Invariant {
        name: String::from("INV_C5_NO_DOUBLE_FREE"),
        condition: String::from("consume r = none when r = AffineResource.consumed"),
    });

    if has_heap_alloc {
        obligations.push(ProofObligation {
            name: String::from("proof_heap_no_double_free"),
            hypotheses: vec![
                String::from("r.state = AffineResource.consumed"),
            ],
            goal: String::from("consume r = none"),
        });
    }

    // Invariantes de sesión de hardware (Lean 4 C5Affine.lean)
    if has_hardware_session {
        invariants.push(Invariant {
            name: String::from("INV_SESSION_TERMINAL"),
            condition: String::from("hardwareStep s = HardwareSessionState.Consumed when s = .Consumed"),
        });
        invariants.push(Invariant {
            name: String::from("INV_FAULT_ISOLATION"),
            condition: String::from("hardwareStep (.ApoptosisFault code) ≠ .Active 1"),
        });

        obligations.push(ProofObligation {
            name: String::from("proof_hardware_session_linear_drain"),
            hypotheses: vec![
                String::from("s = HardwareSessionState.Active token"),
                String::from("hardwareStep s = .Consumed"),
            ],
            goal: String::from("session_consumed_is_terminal s"),
        });

        obligations.push(ProofObligation {
            name: String::from("proof_kudurru64_channel_isolation"),
            hypotheses: vec![
                String::from("st = MultiChannelState.mk chA chB"),
                String::from("st' = stepChannelA st"),
            ],
            goal: String::from("st'.chB = chB"),
        });
    }

    ProofIR {
        state: AbstractState { variables },
        invariants,
        obligations,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ir::{BlockId, Reg, Terminator};

    #[test]
    fn test_empty_proof_ir() {
        let ir = generate_proof_ir();
        assert_eq!(ir.invariants.len(), 1);
        assert_eq!(ir.invariants[0].name, "INV_C5_NO_DOUBLE_FREE");
        assert!(ir.obligations.is_empty());
        assert!(ir.state.variables.is_empty());
    }

    #[test]
    fn test_hardware_session_proof_ir_generation() {
        let block = BasicBlock {
            id: BlockId(0),
            instructions: vec![
                IrOp::HardwareAcquire {
                    dest: Reg(1),
                    peripheral_id: 64,
                },
                IrOp::HardwareTransition {
                    reg: Reg(1),
                    from_channel: 0,
                    to_channel: 1,
                },
                IrOp::HardwareRelease { reg: Reg(1) },
            ],
            terminator: Terminator::Return,
        };

        let ir = generate_proof_ir_from_blocks(&[block]);
        assert_eq!(ir.state.variables.len(), 1);
        assert_eq!(ir.state.variables[0].0, "reg_1");
        assert_eq!(ir.invariants.len(), 3);
        assert_eq!(ir.obligations.len(), 2);
        assert!(ir.obligations.iter().any(|o| o.name == "proof_hardware_session_linear_drain"));
        assert!(ir.obligations.iter().any(|o| o.name == "proof_kudurru64_channel_isolation"));
    }
}
