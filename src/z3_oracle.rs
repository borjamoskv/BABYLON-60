//! Cliente Rust para MUSHUSHU-0 (Vértice Gamma / Z3 SMT Firewall)
//! 
//! Responsable de canalizar las trazas físicas hacia el oráculo Z3 para la poda booleana
//! sub-milisegundo ANTES de invocar a Lean 4, cumpliendo con la regla INV_C5_Z3_SMT_PRE_LEAN.

use std::path::Path;
use std::process::Command;
use crate::aot_oracle::OracleVerdict; // Reutilizamos el enum de veredicto

/// Cliente interactivo para invocar el Firewall SMT en Python (MUSHUSHU-0).
pub struct Z3FirewallClient;

impl Z3FirewallClient {
    /// Inyecta la traza en el Firewall Z3 para verificar la Monotonía de Lamport y
    /// la ausencia de ciclos causales subyacentes.
    pub fn verify_causality<P: AsRef<Path>>(trace_path: P) -> OracleVerdict {
        let path_ref = trace_path.as_ref();
        
        // 1. Inyección C-FFI Inversa (Fast Path Zero-Process)
        if let Some(cb) = crate::ffi_oracle::get_z3_callback() {
            let bytes = std::fs::read(path_ref).unwrap_or_default();
            let res = cb(bytes.as_ptr(), bytes.len());
            return match res {
                0 => OracleVerdict::Validated,
                2 => OracleVerdict::ParadoxDetected,
                _ => OracleVerdict::SystemFailure,
            };
        }

        // 2. Slow Path (Subproceso) para Tests Nativos Puros
        let status = Command::new("python3")
            .arg("01_ORCHESTRATOR/babylon60/kernel/ns_z3_firewall.py")
            .arg("--verify-causality")
            .arg(path_ref.as_os_str())
            .status();

        match status {
            Ok(s) if s.success() => {
                // EXIT 0 => Z3_OK
                OracleVerdict::Validated
            }
            Ok(s) => {
                // EXIT 2 => Z3_PARADOX, EXIT 1 => ERROR
                match s.code() {
                    Some(2) => OracleVerdict::ParadoxDetected,
                    _ => OracleVerdict::SystemFailure,
                }
            }
            Err(_) => {
                OracleVerdict::SystemFailure
            }
        }
    }
}
