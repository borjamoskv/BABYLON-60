//! Bounded, effect-free control-flow proofs. This is not a model of the full ISA.
use crate::isa::SexaOpCode;
use std::collections::HashSet;

const MAX_BYTES: usize = 4096;
const VM_FUEL: u64 = 100_000;

#[derive(Clone, Copy, Debug)]
enum ControlOp {
    Halt,
    NoOp,
    Jump(u16),
}

impl ControlOp {
    fn width(self) -> usize {
        if matches!(self, Self::Jump(_)) {
            3
        } else {
            1
        }
    }

    fn lean(self) -> String {
        match self {
            Self::Halt => "ControlOp.halt".into(),
            Self::NoOp => "ControlOp.noop".into(),
            Self::Jump(target) => format!("ControlOp.jump {target}"),
        }
    }
}

fn decode(bytecode: &[u8]) -> Result<Vec<(usize, ControlOp)>, String> {
    if bytecode.is_empty() || bytecode.len() > MAX_BYTES {
        return Err(format!("proof input must contain 1..={MAX_BYTES} bytes"));
    }
    let mut instructions = Vec::new();
    let mut pc = 0;
    while pc < bytecode.len() {
        let op = match SexaOpCode::from_u8(bytecode[pc]) {
            Some(SexaOpCode::Halt) => ControlOp::Halt,
            Some(SexaOpCode::NoOp) => ControlOp::NoOp,
            Some(SexaOpCode::Jump) => {
                let operands = bytecode
                    .get(pc + 1..pc + 3)
                    .ok_or_else(|| format!("truncated JUMP at byte {pc}"))?;
                ControlOp::Jump(u16::from_le_bytes([operands[0], operands[1]]))
            }
            Some(op) => {
                return Err(format!(
                    "{} at byte {pc} is outside the verified HALT/NOOP/JUMP subset",
                    op.mnemonic()
                ))
            }
            None => {
                return Err(format!(
                    "invalid opcode 0x{:02X} at byte {pc}",
                    bytecode[pc]
                ))
            }
        };
        instructions.push((pc, op));
        pc += op.width();
    }
    for (pc, op) in &instructions {
        if let ControlOp::Jump(target) = op {
            if !instructions
                .iter()
                .any(|(start, _)| *start == usize::from(*target))
            {
                return Err(format!(
                    "JUMP at byte {pc} targets a non-instruction boundary: {target}"
                ));
            }
        }
    }
    Ok(instructions)
}

