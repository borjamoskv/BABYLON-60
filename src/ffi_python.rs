use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use std::panic::{catch_unwind, AssertUnwindSafe};

/// Retorna la versión del Kernel y el estado Termodinámico base
#[pyfunction]
fn kernel_status() -> PyResult<String> {
    Ok("BABYLON-60 Kernel C5-REAL (PyO3) - Exergy: Optimal".to_string())
}

/// Ejecuta un cierre de Rust de forma segura aislando panics a través de `catch_unwind`.
fn safe_ffi_call<F, R>(f: F) -> PyResult<R>
where
    F: FnOnce() -> R + std::panic::UnwindSafe,
{
    catch_unwind(AssertUnwindSafe(f)).map_err(|err| {
        let panic_msg = if let Some(s) = err.downcast_ref::<&str>() {
            s.to_string()
        } else if let Some(s) = err.downcast_ref::<String>() {
            s.clone()
        } else {
            "Unknown Rust Panic in BABYLON-60 Kernel FFI Boundary".to_string()
        };
        PyRuntimeError::new_err(format!("BABYLON-60 FFI Panic Shield: {}", panic_msg))
    })
}

/// Verifica el estado del manifiesto aislado de panics.
#[pyfunction]
fn safe_kernel_eval(payload: String) -> PyResult<String> {
    safe_ffi_call(|| {
        if payload.contains("TRIGGER_PANIC") {
            panic!("Epistemic Invariant Violation Triggered in FFI Boundary");
        }
        format!("OK: Processed payload '{}' safely", payload)
    })
}

/// Módulo raíz exportado a Python.
/// El nombre de la función debe coincidir con el nombre de la librería `lib.name` ("babylon60").
#[pymodule]
fn babylon60(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(kernel_status, m)?)?;
    m.add_function(wrap_pyfunction!(safe_kernel_eval, m)?)?;
    Ok(())
}

