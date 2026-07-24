#![allow(unsafe_op_in_unsafe_fn)]
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use std::sync::{Arc, Mutex};

use crate::ledger::MasterLedger;
use crate::atms::Atms;
use crate::omega0::{Statement, Modality, Justification, JustifiedStatement};
use crate::publisher::{Publisher, ExportFormat};

#[derive(Clone)]
struct CortexKernelInner {
    ledger: Arc<Mutex<MasterLedger>>,
    atms: Arc<Mutex<Atms>>,
}

#[pyclass]
#[derive(Clone)]
pub struct CortexKernel {
    inner: CortexKernelInner,
}

#[pymethods]
impl CortexKernel {
    #[new]
    pub fn new(db_path: &str) -> PyResult<Self> {
        let ledger = MasterLedger::new(db_path)
            .map_err(|e| PyRuntimeError::new_err(format!("Ledger init failed: {}", e)))?;
        
        // Carga síncrona obligatoria desde disco (Rule Ω4)
        let state = ledger.replay_to_atms_state()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to replay Ledger state: {}", e)))?;

        let mut atms = Atms::new();
        // Reconstruct ATMS nodes from historical assertions in causal order
        if let Ok(assertions) = ledger.get_all_assertions() {
            for (_id, stmt_hash, just_hash, _env) in assertions {
                if let (Ok(stmt), Ok(just)) = (ledger.get_statement(&stmt_hash), ledger.get_justification(&just_hash)) {
                    let js = JustifiedStatement { statement: stmt, justification: just };
                    atms.install(&js);
                }
            }
        }
        // Reconstruct nogoods and trigger contradiction propagation
        for nogood_hash in &state.nogoods {
            if let Ok(stmt) = ledger.get_statement(nogood_hash) {
                let node_id = if let Some(node_id) = atms.find_node_by_datum(&stmt.content) {
                    node_id
                } else {
                    let js = JustifiedStatement {
                        statement: stmt,
                        justification: Justification::Conjecture,
                    };
                    atms.install(&js)
                };
                atms.contradict(&[node_id]);
            }
        }
        
        Ok(Self {
            inner: CortexKernelInner {
                ledger: Arc::new(Mutex::new(ledger)),
                atms: Arc::new(Mutex::new(atms)),
            }
        })
    }

    /// Inyecta conocimiento en el Kernel (C5-REAL SQLite WAL + ATMS)
    pub fn assert_knowledge(&self, py: Python<'_>, content: String, sensor: String, environment_id: String) -> PyResult<String> {
        let inner = self.inner.clone();
        
        py.allow_threads(move || {
            let mut ledger = inner.ledger.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: Ledger mutex poisoned"))?;
            let mut atms = inner.atms.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: ATMS mutex poisoned"))?;

            let js = JustifiedStatement {
                statement: Statement {
                    content: content.clone(),
                    modality: Modality::Epistemic,
                    obligations: vec![],
                },
                justification: Justification::Observation {
                    timestamp: 0,
                    sensor,
                }
            };

            // Master Ledger (SQLite)
            let taint = ledger.assert_knowledge(&js, &environment_id)
                .map_err(|e| PyRuntimeError::new_err(format!("C5-REAL FATAL: Ledger error: {}", e)))?;
            
            // ATMS Memory
            atms.install(&js);
            
            Ok(taint)
        })
    }

    /// Inyecta una contradicción (nogood) en el Kernel y propaga DDB en ATMS
    pub fn contradict_knowledge(&self, py: Python<'_>, content: String, environment_id: String) -> PyResult<String> {
        let inner = self.inner.clone();
        
        py.allow_threads(move || {
            let mut ledger = inner.ledger.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: Ledger mutex poisoned"))?;
            let mut atms = inner.atms.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: ATMS mutex poisoned"))?;

            let stmt = Statement {
                content: content.clone(),
                modality: Modality::Epistemic,
                obligations: vec![],
            };
            let js = JustifiedStatement {
                statement: stmt.clone(),
                justification: Justification::Conjecture,
            };
            
            // Ensure statement is recorded in Master Ledger so nogood replay can find it
            ledger.assert_knowledge(&js, &environment_id)
                .map_err(|e| PyRuntimeError::new_err(format!("C5-REAL FATAL: Ledger error asserting knowledge for nogood: {}", e)))?;

            let statement_hash = MasterLedger::hash_statement(&stmt);
            let taint = ledger.assert_nogood(&statement_hash, &environment_id)
                .map_err(|e| PyRuntimeError::new_err(format!("C5-REAL FATAL: Ledger error asserting nogood: {}", e)))?;
                
            let node_id = if let Some(node_id) = atms.find_node_by_datum(&content) {
                node_id
            } else {
                atms.install(&js)
            };
            atms.contradict(&[node_id]);
            
            Ok(taint)
        })
    }

