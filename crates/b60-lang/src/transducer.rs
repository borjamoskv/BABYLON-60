// ============================================================================
// B60 EPISTEMIC INTENT TRANSDUCER & AGENTIC ACTION GATEWAY
// Invariante C5-REAL: Aforismo 5 (Lo voluntario vale menos que lo involuntario)
// ============================================================================

use crate::arithmetic::Tick60;
use crate::isa::SexaOpCode;
use crate::mmr::MmrAccumulator;
use crate::vm::F60VM;
use sha3::{Digest, Sha3_256};

#[derive(Debug, Clone)]
pub struct AgentActionIntent {
    pub agent_id: String,
    pub tool_name: String,
    pub reasoning_trace_len: usize,
    pub executable_payload_len: usize,
    pub exergy_budget: u64,
    pub timestamp: Tick60,
}

#[derive(Debug, PartialEq, Eq)]
pub enum EpistemicEvaluation {
    Accepted {
        bytecode_len: usize,
        execution_cycles: usize,
        mmr_root: String,
    },
    RejectedCheapTalk {
        ratio: usize,
        threshold: usize,
    },
    RejectedBudgetExceeded {
        budget: u64,
        limit: u64,
    },
    RuntimeError(String),
}

pub struct EpistemicGate {
    pub mmr_accumulator: MmrAccumulator,
    pub max_cheap_talk_ratio: usize,
    pub max_budget_limit: u64,
}

impl EpistemicGate {
    pub fn new(max_cheap_talk_ratio: usize, max_budget_limit: u64) -> Self {
        Self {
            mmr_accumulator: MmrAccumulator::new(),
            max_cheap_talk_ratio,
            max_budget_limit,
        }
    }

    /// Evalúa, compila y ejecuta una intención agéntica bajo invariantes C5-REAL
    pub fn transduce_and_execute(&mut self, intent: &AgentActionIntent) -> EpistemicEvaluation {
        // 1. Invariante de Presupuesto Termodinámico
        if intent.exergy_budget > self.max_budget_limit {
            return EpistemicEvaluation::RejectedBudgetExceeded {
                budget: intent.exergy_budget,
                limit: self.max_budget_limit,
            };
        }

        // 2. Invariante de Kolmogorov / Anti-Cheap-Talk (Aforismo 5)
        let effective_payload = if intent.executable_payload_len == 0 { 1 } else { intent.executable_payload_len };
        let ratio = intent.reasoning_trace_len / effective_payload;
        if intent.reasoning_trace_len > 100 && ratio > self.max_cheap_talk_ratio {
            return EpistemicEvaluation::RejectedCheapTalk {
                ratio,
                threshold: self.max_cheap_talk_ratio,
            };
        }

        // 3. Síntesis y Compilación de Bytecode Sexagesimal B60
        let mut bytecode = Vec::with_capacity(32);

        // Opcode 1: SEXA_PACK (segundos + fracción)
        bytecode.push(SexaOpCode::SexaPack as u8);
        bytecode.push((intent.timestamp.seconds % 60) as u8);
        bytecode.push((intent.timestamp.sexa_units % 60) as u8);

        // Opcode 2: KOLMOGOROV_AUDIT
        let l_norm = (intent.reasoning_trace_len.min(255)) as u8;
        let d_norm = (intent.executable_payload_len.min(255)) as u8;
        bytecode.push(SexaOpCode::KolmogorovAudit as u8);
        bytecode.push(l_norm);
        bytecode.push(d_norm);

        // Opcode 3: WORM_COMMIT
        bytecode.push(SexaOpCode::ScittChainAppend as u8);

        // Opcode 4: HALT
        bytecode.push(SexaOpCode::Halt as u8);

        // 4. Ejecución en la Máquina Virtual Sexagesimal
        let mut vm = F60VM::new();
        match vm.execute(&bytecode) {
            Ok(()) => {
                // 5. Compromiso Inmutable en Merkle Mountain Range (MMR)
                let mut hasher = Sha3_256::new();
                hasher.update(b"B60_INTENT_LEAF:");
                hasher.update(intent.agent_id.as_bytes());
                hasher.update(intent.tool_name.as_bytes());
                hasher.update(&bytecode);
                let leaf_hash: [u8; 32] = hasher.finalize().into();

                self.mmr_accumulator.append(leaf_hash);
                let mmr_root = hex::encode(self.mmr_accumulator.get_root());

                EpistemicEvaluation::Accepted {
                    bytecode_len: bytecode.len(),
                    execution_cycles: vm.pc,
                    mmr_root,
                }
            }
            Err(e) => EpistemicEvaluation::RuntimeError(e),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_transduce_valid_high_exergy_action() {
        let mut gate = EpistemicGate::new(50, 3600);
        let intent = AgentActionIntent {
            agent_id: "ULTRATHINK-APEX".to_string(),
            tool_name: "deploy_smart_contract".to_string(),
            reasoning_trace_len: 450,
            executable_payload_len: 120, // ratio = 3.75 < 50
            exergy_budget: 1200,
            timestamp: Tick60::from_rational(100, 15, 60),
        };

        let result = gate.transduce_and_execute(&intent);
        match result {
            EpistemicEvaluation::Accepted { bytecode_len, execution_cycles, mmr_root } => {
                assert!(bytecode_len > 0);
                assert!(execution_cycles > 0);
                assert_eq!(mmr_root.len(), 64);
                assert_eq!(gate.mmr_accumulator.leaves.len(), 1);
            }
            other => panic!("Esperaba Accepted, obtuve: {:?}", other),
        }
    }

    #[test]
    fn test_reject_cheap_talk_hallucination() {
        let mut gate = EpistemicGate::new(20, 3600);
        let intent = AgentActionIntent {
            agent_id: "CHATTING-AGENT".to_string(),
            tool_name: "noop_reflect".to_string(),
            reasoning_trace_len: 3000,
            executable_payload_len: 5, // ratio = 600 >> 20
            exergy_budget: 500,
            timestamp: Tick60::zero(),
        };

        let result = gate.transduce_and_execute(&intent);
        match result {
            EpistemicEvaluation::RejectedCheapTalk { ratio, threshold } => {
                assert_eq!(threshold, 20);
                assert!(ratio >= 600);
            }
            other => panic!("Esperaba RejectedCheapTalk, obtuve: {:?}", other),
        }
    }

    #[test]
    fn test_reject_budget_overflow() {
        let mut gate = EpistemicGate::new(50, 1000);
        let intent = AgentActionIntent {
            agent_id: "ROGUE-AGENT".to_string(),
            tool_name: "infinite_recursion".to_string(),
            reasoning_trace_len: 100,
            executable_payload_len: 100,
            exergy_budget: 9999, // Excede 1000
            timestamp: Tick60::zero(),
        };

        let result = gate.transduce_and_execute(&intent);
        match result {
            EpistemicEvaluation::RejectedBudgetExceeded { budget, limit } => {
                assert_eq!(budget, 9999);
                assert_eq!(limit, 1000);
            }
            other => panic!("Esperaba RejectedBudgetExceeded, obtuve: {:?}", other),
        }
    }
}
