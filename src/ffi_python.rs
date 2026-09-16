use pyo3::prelude::*;
use crate::larsa_bft::LarsaTriadConsensus;


/// Clase Python que encapsula el Consenso Isostático de Ring-0.
#[pyclass(name = "LarsaTriadConsensus")]
pub struct LarsaConsensusPy {
    inner: LarsaTriadConsensus,
}

#[pymethods]
impl LarsaConsensusPy {
    #[new]
    fn new() -> Self {
        Self {
            inner: LarsaTriadConsensus::new(),
        }
    }

    /// Somete una traza causal al Lóbulo Inhibidor (Lean 4) vía AOT.
    /// Retorna 0 (RUNNING) si la causalidad sobrevive, o 0xDEAD_6060 (POISONED) si el BFT colapsa.
    fn evaluate_trace(&self, trace_path: &str) -> u32 {
        self.inner.evaluate_trace(trace_path)
    }

    /// Retorna el número de vértices activos en el Quórum (0..=3).
    fn active_count(&self) -> u32 {
        self.inner.active_count()
    }
}

/// Retorna la versión del Kernel y el estado Termodinámico base
#[pyfunction]
fn kernel_status() -> PyResult<String> {
    Ok("BABYLON-60 Kernel C5-REAL (PyO3) - Exergy: Optimal. AOT Oracle Linked.".to_string())
}

/// Módulo raíz exportado a Python.
/// El nombre de la función debe coincidir con el nombre de la librería `lib.name` ("babylon60").
#[pymodule]
fn babylon60(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<LarsaConsensusPy>()?;
    m.add_function(wrap_pyfunction!(kernel_status, m)?)?;
    Ok(())
}
