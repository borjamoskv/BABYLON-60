// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | THERMODYNAMICS & INFORMATION GEOMETRY
// ============================================================================
// Referencias Epistémicas Cristalizadas:
// 1. Termodinámica Estocástica & Geometría de la Información (Parr & Friston, 2020)
// 2. Coste Termodinámico de la Inferencia Activa (Fields et al., 2024)
// 3. Coarse-Graining del Ruliad (Wolfram, 2023)
// 4. Irreducibilidad y No-Ergodicidad Biológica (Landgrebe, 2024)
// 5. Active Inference in Graphical Models (van de Laar et al., 2022)

use crate::shared_manifest::SharedManifest;
use core::sync::atomic::{AtomicBool, AtomicU64, Ordering};

/// [INVARIANTE C5-REAL] AFORISMO 1: Métrica de Información de Fisher.
/// Esta estructura modela topológicamente una "Manta de Markov".
/// Define el límite físico y epistémico entre el Agente (Internal) y el Entorno (External)
/// utilizando la tubería `SharedManifest` (64B) para garantizar cero false-sharing.
pub struct MarkovBlanket<'a> {
    /// Estados Internos (\mu) - El Modelo Generativo (Creencias locales del agente).
    internal_belief: AtomicU64,

    /// Estados Sensoriales (s) - IPC lock-free recibiendo datos del entorno.
    sensory_input: &'a SharedManifest,

    /// Estados Activos (a) - IPC lock-free inyectando acciones (CBFE) al entorno.
    active_output: &'a SharedManifest,

    /// Legacy field name: dimensionless software budget, not measured energy or heat.
    tfe_dissipated: AtomicU64,

    /// Maximum logical budget in the same dimensionless units.
    max_tfe_capacity: u64,
    budget_exhausted: AtomicBool,
}

impl<'a> MarkovBlanket<'a> {
    pub const fn new(
        capacity: u64,
        sensory: &'a SharedManifest,
        active: &'a SharedManifest,
    ) -> Self {
        Self {
            internal_belief: AtomicU64::new(0),
            sensory_input: sensory,
            active_output: active,
            tfe_dissipated: AtomicU64::new(0),
            max_tfe_capacity: capacity,
            budget_exhausted: AtomicBool::new(false),
        }
    }

    /// Update a scalar belief using a dimensionless, explicitly synthetic work budget.
    /// No energy measurement or thermodynamic attestation is produced. On exhaustion,
    /// freeze the output without manufacturing a signed receipt or hardware identity.
    pub fn epistemic_update(&self) -> Result<(), &'static str> {
        if self.budget_exhausted.load(Ordering::Acquire) {
            return Err("LOGICAL_BUDGET_EXHAUSTED");
        }
        let sensory_data = match self.sensory_input.read() {
            Some((_epoch, hash)) => hash[0], // Usamos el primer hash como variable de estado escalar (Surprise)
            None => return Err("POISONED_SENSORY_INPUT"),
        };

        let current_belief = self.internal_belief.load(Ordering::Acquire);
        let prediction_error = current_belief.abs_diff(sensory_data);

        // Coarse-Graining (Wolfram): Si la sorpresa es trivial, la absorbemos.
        if prediction_error < 2 {
            return Ok(());
        }

