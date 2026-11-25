// ============================================================================
// BABYLON-60 v4.0 | SCHEDULER (Tier 1 C5-REAL)
// ============================================================================
//! The sexagesimal scheduler for the Causal-Determinist Execution Engine.
//! It uses deterministic, quantized Q32.32 time; logical ticks are integer counts.

pub mod time;

#[cfg(target_os = "linux")]
use perf_event::{Builder, Counter};

/// C5-REAL Exergy Telemetry (Pillar 5)
/// Samples available hardware PMU counters; these do not establish energy or Landauer limits.
pub struct ExergyTelemetry {
    #[cfg(target_os = "linux")]
    cache_misses: Option<Counter>,
    #[cfg(target_os = "linux")]
    branch_misses: Option<Counter>,
}

impl Default for ExergyTelemetry {
    fn default() -> Self {
        Self::new()
    }
}

impl ExergyTelemetry {
    pub fn new() -> Self {
        #[cfg(target_os = "linux")]
        {
            let l1d = Builder::new().kind(perf_event::events::Hardware::CACHE_MISSES).build().ok();
            let branch = Builder::new().kind(perf_event::events::Hardware::BRANCH_MISSES).build().ok();
            Self { cache_misses: l1d, branch_misses: branch }
        }
        #[cfg(not(target_os = "linux"))]
        Self {}
    }

    /// Each counter is independently unavailable if unsupported or unreadable.
    pub fn sample_entropy(&mut self) -> (Option<u64>, Option<u64>) {
        #[cfg(target_os = "linux")]
        {
            let cache = self.cache_misses.as_mut().and_then(|c| c.read().ok());
            let br = self.branch_misses.as_mut().and_then(|c| c.read().ok());
            (cache, br)
        }
        #[cfg(not(target_os = "linux"))]
        (None, None)
    }
}

use crate::scheduler::time::{LogicalClock, SimulationClock};
use crate::thermodynamics::MarkovBlanket;

/// Estado de ejecución de un agente gobernado por el ciclo F60.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentExecutionState {
    Active,
    BurnoutHalted { at_tick: u64 },
}

/// Planificador Determinista Sexagesimal acoplado a la Manta de Markov (F60 / 60Hz).
/// El reloj usa aritmética entera determinista; no acredita comportamiento termodinámico físico.
pub struct F60ThermodynamicScheduler {
    pub logical_clock: LogicalClock,
    pub simulation_clock: SimulationClock,
}

impl Default for F60ThermodynamicScheduler {
    fn default() -> Self {
        Self::new()
    }
}

impl F60ThermodynamicScheduler {
    /// Floor of one 60 Hz interval in Q32.32. The remainder is 16/60 raw units.
    /// Before saturation, 60 steps lose 16 raw units; this is not exact rational F60.
    pub const TICK_60HZ: u64 = SimulationClock::SCALE / 60;

    pub const fn new() -> Self {
        Self {
            logical_clock: LogicalClock::new(0),
            simulation_clock: SimulationClock::new(0),
        }
    }

    /// Ejecuta un paso de simulación a 60Hz.
    /// Alimenta la Manta de Markov del agente con el gradiente sensorial y avanza el reloj.
    pub fn step<'a>(
        &mut self,
        blanket: &MarkovBlanket<'a>,
    ) -> Result<AgentExecutionState, &'static str> {
        self.logical_clock = self.logical_clock.tick();
        self.simulation_clock = self.simulation_clock.advance(Self::TICK_60HZ);

        match blanket.epistemic_update() {
            Ok(()) => Ok(AgentExecutionState::Active),
            Err(_) => Ok(AgentExecutionState::BurnoutHalted {
                at_tick: self.logical_clock.0,
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared_manifest::SharedManifest;
    use crate::thermodynamics::MarkovBlanket;

    #[test]
    fn q32_tick_quantization_is_bounded_not_exact() {
        let scale = SimulationClock::SCALE;
        let tick = F60ThermodynamicScheduler::TICK_60HZ;
        assert_eq!(tick, 71_582_788);
        assert_eq!(scale - 60 * tick, 16);
        let day = 86_400_u64;
        let elapsed = (0..60).fold(SimulationClock::new(0), |clock, _| clock.advance(tick));
        assert_eq!(elapsed.0, scale - 16);
        assert_eq!(day * scale - day * 60 * tick, 1_382_400);
    }

    #[cfg(not(target_os = "linux"))]
    #[test]
    fn unavailable_pmu_is_not_a_zero_measurement() {
        assert_eq!(ExergyTelemetry::new().sample_entropy(), (None, None));
    }

    #[test]
    fn test_f60_scheduler_active_inference_tick() {
        let mut scheduler = F60ThermodynamicScheduler::new();
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(10_000, &sensory, &active);

        // Estímulo sensorial coherente
        sensory.publish(1, &[42, 0, 0, 0]).expect("BFT Fallback");

        let state = scheduler.step(&blanket).expect("BFT Fallback");
        assert_eq!(state, AgentExecutionState::Active);
        assert_eq!(scheduler.logical_clock.0, 1);
        assert_eq!(scheduler.simulation_clock.0, F60ThermodynamicScheduler::TICK_60HZ);
    }

    #[test]
    fn test_f60_scheduler_burnout_halt() {
        let mut scheduler = F60ThermodynamicScheduler::new();
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        // Capacidad extremadamente baja para inducir Burnout Térmico inmediato
        let blanket = MarkovBlanket::new(5, &sensory, &active);

        // Gran sorpresa estocástica (ruido no integrable)
        sensory.publish(1, &[500, 0, 0, 0]).expect("BFT Fallback");

        let state = scheduler.step(&blanket).expect("BFT Fallback");
        match state {
            AgentExecutionState::BurnoutHalted { at_tick } => {
                assert_eq!(at_tick, 1);
            }
            _ => panic!("El nodo debió colapsar por agotamiento termodinámico."),
        }
    }
}

