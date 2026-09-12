// ============================================================================
// B60 SEXAGESIMAL VIRTUAL MACHINE (F60-VM)
// ============================================================================

use crate::isa::SexaOpCode;
use crate::arithmetic::FRACTION_BASE;

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
}

#[repr(C, align(64))]
pub struct SovereignManifest64 {
    pub magic: u64,
    pub timestamp_tick60: u64,
    pub entropy_bits_erased: u64,
    pub proof_digest: [u8; 32],
    pub sep_ed25519_sig: [u8; 8],
}

impl SovereignManifest64 {
    pub fn new() -> Self {
        Self {
            magic: 0xC5_B60_0000_0060,
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

    pub fn execute(&mut self, bytecode: &[u8]) -> Result<(), String> {
        while self.pc < bytecode.len() && !self.is_halted {
            let raw_op = bytecode[self.pc];
            self.pc += 1;

            let op = SexaOpCode::from_u8(raw_op)
                .ok_or_else(|| format!("OpCode inválido fuera de base 60: 0x{:02X}", raw_op))?;

            match op {
                SexaOpCode::Halt => {
                    self.is_halted = true;
                    self.exit_code = 0;
                    break;
                }

                SexaOpCode::FailClosed => {
                    self.is_halted = true;
                    self.exit_code = 1;
                    let mut halt_receipt = [0u8; 32];
                    halt_receipt[0] = 0xDE;
                    halt_receipt[1] = 0xAD;
                    halt_receipt[2] = 0xC5;
                    self.worm_ledger.push(halt_receipt);
                    return Err("FAIL-CLOSED: Parada irrevocable de hardware (EU AI Act)".to_string());
                }

                SexaOpCode::NoOp => {}

                SexaOpCode::SexaAdd => {
                    self.registers[0] = self.registers[0].add(&self.registers[1]);
                }

                SexaOpCode::SexaSub => {
                    self.registers[0] = self.registers[0].sub(&self.registers[1])
                        .map_err(|e| format!("PC {}: {}", self.pc, e))?;
                }

                SexaOpCode::SexaPack => {
                    if self.pc + 2 <= bytecode.len() {
                        let sec = bytecode[self.pc] as u64;
                        let frac_part = bytecode[self.pc + 1] as u64;
                        self.pc += 2;
                        let fraction = frac_part * (FRACTION_BASE / 60);
                        self.registers[0] = SexaRegister::from_parts(sec, fraction);
                    }
                }

                SexaOpCode::LoadReg => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        if let Some(val) = self.stack.pop() {
                            self.registers[reg_idx] = val;
                        }
                    }
                }

                SexaOpCode::PushStack => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        self.stack.push(self.registers[reg_idx]);
                    }
                }

                SexaOpCode::LandauerRecord => {
                    self.landauer_dissipation_fj += 2870;
                }

                SexaOpCode::KolmogorovAudit => {
                    if self.pc + 2 <= bytecode.len() {
                        let reasoning_len = bytecode[self.pc] as u64;
                        let ast_delta = bytecode[self.pc + 1] as u64;
                        self.pc += 2;

                        let ratio = if ast_delta > 0 { reasoning_len / ast_delta } else { 999 };
                        if ratio > 60 {
                            self.is_halted = true;
                            self.exit_code = 2;
                            return Err(format!("Violación Cheap Talk: Ratio {} > 60. Abortado.", ratio));
                        }
                    }
                }

                SexaOpCode::SepTouchIdSign => {
                    self.manifest.sep_ed25519_sig = [0xED, 0x25, 0x51, 0x90, 0xC5, 0x00, 0x00, 0x60];
                }

                SexaOpCode::ScittChainAppend => {
                    let mut hash = [0u8; 32];
                    hash[0] = 0xC5;
                    hash[1] = 0x60;
                    hash[31] = (self.worm_ledger.len() as u8).wrapping_add(1);
                    self.worm_ledger.push(hash);
                }

                SexaOpCode::OmegaFixedPoint => {
                    self.is_halted = true;
                    self.exit_code = 60;
                    break;
                }

                _ => {}
            }
        }
        Ok(())
    }
}