/// Emit a concrete control-flow proof only for decoded, terminating pure programs.
/// The Lean statements bind the encoding to the exact byte stream and evaluate
/// HALT/NOOP/JUMP with fixed-width PC/fuel. Other ISA effects are not certified.
pub fn emit(bytecode: &[u8], module_name: &str) -> Result<String, String> {
    if module_name.is_empty()
        || !module_name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_')
    {
        return Err("proof name must be an ASCII identifier".into());
    }
    let instructions = decode(bytecode)?;
    let mut pc = 0;
    let mut visited = HashSet::new();
    let mut steps = 0u64;
    let final_pc = loop {
        if !visited.insert(pc) {
            return Err(format!(
                "control-flow cycle at byte {pc}; successful HALT is not proved"
            ));
        }
        let (_, op) = instructions
            .iter()
            .find(|(start, _)| *start == pc)
            .ok_or_else(|| "execution leaves the program without HALT".to_string())?;
        steps += 1;
        if steps > VM_FUEL {
            return Err("proof exceeds the VM fuel limit".into());
        }
        match op {
            ControlOp::Halt => break pc + 1,
            ControlOp::NoOp => pc += 1,
            ControlOp::Jump(target) => pc = usize::from(*target),
        }
    };
    let bytes = bytecode
        .iter()
        .map(u8::to_string)
        .collect::<Vec<_>>()
        .join(", ");
    let program = instructions
        .iter()
        .map(|(pc, op)| format!("{{ pc := {pc}, op := {} }}", op.lean()))
        .collect::<Vec<_>>()
        .join(", ");
    Ok(format!(
        r#"import Init

set_option warningAsError true
set_option maxRecDepth 20000
set_option maxHeartbeats 4000000

-- {module_name}: concrete HALT/NOOP/JUMP control flow, not the full F60 ISA.
-- PC and fuel use the same 64-bit unsigned modular arithmetic as the target.
namespace BytecodeTrace

inductive ControlOp where
  | halt
  | noop
  | jump (target : BitVec 64)
  deriving Repr, BEq, DecidableEq

structure Instruction where
  pc : BitVec 64
  op : ControlOp
  deriving Repr, BEq, DecidableEq

def encodeOp : ControlOp → List (BitVec 8)
  | .halt => [0]
  | .noop => [2]
  | .jump target => [3, BitVec.ofNat 8 target.toNat, BitVec.ofNat 8 (target.toNat / 256)]

def traceBytes : List (BitVec 8) := [{bytes}]
def traceProgram : List Instruction := [{program}]

def contiguous : BitVec 64 → List Instruction → Bool
  | _, [] => true
  | pc, i :: rest => i.pc == pc && contiguous (pc + BitVec.ofNat 64 (encodeOp i.op).length) rest

def branchesAligned : Bool := traceProgram.all fun i =>
  match i.op with
  | .jump target => traceProgram.any (fun j => j.pc == target)
  | _ => true

structure VMState where
  pc : BitVec 64
  fuel : BitVec 64
  halted : Bool
  rejected : Bool
  deriving Repr, BEq, DecidableEq

def stepVM (s : VMState) : VMState :=
  if s.halted || s.rejected then s
  else if s.fuel == 0 then {{ s with rejected := true }}
  else match traceProgram.find? (fun i => i.pc == s.pc) with
    | none => {{ s with rejected := true }}
    | some i => match i.op with
      | .halt => {{ s with pc := s.pc + 1, fuel := s.fuel - 1, halted := true }}
      | .noop => {{ s with pc := s.pc + 1, fuel := s.fuel - 1 }}
      | .jump target => {{ s with pc := target, fuel := s.fuel - 1 }}

-- Structural recursion is only the proof-checking bound; VM words stay BitVec 64.
def run : Nat → VMState → VMState
  | 0, s => s
  | n + 1, s => run n (stepVM s)

def initial : VMState := {{ pc := 0, fuel := {VM_FUEL}, halted := false, rejected := false }}
def expected : VMState := {{ pc := {final_pc}, fuel := {fuel}, halted := true, rejected := false }}
def initialInvariant (s : VMState) : Bool :=
  s.pc == 0 && s.fuel == {VM_FUEL} && !s.halted && !s.rejected

theorem inv_inhabited : ∃ s, initialInvariant s = true := by
  exact ⟨initial, by decide⟩

theorem encoding_matches : traceProgram.flatMap (fun i => encodeOp i.op) = traceBytes := by decide
theorem instruction_boundaries_valid : contiguous 0 traceProgram = true := by decide
theorem jump_targets_valid : branchesAligned = true := by decide
theorem execution_reaches_halt : run {steps} initial = expected := by decide
theorem execution_accepted : (run {steps} initial).halted = true ∧
    (run {steps} initial).rejected = false := by decide

/-- info: 'BytecodeTrace.execution_reaches_halt' does not depend on any axioms -/
#guard_msgs in
#print axioms execution_reaches_halt

end BytecodeTrace
"#,
        fuel = VM_FUEL - steps
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::vm::F60VM;

    #[test]
    fn rejects_unknown_unsupported_truncated_and_invalid_target() {
        for bytes in [
            &[255][..],
            &[1],
            &[3],
            &[3, 0],
            &[3, 1, 0, 0],
            &[3, 20, 0, 0],
        ] {
            assert!(emit(bytes, "Invalid").is_err(), "{bytes:?}");
        }
    }

    #[test]
    fn rejects_non_halting_control_flow() {
        assert!(emit(&[3, 0, 0], "Loop").is_err());
        assert!(emit(&[2], "Fallthrough").is_err());
        assert!(emit(&[], "Empty").is_err());
    }

    #[test]
    fn accepts_exact_pure_control_flow_and_matches_vm_pc() {
        for bytes in [&[0][..], &[2, 0], &[3, 4, 0, 2, 0], &[2, 3, 4, 0, 0]] {
            let proof = emit(bytes, "Pure").unwrap();
            let mut vm = F60VM::new();
            vm.execute(bytes).unwrap();
            assert!(vm.is_halted);
            assert_eq!(vm.exit_code, 0);
            assert!(proof.contains(&format!("pc := {}, fuel :=", vm.pc)));
            assert!(proof.contains("theorem encoding_matches"));
        }
    }
}
