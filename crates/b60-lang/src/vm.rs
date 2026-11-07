// ============================================================================
// B60 SEXAGESIMAL VIRTUAL MACHINE (F60-VM)
// ============================================================================

use crate::isa::SexaOpCode;
use crate::arithmetic::FRACTION_BASE;
use sha2::{Digest, Sha256};

pub const MANIFEST_RUNNING: u32 = 0x0000_0001;
pub const MANIFEST_POISONED: u32 = 0xDEAD_6060;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SexaRegister {
    pub seconds: u64,
    pub sexa_fraction: u64,
}

impl SexaRegister {
    pub fn zero() -> Self {
        SexaRegister { seconds: 0, sexa_fraction: 0 }
    }

    pub fn from_parts(seconds: u64, fraction: u64) -> Self {
        let carry = fraction / FRACTION_BASE;
        SexaRegister {
            seconds: seconds + carry,
            sexa_fraction: fraction % FRACTION_BASE,
        }
    }

    pub fn add(&self, other: &Self) -> Self {
        let total_frac = self.sexa_fraction + other.sexa_fraction;
        let carry = total_frac / FRACTION_BASE;
        SexaRegister {
            seconds: self.seconds + other.seconds + carry,
            sexa_fraction: total_frac % FRACTION_BASE,
        }
    }

    pub fn sub(&self, other: &Self) -> Result<Self, &'static str> {
        if self.seconds < other.seconds || (self.seconds == other.seconds && self.sexa_fraction < other.sexa_fraction) {
            return Err("Underflow sexagesimal: tiempo no puede ser negativo");
        }
        let (secs, frac) = if self.sexa_fraction >= other.sexa_fraction {
            (self.seconds - other.seconds, self.sexa_fraction - other.sexa_fraction)
        } else {
            (self.seconds - other.seconds - 1, (FRACTION_BASE + self.sexa_fraction) - other.sexa_fraction)
        };
        Ok(SexaRegister { seconds: secs, sexa_fraction: frac })
    }

    pub fn mul_scalar(&self, factor: u64) -> Self {
        let total_units = (self.seconds as u128 * FRACTION_BASE as u128 + self.sexa_fraction as u128) * (factor as u128);
        let secs = (total_units / FRACTION_BASE as u128) as u64;
        let frac = (total_units % FRACTION_BASE as u128) as u64;
        SexaRegister { seconds: secs, sexa_fraction: frac }
    }

    pub fn div_exact(&self, divisor: u64) -> Result<Self, &'static str> {
        if divisor == 0 {
            return Err("División por cero en Q60");
        }
        let total_units = self.seconds as u128 * FRACTION_BASE as u128 + self.sexa_fraction as u128;
        if !total_units.is_multiple_of(divisor as u128) {
            return Err("FALSATION_ERROR: TRUNCATION (División no exacta en base 60^4)");
        }
        let quot = total_units / (divisor as u128);
        Ok(SexaRegister {
            seconds: (quot / FRACTION_BASE as u128) as u64,
            sexa_fraction: (quot % FRACTION_BASE as u128) as u64,
        })
    }
}

#[repr(C, align(64))]
pub struct SovereignManifest64 {
    pub status_flag: u32,
    pub seq: u32,
    pub timestamp_tick60: u64,
    pub entropy_bits_erased: u64,
    pub proof_digest: [u8; 32],
    pub sep_ed25519_sig: [u8; 8],
}

const _MANIFEST_LAYOUT_ASSERT: () = {
    assert!(core::mem::size_of::<SovereignManifest64>() == 64);
    assert!(core::mem::align_of::<SovereignManifest64>() == 64);
};

impl Default for SovereignManifest64 {
    fn default() -> Self {
        Self::new()
    }
}

impl SovereignManifest64 {
    pub fn new() -> Self {
        Self {
            status_flag: MANIFEST_RUNNING,
            seq: 0,
            timestamp_tick60: 0,
            entropy_bits_erased: 0,
            proof_digest: [0u8; 32],
            sep_ed25519_sig: [0xED, 0x25, 0x51, 0x90, 0xC5, 0x00, 0x00, 0x60],
        }
    }
}

pub struct F60VM {
    pub registers: [SexaRegister; 8],
    pub pc: usize,
    pub stack: Vec<SexaRegister>,
    pub manifest: SovereignManifest64,
    pub landauer_dissipation_fj: u64,
    pub worm_ledger: Vec<[u8; 32]>,
    pub is_halted: bool,
    pub exit_code: u8,
}

impl Default for F60VM {
    fn default() -> Self {
        Self::new()
    }
}

impl F60VM {
    pub fn new() -> Self {
        F60VM {
            registers: [SexaRegister::zero(); 8],
            pc: 0,
            stack: Vec::with_capacity(64),
            manifest: SovereignManifest64::new(),
            landauer_dissipation_fj: 0,
            worm_ledger: Vec::new(),
            is_halted: false,
            exit_code: 0,
        }
    }