    /// Verifica si una proposición es creída en el punto fijo ATMS actual
    pub fn is_believed(&self, py: Python<'_>, content: String) -> PyResult<bool> {
        let inner = self.inner.clone();
        py.allow_threads(move || {
            let atms = inner.atms.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: ATMS mutex poisoned"))?;
            if let Some(node_id) = atms.find_node_by_datum(&content) {
                Ok(atms.is_believed(node_id))
            } else {
                Ok(false)
            }
        })
    }

    /// Descarga en tiempo de ejecución la obligación de no-contradicción
    pub fn contradiction_free(&self, py: Python<'_>, content: String) -> PyResult<bool> {
        let inner = self.inner.clone();
        py.allow_threads(move || {
            let atms = inner.atms.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: ATMS mutex poisoned"))?;
            if let Some(node_id) = atms.find_node_by_datum(&content) {
                Ok(atms.contradiction_free(node_id))
            } else {
                Ok(true)
            }
        })
    }

    /// Exporta el subgrafo BFT como Markdown o JSON
    pub fn publish(&self, py: Python<'_>, environment_id: String, format: String) -> PyResult<String> {
        let inner = self.inner.clone();
        py.allow_threads(move || {
            let ledger = inner.ledger.lock().map_err(|_| PyRuntimeError::new_err("C5-REAL FATAL: Ledger mutex poisoned"))?;
            let publisher = Publisher::new(&ledger);
            let export_format = match format.to_lowercase().as_str() {
                "json" => ExportFormat::Json,
                "markdown" | "md" => ExportFormat::Markdown,
                _ => return Err(PyRuntimeError::new_err("Unsupported format. Use 'json' or 'markdown'")),
            };

            publisher.publish(&environment_id, export_format)
                .map_err(PyRuntimeError::new_err)
        })
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn strike_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CortexKernel>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_cortex_kernel_atms_hardening_and_replay() {
        let db_path = "target/test_cortex_kernel_replay.db";
        let _ = fs::remove_file(db_path);

        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            {
                let kernel = CortexKernel::new(db_path).expect("[C5-REAL] FATAL: Failed to initialize CortexKernel");

                let id1 = kernel.assert_knowledge(py, "Water is H2O".to_string(), "sensor_a".to_string(), "env_master".to_string())
                    .expect("[C5-REAL] FATAL: assert_knowledge failed");
                assert!(!id1.is_empty() && id1.contains('-'), "Expected UUID assertion ID");

                assert!(kernel.is_believed(py, "Water is H2O".to_string()).unwrap());
                assert!(kernel.contradiction_free(py, "Water is H2O".to_string()).unwrap());

                let taint_nogood = kernel.contradict_knowledge(py, "Alien hypothesis X".to_string(), "env_master".to_string())
                    .expect("[C5-REAL] FATAL: contradict_knowledge failed");
                assert!(taint_nogood.contains(":NOGOOD:"));

                assert!(kernel.is_believed(py, "Water is H2O".to_string()).unwrap(), "Uncontradicted premise must remain believed");
                assert!(!kernel.is_believed(py, "Alien hypothesis X".to_string()).unwrap(), "Contradicted hypothesis label must be pruned");
                assert!(!kernel.contradiction_free(py, "Alien hypothesis X".to_string()).unwrap());
            }

            {
                let kernel_replayed = CortexKernel::new(db_path).expect("[C5-REAL] FATAL: Failed to reopen CortexKernel");
                assert!(kernel_replayed.is_believed(py, "Water is H2O".to_string()).unwrap(), "Replayed uncontradicted premise must be believed");
                assert!(kernel_replayed.contradiction_free(py, "Water is H2O".to_string()).unwrap());
                assert!(!kernel_replayed.is_believed(py, "Alien hypothesis X".to_string()).unwrap(), "Replayed contradicted hypothesis must remain pruned");
                assert!(!kernel_replayed.contradiction_free(py, "Alien hypothesis X".to_string()).unwrap(), "Replayed ATMS must preserve nogood state");
            }
        });

        let _ = fs::remove_file(db_path);
    }
}
