// ============================================================================
// B60 INTERACTIVE REPL & EPISTEMIC SHELL
// Framework: C5-REAL | Teorema 15: Invarianza de Chentsov en el REPL
// ============================================================================

use std::io::{self, Write};
use crate::arithmetic::{Tick60, FRACTION_BASE};
use crate::fisher::FisherSimplex;
use crate::transducer::{AgentActionIntent, EpistemicEvaluation, EpistemicGate};
use crate::compiler::B60Compiler;
use crate::vm::F60VM;

pub struct B60Repl {
    gate: EpistemicGate,
}

impl B60Repl {
    pub fn new() -> Self {
        Self {
            gate: EpistemicGate::new(50, 3600),
        }
    }

    pub fn eval_line(&mut self, line: &str) -> String {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            return String::new();
        }

        let parts: Vec<&str> = trimmed.split_whitespace().collect();
        match parts[0].to_lowercase().as_str() {
            "help" => {
                "Comandos disponibles en B60 REPL:\n\
                 • sexa add <s1> <f1> <s2> <f2>         - Suma sexagesimal exacta Q60\n\
                 • fisher dist <p1,p2,...> <q1,q2,...> - Distancia geodésica de Fisher-Rao\n\
                 • fisher kl <p1,p2,...> <q1,q2,...>   - Divergencia de Kullback-Leibler\n\
                 • transduce <agent> <tool> <r_len> <p_len> <budget> - Evaluación epistémica\n\
                 • run <file.b60>                      - Ejecuta un script B60\n\
                 • info                                - Muestra estado termodinámico\n\
                 • quit / exit                         - Salir del REPL".to_string()
            }
            "info" => {
                "B60 REPL v1.0.0-omega · Substrato: BABYLON-60 C5-REAL · Exergía: 20.920/21.000".to_string()
            }
            "sexa" => {
                if parts.len() >= 6 && parts[1] == "add" {
                    let s1: u64 = parts[2].parse().unwrap_or(0);
                    let f1: u64 = parts[3].parse().unwrap_or(0);
                    let s2: u64 = parts[4].parse().unwrap_or(0);
                    let f2: u64 = parts[5].parse().unwrap_or(0);

                    let total_frac = f1 + f2;
                    let carry = total_frac / FRACTION_BASE;
                    let rem = total_frac % FRACTION_BASE;
                    let total_s = s1 + s2 + carry;
                    format!("Resultado Q60: {}s + {}/{} u (carry: {})", total_s, rem, FRACTION_BASE, carry)
                } else {
                    "Uso: sexa add <s1> <f1> <s2> <f2>".to_string()
                }
            }
            "fisher" => {
                if parts.len() >= 4 && parts[1] == "dist" {
                    let p: Result<Vec<f64>, _> = parts[2].split(',').map(|s| s.parse()).collect();
                    let q: Result<Vec<f64>, _> = parts[3].split(',').map(|s| s.parse()).collect();
                    match (p, q) {
                        (Ok(pv), Ok(qv)) => {
                            if pv.len() == qv.len() && !pv.is_empty() {
                                let dist = FisherSimplex::fisher_rao_distance(&pv, &qv);
                                format!("Distancia Fisher-Rao d_F(p, q): {:.6} rad", dist)
                            } else {
                                "Dimensiones deben ser idénticas y no vacías".to_string()
                            }
                        }
                        _ => "Error parseando vectores. Formato: 0.5,0.5".to_string(),
                    }
                } else if parts.len() >= 4 && parts[1] == "kl" {
                    let p: Result<Vec<f64>, _> = parts[2].split(',').map(|s| s.parse()).collect();
                    let q: Result<Vec<f64>, _> = parts[3].split(',').map(|s| s.parse()).collect();
                    match (p, q) {
                        (Ok(pv), Ok(qv)) => {
                            if pv.len() == qv.len() && !pv.is_empty() {
                                let kl = FisherSimplex::relative_entropy_kl(&pv, &qv);
                                format!("Divergencia KL D_KL(p || q): {:.6} nats", kl)
                            } else {
                                "Dimensiones deben ser idénticas y no vacías".to_string()
                            }
                        }
                        _ => "Error parseando vectores. Formato: 0.5,0.5".to_string(),
                    }
                } else {
                    "Uso: fisher dist <p1,p2,...> <q1,q2,...> | fisher kl <p1,p2,...> <q1,q2,...>".to_string()
                }
            }
            "transduce" => {
                if parts.len() >= 6 {
                    let agent = parts[1].to_string();
                    let tool = parts[2].to_string();
                    let r_len: usize = parts[3].parse().unwrap_or(0);
                    let p_len: usize = parts[4].parse().unwrap_or(0);
                    let budget: u64 = parts[5].parse().unwrap_or(0);

                    let intent = AgentActionIntent {
                        agent_id: agent,
                        tool_name: tool,
                        reasoning_trace_len: r_len,
                        executable_payload_len: p_len,
                        exergy_budget: budget,
                        timestamp: Tick60::zero(),
                    };

                    match self.gate.transduce_and_execute(&intent) {
                        EpistemicEvaluation::Accepted { bytecode_len, execution_cycles, mmr_root } => {
                            format!("[✓] ADMITIDO: {} bytes bytecode, {} ciclos, MMR Root: {}", bytecode_len, execution_cycles, mmr_root)
                        }
                        EpistemicEvaluation::RejectedCheapTalk { ratio, threshold } => {
                            format!("[✗] RECHAZADO (Cheap Talk): Ratio {} > {}", ratio, threshold)
                        }
                        EpistemicEvaluation::RejectedBudgetExceeded { budget, limit } => {
                            format!("[✗] RECHAZADO (Presupuesto): {} > {}", budget, limit)
                        }
                        EpistemicEvaluation::RuntimeError(e) => {
                            format!("[✗] ERROR RUNTIME: {}", e)
                        }
                    }
                } else {
                    "Uso: transduce <agent_id> <tool_name> <reasoning_len> <payload_len> <budget>".to_string()
                }
            }
            "run" => {
                if parts.len() >= 2 {
                    match std::fs::read_to_string(parts[1]) {
                        Ok(src) => match B60Compiler::compile_source(&src) {
                            Ok(bc) => {
                                let mut vm = F60VM::new();
                                match vm.execute(&bc) {
                                    Ok(()) => format!("[✓] Script ejecutado exitosamente (PC={})", vm.pc),
                                    Err(e) => format!("[✗] Error VM: {}", e),
                                }
                            }
                            Err(e) => format!("[✗] Error compilación: {}", e),
                        },
                        Err(e) => format!("Error leyendo archivo: {}", e),
                    }
                } else {
                    "Uso: run <file.b60>".to_string()
                }
            }
            "quit" | "exit" => "EXIT".to_string(),
            other => format!("Comando no reconocido '{}'. Escribe 'help' para ver la lista.", other),
        }
    }

    pub fn run_interactive(&mut self) {
        println!("==================================================================");
        println!("         B60 INTERACTIVE REPL · SISTEMA OPERATIVO C5-REAL         ");
        println!("  Escribe 'help' para ver comandos o 'exit' para salir.           ");
        println!("==================================================================");

        let stdin = io::stdin();
        loop {
            print!("b60> ");
            let _ = io::stdout().flush();

            let mut buffer = String::new();
            if stdin.read_line(&mut buffer).is_err() {
                break;
            }

            let output = self.eval_line(&buffer);
            if output == "EXIT" {
                println!("Saliendo de B60 REPL. Homeostasis preservada.");
                break;
            }
            if !output.is_empty() {
                println!("{}", output);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_repl_sexa_add() {
        let mut repl = B60Repl::new();
        let res = repl.eval_line("sexa add 10 0 20 0");
        assert!(res.contains("Resultado Q60: 30s"));
    }

    #[test]
    fn test_repl_fisher() {
        let mut repl = B60Repl::new();
        let res = repl.eval_line("fisher dist 0.5,0.5 0.5,0.5");
        assert!(res.contains("0.000000 rad"));
    }

    #[test]
    fn test_repl_transduce() {
        let mut repl = B60Repl::new();
        let res = repl.eval_line("transduce AGENT_X tool_y 100 50 1000");
        assert!(res.contains("[✓] ADMITIDO"));
    }
}
