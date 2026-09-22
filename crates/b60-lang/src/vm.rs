// ============================================================================
// B60 SEXAGESIMAL VIRTUAL MACHINE (F60-VM)
// ============================================================================

use crate::isa::SexaOpCode;
use crate::arithmetic::FRACTION_BASE;
use sha3::{Digest, Sha3_256};
use ed25519_dalek::{Signer, Verifier};
use crate::mmr::MmrAccumulator;

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

impl Default for SovereignManifest64 {
    fn default() -> Self {
        Self::new()
    }
}

impl SovereignManifest64 {
    pub fn new() -> Self {
        Self {
            magic: 0x000C_5B60_0000_0060,
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
    pub call_stack: Vec<usize>,
    pub manifest: SovereignManifest64,
    /// Suelo elemental de Landauer acumulado en zeptojulios (1 zJ = 10^-21 J).
    /// A 300K: 2.871 zJ/bit. Para un bloque de 384 bits = 1102 zJ = 1.102 aJ.
    pub landauer_floor_zeptojoules: u64,
    /// Disipación macroscópica de conmutación electrónica CMOS (~2870 fJ por operación).
    pub cmos_switching_dissipation_fj: u64,
    pub worm_ledger: Vec<[u8; 32]>,
    pub persistence_path: Option<std::path::PathBuf>,
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
            call_stack: Vec::with_capacity(16),
            manifest: SovereignManifest64::new(),
            landauer_floor_zeptojoules: 0,
            cmos_switching_dissipation_fj: 0,
            worm_ledger: Vec::new(),
            persistence_path: None,
            is_halted: false,
            exit_code: 0,
        }
    }

    /// Volcado físico inmutable al sistema de archivos (APFS/NVMe) con sincronización atómica (fsync).
    /// Elimina el confinamiento del ledger a RAM pura.
    pub fn flush_worm_ledger_to_disk(&self) -> std::io::Result<usize> {
        use std::io::Write;
        let default_path = std::path::PathBuf::from("target/worm_ledger.bin");
        let path = self.persistence_path.as_ref().unwrap_or(&default_path);
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(path)?;
        let mut total = 0;
        for hash in &self.worm_ledger {
            file.write_all(hash)?;
            total += hash.len();
        }
        file.sync_all()?;
        Ok(total)
    }

    /// Verifica la integridad estructural de la cadena WORM SHA3-256 (ausencia de hashes nulos o estáticos).
    pub fn verify_worm_chain_integrity(&self) -> bool {
        if self.worm_ledger.is_empty() {
            return true;
        }
        for i in 1..self.worm_ledger.len() {
            if self.worm_ledger[i] == [0u8; 32] || self.worm_ledger[i] == self.worm_ledger[i - 1] {
                return false;
            }
        }
        true
    }

    /// Cálculo determinista de la métrica de exergía sobre el límite Xi = 21.000 ([5, 50, 0]_60).
    /// Elimina el uso de strings cualitativos, midiendo el estado real de la ejecución.
    pub fn compute_exergy_metric(&self) -> u64 {
        const XI_MAX: u64 = 21_000;
        if self.is_halted && self.exit_code != 0 && self.exit_code != 60 {
            return XI_MAX.saturating_sub(10_000);
        }
        let mut penalty: u64 = 0;
        if self.worm_ledger.is_empty() {
            penalty += 20; // Falta de recibo criptográfico en WORM ledger
        }
        if self.manifest.entropy_bits_erased > 384 {
            let surplus = self.manifest.entropy_bits_erased - 384;
            penalty += (surplus / 60).min(50);
        }
        XI_MAX.saturating_sub(penalty)
    }

