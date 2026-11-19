// ============================================================================
// B60 COMPILER: PARSER AND BYTECODE GENERATOR FOR .b60 SCRIPTS
// ============================================================================

use std::collections::HashMap;
use crate::isa::SexaOpCode;

pub struct B60Compiler;

impl B60Compiler {
    fn parse_cuneiform_digit(token: &str) -> u64 {
        if token == "-" {
            return 0;
        }
        let tens = token.chars().filter(|&c| c == '<').count() as u64;
        let ones = token.chars().filter(|&c| c == 'Y' || c == 'v' || c == 'T').count() as u64;
        tens * 10 + ones
    }

    pub fn parse_cuneiform_literal(raw: &str) -> u64 {
        let inner = raw.trim_matches(|c| c == '[' || c == ']' || c == ' ');
        if inner.is_empty() {
            return 0;
        }
        let places: Vec<&str> = inner.split_whitespace().collect();
        let mut total = 0u64;
        let mut power = (places.len() - 1) as u32;
        for p in places {
            total = total.saturating_add(Self::parse_cuneiform_digit(p).saturating_mul(60u64.saturating_pow(power)));
            power = power.saturating_sub(1);
        }
        total
    }

    fn resolve_reg(name: &str, sym_table: &mut HashMap<String, u8>) -> u8 {
        if let Ok(idx) = name.parse::<u8>() {
            return idx % 8;
        }
        if let Some(stripped) = name.strip_prefix('R') {
            if let Ok(idx) = stripped.parse::<u8>() {
                return idx % 8;
            }
        }
        let next_idx = 2 + ((sym_table.len() as u8) % 6);
        *sym_table.entry(name.to_string()).or_insert(next_idx)
    }

