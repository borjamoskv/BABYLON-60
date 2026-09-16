//! # Tríada de Larsa — Consenso Isostático BFT (Ring-0)
//!
//! Implementación topológica del isomorfismo de la Tríada de Larsa a 120º.
//! Modela un sistema híbrido CFT/BFT de 3 nodos (Quórum 2/3) sobre la
//! Trinidad Arquitectónica: Rust (Alpha), Lean 4 (Beta), y Z3 SMT (Gamma).

use core::sync::atomic::{AtomicU32, Ordering};
use crate::manifest::{POISONED, RUNNING};

/// Vértices de la Tríada Arquitectónica de Larsa.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LarsaVertex {
    /// Íbice α: Rust / C-ABI (Hardware / Landauer) @ 0º
    Alpha,
    /// Íbice β: Lean 4 / Prover (Curry-Howard) @ 120º
    Beta,
    /// Íbice γ: Z3 SMT / Verifier (Firewall) @ 240º
    Gamma,
}

/// Estado del Vértice.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u32)]
pub enum VertexState {
    /// El vértice opera normalmente.
    Active = 1,
    /// El vértice ha colapsado o sido comprometido.
    Fallen = 0,
}

/// Simulador de Consenso BFT Isostático de Larsa.
/// Requiere un quórum de 2/3 para mantener la estabilidad del Ring-0.
pub struct LarsaTriadConsensus {
    /// Estado del íbice $\alpha$ (Rust).
    pub alpha: AtomicU32,
    /// Estado del íbice $\beta$ (Lean 4).
    pub beta: AtomicU32,
    /// Estado del íbice $\gamma$ (Z3).
    pub gamma: AtomicU32,
}

impl Default for LarsaTriadConsensus {
    fn default() -> Self {
        Self::new()
    }
}

impl LarsaTriadConsensus {
    /// Inicializa la Tríada de Larsa en perfecto equilibrio isostático.
    pub const fn new() -> Self {
        Self {
            alpha: AtomicU32::new(VertexState::Active as u32),
            beta: AtomicU32::new(VertexState::Active as u32),
            gamma: AtomicU32::new(VertexState::Active as u32),
        }
    }

    /// Reporta la falla de un vértice.
    pub fn report_failure(&self, vertex: LarsaVertex) {
        match vertex {
            LarsaVertex::Alpha => self.alpha.store(VertexState::Fallen as u32, Ordering::Release),
            LarsaVertex::Beta => self.beta.store(VertexState::Fallen as u32, Ordering::Release),
            LarsaVertex::Gamma => self.gamma.store(VertexState::Fallen as u32, Ordering::Release),
        }
    }

    /// Restaura un vértice tras remediación o prueba formal.
    pub fn restore_vertex(&self, vertex: LarsaVertex) {
        match vertex {
            LarsaVertex::Alpha => self.alpha.store(VertexState::Active as u32, Ordering::Release),
            LarsaVertex::Beta => self.beta.store(VertexState::Active as u32, Ordering::Release),
            LarsaVertex::Gamma => self.gamma.store(VertexState::Active as u32, Ordering::Release),
        }
    }

    /// Retorna el estado actual de un vértice dado.
    pub fn get_state(&self, vertex: LarsaVertex) -> VertexState {
        let val = match vertex {
            LarsaVertex::Alpha => self.alpha.load(Ordering::Acquire),
            LarsaVertex::Beta => self.beta.load(Ordering::Acquire),
            LarsaVertex::Gamma => self.gamma.load(Ordering::Acquire),
        };
        if val == VertexState::Active as u32 {
            VertexState::Active
        } else {
            VertexState::Fallen
        }
    }

    /// Retorna el número de nodos activos (0..=3).
    pub fn active_count(&self) -> u32 {
        let a = self.alpha.load(Ordering::Acquire);
        let b = self.beta.load(Ordering::Acquire);
        let c = self.gamma.load(Ordering::Acquire);
        a + b + c
    }

    /// Evalúa el quórum. Si < 2 nodos están activos, detona la apoptosis.
    /// Retorna `POISONED` (0xDEAD_6060) si colapsa, o `RUNNING` si resiste.
    pub fn evaluate_quorum(&self) -> u32 {
        if self.active_count() < 2 {
            POISONED
        } else {
            RUNNING
        }
    }

    /// Somete una traza causal a la Tríada de Larsa.
    /// Según INV_C5_Z3_SMT_PRE_LEAN, primero pasa por MUSHUSHU-0 (Z3 / Vértice Gamma) para poda booleana.
    /// Solo si Z3 certifica la traza sin contradicción matemática, se escala al Lóbulo Inhibidor (Lean 4 / Vértice Beta).
    pub fn evaluate_trace<P: core::convert::AsRef<std::path::Path>>(&self, trace_path: P) -> u32 {
        use crate::aot_oracle::{AotOracleClient, OracleVerdict};
        use crate::z3_oracle::Z3FirewallClient;
        
        let path_ref = trace_path.as_ref();
        
        // 1. VÉRTICE GAMMA (Z3 SMT - Poda rápida Booleana)
        match Z3FirewallClient::verify_causality(path_ref) {
            OracleVerdict::Validated => {
                self.restore_vertex(LarsaVertex::Gamma);
            }
            OracleVerdict::ParadoxDetected | OracleVerdict::SystemFailure => {
                self.report_failure(LarsaVertex::Gamma);
                // MUSHUSHU-0 aborta y colapsa la evaluación. No se llega a invocar Lean 4.
                return self.evaluate_quorum();
            }
        }

        // 2. VÉRTICE BETA (Lean 4 - Reflejo Isomórfico)
        match AotOracleClient::verify_trace(path_ref) {
            OracleVerdict::Validated => {
                self.restore_vertex(LarsaVertex::Beta);
            }
            OracleVerdict::ParadoxDetected | OracleVerdict::SystemFailure => {
                self.report_failure(LarsaVertex::Beta);
            }
        }
        
        self.evaluate_quorum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_larsa_bft_isostatic_balance() {
        let triad = LarsaTriadConsensus::new();
        assert_eq!(triad.evaluate_quorum(), RUNNING);
        assert_eq!(triad.active_count(), 3);

        // Fallo de un vértice tolerado (Quorum 2/3 se mantiene)
        triad.report_failure(LarsaVertex::Beta);
        assert_eq!(triad.evaluate_quorum(), RUNNING);
        assert_eq!(triad.active_count(), 2);

        // Fallo del segundo vértice dispara Apoptosis (Quorum < 2/3 roto)
        triad.report_failure(LarsaVertex::Gamma);
        assert_eq!(triad.evaluate_quorum(), POISONED);
        assert_eq!(triad.active_count(), 1);

        // Restauración recupera estado
        triad.restore_vertex(LarsaVertex::Beta);
        assert_eq!(triad.evaluate_quorum(), RUNNING);
        assert_eq!(triad.active_count(), 2);
    }
}
