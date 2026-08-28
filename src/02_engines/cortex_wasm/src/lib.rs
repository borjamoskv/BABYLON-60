// C5-REAL EXERGY CERTIFIED — WASM SCORE ENGINE (Ω32)
// Compiles physical SIMD logic into WebAssembly to replace JavaScript stochastics

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct WasmScoreEngine {
    max: usize,
    primes: Vec<bool>,
    divisors: Vec<u32>,
}

#[wasm_bindgen]
impl WasmScoreEngine {
    #[wasm_bindgen(constructor)]
    pub fn new(max: usize) -> Self {
        let mut engine = Self {
            max,
            primes: vec![true; max + 1],
            divisors: vec![0; max + 1],
        };
        engine.compute_sieve();
        engine.compute_divisors();
        engine
    }

    fn compute_divisors(&mut self) {
        // Sieve-like approach to precompute divisors O(N log N)
        for i in 1..=self.max {
            let mut j = i;
            while j <= self.max {
                self.divisors[j] += 1;
                j += i;
            }
        }
    }

    fn compute_sieve(&mut self) {
        if self.max > 0 { self.primes[0] = false; }
        if self.max > 1 { self.primes[1] = false; }

        let limit = (self.max as f64).sqrt() as usize;
        for i in 2..=limit {
            if self.primes[i] {
                let mut j = i * i;
                while j <= self.max {
                    self.primes[j] = false;
                    j += i;
                }
            }
        }
    }

    #[wasm_bindgen]
    pub fn is_prime(&self, n: usize) -> bool {
        if n <= self.max {
            self.primes[n]
        } else {
            false
        }
    }

    #[wasm_bindgen]
    pub fn get_divisors(&self, n: usize) -> u32 {
        if n <= self.max {
            self.divisors[n]
        } else {
            0
        }
    }

    /// Evaluates a batch of integers and returns a flat Float32Array
    /// Returns [score_n, score_n+1, ...]
    #[wasm_bindgen]
    pub fn evaluate_batch(&self, start: u32, len: usize, max_divisors: u32) -> Vec<f32> {
        let mut out = vec![0.0f32; len];

        let weight_prime = 30.0;
        let weight_div = 25.0;
        let weight_bits = 20.0;
        let total_weight = 75.0; // Simplifying for WASM speed demo (Prime, Div, Bits)

        let mut i = 0;
        let chunks = len / 4;

        // ILP 4x Unrolled Loop (Axiom Ω21)
        while i < chunks * 4 {
            let n0 = start + i as u32;
            let n1 = n0 + 1;
            let n2 = n0 + 2;
            let n3 = n0 + 3;

            let mut s0 = 0.0;
            let mut s1 = 0.0;
            let mut s2 = 0.0;
            let mut s3 = 0.0;

            // 1. Primality
            if self.is_prime(n0 as usize) { s0 += weight_prime; }
            if self.is_prime(n1 as usize) { s1 += weight_prime; }
            if self.is_prime(n2 as usize) { s2 += weight_prime; }
            if self.is_prime(n3 as usize) { s3 += weight_prime; }

            // 2. Divisor Richness
            if max_divisors > 0 {
                let div_norm = 1.0 / (1.0 + max_divisors as f32).ln();
                s0 += ((1.0 + self.divisors[n0 as usize] as f32).ln() * div_norm) * weight_div;
                s1 += ((1.0 + self.divisors[n1 as usize] as f32).ln() * div_norm) * weight_div;
                s2 += ((1.0 + self.divisors[n2 as usize] as f32).ln() * div_norm) * weight_div;
                s3 += ((1.0 + self.divisors[n3 as usize] as f32).ln() * div_norm) * weight_div;
            }

            // 3. Bit Density
            s0 += ((n0.count_ones() as f32) / (32 - n0.leading_zeros()).max(1) as f32) * weight_bits;
            s1 += ((n1.count_ones() as f32) / (32 - n1.leading_zeros()).max(1) as f32) * weight_bits;
            s2 += ((n2.count_ones() as f32) / (32 - n2.leading_zeros()).max(1) as f32) * weight_bits;
            s3 += ((n3.count_ones() as f32) / (32 - n3.leading_zeros()).max(1) as f32) * weight_bits;

            out[i] = (s0 / total_weight) * 100.0;
            out[i+1] = (s1 / total_weight) * 100.0;
            out[i+2] = (s2 / total_weight) * 100.0;
            out[i+3] = (s3 / total_weight) * 100.0;

            i += 4;
        }

        // Remainder
        while i < len {
            let n = start + i as u32;
            let mut score = 0.0;
            if self.is_prime(n as usize) { score += weight_prime; }
            if max_divisors > 0 {
                score += ((1.0 + self.divisors[n as usize] as f32).ln() / (1.0 + max_divisors as f32).ln()) * weight_div;
            }
            score += ((n.count_ones() as f32) / (32 - n.leading_zeros()).max(1) as f32) * weight_bits;
            out[i] = (score / total_weight) * 100.0;
            i += 1;
        }

        out
    }
}
