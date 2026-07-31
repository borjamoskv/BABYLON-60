// C5-REAL EXERGY CERTIFIED — WASM SCORE ENGINE (Ω32)
// Compiles physical SIMD logic into WebAssembly to replace JavaScript stochastics

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct WasmScoreEngine {
    max: usize,
    primes: Vec<bool>,
}

#[wasm_bindgen]
impl WasmScoreEngine {
    #[wasm_bindgen(constructor)]
    pub fn new(max: usize) -> Self {
        let mut engine = Self {
            max,
            primes: vec![true; max + 1],
        };
        engine.compute_sieve();
        engine
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
    pub fn count_divisors(n: u32) -> u32 {
        if n == 0 { return 0; }
        let mut count = 0;
        let limit = (n as f64).sqrt() as u32;
        for i in 1..=limit {
            if n % i == 0 {
                count += if i == n / i { 1 } else { 2 };
            }
        }
        count
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

        for i in 0..len {
            let n = start + i as u32;
            let mut score = 0.0;

            // 1. Primality
            if self.is_prime(n as usize) {
                score += weight_prime;
            }

            // 2. Divisor Richness (log-normalized)
            let divs = Self::count_divisors(n);
            if max_divisors > 0 {
                let div_score = ((1.0 + divs as f32).ln()) / ((1.0 + max_divisors as f32).ln());
                score += div_score * weight_div;
            }

            // 3. Bit Density (ILP Unrolled conceptually in Rust)
            let pc = n.count_ones() as f32;
            let bl = (32 - n.leading_zeros()).max(1) as f32;
            score += (pc / bl) * weight_bits;

            // Normalize to 0-100
            out[i] = (score / total_weight) * 100.0;
        }

        out
    }
}
