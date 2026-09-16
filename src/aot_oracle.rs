//! # Cliente del Oráculo AOT (INV_C5_LEAN_AOT_ORACLE)
//!
//! Punto de anclaje termodinámico para invocar el binario nativo compilado desde Lean 4.
//! Transduce la causalidad de Ring-0 al Lóbulo Inhibidor (Proof-Carrying Execution)
//! mediante streaming de I/O a coste O(1).

use std::process::Command;
use std::path::Path;
use std::time::Instant;

/// Resultado de la Inferencia AOT.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OracleVerdict {
    /// El oráculo certificó la traza. Exit 0. Causalidad intacta.
    Validated,
    /// El oráculo colapsó la traza por paradoja o violación estructural. Exit != 0.
    ParadoxDetected,
    /// Error de Invocación (el binario no existe o el I/O falló).
    SystemFailure,
}

/// Cliente proxy para el Oráculo de C-FFI compilado desde Lean 4.
pub struct AotOracleClient;

impl AotOracleClient {
    /// Invoca el oráculo binario precompilado pasándole el `trace_path`.
    /// La invocación es síncrona pero fuera del Hot Path (vía I/O de disco o pipes).
    pub fn verify_trace<P: AsRef<Path>>(trace_path: P) -> OracleVerdict {
        let binary_path = "proof/lean/.lake/build/bin/babylon_aot_oracle";
        
        if !Path::new(binary_path).exists() {
            return OracleVerdict::SystemFailure;
        }

        match Command::new(binary_path)
            .arg(trace_path.as_ref())
            .status() 
        {
            Ok(status) => {
                if status.success() {
                    OracleVerdict::Validated
                } else {
                    OracleVerdict::ParadoxDetected
                }
            }
            Err(_) => OracleVerdict::SystemFailure,
        }
    }

    /// Método analítico: devuelve además la latencia de la certificación formal.
    pub fn verify_trace_with_latency<P: AsRef<Path>>(trace_path: P) -> (OracleVerdict, std::time::Duration) {
        let t0 = Instant::now();
        let verdict = Self::verify_trace(trace_path);
        (verdict, t0.elapsed())
    }
}
