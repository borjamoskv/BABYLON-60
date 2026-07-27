#![allow(unsafe_op_in_unsafe_fn)]
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

use crate::ledger::MasterLedger;
use crate::atms::Atms;
use crate::omega0::{Statement, Modality, Justification, JustifiedStatement};
use crate::publisher::{Publisher, ExportFormat};
use crate::bft_engine::{BftAsyncEngine, BftNode};
use crate::kda_memory::KdaMemoryBuffer;
use crate::gelabp_calc::ExergyParams;
use std::sync::Arc;
use tokio::sync::RwLock;

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

    /// Inyecta una contradicción (nogood) en el Kernel y propaga DDB en ATMS
    pub fn contradict_knowledge(&mut self, content: &str, environment_id: &str) -> PyResult<String> {
        let stmt = Statement {
            content: content.to_string(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js = JustifiedStatement {
            statement: stmt.clone(),
            justification: Justification::Conjecture,
        };
        // Ensure statement is recorded in Master Ledger so nogood replay can find it
        self.ledger.assert_knowledge(&js, environment_id)
            .map_err(|e| PyRuntimeError::new_err(format!("C5-REAL FATAL: Ledger error asserting knowledge for nogood: {}", e)))?;

        let statement_hash = MasterLedger::hash_statement(&stmt);
        let taint = self.ledger.assert_nogood(&statement_hash, environment_id)
            .map_err(|e| PyRuntimeError::new_err(format!("C5-REAL FATAL: Ledger error asserting nogood: {}", e)))?;
            
        let node_id = if let Some(node_id) = self.atms.find_node_by_datum(content) {
            node_id
        } else {
            self.atms.install(&js)
        };
        self.atms.contradict(&[node_id]);
        
        Ok(taint)
    }

    /// Verifica si una proposición es creída en el punto fijo ATMS actual
    pub fn is_believed(&self, content: &str) -> PyResult<bool> {
        if let Some(node_id) = self.atms.find_node_by_datum(content) {
            Ok(self.atms.is_believed(node_id))
        } else {
            Ok(false)
        }
    }

    /// Descarga en tiempo de ejecución la obligación de no-contradicción
    pub fn contradiction_free(&self, content: &str) -> PyResult<bool> {
        if let Some(node_id) = self.atms.find_node_by_datum(content) {
            Ok(self.atms.contradiction_free(node_id))
        } else {
            Ok(true)
        }
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
    m.add_class::<BftSwarmEngine>()?;
    Ok(())
}

#[pyclass]
pub struct BftSwarmEngine {
    engine: BftAsyncEngine,
    memory: Arc<RwLock<KdaMemoryBuffer>>,
}

#[pymethods]
impl BftSwarmEngine {
    #[new]
    pub fn new(concurrency_limit: usize, memory_capacity: usize) -> Self {
        Self {
            engine: BftAsyncEngine::new(concurrency_limit),
            memory: Arc::new(RwLock::new(KdaMemoryBuffer::new(memory_capacity))),
        }
    }

    pub fn add_node(&mut self, id: String, deps: Vec<String>, payload: String, latency_ms: u64, should_fail: bool) {
        self.engine.add_node(BftNode {
            id,
            deps,
            payload,
            latency_ms,
            should_fail,
        });
    }

    pub fn run_dag(&self, g: f64, l: f64, e_base: f64, db_path: String) -> PyResult<String> {
        let rt = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to build tokio runtime: {}", e)))?;
        
        let params = ExergyParams { g, l, a: 1.0, b: 1.0, p: 1.0, e_base };

        rt.block_on(async {
            match self.engine.run_dag(self.memory.clone(), params, &db_path).await {
                Ok(_) => {
                    let mem = self.memory.read().await;
                    Ok(format!("SUCCESS: DAG executed. Memory entries: {} crystallized in {}", mem.len(), db_path))
                },
                Err(e) => Err(PyRuntimeError::new_err(format!("BFT Rollback Triggered: {}", e))),
            }
        })
    }

    pub fn stress_test_native(&mut self, count: usize) {
        self.engine.stress_test_native(count);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_cortex_kernel_atms_hardening_and_replay() {
        let db_path = "target/test_cortex_kernel_replay.db";
        let _ = fs::remove_file(db_path);

        {
            let mut kernel = CortexKernel::new(db_path).expect("[C5-REAL] FATAL: Failed to initialize CortexKernel");

            // Assert empirical knowledge (Observation -> Premise in ATMS)
            let id1 = kernel.assert_knowledge("Water is H2O", "sensor_a", "env_master")
                .expect("[C5-REAL] FATAL: assert_knowledge failed");
            assert!(!id1.is_empty() && id1.contains('-'), "Expected UUID assertion ID");

            // Verify belief in ATMS
            assert!(kernel.is_believed("Water is H2O").unwrap());
            assert!(kernel.contradiction_free("Water is H2O").unwrap());

            // Assert contradiction (nogood) against a conjecture hypothesis
            let taint_nogood = kernel.contradict_knowledge("Alien hypothesis X", "env_master")
                .expect("[C5-REAL] FATAL: contradict_knowledge failed");
            assert!(taint_nogood.contains(":NOGOOD:"));

            // Verify DDB contradiction propagation pruned the label of the contradicted conjecture
            assert!(kernel.is_believed("Water is H2O").unwrap(), "Uncontradicted premise must remain believed");
            assert!(!kernel.is_believed("Alien hypothesis X").unwrap(), "Contradicted hypothesis label must be pruned");
            assert!(!kernel.contradiction_free("Alien hypothesis X").unwrap());
        }

        // Reopen new kernel instance from same disk DB and verify exact state replay
        {
            let kernel_replayed = CortexKernel::new(db_path).expect("[C5-REAL] FATAL: Failed to reopen CortexKernel");
            assert!(kernel_replayed.is_believed("Water is H2O").unwrap(), "Replayed uncontradicted premise must be believed");
            assert!(kernel_replayed.contradiction_free("Water is H2O").unwrap());
            assert!(!kernel_replayed.is_believed("Alien hypothesis X").unwrap(), "Replayed contradicted hypothesis must remain pruned");
            assert!(!kernel_replayed.contradiction_free("Alien hypothesis X").unwrap(), "Replayed ATMS must preserve nogood state");
        }

        let _ = fs::remove_file(db_path);
    }
}
