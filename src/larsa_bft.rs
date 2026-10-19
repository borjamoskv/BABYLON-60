//! # Tríada de Larsa — Consenso Isostático BFT (Ring-0)
//!
//! Implementación topológica del isomorfismo de la Tríada de Larsa a 120º.
//! Modela un sistema híbrido CFT/BFT de 3 nodos (Quórum 2/3) sobre la
//! Trinidad Arquitectónica: Rust (Alpha), Lean 4 (Beta), y Z3 SMT (Gamma).

use crate::manifest::{POISONED, RUNNING};
use core::sync::atomic::{AtomicU32, Ordering};

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

/// Quórum de Verificación Heterogénea N-Versión (N-version heterogeneous verification).
/// Requiere un quórum de 2/3 para mantener la estabilidad del Ring-0.
///
/// Nota de arquitectura: A nivel de red no constituye un protocolo BFT distribuido bizantino
/// (PBFT/HotStuff/Tendermint), sino un quórum heterogéneo de tres verificadores
/// ortogonales en el mismo host: Rust (Alpha / Runtime), Lean 4 (Beta / Prover) y Z3 SMT (Gamma / Solver).
pub struct LarsaTriadConsensus {
    /// Estado del íbice $\alpha$ (Rust).
    pub alpha: AtomicU32,
    /// Estado del íbice $\beta$ (Lean 4).
    pub beta: AtomicU32,
    /// Estado del íbice $\gamma$ (Z3).
    pub gamma: AtomicU32,
}

/// Alias formal de arquitectura de sistemas para `LarsaTriadConsensus`.
///
/// [FRENTE-004] Calificación formal: LARSA-120 opera como una barrera de triple-atestación
/// conjuntiva y quórum heterogéneo multi-motor (Rust α, Lean 4 β, Z3 γ) en silicio local.
/// No es un protocolo PBFT distribuido por red (que requeriría 3f+1 = 4 para tolerar f=1).
/// En el modelo isostático de 3 vértices, la regla `active_count() >= 2` actúa como un
/// filtro *fail-stop* de seguridad crítica: ante la caída de 2 vértices, se aborta con `POISONED`.
pub type HeterogeneousVerificationQuorum = LarsaTriadConsensus;

/// Disponibilidad del quórum, independiente del veredicto de cada traza.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum QuorumHealth {
    /// Los tres vértices están disponibles.
    Running,
    /// Dos vértices están disponibles.
    Degraded,
    /// Menos de dos vértices están disponibles.
    Halted,
}

/// Resultado terminal de una evaluación; un rechazo no bloquea peticiones futuras.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TraceVerdict {
    /// Ambos oráculos validaron esta traza y el quórum está disponible.
    Validated,
    /// Un oráculo rechazó la traza, falló o el quórum no está disponible.
    TraceRejected,
}

