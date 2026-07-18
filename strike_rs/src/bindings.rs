#![allow(unsafe_op_in_unsafe_fn)]
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

use crate::ledger::MasterLedger;
use crate::atms::Atms;
use crate::omega0::{Statement, Modality, Justification, JustifiedStatement};
use crate::publisher::{Publisher, ExportFormat};

#[pyclass]
pub struct CortexKernel {
    ledger: MasterLedger,
    atms: Atms,
}

#[pymethods]
impl CortexKernel {
    #[new]
    pub fn new(db_path: &str) -> PyResult<Self> {
        let ledger = MasterLedger::new(db_path)
            .map_err(|e| PyRuntimeError::new_err(format!("Ledger init failed: {}", e)))?;
        
        // Carga síncrona obligatoria desde disco (Rule Ω4)
        let _state = ledger.replay_to_atms_state()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to replay Ledger state: {}", e)))?;

        let atms = Atms::new();
        // Here we ideally initialize ATMS with state, but for now we keep it simple.
        
        Ok(Self {
            ledger,
            atms,
        })
    }

    /// Inyecta conocimiento en el Kernel (C5-REAL SQLite WAL + ATMS)
    pub fn assert_knowledge(&mut self, content: &str, sensor: &str, environment_id: &str) -> PyResult<String> {
        let js = JustifiedStatement {
            statement: Statement {
                content: content.to_string(),
                modality: Modality::Epistemic,
                obligations: vec![],
            },
            justification: Justification::Observation {
                timestamp: 0,
                sensor: sensor.to_string(),
            }
        };

        // Master Ledger (SQLite)
        let taint = self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| PyRuntimeError::new_err(format!("C5-REAL FATAL: Ledger error: {}", e)))?;
        
        // ATMS Memory
        self.atms.install(&js);
        
        Ok(taint)
    }

    /// Exporta el subgrafo BFT como Markdown o JSON
    pub fn publish(&self, environment_id: &str, format: &str) -> PyResult<String> {
        let publisher = Publisher::new(&self.ledger);
        let export_format = match format.to_lowercase().as_str() {
            "json" => ExportFormat::Json,
            "markdown" | "md" => ExportFormat::Markdown,
            _ => return Err(PyRuntimeError::new_err("Unsupported format. Use 'json' or 'markdown'")),
        };

        publisher.publish(environment_id, export_format)
            .map_err(|e| PyRuntimeError::new_err(e))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn strike_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CortexKernel>()?;
    Ok(())
}
