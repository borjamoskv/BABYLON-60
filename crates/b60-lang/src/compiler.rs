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
                "SEXA_ADD" => {
                    bytecode.push(SexaOpCode::SexaAdd as u8);
                }
                "SEXA_SUB" => {
                    bytecode.push(SexaOpCode::SexaSub as u8);
                }
                "PUSH" => {
                    let reg: u8 = if tokens.len() > 1 {
                        tokens[1].parse().unwrap_or(0)
                    } else {
                        0
                    };
                    bytecode.push(SexaOpCode::PushStack as u8);
                    bytecode.push(reg);
                }
                "LOAD_REG" => {
                    let reg: u8 = if tokens.len() > 1 {
                        tokens[1].parse().unwrap_or(0)
                    } else {
                        0
                    };
                    bytecode.push(SexaOpCode::LoadReg as u8);
                    bytecode.push(reg);
                }
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
                "TOUCHID_SIGN" => {
                    bytecode.push(SexaOpCode::SepTouchIdSign as u8);
                }
                "LANDAUER_RECORD" => {
                    bytecode.push(SexaOpCode::LandauerRecord as u8);
                }
                "WORM_COMMIT" => {
                    bytecode.push(SexaOpCode::ScittChainAppend as u8);
                }
                "FAIL_CLOSED" => {
                    bytecode.push(SexaOpCode::FailClosed as u8);
                }
                "OMEGA_FIXED_POINT" => {
                    bytecode.push(SexaOpCode::OmegaFixedPoint as u8);
                }
                "C5_EXERGY_SCORE" => {
                    bytecode.push(SexaOpCode::C5RealExergyScore as u8);
                }
                "HALT" => {
                    bytecode.push(SexaOpCode::Halt as u8);
                }
                unknown => {
                    return Err(format!("Línea {}: Opcode o directiva desconocida '{}'", line_num + 1, unknown));
                }
            }
        }

        Ok(bytecode)
    }
}
