//! Bounded typed Python boundary for the FL-019 integer affine verifier.
use crate::geometry_integrity::{GeometryVerifier as RustGeometryVerifier, CHECKER_VERSION};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Stateful geometry checker. Caller-provided evaluator votes are never accepted.
#[pyclass(name = "GeometryVerifier")]
pub struct GeometryVerifier {
    inner: RustGeometryVerifier,
}

#[pymethods]
impl GeometryVerifier {
    #[new]
    fn new() -> Self {
        Self {
            inner: RustGeometryVerifier::new(),
        }
    }

    fn verify(&mut self, request_json: &str) -> PyResult<String> {
        let report = self
            .inner
            .verify_json(request_json)
            .map_err(|error| PyValueError::new_err(error.to_string()))?;
        serde_json::to_string(&report).map_err(|error| PyValueError::new_err(error.to_string()))
    }
}

/// Additional extension entry point; no generic tool or network entry point.
#[pymodule]
fn _babylon60_geometry(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<GeometryVerifier>()?;
    module.add("CHECKER_VERSION", CHECKER_VERSION)?;
    Ok(())
}