    pub fn compile_source(source: &str) -> Result<Vec<u8>, String> {
        let mut bytecode = Vec::new();
        let mut sym_regs: HashMap<String, u8> = HashMap::new();

        for (line_num, raw_line) in source.lines().enumerate() {
            let line = raw_line.split('#').next().unwrap_or("").trim();
            if line.is_empty() || line.starts_with("//") {
                continue;
            }

            let tokens: Vec<&str> = line.split_whitespace().collect();
            if tokens.is_empty() {
                continue;
            }

            let op_upper = tokens[0].to_uppercase();
            match op_upper.as_str() {
                // --- Dialecto B60-ISA Directo ---
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
                "SEXA_ADD" => bytecode.push(SexaOpCode::SexaAdd as u8),
                "SEXA_SUB" => bytecode.push(SexaOpCode::SexaSub as u8),
                "SEXA_MUL" => bytecode.push(SexaOpCode::SexaMulRational as u8),
                "SEXA_DIV" => bytecode.push(SexaOpCode::SexaDivRational as u8),
                "SEXA_MOD60" => bytecode.push(SexaOpCode::SexaMod60 as u8),
                "SEXA_FLOOR" => bytecode.push(SexaOpCode::SexaFloor as u8),
                "SEXA_CEIL" => bytecode.push(SexaOpCode::SexaCeil as u8),
                "SEXA_ABS" => bytecode.push(SexaOpCode::SexaAbs as u8),
                "PUSH" => {
                    let reg = if tokens.len() > 1 { Self::resolve_reg(tokens[1], &mut sym_regs) } else { 0 };
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(reg);
                }
                "POP" => bytecode.push(SexaOpCode::PopStack as u8),
                "SWAP" => bytecode.push(SexaOpCode::SwapStack as u8),
                "LOAD_REG" => {
                    let reg = if tokens.len() > 1 { Self::resolve_reg(tokens[1], &mut sym_regs) } else { 0 };
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(reg);
                }
                "STORE_REG" => {
                    let reg = if tokens.len() > 1 { Self::resolve_reg(tokens[1], &mut sym_regs) } else { 0 };
                    bytecode.push(SexaOpCode::StoreReg as u8);
                    bytecode.push(reg);
                }
                "MANIFEST_SYNC" => bytecode.push(SexaOpCode::ManifestSync as u8),
                "MANIFEST_ACQUIRE" => bytecode.push(SexaOpCode::ManifestAcquire as u8),
                "MARKOV_ENTER" => bytecode.push(SexaOpCode::MarkovEnter as u8),
                "MARKOV_EXIT" => bytecode.push(SexaOpCode::MarkovExit as u8),
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
                "TOUCHID_SIGN" => bytecode.push(SexaOpCode::SepTouchIdSign as u8),
                "LANDAUER_RECORD" => bytecode.push(SexaOpCode::LandauerRecord as u8),
                "WORM_COMMIT" => bytecode.push(SexaOpCode::ScittChainAppend as u8),
                "FAIL_CLOSED" => bytecode.push(SexaOpCode::FailClosed as u8),
                "OMEGA_FIXED_POINT" => bytecode.push(SexaOpCode::OmegaFixedPoint as u8),
                "HALT" => bytecode.push(SexaOpCode::Halt as u8),
                "NOOP" | "YIELD_TICK" => bytecode.push(SexaOpCode::NoOp as u8),

                // --- Transpilador Dialecto Cuneiforme Sumerio (DUB / MUB) ---
                "DUB" | "MUB" | "ALLOC" => {
                    bytecode.push(SexaOpCode::NoOp as u8);
                }
                "NIG" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: NIG requiere destino y operando", line_num + 1));
                    }
                    let dest = Self::resolve_reg(tokens[1], &mut sym_regs);
                    if let (Some(start), Some(end)) = (line.find('['), line.find(']')) {
                        let val = Self::parse_cuneiform_literal(&line[start..=end]);
                        let sec = (val.min(255)) as u8;
                        if dest == 0 {
                            bytecode.push(SexaOpCode::SexaPack as u8);
                            bytecode.push(sec);
                            bytecode.push(0);
                        } else {
                            bytecode.push(SexaOpCode::PushStack as u8);
                            bytecode.push(0);
                            bytecode.push(SexaOpCode::SexaPack as u8);
                            bytecode.push(sec);
                            bytecode.push(0);
                            bytecode.push(SexaOpCode::PushStack as u8);
                            bytecode.push(0);
                            bytecode.push(SexaOpCode::LoadReg as u8);
                            bytecode.push(dest);
                            bytecode.push(SexaOpCode::LoadReg as u8);
                            bytecode.push(0);
                        }
                    } else {
                        let src = Self::resolve_reg(tokens[2], &mut sym_regs);
                        bytecode.push(SexaOpCode::PushStack as u8);
                        bytecode.push(src);
                        bytecode.push(SexaOpCode::LoadReg as u8);
                        bytecode.push(dest);
                    }
                }
                "DAH" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: DAH requiere destino y operando", line_num + 1));
                    }
                    let dest = Self::resolve_reg(tokens[1], &mut sym_regs);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(dest);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(0);
                    if let (Some(start), Some(end)) = (line.find('['), line.find(']')) {
                        let val = Self::parse_cuneiform_literal(&line[start..=end]);
                        bytecode.push(SexaOpCode::SexaPack as u8);
                        bytecode.push((val.min(255)) as u8);
                        bytecode.push(0);
                        bytecode.push(SexaOpCode::PushStack as u8);
                        bytecode.push(0);
                        bytecode.push(SexaOpCode::LoadReg as u8);
                        bytecode.push(1);
                        bytecode.push(SexaOpCode::PushStack as u8);
                        bytecode.push(dest);
                        bytecode.push(SexaOpCode::LoadReg as u8);
                        bytecode.push(0);
                    } else {
                        let src = Self::resolve_reg(tokens[2], &mut sym_regs);
                        bytecode.push(SexaOpCode::PushStack as u8);
                        bytecode.push(src);
                        bytecode.push(SexaOpCode::LoadReg as u8);
                        bytecode.push(1);
                    }
                    bytecode.push(SexaOpCode::SexaAdd as u8);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(dest);
                }
                "LAL" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: LAL requiere destino y operando", line_num + 1));
                    }
                    let dest = Self::resolve_reg(tokens[1], &mut sym_regs);
                    if let (Some(start), Some(end)) = (line.find('['), line.find(']')) {
                        let val = Self::parse_cuneiform_literal(&line[start..=end]);
                        bytecode.push(SexaOpCode::SexaPack as u8);
                        bytecode.push((val.min(255)) as u8);
                        bytecode.push(0);
                        bytecode.push(SexaOpCode::PushStack as u8);
                        bytecode.push(0);
                        bytecode.push(SexaOpCode::LoadReg as u8);
                        bytecode.push(1);
                    } else {
                        let src = Self::resolve_reg(tokens[2], &mut sym_regs);
                        bytecode.push(SexaOpCode::PushStack as u8);
                        bytecode.push(src);
                        bytecode.push(SexaOpCode::LoadReg as u8);
                        bytecode.push(1);
                    }
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(dest);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::SexaSub as u8);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(dest);
                }
                "ARA" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: ARA requiere destino y factor", line_num + 1));
                    }
                    let dest = Self::resolve_reg(tokens[1], &mut sym_regs);
                    let src = Self::resolve_reg(tokens[2], &mut sym_regs);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(dest);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(src);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(1);
                    bytecode.push(SexaOpCode::SexaMulRational as u8);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(dest);
                }
                "BA" | "BA.EXACT" => {
                    if tokens.len() < 3 {
                        return Err(format!("Línea {}: {} requiere destino y divisor", line_num + 1, op_upper));
                    }
                    let dest = Self::resolve_reg(tokens[1], &mut sym_regs);
                    let src = Self::resolve_reg(tokens[2], &mut sym_regs);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(dest);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(src);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(1);
                    bytecode.push(SexaOpCode::SexaDivRational as u8);
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(0);
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(dest);
                }
                "SAR" | "SAR.B60" => {
                    let reg = if tokens.len() > 1 { Self::resolve_reg(tokens[1], &mut sym_regs) } else { 0 };
                    bytecode.push(SexaOpCode::StoreReg as u8);
                    bytecode.push(reg);
                }
                "FORK" => bytecode.push(SexaOpCode::ForkSwarm as u8),
                "AWAIT" | "AFTER" => bytecode.push(SexaOpCode::YieldTick as u8),
                "EXECUTE" => {
                    if line.contains("CRITICAL_HALT") {
                        bytecode.push(SexaOpCode::FailClosed as u8);
                    } else {
                        bytecode.push(SexaOpCode::ScittChainAppend as u8);
                    }
                }
                "CRITICAL" if tokens.get(1).map(|s| s.eq_ignore_ascii_case("HALT")).unwrap_or(false) => {
                    bytecode.push(SexaOpCode::FailClosed as u8);
                }
                "NU" | "TUKU" | "GIN" => {
                    bytecode.push(SexaOpCode::YieldTick as u8);
                }
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
    use crate::vm::F60VM;

    #[test]
    fn test_compile_and_execute_sumerian_exergy_dialect() {
        let src = r#"
            DUB
            NIG EXERGY [ Y - ]
            SAR.B60 EXERGY
            NIG DIVISOR [ <YY ]
            NIG RESULT EXERGY
            BA RESULT DIVISOR
            SAR.B60 RESULT
            HALT
        "#;
        let bc = B60Compiler::compile_source(src).expect("Debe compilar dialecto sumerio");
        let mut vm = F60VM::new();
        vm.execute(&bc).expect("Debe ejecutar sin error");
        // 60 / 12 = 5
        assert_eq!(vm.registers[0].seconds, 5);
        assert_eq!(vm.registers[0].sexa_fraction, 0);
    }
}
