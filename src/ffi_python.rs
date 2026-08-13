use pyo3::prelude::*;

/// Retorna la versión del Kernel y el estado Termodinámico base
#[pyfunction]
fn kernel_status() -> PyResult<String> {
    Ok("BABYLON-60 Kernel C5-REAL (PyO3) - Exergy: Optimal".to_string())
}

/// Módulo raíz exportado a Python.
/// El nombre de la función debe coincidir con el nombre de la librería `lib.name` ("babylon60").
#[pymodule]
fn babylon60(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(kernel_status, m)?)?;
    Ok(())
}
