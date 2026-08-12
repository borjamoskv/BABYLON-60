pub mod core {
    use std::collections::HashMap;

    #[derive(Debug, Clone, PartialEq)]
    pub enum Instruction {
        Mub(String),          // MUB <label>: Define entry point / label
        Gin(String),          // GIN <label>: Unconditional jump
        Tuku(String, String), // TUKU <reg> <label>: Jump if reg != 0
        Nu(String),           // NU <reg>: Logical NOT (0 -> 1, non-zero -> 0)
        Wal(String),          // WAL <data>: Write to DAG state
        Out,                  // OUT: Commit & Halt
        Add(String, i64),     // ADD <reg> <val>: Arithmetic injection
        Dec(String),          // DEC <reg>: Decrement
    }

    pub struct BabylonVM {
        pub registers: HashMap<String, i64>,
        pub pc: usize,
        pub instructions: Vec<Instruction>,
        pub labels: HashMap<String, usize>,
        pub state_log: Vec<String>,
    }

    impl BabylonVM {
        pub fn new() -> Self {
            Self {
                registers: HashMap::new(),
                pc: 0,
                instructions: Vec::new(),
                labels: HashMap::new(),
                state_log: Vec::new(),
            }
        }

        /// C5-REAL Cuneiform Parser (Base-60)
        /// Escudo Criptográfico Anti-LLM Slop
        pub fn parse_cuneiform(symbol: &str) -> i64 {
            let mut val = 0;
            for c in symbol.chars() {
                match c {
                    '<' => val += 10,
                    'Y' => val += 1,
                    _ => {}
                }
            }
            val
        }

        pub fn load(&mut self, source: &str) {
            let mut idx = 0;
            for line in source.lines() {
                let tokens: Vec<&str> = line.split_whitespace().collect();
                if tokens.is_empty() {
                    continue;
                }

                let instr = match tokens[0] {
                    "MUB" => {
                        self.labels.insert(tokens[1].to_string(), idx);
                        Instruction::Mub(tokens[1].to_string())
                    }
                    "GIN" => Instruction::Gin(tokens[1].to_string()),
                    "TUKU" => Instruction::Tuku(tokens[1].to_string(), tokens[2].to_string()),
                    "NU" => Instruction::Nu(tokens[1].to_string()),
                    "WAL" => Instruction::Wal(tokens[1].to_string()),
                    "OUT" => Instruction::Out,
                    "ADD" => {
                        let val = if tokens[2].starts_with('[') {
                            Self::parse_cuneiform(tokens[2])
                        } else {
                            tokens[2].parse().unwrap_or(0)
                        };
                        Instruction::Add(tokens[1].to_string(), val)
                    }
                    "DEC" => Instruction::Dec(tokens[1].to_string()),
                    _ => continue, // Filter LLM Noise
                };
                self.instructions.push(instr);
                idx += 1;
            }
        }

        pub fn execute(&mut self) -> Result<Vec<String>, String> {
            self.pc = 0;
            let mut cycle_count = 0;
            let max_cycles = 1_000_000;

            while self.pc < self.instructions.len() {
                cycle_count += 1;
                if cycle_count > max_cycles {
                    return Err("EXERGY_DEPLETION: Infinite loop".into());
                }

                match &self.instructions[self.pc] {
                    Instruction::Mub(_) => {
                        self.pc += 1;
                    }
                    Instruction::Gin(label) => {
                        self.pc = *self.labels.get(label).expect("Label no definido");
                    }
                    Instruction::Tuku(reg, label) => {
                        let val = *self.registers.get(reg).unwrap_or(&0);
                        if val != 0 {
                            self.pc = *self.labels.get(label).expect("Label no definido");
                        } else {
                            self.pc += 1;
                        }
                    }
                    Instruction::Nu(reg) => {
                        let val = *self.registers.get(reg).unwrap_or(&0);
                        let new_val = if val == 0 { 1 } else { 0 };
                        self.registers.insert(reg.clone(), new_val);
                        self.pc += 1;
                    }
                    Instruction::Wal(data) => {
                        self.state_log.push(data.clone());
                        self.pc += 1;
                    }
                    Instruction::Add(reg, val) => {
                        *self.registers.entry(reg.clone()).or_insert(0) += *val;
                        self.pc += 1;
                    }
                    Instruction::Dec(reg) => {
                        *self.registers.entry(reg.clone()).or_insert(0) -= 1;
                        self.pc += 1;
                    }
                    Instruction::Out => {
                        return Ok(self.state_log.clone());
                    }
                }
            }
            Ok(self.state_log.clone())
        }
    }
}