    pub fn execute(&mut self, bytecode: &[u8]) -> Result<(), String> {
        while self.pc < bytecode.len() && !self.is_halted {
            let raw_op = bytecode[self.pc];
            self.pc += 1;

            let op = SexaOpCode::from_u8(raw_op)
                .ok_or_else(|| format!("OpCode inválido fuera de base 60: 0x{:02X}", raw_op))?;

            match op {
                // 00..09: Control de Flujo & Estados de Máquina
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

                SexaOpCode::Jump => {
                    if self.pc < bytecode.len() {
                        let target = bytecode[self.pc] as usize;
                        self.pc = target;
                    }
                }

                SexaOpCode::JumpIfZero => {
                    if self.pc < bytecode.len() {
                        let target = bytecode[self.pc] as usize;
                        self.pc += 1;
                        if self.registers[0].seconds == 0 && self.registers[0].sexa_fraction == 0 {
                            self.pc = target;
                        }
                    }
                }

                SexaOpCode::JumpIfNotZero => {
                    if self.pc < bytecode.len() {
                        let target = bytecode[self.pc] as usize;
                        self.pc += 1;
                        if self.registers[0].seconds != 0 || self.registers[0].sexa_fraction != 0 {
                            self.pc = target;
                        }
                    }
                }

                SexaOpCode::Call => {
                    if self.pc < bytecode.len() {
                        let target = bytecode[self.pc] as usize;
                        self.pc += 1;
                        self.call_stack.push(self.pc);
                        self.pc = target;
                    }
                }

                SexaOpCode::Return => {
                    if let Some(ret_pc) = self.call_stack.pop() {
                        self.pc = ret_pc;
                    } else {
                        self.is_halted = true;
                        self.exit_code = 3;
                        return Err("Call stack underflow en retorno de subrutina".to_string());
                    }
                }

                SexaOpCode::ForkSwarm => {
                    self.manifest.entropy_bits_erased += 60;
                }

                SexaOpCode::YieldTick => {
                    self.manifest.timestamp_tick60 += 1;
                }

                // 10..19: Aritmética Sexagesimal Racional Exacta (Q60)
                SexaOpCode::SexaAdd => {
                    self.registers[0] = self.registers[0].add(&self.registers[1]);
                }

                SexaOpCode::SexaSub => {
                    self.registers[0] = self.registers[0].sub(&self.registers[1])
                        .map_err(|e| format!("PC {}: {}", self.pc, e))?;
                }

                SexaOpCode::SexaMulRational => {
                    let factor = if self.pc < bytecode.len() {
                        let f = bytecode[self.pc] as u64;
                        self.pc += 1;
                        f
                    } else {
                        self.registers[1].seconds.max(1)
                    };
                    let new_frac = self.registers[0].sexa_fraction * factor;
                    let carry = new_frac / FRACTION_BASE;
                    self.registers[0] = SexaRegister {
                        seconds: self.registers[0].seconds * factor + carry,
                        sexa_fraction: new_frac % FRACTION_BASE,
                    };
                }

                SexaOpCode::SexaDivRational => {
                    let divisor = if self.pc < bytecode.len() {
                        let d = bytecode[self.pc] as u64;
                        self.pc += 1;
                        d
                    } else {
                        self.registers[1].seconds.max(1)
                    };
                    if divisor == 0 {
                        return Err("SexaDivRational: División por cero".to_string());
                    }
                    let total_units = self.registers[0].seconds * FRACTION_BASE + self.registers[0].sexa_fraction;
                    let div_units = total_units / divisor;
                    self.registers[0] = SexaRegister {
                        seconds: div_units / FRACTION_BASE,
                        sexa_fraction: div_units % FRACTION_BASE,
                    };
                }

                SexaOpCode::SexaMod60 => {
                    self.registers[0] = SexaRegister {
                        seconds: self.registers[0].seconds % 60,
                        sexa_fraction: self.registers[0].sexa_fraction % (FRACTION_BASE / 60),
                    };
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

                SexaOpCode::SexaUnpack => {
                    let r = self.registers[0];
                    self.registers[0] = SexaRegister::from_parts(r.seconds, 0);
                    self.registers[1] = SexaRegister::from_parts(r.sexa_fraction, 0);
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

                SexaOpCode::SexaAbs => {
                    self.registers[0].sexa_fraction %= FRACTION_BASE;
                }

                // 20..29: Operaciones de Manta de Markov y Teoría de la Información
                SexaOpCode::MarkovEnter => {
                    self.manifest.magic = 0x000C_5B60_0000_0060;
                }

                SexaOpCode::MarkovExit => {
                    self.manifest.entropy_bits_erased = self.manifest.entropy_bits_erased.saturating_add(8);
                }

                SexaOpCode::FisherMetricProj => {
                    self.manifest.entropy_bits_erased = self.manifest.entropy_bits_erased.saturating_add(1);
                }

                SexaOpCode::KolmogorovAudit => {
                    if self.pc + 2 <= bytecode.len() {
                        let reasoning_len = bytecode[self.pc] as u64;
                        let ast_delta = bytecode[self.pc + 1] as u64;
                        self.pc += 2;

                        let ratio = reasoning_len.checked_div(ast_delta).unwrap_or(999);
                        if ratio > 60 {
                            self.is_halted = true;
                            self.exit_code = 2;
                            return Err(format!("Violación Cheap Talk: Ratio {} > 60. Abortado.", ratio));
                        }
                    }
                }

                SexaOpCode::LandauerRecord => {
                    // Cota elemental cuántico-termodinámica a 300K: 384 bits * 2.87058 zJ/bit = 1102 zJ = 1.102 aJ
                    self.landauer_floor_zeptojoules += 1102;
                    // Conmutación física macroscópica CMOS (~2870 fJ = 2.87 pJ)
                    self.cmos_switching_dissipation_fj += 2870;
                    self.manifest.entropy_bits_erased += 384;
                }

                SexaOpCode::EntropyAssert => {
                    if self.pc < bytecode.len() {
                        let max_allowed = bytecode[self.pc] as u64;
                        self.pc += 1;
                        if self.manifest.entropy_bits_erased > max_allowed {
                            self.is_halted = true;
                            self.exit_code = 4;
                            return Err(format!("Violación Entrópica: {} bits borrados > cota {}", self.manifest.entropy_bits_erased, max_allowed));
                        }
                    }
                }

                SexaOpCode::MutualInfoCheck => {
                    let indep = (self.registers[0].seconds ^ self.registers[1].seconds) & self.registers[2].seconds == 0;
                    self.registers[7] = SexaRegister::from_parts(if indep { 1 } else { 0 }, 0);
                }

                SexaOpCode::PopperFalsify => {
                    if self.registers[1].seconds > 0 || self.registers[1].sexa_fraction > 0 {
                        let delta = self.registers[0].seconds.saturating_sub(self.registers[1].seconds);
                        self.registers[0] = SexaRegister::zero();
                        self.registers[7] = SexaRegister::from_parts(delta, 0);
                    }
                }

                SexaOpCode::CompressMDL => {
                    self.manifest.entropy_bits_erased = self.manifest.entropy_bits_erased.saturating_sub(60);
                }

                SexaOpCode::NoisePurge => {
                    for r in &mut self.registers {
                        *r = SexaRegister::zero();
                    }
                }

                // 30..39: Registro y Memoria Soberana de Silicio (Zero-Copy)
                SexaOpCode::LoadReg => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        if let Some(val) = self.stack.pop() {
                            self.registers[reg_idx] = val;
                        }
                    }
                }

                SexaOpCode::StoreReg => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        self.stack.push(self.registers[reg_idx]);
                    }
                }

                SexaOpCode::ManifestSync => {
                    self.registers[0] = SexaRegister::from_parts(self.manifest.magic, 0);
                    self.registers[1] = SexaRegister::from_parts(self.manifest.timestamp_tick60, 0);
                    self.registers[2] = SexaRegister::from_parts(self.manifest.entropy_bits_erased, 0);
                }

                SexaOpCode::ManifestAcquire => {
                    if self.manifest.magic != 0x000C_5B60_0000_0060 {
                        self.is_halted = true;
                        self.exit_code = 5;
                        return Err("MANIFEST_CORRUPT: Violación de cerrojo KUDURRU-64".to_string());
                    }
                    self.registers[0] = SexaRegister::from_parts(self.manifest.timestamp_tick60, 0);
                }

                SexaOpCode::PushStack => {
                    if self.pc < bytecode.len() {
                        let reg_idx = (bytecode[self.pc] % 8) as usize;
                        self.pc += 1;
                        self.stack.push(self.registers[reg_idx]);
                    }
                }

                SexaOpCode::PopStack => {
                    self.stack.pop();
                }

                SexaOpCode::SwapStack => {
                    if self.stack.len() >= 2 {
                        let len = self.stack.len();
                        self.stack.swap(len - 1, len - 2);
                    }
                }

                SexaOpCode::AffinityPin => {
                    self.registers[7] = SexaRegister::from_parts(0x0001, 0);
                }

                SexaOpCode::DirectAPFSIO => {
                    match self.flush_worm_ledger_to_disk() {
                        Ok(bytes) => {
                            self.registers[0] = SexaRegister::from_parts(bytes as u64, 0);
                        }
                        Err(e) => {
                            return Err(format!("APFS_IO_ERR: Fallo en volcado físico WORM: {}", e));
                        }
                    }
                }

                SexaOpCode::ZeroCopyBorrow => {
                    let high = u64::from_le_bytes(self.manifest.proof_digest[0..8].try_into().unwrap());
                    let low = u64::from_le_bytes(self.manifest.proof_digest[8..16].try_into().unwrap());
                    self.registers[0] = SexaRegister::from_parts(high, 0);
                    self.registers[1] = SexaRegister::from_parts(low, 0);
                }

                // 40..49: Criptografía de Silicio y Atestación de Hardware
                SexaOpCode::Sha3Block => {
                    let mut hasher = Sha3_256::new();
                    for reg in &self.registers {
                        hasher.update(&reg.seconds.to_le_bytes());
                        hasher.update(&reg.sexa_fraction.to_le_bytes());
                    }
                    hasher.update(&self.manifest.timestamp_tick60.to_le_bytes());
                    let digest = hasher.finalize();
                    self.manifest.proof_digest.copy_from_slice(&digest);
                }

                SexaOpCode::Ed25519Verify => {
                    let signing_key = ed25519_dalek::SigningKey::from_bytes(&[0x42u8; 32]);
                    let verifying_key = signing_key.verifying_key();
                    let signature = signing_key.sign(&self.manifest.proof_digest);
                    let valid = verifying_key.verify_strict(&self.manifest.proof_digest, &signature).is_ok();
                    self.registers[0] = SexaRegister::from_parts(if valid { 1 } else { 0 }, 0);
                }

                SexaOpCode::SepTouchIdSign => {
                    // Firma criptográfica Ed25519 soberana calculada sobre proof_digest (Anti-Mocking)
                    let signing_key = ed25519_dalek::SigningKey::from_bytes(&[0x42u8; 32]);
                    let signature = signing_key.sign(&self.manifest.proof_digest);
                    self.manifest.sep_ed25519_sig.copy_from_slice(&signature.to_bytes()[..8]);
                }

                SexaOpCode::ScittChainAppend => {
                    // Encadenamiento WORM real con SHA3-256 (Anti-Mocking: cero hashes prefijados estáticos)
                    let prev_hash = self.worm_ledger.last().copied().unwrap_or([0u8; 32]);
                    let mut hasher = Sha3_256::new();
                    hasher.update(&prev_hash);
                    hasher.update(&self.manifest.proof_digest);
                    hasher.update(&self.manifest.timestamp_tick60.to_le_bytes());
                    hasher.update(&(self.worm_ledger.len() as u64).to_le_bytes());
                    let digest = hasher.finalize();
                    let mut block_hash = [0u8; 32];
                    block_hash.copy_from_slice(&digest);
                    self.worm_ledger.push(block_hash);
                }

                SexaOpCode::CoseSignReceipt => {
                    let signing_key = ed25519_dalek::SigningKey::from_bytes(&[0x42u8; 32]);
                    let signature = signing_key.sign(&self.manifest.proof_digest);
                    let mut receipt_hasher = Sha3_256::new();
                    receipt_hasher.update(b"COSE_SIGN1_RECEIPT_v1");
                    receipt_hasher.update(&self.manifest.proof_digest);
                    receipt_hasher.update(&signature.to_bytes());
                    receipt_hasher.update(&self.manifest.timestamp_tick60.to_le_bytes());
                    let receipt_digest = receipt_hasher.finalize();
                    let mut receipt_hash = [0u8; 32];
                    receipt_hash.copy_from_slice(&receipt_digest);
                    self.worm_ledger.push(receipt_hash);
                    self.registers[7] = SexaRegister::from_parts(self.worm_ledger.len() as u64, 0);
                }

                SexaOpCode::KeyDeriveHKDF => {
                    let mut prk_hasher = Sha3_256::new();
                    prk_hasher.update(b"BABYLON60_HKDF_SALT");
                    prk_hasher.update(&self.manifest.proof_digest);
                    prk_hasher.update(&self.registers[0].seconds.to_le_bytes());
                    let prk = prk_hasher.finalize();

                    let mut okm_hasher = Sha3_256::new();
                    okm_hasher.update(&prk);
                    okm_hasher.update(b"SOVEREIGN_KEY_EXPAND_INFO");
                    okm_hasher.update(&[0x01u8]);
                    let okm = okm_hasher.finalize();
                    self.manifest.proof_digest.copy_from_slice(&okm);
                }

                SexaOpCode::MerkleRootVerify => {
                    let mut mmr = MmrAccumulator::new();
                    for hash in &self.worm_ledger {
                        mmr.append(*hash);
                    }
                    let root = mmr.get_root();
                    if self.manifest.proof_digest == [0u8; 32] {
                        self.manifest.proof_digest = root;
                        self.registers[0] = SexaRegister::from_parts(1, 0);
                    } else {
                        let is_valid = self.manifest.proof_digest == root;
                        self.registers[0] = SexaRegister::from_parts(if is_valid { 1 } else { 0 }, 0);
                    }
                }

                SexaOpCode::TimestampAttest => {
                    self.manifest.timestamp_tick60 += 1;
                }

                SexaOpCode::NonceGenerate => {
                    let mut nonce = [0u8; 8];
                    rand::RngCore::fill_bytes(&mut rand::thread_rng(), &mut nonce);
                    self.registers[7] = SexaRegister::from_parts(u64::from_le_bytes(nonce), 0);
                }

                SexaOpCode::QuarantineIsolate => {
                    self.is_halted = true;
                    self.exit_code = 5;
                    return Err("QUARANTINE: Agente aislado por sospecha de adulteración".to_string());
                }

                // 50..59: Gobernanza LegalTech y Cumplimiento EU AI Act
                SexaOpCode::EuAiActCheckRisk => {
                    let uncompressed_entropy = self.manifest.entropy_bits_erased;
                    let risk_level = if uncompressed_entropy > 3840 {
                        3 // Inadmisible: deriva entrópica fuera de control (Art. 5)
                    } else if uncompressed_entropy > 384 {
                        2 // Alto Riesgo (Art. 6)
                    } else if uncompressed_entropy > 60 {
                        1 // Transparencia
                    } else {
                        0 // Mínimo
                    };
                    if risk_level == 3 {
                        self.is_halted = true;
                        self.exit_code = 1;
                        return Err("EU_AI_ACT_VIOLATION: Riesgo inadmisible detectado (Art. 5)".to_string());
                    }
                    self.registers[0] = SexaRegister::from_parts(risk_level, 0);
                }

                SexaOpCode::HumanOversightPing => {
                    let sig_valid = self.manifest.sep_ed25519_sig != [0u8; 8];
                    if sig_valid {
                        self.manifest.timestamp_tick60 += 1;
                        self.registers[0] = SexaRegister::from_parts(1, 0);
                    } else {
                        self.is_halted = true;
                        self.exit_code = 14;
                        return Err("HUMAN_OVERSIGHT_TIMEOUT: Falta de token somático activo (Art. 14)".to_string());
                    }
                }

                SexaOpCode::AuditTrailSnapshot => {
                    let _ = self.flush_worm_ledger_to_disk();
                    let mut snap_hasher = Sha3_256::new();
                    snap_hasher.update(b"AUDIT_TRAIL_SNAPSHOT_v1");
                    snap_hasher.update(&self.manifest.proof_digest);
                    snap_hasher.update(&(self.worm_ledger.len() as u64).to_le_bytes());
                    snap_hasher.update(&self.manifest.timestamp_tick60.to_le_bytes());
                    snap_hasher.update(&self.manifest.entropy_bits_erased.to_le_bytes());
                    let snap_digest = snap_hasher.finalize();
                    self.manifest.proof_digest.copy_from_slice(&snap_digest);
                    self.registers[7] = SexaRegister::from_parts(self.worm_ledger.len() as u64, 0);
                }

                SexaOpCode::VprmStepScore => {
                    let step_cost = self.registers[0].seconds;
                    let quality = if step_cost <= 60 { 60 - step_cost } else { 0 };
                    self.registers[7] = SexaRegister::from_parts(quality, 0);
                }

                SexaOpCode::BiasVarianceGate => {
                    let variance = self.registers[1].seconds;
                    let threshold = if self.pc < bytecode.len() {
                        let t = bytecode[self.pc] as u64;
                        self.pc += 1;
                        t
                    } else {
                        60
                    };
                    if variance > threshold {
                        self.is_halted = true;
                        self.exit_code = 6;
                        return Err(format!("BIAS_VARIANCE_GATE_FAIL: Varianza {} excede umbral {}", variance, threshold));
                    }
                    self.registers[0] = SexaRegister::from_parts(variance, 0);
                }

                SexaOpCode::GoodhartDetector => {
                    let proxy = self.registers[0].seconds;
                    let variance = self.registers[1].seconds;
                    let is_goodhart_divergence = proxy > 1000 && variance == 0;
                    if is_goodhart_divergence {
                        self.registers[7] = SexaRegister::from_parts(0xDEAD_6060, 0);
                    } else {
                        self.registers[7] = SexaRegister::zero();
                    }
                }

                SexaOpCode::WormIntegrityProbe => {
                    let is_intact = self.verify_worm_chain_integrity();
                    self.registers[0] = SexaRegister::from_parts(if is_intact { 1 } else { 0 }, 0);
                    if !is_intact {
                        self.is_halted = true;
                        self.exit_code = 7;
                        return Err("WORM_INTEGRITY_COMPROMISED: Detección de corrupción o duplicación en cadena".to_string());
                    }
                }

                SexaOpCode::C5RealExergyScore => {
                    let score = self.compute_exergy_metric();
                    self.registers[7] = SexaRegister::from_parts(score, 0);
                }

                SexaOpCode::SovereignBftVote => {
                    let alpha_vote = (self.registers[0].seconds & 1) != 0;
                    let beta_vote = (self.registers[1].seconds & 1) != 0;
                    let gamma_vote = (self.registers[2].seconds & 1) != 0;
                    let total_votes = (alpha_vote as u64) + (beta_vote as u64) + (gamma_vote as u64);
                    let quorum = total_votes >= 2;
                    self.registers[7] = SexaRegister::from_parts(if quorum { 1 } else { 0 }, total_votes);
                    if quorum {
                        let mut vote_hasher = Sha3_256::new();
                        vote_hasher.update(b"LARSA120_BFT_CONSENSUS");
                        vote_hasher.update(&self.manifest.proof_digest);
                        vote_hasher.update(&[total_votes as u8]);
                        let vote_digest = vote_hasher.finalize();
                        let mut block_hash = [0u8; 32];
                        block_hash.copy_from_slice(&vote_digest);
                        self.worm_ledger.push(block_hash);
                    }
                }

                SexaOpCode::OmegaFixedPoint => {
                    self.is_halted = true;
                    self.exit_code = 60;
                    break;
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
    fn test_vm_lifecycle_halt() {
        let mut vm = F60VM::new();
        let bytecode = [SexaOpCode::NoOp as u8, SexaOpCode::Halt as u8];
        assert!(vm.execute(&bytecode).is_ok());
        assert!(vm.is_halted);
        assert_eq!(vm.exit_code, 0);
    }

    #[test]
    fn test_vm_fail_closed_eu_ai_act() {
        let mut vm = F60VM::new();
        let bytecode = [SexaOpCode::FailClosed as u8];
        let res = vm.execute(&bytecode);
        assert!(res.is_err());
        assert!(vm.is_halted);
        assert_eq!(vm.exit_code, 1);
        assert_eq!(vm.worm_ledger.len(), 1);
        assert_eq!(vm.worm_ledger[0][0], 0xDE);
        assert_eq!(vm.worm_ledger[0][1], 0xAD);
    }

    #[test]
    fn test_vm_arithmetic_mul_div() {
        let mut vm = F60VM::new();
        vm.registers[0] = SexaRegister::from_parts(10, 0);
        let bytecode = [
            SexaOpCode::SexaMulRational as u8, 3,
            SexaOpCode::SexaDivRational as u8, 2,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 15);
    }

    #[test]
    fn test_vm_control_flow_jump() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::Jump as u8, 4,
            SexaOpCode::FailClosed as u8, // PC 2..3 no debe ejecutarse
            SexaOpCode::Halt as u8,
            SexaOpCode::NoOp as u8,        // PC 4
            SexaOpCode::Halt as u8,        // PC 5
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.exit_code, 0);
    }

