use std::hash::{Hash, Hasher};
use crate::dashboard::Babylon60State;
use std::sync::{Arc, Mutex};

/// Dimensión del Hypervector (D=1024 para balancing exergy/accuracy)
const D: usize = 1024;
const SIMILARITY_THRESHOLD: f64 = 0.85;

#[derive(Clone, Debug)]
pub struct Hypervector {
    pub data: Vec<i8>, // Bipolar encoding {-1, 1}
}

impl Hypervector {
    #[allow(dead_code)]
    pub fn new_random() -> Self {
        use rand::Rng;
        let mut rng = rand::rng();
        let data: Vec<i8> = (0..D).map(|_| if rng.random_bool(0.5) { 1 } else { -1 }).collect();
        Self { data }
    }

    pub fn similarity(&self, other: &Self) -> f64 {
        let dot_product: i32 = self.data.iter().zip(other.data.iter())
            .map(|(a, b)| (*a as i32) * (*b as i32))
            .sum();
        (dot_product as f64) / (D as f64)
    }
}

pub struct VsaMemory {
    /// SDM: Hard locations (scam patterns)
    pub honeypot_patterns: Vec<Hypervector>,
    /// Firmas de vulnerabilidades conocidas (V-Signatures)
    pub vuln_patterns: Vec<Hypervector>,
    pub state: Arc<Mutex<Babylon60State>>,
}

impl VsaMemory {
    pub fn new(state: Arc<Mutex<Babylon60State>>) -> Self {
        Self {
            honeypot_patterns: Vec::new(),
            vuln_patterns: Vec::new(),
            state,
        }
    }

    /// Codifica bytecode de contrato en un Hypervector (BABYLON60 HV-1)
    pub fn encode_bytecode(&self, bytecode: &[u8]) -> Hypervector {
        // [RESOLVER] Deterministic projection (Ley Ω₆)
        // Usamos trozos del bytecode para mutar un vector base
        let mut hv = vec![0i32; D];

        for chunk in bytecode.chunks(8) {
            let mut s = std::collections::hash_map::DefaultHasher::new();
            chunk.hash(&mut s);
            let seed = s.finish();

            // Proyección estocástica pero determinista basada en el chunk
            for i in 0..D {
                if (seed ^ (i as u64)).count_ones() % 2 == 0 {
                    hv[i] += 1;
                } else {
                    hv[i] -= 1;
                }
            }
        }

        // Normalización bipolar
        let data = hv.into_iter().map(|v| if v >= 0 { 1 } else { -1 }).collect();
        Hypervector { data }
    }

    /// Verifica si un nuevo contrato es un Honeypot conocido
    pub fn is_honeypot(&self, bytecode: &[u8]) -> bool {
        let current_hv = self.encode_bytecode(bytecode);

        for pattern in &self.honeypot_patterns {
            if current_hv.similarity(pattern) > SIMILARITY_THRESHOLD {
                return true;
            }
        }
        false
    }

    /// Verifica si un contrato tiene una vulnerabilidad conocida (p.ej. Ghost Debt)
    pub fn has_vulnerability(&self, bytecode: &[u8]) -> bool {
        let current_hv = self.encode_bytecode(bytecode);

        for pattern in &self.vuln_patterns {
            if current_hv.similarity(pattern) > SIMILARITY_THRESHOLD {
                return true;
            }
        }
        false
    }

    #[allow(dead_code)]
    pub fn add_honeypot(&mut self, bytecode: &[u8]) {
        let hv = self.encode_bytecode(bytecode);
        self.honeypot_patterns.push(hv);

        let mut s = self.state.lock().unwrap();
        s.log.push("[VSA-SDM] Nueva firma de Honeypot asimilada.".to_string());
    }

    pub fn add_vulnerability_pattern(&mut self, bytecode: &[u8]) {
        let hv = self.encode_bytecode(bytecode);
        self.vuln_patterns.push(hv);

        let mut s = self.state.lock().unwrap();
        s.log.push("[VSA-SDM] Nueva firma de Vulnerabilidad (V-Alpha) asimilada.".to_string());
    }
}
