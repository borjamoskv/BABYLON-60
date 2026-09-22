// ============================================================================
// B60 COMPILER: PARSER AND BYTECODE GENERATOR FOR .b60 SCRIPTS
// ============================================================================

use crate::isa::SexaOpCode;

pub struct B60Compiler;

impl B60Compiler {
    pub fn compile_source(source: &str) -> Result<Vec<u8>, String> {
        let mut bytecode = Vec::new();

        for (line_num, line) in source.lines().enumerate() {
            let line = line.trim();
            if line.is_empty() || line.starts_with("//") || line.starts_with('#') {
                continue;
            }

            let tokens: Vec<&str> = line.split_whitespace().collect();
            if tokens.is_empty() {
                continue;
            }

            match tokens[0].to_uppercase().as_str() {
                // 00..09: Control de Flujo & Estados de Máquina
                "HALT" => bytecode.push(SexaOpCode::Halt as u8),
                "FAIL_CLOSED" => bytecode.push(SexaOpCode::FailClosed as u8),
                "NOOP" => bytecode.push(SexaOpCode::NoOp as u8),
                "JUMP" => {
                    let target: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::Jump as u8);
                    bytecode.push(target);
                }
                "JZ" | "JUMP_IF_ZERO" => {
                    let target: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::JumpIfZero as u8);
                    bytecode.push(target);
                }
                "JNZ" | "JUMP_IF_NOT_ZERO" => {
                    let target: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::JumpIfNotZero as u8);
                    bytecode.push(target);
                }
                "CALL" => {
                    let target: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::Call as u8);
                    bytecode.push(target);
                }
                "RET" | "RETURN" => bytecode.push(SexaOpCode::Return as u8),
                "FORK_SWARM" => bytecode.push(SexaOpCode::ForkSwarm as u8),
                "YIELD_TICK" => bytecode.push(SexaOpCode::YieldTick as u8),

                // 10..19: Aritmética Sexagesimal Racional Exacta (Q60)
                "SEXA_ADD" => bytecode.push(SexaOpCode::SexaAdd as u8),
                "SEXA_SUB" => bytecode.push(SexaOpCode::SexaSub as u8),
                "SEXA_MUL" => {
                    bytecode.push(SexaOpCode::SexaMulRational as u8);
                    if let Some(arg) = tokens.get(1).and_then(|t| t.parse::<u8>().ok()) {
                        bytecode.push(arg);
                    }
                }
                "SEXA_DIV" => {
                    bytecode.push(SexaOpCode::SexaDivRational as u8);
                    if let Some(arg) = tokens.get(1).and_then(|t| t.parse::<u8>().ok()) {
                        bytecode.push(arg);
                    }
                }
                "SEXA_MOD60" => bytecode.push(SexaOpCode::SexaMod60 as u8),
                "SEXA_PACK" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: SEXA_PACK requiere <segundos> <fracción_60>", line_num + 1));
                    }
                    let sec: u8 = tokens[1].parse().map_err(|_| format!("Línea {}: segundos inválidos", line_num + 1))?;
                    let frac: u8 = tokens[2].parse().map_err(|_| format!("Línea {}: fracción inválida", line_num + 1))?;
                    bytecode.push(SexaOpCode::SexaPack as u8);
                    bytecode.push(sec);
                    bytecode.push(frac);
                }
                "SEXA_UNPACK" => bytecode.push(SexaOpCode::SexaUnpack as u8),
                "SEXA_FLOOR" => bytecode.push(SexaOpCode::SexaFloor as u8),
                "SEXA_CEIL" => bytecode.push(SexaOpCode::SexaCeil as u8),
                "SEXA_ABS" => bytecode.push(SexaOpCode::SexaAbs as u8),

                // 20..29: Operaciones de Manta de Markov y Teoría de la Información
                "MARKOV_ENTER" => bytecode.push(SexaOpCode::MarkovEnter as u8),
                "MARKOV_EXIT" => bytecode.push(SexaOpCode::MarkovExit as u8),
                "FISHER_PROJ" => bytecode.push(SexaOpCode::FisherMetricProj as u8),
                "KOLMOGOROV_AUDIT" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: KOLMOGOROV_AUDIT requiere <l_reasoning> <delta_ast>", line_num + 1));
                    }
                    let l: u8 = tokens[1].parse().map_err(|_| format!("Línea {}: l_reasoning inválido", line_num + 1))?;
                    let d: u8 = tokens[2].parse().map_err(|_| format!("Línea {}: delta_ast inválido", line_num + 1))?;
                    bytecode.push(SexaOpCode::KolmogorovAudit as u8);
                    bytecode.push(l);
                    bytecode.push(d);
                }
                "LANDAUER_RECORD" => bytecode.push(SexaOpCode::LandauerRecord as u8),
                "ENTROPY_ASSERT" => {
                    let max_allowed: u16 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(384);
                    bytecode.push(SexaOpCode::EntropyAssert as u8);
                    bytecode.extend_from_slice(&max_allowed.to_le_bytes());
                }
                "MUTUAL_INFO_CHECK" => bytecode.push(SexaOpCode::MutualInfoCheck as u8),
                "POPPER_FALSIFY" => bytecode.push(SexaOpCode::PopperFalsify as u8),
                "COMPRESS_MDL" => bytecode.push(SexaOpCode::CompressMDL as u8),
                "NOISE_PURGE" => bytecode.push(SexaOpCode::NoisePurge as u8),

                // 30..39: Registro y Memoria Soberana de Silicio (Zero-Copy)
                "LOAD_REG" => {
                    let reg: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(reg);
                }
                "STORE_REG" => {
                    let reg: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::StoreReg as u8);
                    bytecode.push(reg);
                }
                "MANIFEST_SYNC" => bytecode.push(SexaOpCode::ManifestSync as u8),
                "MANIFEST_ACQUIRE" => bytecode.push(SexaOpCode::ManifestAcquire as u8),
                "PUSH" => {
                    let reg: u8 = tokens.get(1).and_then(|t| t.parse().ok()).unwrap_or(0);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(reg);
                }
                "POP" => bytecode.push(SexaOpCode::PopStack as u8),
                "SWAP" => bytecode.push(SexaOpCode::SwapStack as u8),
                "AFFINITY_PIN" => bytecode.push(SexaOpCode::AffinityPin as u8),
                "DIRECT_APFS_IO" => bytecode.push(SexaOpCode::DirectAPFSIO as u8),
                "ZERO_COPY_BORROW" => bytecode.push(SexaOpCode::ZeroCopyBorrow as u8),

                // 40..49: Criptografía de Silicio y Atestación de Hardware
                "SHA3_BLOCK" => bytecode.push(SexaOpCode::Sha3Block as u8),
                "ED25519_VERIFY" => bytecode.push(SexaOpCode::Ed25519Verify as u8),
                "TOUCHID_SIGN" => bytecode.push(SexaOpCode::SepTouchIdSign as u8),
                "WORM_COMMIT" => bytecode.push(SexaOpCode::ScittChainAppend as u8),
                "COSE_RECEIPT" => bytecode.push(SexaOpCode::CoseSignReceipt as u8),
                "KEY_DERIVE" => bytecode.push(SexaOpCode::KeyDeriveHKDF as u8),
                "MERKLE_VERIFY" => bytecode.push(SexaOpCode::MerkleRootVerify as u8),
                "TIMESTAMP_ATTEST" => bytecode.push(SexaOpCode::TimestampAttest as u8),
                "NONCE_GEN" => bytecode.push(SexaOpCode::NonceGenerate as u8),
                "QUARANTINE_ISOLATE" => bytecode.push(SexaOpCode::QuarantineIsolate as u8),

                // 50..59: Gobernanza LegalTech y Cumplimiento EU AI Act
                "EU_AI_CHECK_RISK" => bytecode.push(SexaOpCode::EuAiActCheckRisk as u8),
                "HUMAN_OVERSIGHT_PING" => bytecode.push(SexaOpCode::HumanOversightPing as u8),
                "AUDIT_TRAIL_SNAP" => bytecode.push(SexaOpCode::AuditTrailSnapshot as u8),
                "VPRM_STEP_SCORE" => bytecode.push(SexaOpCode::VprmStepScore as u8),
                "BIAS_VARIANCE_GATE" => {
                    bytecode.push(SexaOpCode::BiasVarianceGate as u8);
                    if let Some(arg) = tokens.get(1).and_then(|t| t.parse::<u8>().ok()) {
                        bytecode.push(arg);
                    }
                }
                "GOODHART_DETECTOR" => bytecode.push(SexaOpCode::GoodhartDetector as u8),
                "WORM_PROBE" => bytecode.push(SexaOpCode::WormIntegrityProbe as u8),
                "C5_EXERGY_SCORE" => bytecode.push(SexaOpCode::C5RealExergyScore as u8),
                "BFT_VOTE" => bytecode.push(SexaOpCode::SovereignBftVote as u8),
                "OMEGA_FIXED_POINT" => bytecode.push(SexaOpCode::OmegaFixedPoint as u8),

                unknown => {
                    return Err(format!("Línea {}: Opcode o directiva desconocida '{}'", line_num + 1, unknown));
                }
            }
        }

        Ok(bytecode)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compile_all_60_opcodes_coverage() {
        let script = r#"
            // 00..09
            HALT
            FAIL_CLOSED
            NOOP
            JUMP 4
            JZ 6
            JNZ 8
            CALL 10
            RET
            FORK_SWARM
            YIELD_TICK
            // 10..19
            SEXA_ADD
            SEXA_SUB
            SEXA_MUL 3
            SEXA_DIV 2
            SEXA_MOD60
            SEXA_PACK 10 30
            SEXA_UNPACK
            SEXA_FLOOR
            SEXA_CEIL
            SEXA_ABS
            // 20..29
            MARKOV_ENTER
            MARKOV_EXIT
            FISHER_PROJ
            KOLMOGOROV_AUDIT 10 5
            LANDAUER_RECORD
            ENTROPY_ASSERT 50
            MUTUAL_INFO_CHECK
            POPPER_FALSIFY
            COMPRESS_MDL
            NOISE_PURGE
            // 30..39
            LOAD_REG 0
            STORE_REG 1
            MANIFEST_SYNC
            MANIFEST_ACQUIRE
            PUSH 2
            POP
            SWAP
            AFFINITY_PIN
            DIRECT_APFS_IO
            ZERO_COPY_BORROW
            // 40..49
            SHA3_BLOCK
            ED25519_VERIFY
            TOUCHID_SIGN
            WORM_COMMIT
            COSE_RECEIPT
            KEY_DERIVE
            MERKLE_VERIFY
            TIMESTAMP_ATTEST
            NONCE_GEN
            QUARANTINE_ISOLATE
            // 50..59
            EU_AI_CHECK_RISK
            HUMAN_OVERSIGHT_PING
            AUDIT_TRAIL_SNAP
            VPRM_STEP_SCORE
            BIAS_VARIANCE_GATE 30
            GOODHART_DETECTOR
            WORM_PROBE
            C5_EXERGY_SCORE
            BFT_VOTE
            OMEGA_FIXED_POINT
        "#;
        let bytecode = B60Compiler::compile_source(script).expect("Debe compilar todos los opcodes");
        assert!(!bytecode.is_empty());
    }
}