        // Policy heuristic only: ten logical units per scalar error. Saturate storage
        // and reject arithmetic overflow instead of wrapping around the budget gate.
        let cost = prediction_error.checked_mul(10);
        let logical_cost = cost.unwrap_or(u64::MAX);
        let previous = self
            .tfe_dissipated
            .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |value| {
                Some(value.saturating_add(logical_cost))
            })
            .expect("budget update always returns Some");

        if cost.is_none()
            || previous
                .checked_add(logical_cost)
                .map_or(true, |total| total > self.max_tfe_capacity)
        {
            self.budget_exhausted.store(true, Ordering::Release);
            self.active_output.freeze()?;
            return Err("LOGICAL_BUDGET_EXCEEDED_UNAUTHENTICATED_HALT");
        }

        // Caída por el gradiente: el agente adapta su creencia a la realidad.
        self.internal_belief.store(sensory_data, Ordering::Release);
        Ok(())
    }

    /// Inferencia Activa Clásica (van de Laar, 2022).
    /// En lugar de cambiar nuestra creencia, inyectamos un estado deseado en el entorno
    /// usando el `SharedManifest` de salida (CBFE Message Passing).
    pub fn emit_active_state(&self, epoch: u64, target_state: u64) -> Result<(), &'static str> {
        if self.budget_exhausted.load(Ordering::Acquire) {
            return Err("LOGICAL_BUDGET_EXHAUSTED");
        }
        let payload = [target_state, 0, 0, 0];
        self.active_output.publish(epoch, &payload)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_markov_blanket_coarse_graining() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(1000, &sensory, &active);
        sensory.publish(1, &[1, 0, 0, 0]).expect("BFT Fallback");
        // Sorpresa trivial (< 2): debe ser absorbida sin quemar exergía
        assert!(blanket.epistemic_update().is_ok());
        assert_eq!(blanket.tfe_dissipated.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn test_markov_blanket_epistemic_burnout() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(50, &sensory, &active);
        // Error de 10 -> costo 10 * 10 = 100 > 50 (capacidad)
        sensory.publish(1, &[10, 0, 0, 0]).expect("BFT Fallback");
        let res = blanket.epistemic_update();
        assert!(res.is_err());
        assert_eq!(res, Err("LOGICAL_BUDGET_EXCEEDED_UNAUTHENTICATED_HALT"));
        assert!(active.read().is_none());
        assert_eq!(blanket.epistemic_update(), Err("LOGICAL_BUDGET_EXHAUSTED"));
        assert_eq!(
            blanket.emit_active_state(2, 42),
            Err("LOGICAL_BUDGET_EXHAUSTED")
        );
    }

    #[test]
    fn logical_budget_overflow_fails_closed() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(u64::MAX, &sensory, &active);
        sensory.publish(1, &[u64::MAX, 0, 0, 0]).unwrap();
        assert_eq!(
            blanket.epistemic_update(),
            Err("LOGICAL_BUDGET_EXCEEDED_UNAUTHENTICATED_HALT")
        );
        assert_eq!(blanket.tfe_dissipated.load(Ordering::Acquire), u64::MAX);
        assert!(active.read().is_none());
    }

    #[test]
    fn logical_budget_exact_limit_then_exhaustion() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(100, &sensory, &active);
        sensory.publish(1, &[10, 0, 0, 0]).unwrap();
        assert_eq!(blanket.epistemic_update(), Ok(()));
        assert_eq!(blanket.tfe_dissipated.load(Ordering::Acquire), 100);
        assert!(blanket.emit_active_state(1, 10).is_ok());
        sensory.publish(2, &[12, 0, 0, 0]).unwrap();
        assert_eq!(
            blanket.epistemic_update(),
            Err("LOGICAL_BUDGET_EXCEEDED_UNAUTHENTICATED_HALT")
        );
        assert!(active.read().is_none());
    }

    #[test]
    fn accumulated_budget_never_wraps() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(u64::MAX, &sensory, &active);
        blanket
            .tfe_dissipated
            .store(u64::MAX - 5, Ordering::Release);
        sensory.publish(1, &[2, 0, 0, 0]).unwrap();
        assert!(blanket.epistemic_update().is_err());
        assert_eq!(blanket.tfe_dissipated.load(Ordering::Acquire), u64::MAX);
        assert!(active.read().is_none());
    }

    #[test]
    fn test_markov_blanket_active_inference() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(1000, &sensory, &active);
        assert!(blanket.emit_active_state(1, 42).is_ok());
        let read_val = active.read().expect("BFT Fallback");
        assert_eq!(read_val.1[0], 42);
    }
}
