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

use core::sync::atomic::{AtomicU64, Ordering};
use core::hint::spin_loop;
use crate::shared_manifest::SharedManifest;

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
    
    /// Acumulador de Energía Libre Termodinámica (TFE) disipada (Coste de Landauer).
    tfe_dissipated: AtomicU64,
    
    /// Límite de exergía antes del colapso / Burnout epistémico.
    max_tfe_capacity: u64,
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
        }
    }

    /// Flujo de Gradiente Epistémico (Gradient Flow sobre la Energía Libre Variacional).
    /// El agente consume su `sensory_input` (SharedManifest) y paga un peaje térmico (TFE).
    pub fn epistemic_update(&self) -> Result<(), &'static str> {
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

        // Coste termodinámico (Fields 2024 / Métrica de Fisher).
        let thermodynamic_cost = prediction_error.saturating_mul(10);
        let total_dissipated = self.tfe_dissipated.fetch_add(thermodynamic_cost, Ordering::SeqCst) + thermodynamic_cost;

        if total_dissipated > self.max_tfe_capacity {
            // [AFORISMO 3] BURNOUT COGNITIVO.
            // Envenenamos el canal activo emitiendo SCITT, cortando el acoplamiento con el exterior.
            let secret = [0u8; 32];
            let _ = self.active_output.epistemic_halt(&secret);
            return Err("[C5-REAL] BURNOUT TERMICO: Límite de Disipación de Exergía Excedido. Manta de Markov Fracturada.");
        }

        // Fricción temporal impuesta simulando la disipación térmica (Ecuación de Langevin).
        let friction_cycles = 1 << prediction_error.min(8);
        for _ in 0..friction_cycles {
            spin_loop();
        }

        // Caída por el gradiente: el agente adapta su creencia a la realidad.
        self.internal_belief.store(sensory_data, Ordering::Release);
        Ok(())
    }

    /// Inferencia Activa Clásica (van de Laar, 2022).
    /// En lugar de cambiar nuestra creencia, inyectamos un estado deseado en el entorno
    /// usando el `SharedManifest` de salida (CBFE Message Passing).
    pub fn emit_active_state(&self, epoch: u64, target_state: u64) -> Result<(), &'static str> {
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
        sensory.publish(1, &[1, 0, 0, 0]).unwrap();
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
        sensory.publish(1, &[10, 0, 0, 0]).unwrap();
        let res = blanket.epistemic_update();
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("BURNOUT TERMICO"));
    }

    #[test]
    fn test_markov_blanket_active_inference() {
        let sensory = SharedManifest::new();
        let active = SharedManifest::new();
        let blanket = MarkovBlanket::new(1000, &sensory, &active);
        assert!(blanket.emit_active_state(1, 42).is_ok());
        let read_val = active.read().unwrap();
        assert_eq!(read_val.1[0], 42);
    }
}