    fn poison_and_abort(&mut self, code: u8, msg: String) -> Result<(), String> {
        self.manifest.status_flag = MANIFEST_POISONED;
        self.is_halted = true;
        self.exit_code = code;
        let mut halt_receipt = [0u8; 32];
        halt_receipt[0] = 0xDE;
        halt_receipt[1] = 0xAD;
        halt_receipt[2] = 0x60;
        halt_receipt[3] = 0x60;
        self.worm_ledger.push(halt_receipt);
        Err(msg)
    }

    pub fn execute(&mut self, bytecode: &[u8]) -> Result<(), String> {
        let mut steps = 0usize;
        let max_steps = 100_000usize;

        while self.pc < bytecode.len() && !self.is_halted {
            steps += 1;
            if steps > max_steps {
                return self.poison_and_abort(
                    1,
                    "FAIL-CLOSED (0xDEAD_6060): Horizonte de combustible agotado (bucle no contractible)".to_string(),
                );
            }

            let raw_op = bytecode[self.pc];
            self.pc += 1;

            let op = match SexaOpCode::from_u8(raw_op) {
                Some(o) => o,
                None => {
                    return self.poison_and_abort(
                        1,
                        format!("OpCode inválido fuera de base 60: 0x{:02X}", raw_op),
                    );
                }
            };

            match op {
                SexaOpCode::Halt => {
                    self.is_halted = true;
                    self.exit_code = 0;
                    break;
                }

                SexaOpCode::FailClosed | SexaOpCode::QuarantineIsolate => {
                    return self.poison_and_abort(
                        1,
                        "FAIL-CLOSED (0xDEAD_6060): Parada irrevocable de hardware (EU AI Act Art. 14)".to_string(),
                    );
                }

                SexaOpCode::NoOp | SexaOpCode::YieldTick | SexaOpCode::MarkovEnter | SexaOpCode::MarkovExit | SexaOpCode::ForkSwarm => {}

                SexaOpCode::Jump => {
                    if self.pc + 2 <= bytecode.len() {
                        let target = u16::from_le_bytes([bytecode[self.pc], bytecode[self.pc + 1]]) as usize;
                        self.pc = target;
                    } else {
                        return self.poison_and_abort(1, "JUMP: operando de destino truncado".to_string());
                    }
                }

                SexaOpCode::JumpIfZero => {
                    if self.pc + 3 <= bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        let target = u16::from_le_bytes([bytecode[self.pc + 1], bytecode[self.pc + 2]]) as usize;
                        self.pc += 3;
                        if self.registers[reg_idx].seconds == 0 && self.registers[reg_idx].sexa_fraction == 0 {
                            self.pc = target;
                        }
                    } else {
                        return self.poison_and_abort(1, "JZ: operandos truncados".to_string());
                    }
                }

                SexaOpCode::JumpIfNotZero => {
                    if self.pc + 3 <= bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        let target = u16::from_le_bytes([bytecode[self.pc + 1], bytecode[self.pc + 2]]) as usize;
                        self.pc += 3;
                        if self.registers[reg_idx].seconds != 0 || self.registers[reg_idx].sexa_fraction != 0 {
                            self.pc = target;
                        }
                    } else {
                        return self.poison_and_abort(1, "JNZ: operandos truncados".to_string());
                    }
                }

                SexaOpCode::SexaAdd => {
                    self.registers[0] = self.registers[0].add(&self.registers[1]);
                }

                SexaOpCode::SexaSub => {
                    match self.registers[0].sub(&self.registers[1]) {
                        Ok(res) => self.registers[0] = res,
                        Err(e) => return self.poison_and_abort(1, format!("PC {}: {}", self.pc, e)),
                    }
                }

                SexaOpCode::SexaMulRational => {
                    let factor = self.registers[1].seconds;
                    self.registers[0] = self.registers[0].mul_scalar(factor);
                }

                SexaOpCode::SexaDivRational => {
                    let divisor = self.registers[1].seconds;
                    match self.registers[0].div_exact(divisor) {
                        Ok(res) => self.registers[0] = res,
                        Err(e) => return self.poison_and_abort(1, format!("PC {}: {}", self.pc, e)),
                    }
                }

                SexaOpCode::SexaMod60 => {
                    self.registers[0].seconds %= 60;
                }

                SexaOpCode::SexaFloor => {
                    self.registers[0].sexa_fraction = 0;
                }

                SexaOpCode::SexaCeil => {
                    if self.registers[0].sexa_fraction > 0 {
                        self.registers[0].seconds += 1;
                        self.registers[0].sexa_fraction = 0;
                    }
                }

                SexaOpCode::SexaAbs => {}

                SexaOpCode::SexaPack => {
                    if self.pc + 2 <= bytecode.len() {
                        let sec = bytecode[self.pc] as u64;
                        let frac_part = bytecode[self.pc + 1] as u64;
                        self.pc += 2;
                        let fraction = frac_part * (FRACTION_BASE / 60);
                        self.registers[0] = SexaRegister::from_parts(sec, fraction);
                    } else {
                        return self.poison_and_abort(1, "SEXA_PACK: operandos truncados".to_string());
                    }
                }

                SexaOpCode::LoadReg => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        if let Some(val) = self.stack.pop() {
                            self.registers[reg_idx] = val;
                        }
                    } else {
                        return self.poison_and_abort(1, "LOAD_REG: operando truncado".to_string());
                    }
                }

                SexaOpCode::StoreReg => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        self.manifest.timestamp_tick60 = self.registers[reg_idx].seconds;
                        self.manifest.seq = self.manifest.seq.wrapping_add(2);
                    } else {
                        return self.poison_and_abort(1, "STORE_REG: operando truncado".to_string());
                    }
                }

                SexaOpCode::ManifestSync | SexaOpCode::ManifestAcquire => {
                    self.manifest.seq = self.manifest.seq.wrapping_add(2);
                    self.manifest.timestamp_tick60 = self.registers[0].seconds;
                }

                SexaOpCode::PushStack => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        self.stack.push(self.registers[reg_idx]);
                    } else {
                        return self.poison_and_abort(1, "PUSH: operando truncado".to_string());
                    }
                }

                SexaOpCode::PopStack => {
                    let _ = self.stack.pop();
                }

                SexaOpCode::SwapStack => {
                    let len = self.stack.len();
                    if len >= 2 {
                        self.stack.swap(len - 1, len - 2);
                    }
                }

                SexaOpCode::LandauerRecord => {
                    self.landauer_dissipation_fj += 2870;
                    self.manifest.entropy_bits_erased += 1;
                }

                SexaOpCode::KolmogorovAudit => {
                    if self.pc + 2 <= bytecode.len() {
                        let reasoning_len = bytecode[self.pc] as u64;
                        let ast_delta = bytecode[self.pc + 1] as u64;
                        self.pc += 2;

                        let ratio = reasoning_len.checked_div(ast_delta).unwrap_or(999);
                        if ratio > 60 {
                            return self.poison_and_abort(
                                2,
                                format!("Violación Cheap Talk: Ratio {} > 60. Abortado.", ratio),
                            );
                        }
                    } else {
                        return self.poison_and_abort(1, "KOLMOGOROV_AUDIT: operandos truncados".to_string());
                    }
                }

                SexaOpCode::SepTouchIdSign => {
                    self.manifest.sep_ed25519_sig = [0xED, 0x25, 0x51, 0x90, 0xC5, 0x00, 0x00, 0x60];
                }

                SexaOpCode::ScittChainAppend => {
                    let mut hasher = Sha256::new();
                    hasher.update(b"B60_WORM_COMMIT:");
                    if let Some(prev) = self.worm_ledger.last() {
                        hasher.update(prev);
                    }
                    hasher.update((self.pc as u64).to_le_bytes());
                    hasher.update(self.registers[0].seconds.to_le_bytes());
                    hasher.update(self.registers[0].sexa_fraction.to_le_bytes());
                    let digest: [u8; 32] = hasher.finalize().into();
                    self.manifest.proof_digest = digest;
                    self.manifest.seq = self.manifest.seq.wrapping_add(2);
                    self.worm_ledger.push(digest);
                }

                SexaOpCode::OmegaFixedPoint => {
                    self.is_halted = true;
                    self.exit_code = 60;
                    break;
                }

                unhandled => {
                    return self.poison_and_abort(
                        1,
                        format!(
                            "FAIL-CLOSED (0xDEAD_6060): OpCode {:?} (0x{:02X}) carece de sustrato verificado en F60-VM",
                            unhandled,
                            unhandled as u8
                        ),
                    );
                }
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_manifest_64b_layout_and_fail_closed_on_unimplemented_opcode() {
        assert_eq!(core::mem::size_of::<SovereignManifest64>(), 64);
        assert_eq!(core::mem::align_of::<SovereignManifest64>(), 64);

        let mut vm = F60VM::new();
        assert_eq!(vm.manifest.status_flag, MANIFEST_RUNNING);

        // Call (0x06) has no silent NoOp fallback: must trigger Fail-Closed (POISONED = 0xDEAD_6060)
        let res = vm.execute(&[SexaOpCode::Call as u8]);
        assert!(res.is_err());
        assert_eq!(vm.manifest.status_flag, MANIFEST_POISONED);
        assert_eq!(vm.exit_code, 1);
    }
}