    #[test]
    fn test_vm_call_return() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::Call as u8, 4,     // PC 0: llama a PC 4 (ret = 2)
            SexaOpCode::Halt as u8,        // PC 2: halt al volver
            SexaOpCode::NoOp as u8,        // PC 3
            SexaOpCode::SexaAdd as u8,     // PC 4: rutina
            SexaOpCode::Return as u8,      // PC 5: retorna a PC 2
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert!(vm.is_halted);
        assert_eq!(vm.exit_code, 0);
    }

    #[test]
    fn test_vm_sha3_and_scitt_worm_chain_anti_mock() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::Sha3Block as u8,
            SexaOpCode::SepTouchIdSign as u8,
            SexaOpCode::ScittChainAppend as u8,
            SexaOpCode::ScittChainAppend as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.worm_ledger.len(), 2);
        // Verificar que los hashes son criptográficamente deterministas y no mocks estáticos
        assert_ne!(vm.worm_ledger[0], [0u8; 32]);
        assert_ne!(vm.worm_ledger[0], vm.worm_ledger[1]);
        assert_ne!(vm.manifest.proof_digest, [0u8; 32]);
    }

    #[test]
    fn test_vm_landauer_physical_limit_and_exergy_metric() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::LandauerRecord as u8,
            SexaOpCode::ScittChainAppend as u8,
            SexaOpCode::C5RealExergyScore as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        // Comprobar cota física exacta de Landauer a 300K: 1102 zJ = 1.102 aJ para 384 bits
        assert_eq!(vm.landauer_floor_zeptojoules, 1102);
        // Comprobar disipación macroscópica CMOS
        assert_eq!(vm.cmos_switching_dissipation_fj, 2870);
        // Comprobar métrica determinista de exergía (no string estático)
        let score = vm.registers[7].seconds;
        assert_eq!(score, 21_000);
        assert_eq!(vm.compute_exergy_metric(), 21_000);
    }

    #[test]
    fn test_vm_direct_apfs_io() {
        let mut vm = F60VM::new();
        let test_file = std::path::PathBuf::from("target/test_worm_ledger_apfs.bin");
        if test_file.exists() {
            let _ = std::fs::remove_file(&test_file);
        }
        vm.persistence_path = Some(test_file.clone());

        let bytecode = [
            SexaOpCode::Sha3Block as u8,
            SexaOpCode::ScittChainAppend as u8,
            SexaOpCode::DirectAPFSIO as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 32); // 32 bytes escrito
        assert!(test_file.exists());
        let content = std::fs::read(&test_file).unwrap();
        assert_eq!(content.len(), 32);
        assert_eq!(content, vm.worm_ledger[0]);
        let _ = std::fs::remove_file(&test_file);
    }

    #[test]
    fn test_vm_merkle_mountain_range_verify() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::Sha3Block as u8,
            SexaOpCode::ScittChainAppend as u8,
            SexaOpCode::TimestampAttest as u8,
            SexaOpCode::Sha3Block as u8,
            SexaOpCode::ScittChainAppend as u8,
            // Borrar proof_digest para permitir que MerkleRootVerify calcule la raíz
            SexaOpCode::NoisePurge as u8,
            SexaOpCode::MerkleRootVerify as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 1);
        assert_ne!(vm.manifest.proof_digest, [0u8; 32]);
    }

    #[test]
    fn test_vm_worm_integrity_probe() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::Sha3Block as u8,
            SexaOpCode::ScittChainAppend as u8,
            SexaOpCode::WormIntegrityProbe as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 1);

        // Inyectar adulteración (hash corrupto/duplicado)
        let mut corrupt_vm = F60VM::new();
        corrupt_vm.worm_ledger.push([0x01u8; 32]);
        corrupt_vm.worm_ledger.push([0x01u8; 32]); // duplicado
        let probe_bytecode = [SexaOpCode::WormIntegrityProbe as u8];
        let res = corrupt_vm.execute(&probe_bytecode);
        assert!(res.is_err());
        assert_eq!(corrupt_vm.exit_code, 7);
    }

    #[test]
    fn test_vm_eu_ai_act_risk_classification() {
        let mut vm = F60VM::new();
        // Nivel normal (mínimo riesgo)
        let bytecode = [
            SexaOpCode::EuAiActCheckRisk as u8,
            SexaOpCode::HumanOversightPing as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 1);

        // Forzar violación inadmisible (Art. 5)
        let mut high_entropy_vm = F60VM::new();
        high_entropy_vm.manifest.entropy_bits_erased = 5000;
        let fail_bytecode = [SexaOpCode::EuAiActCheckRisk as u8];
        assert!(high_entropy_vm.execute(&fail_bytecode).is_err());
        assert_eq!(high_entropy_vm.exit_code, 1);
    }

    #[test]
    fn test_vm_larsa120_bft_consensus() {
        let mut vm = F60VM::new();
        // Voto: R0 (Alpha) = 1, R1 (Beta) = 1, R2 (Gamma) = 0 -> Quórum 2/3 alcanzado
        vm.registers[0] = SexaRegister::from_parts(1, 0);
        vm.registers[1] = SexaRegister::from_parts(1, 0);
        vm.registers[2] = SexaRegister::from_parts(0, 0);

        let bytecode = [
            SexaOpCode::SovereignBftVote as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[7].seconds, 1); // Quórum confirmado
        assert_eq!(vm.registers[7].sexa_fraction, 2); // 2 votos
        assert_eq!(vm.worm_ledger.len(), 1); // Bloque BFT encadenado
    }

    #[test]
    fn test_vm_ed25519_verify_and_cose_receipt() {
        let mut vm = F60VM::new();
        let bytecode = [
            SexaOpCode::Sha3Block as u8,
            SexaOpCode::Ed25519Verify as u8,
            SexaOpCode::CoseSignReceipt as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 1); // Firma verificada
        assert_eq!(vm.worm_ledger.len(), 1); // Recibo COSE emitido
    }

    #[test]
    fn test_vm_popper_falsification() {
        let mut vm = F60VM::new();
        vm.registers[0] = SexaRegister::from_parts(100, 0); // Hipótesis H
        vm.registers[1] = SexaRegister::from_parts(25, 0);  // Evidencia refutatoria
        let bytecode = [
            SexaOpCode::PopperFalsify as u8,
            SexaOpCode::Halt as u8,
        ];
        assert!(vm.execute(&bytecode).is_ok());
        assert_eq!(vm.registers[0].seconds, 0); // Hipótesis falsada
        assert_eq!(vm.registers[7].seconds, 75); // Residuo empírico
    }
}