impl TraceVerdict {
    /// Conserva los códigos C/Python: solo una traza validada devuelve `RUNNING`.
    pub const fn to_ffi_code(self) -> u32 {
        match self {
            Self::Validated => RUNNING,
            Self::TraceRejected => POISONED,
        }
    }
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
            LarsaVertex::Alpha => self
                .alpha
                .store(VertexState::Fallen as u32, Ordering::Release),
            LarsaVertex::Beta => self
                .beta
                .store(VertexState::Fallen as u32, Ordering::Release),
            LarsaVertex::Gamma => self
                .gamma
                .store(VertexState::Fallen as u32, Ordering::Release),
        }
    }

    /// Restaura la salud de un vértice; no cambia el veredicto de una traza anterior.
    pub fn restore_vertex(&self, vertex: LarsaVertex) {
        match vertex {
            LarsaVertex::Alpha => self
                .alpha
                .store(VertexState::Active as u32, Ordering::Release),
            LarsaVertex::Beta => self
                .beta
                .store(VertexState::Active as u32, Ordering::Release),
            LarsaVertex::Gamma => self
                .gamma
                .store(VertexState::Active as u32, Ordering::Release),
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

    /// Consulta la disponibilidad sin emitir un veredicto sobre ninguna traza.
    pub fn quorum_health(&self) -> QuorumHealth {
        match self.active_count() {
            3 => QuorumHealth::Running,
            2 => QuorumHealth::Degraded,
            _ => QuorumHealth::Halted,
        }
    }

    /// Diagnóstico legado de disponibilidad. `RUNNING` no autoriza una traza.
    pub fn evaluate_quorum(&self) -> u32 {
        match self.quorum_health() {
            QuorumHealth::Running | QuorumHealth::Degraded => RUNNING,
            QuorumHealth::Halted => POISONED,
        }
    }

    /// Evalúa primero Z3 y después Lean/AOT. Cualquier rechazo o fallo termina
    /// esta llamada, aunque otros vértices mantengan el quórum disponible.
    pub fn evaluate_trace<P: AsRef<std::path::Path>>(&self, trace_path: P) -> TraceVerdict {
        match std::fs::read(trace_path) {
            Ok(bytes) => self.evaluate_bytes(&bytes),
            Err(_) => {
                self.report_failure(LarsaVertex::Gamma);
                TraceVerdict::TraceRejected
            },
        }
    }

    /// Both verifiers consume one request-owned snapshot.
    pub(crate) fn evaluate_bytes(&self, bytes: &[u8]) -> TraceVerdict {
        let trace = match crate::ffi_oracle::TraceFile::new(bytes) {
            Ok(trace) => trace,
            Err(_) => return TraceVerdict::TraceRejected,
        };
        use crate::aot_oracle::AotOracleClient;
        use crate::z3_oracle::Z3FirewallClient;

        let path_ref = &trace.path;
        self.evaluate_trace_with(
            || Z3FirewallClient::verify_causality(path_ref),
            || AotOracleClient::verify_trace(path_ref),
        )
    }

    // Private seam for isolated control-flow tests; public callers always use real oracles.
    fn evaluate_trace_with<Z3, Lean>(&self, verify_z3: Z3, verify_lean: Lean) -> TraceVerdict
    where
        Z3: FnOnce() -> crate::aot_oracle::OracleVerdict,
        Lean: FnOnce() -> crate::aot_oracle::OracleVerdict,
    {
        use crate::aot_oracle::OracleVerdict;

        match verify_z3() {
            OracleVerdict::Validated => self.restore_vertex(LarsaVertex::Gamma),
            OracleVerdict::ParadoxDetected | OracleVerdict::SystemFailure => {
                self.report_failure(LarsaVertex::Gamma);
                return TraceVerdict::TraceRejected;
            }
        }
        match verify_lean() {
            OracleVerdict::Validated => self.restore_vertex(LarsaVertex::Beta),
            OracleVerdict::ParadoxDetected | OracleVerdict::SystemFailure => {
                self.report_failure(LarsaVertex::Beta);
                return TraceVerdict::TraceRejected;
            }
        }
        match self.quorum_health() {
            QuorumHealth::Running | QuorumHealth::Degraded => TraceVerdict::Validated,
            QuorumHealth::Halted => TraceVerdict::TraceRejected,
        }
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

    #[test]
    fn rejected_trace_is_independent_of_quorum_and_later_requests() {
        use crate::aot_oracle::OracleVerdict;
        for rejection in [OracleVerdict::ParadoxDetected, OracleVerdict::SystemFailure] {
            for failed_vertex in [LarsaVertex::Gamma, LarsaVertex::Beta] {
                let triad = LarsaTriadConsensus::new();
                let lean_called = std::cell::Cell::new(false);
                let verdict = triad.evaluate_trace_with(
                    || {
                        if failed_vertex == LarsaVertex::Gamma {
                            rejection
                        } else {
                            OracleVerdict::Validated
                        }
                    },
                    || {
                        lean_called.set(true);
                        rejection
                    },
                );
                assert_eq!(verdict, TraceVerdict::TraceRejected);
                assert_eq!(verdict.to_ffi_code(), POISONED);
                assert_eq!(lean_called.get(), failed_vertex == LarsaVertex::Beta);
                assert_eq!(triad.get_state(failed_vertex), VertexState::Fallen);
                assert_eq!(triad.quorum_health(), QuorumHealth::Degraded);
                assert_eq!(triad.evaluate_quorum(), RUNNING);
                // A new call requires both verifiers again, and may succeed.
                assert_eq!(
                    triad.evaluate_trace_with(
                        || OracleVerdict::Validated,
                        || OracleVerdict::Validated,
                    ),
                    TraceVerdict::Validated
                );
                assert_eq!(triad.quorum_health(), QuorumHealth::Running);
                assert_eq!(verdict, TraceVerdict::TraceRejected);
            }
        }
    }

    #[test]
    fn both_verdicts_are_required_for_every_trace() {
        use crate::aot_oracle::OracleVerdict::{ParadoxDetected, SystemFailure, Validated};
        for z3 in [Validated, ParadoxDetected, SystemFailure] {
            for lean in [Validated, ParadoxDetected, SystemFailure] {
                let triad = LarsaTriadConsensus::new();
                let result = triad.evaluate_trace_with(|| z3, || lean);
                assert_eq!(
                    result == TraceVerdict::Validated,
                    matches!((z3, lean), (Validated, Validated))
                );
            }
        }
    }

    #[test]
    fn rejected_requests_remain_rejected_under_parallel_load() {
        use crate::aot_oracle::OracleVerdict::{ParadoxDetected, Validated};
        let triad = LarsaTriadConsensus::new();
        // Isolated warmup and stress cover the control flow, not external solver performance.
        for _ in 0..100 {
            assert_eq!(
                triad.evaluate_trace_with(|| Validated, || Validated),
                TraceVerdict::Validated
            );
        }
        std::thread::scope(|scope| {
            for _ in 0..8 {
                let triad = &triad;
                scope.spawn(move || {
                    for _ in 0..10_000 {
                        assert_eq!(
                            triad.evaluate_trace_with(
                                || ParadoxDetected,
                                || panic!("Z3 rejection must short-circuit Lean"),
                            ),
                            TraceVerdict::TraceRejected
                        );
                        assert_eq!(
                            triad.evaluate_trace_with(|| Validated, || ParadoxDetected),
                            TraceVerdict::TraceRejected
                        );
                    }
                });
            }
        });
        assert_eq!(
            triad.evaluate_trace_with(|| Validated, || Validated),
            TraceVerdict::Validated
        );
    }
}
