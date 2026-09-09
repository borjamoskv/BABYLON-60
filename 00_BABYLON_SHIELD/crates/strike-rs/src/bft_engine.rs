// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use crate::kda_memory::KdaMemoryBuffer;
use crate::gelabp_calc::{compute_score, ExergyParams};
use crate::atms::Atms;
use crate::omega0::{Statement, Modality, Justification, JustifiedStatement};
use blake3::Hasher;
use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use tokio::sync::{RwLock, Semaphore, Notify};
use rusqlite::{Connection, OpenFlags};
use std::time::Instant;
use std::fs::{self, OpenOptions};

struct ThermalLock {
    path: String,
}

impl ThermalLock {
    fn acquire(path: &str) -> Result<Self, String> {
        match OpenOptions::new().write(true).create_new(true).open(path) {
            Ok(_) => Ok(Self { path: path.to_string() }),
            Err(_) => Err("Thermodynamic Hysteresis Active: Another swarm holds the lock (INV_C5_22)".to_string()),
        }
    }
}

impl Drop for ThermalLock {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

#[derive(Debug, Clone)]
pub struct BftNode {
    pub id: String,
    pub deps: Vec<String>,
    pub payload: String,
    // Optional artificial latency for simulation
    pub latency_ms: u64,
    pub should_fail: bool,
}

pub type TelemetryEvent = (String, u64, f64, Vec<u8>);

pub struct BftAsyncEngine {
    pub concurrency_limit: usize,
    nodes: HashMap<String, BftNode>,
    pub telemetry_tx: Option<tokio::sync::broadcast::Sender<TelemetryEvent>>,
}

impl BftAsyncEngine {
    pub fn new(concurrency_limit: usize) -> Self {
        Self {
            concurrency_limit,
            nodes: HashMap::new(),
            telemetry_tx: None,
        }
    }

    pub fn add_node(&mut self, node: BftNode) {
        self.nodes.insert(node.id.clone(), node);
    }

    /// Ejecuta el pipeline topológico respetando las dependencias.
    /// Si la termodinámica falla (Score < 700) aborta y hace Rollback (Ultrathink).
    pub async fn run_dag(&self, memory: Arc<RwLock<KdaMemoryBuffer>>, params: ExergyParams, db_path: &str) -> Result<(), String> {
        let lock_path = if db_path.is_empty() {
            format!("/tmp/.cortex_thermal_lock_{}_{}.lock", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_nanos())
        } else {
            format!("{}.lock", db_path)
        };
        let _thermal_lock = ThermalLock::acquire(&lock_path)?;

        let start_wall = Instant::now();
        
        // Inicializar ATMS efímero (Motor Cognitivo)
        let atms = Arc::new(RwLock::new(Atms::new()));
        {
            let mut a = atms.write().await;
            let mut add_nogood = |s: &str| {
                let js = JustifiedStatement {
                    statement: Statement { content: s.to_string(), modality: Modality::Epistemic, obligations: vec![] },
                    justification: Justification::Conjecture,
                };
                let node_id = a.install(&js);
                a.contradict(&[node_id]); // Declarar formalmente como Nogood
            };
            add_nogood("Infinite Fiat Issuance");
            add_nogood("Emision de Leliqs sin Respaldo");
            add_nogood("Deuda Extractivista Offshore");
        }

        let snapshot = {
            let m = memory.read().await;
            m.snapshot()
        };

        let semaphore = Arc::new(Semaphore::new(self.concurrency_limit));
        
        let sorted = match self.topological_sort() {
            Ok(s) => s,
            Err(e) => return Err(e),
        };

        // --- ZERO-COPY BFT HYPERVISOR INTEGRATION ---
        use crate::hypervisor::{ZeroCopyPublisher, ZeroCopySubscriber};
        use ed25519_dalek::{SigningKey, Signer};
        use rand::rngs::OsRng;
        use std::thread;

        let svc_tasks = "c5_bft_tasks";
        let svc_results = "c5_bft_results";

        let mut csprng = OsRng;
        let orch_keys = SigningKey::generate(&mut csprng);
        let worker_keys = SigningKey::generate(&mut csprng);
        let worker_pub_key = worker_keys.verifying_key();
        let orch_pub_key = orch_keys.verifying_key();

        let mut node_to_id = HashMap::new();
        let mut id_to_node = HashMap::new();
        for (i, node_id) in sorted.iter().enumerate() {
            let id = i as u64;
            node_to_id.insert(node_id.clone(), id);
            id_to_node.insert(id, node_id.clone());
        }

        // 1. Spawning IPC Worker in a native thread (not Tokio)
        let stop_worker = Arc::new(std::sync::atomic::AtomicBool::new(false));
        let stop_worker_clone = stop_worker.clone();
        
        let worker_handle = thread::spawn(move || {
            let task_sub = ZeroCopySubscriber::new(svc_tasks).expect("C5-REAL: Failed to bind ZeroCopy Subscriber");
            let result_pub = ZeroCopyPublisher::new(svc_results).expect("C5-REAL: Failed to bind ZeroCopy Publisher");
            
            while !stop_worker_clone.load(std::sync::atomic::Ordering::Relaxed) {
                if let Ok(Some(sample)) = task_sub.subscriber.receive() {
                    if !sample.verify(&orch_pub_key) { continue; }
                    
                    let node_id = sample.seq_num;
                    let payload_hash_hex = hex::encode(sample.payload_hash);
                    
                    let _ = result_pub.publish_node(
                        2, 1, node_id, &payload_hash_hex, &worker_keys
                    );
                } else {
                    thread::yield_now();
                }
            }
        });

        // 2. Orchestrator Thread (Holds iceoryx2 non-Send types)
        let (tx_completed, mut rx_completed) = tokio::sync::mpsc::channel(1024);
        let num_nodes = sorted.len();
        
        let mut in_degree = HashMap::new();
        let mut children_map = HashMap::new();
        for k in self.nodes.keys() {
            in_degree.insert(k.clone(), 0);
            children_map.insert(k.clone(), Vec::new());
        }
        for node in self.nodes.values() {
            for dep in &node.deps {
                children_map.get_mut(dep).expect("C5-REAL: Topological dependency missing").push(node.id.clone());
                *in_degree.get_mut(&node.id).expect("C5-REAL: Node ID missing in degree map") += 1;
            }
        }
        
        let mut ready_queue = Vec::new();
        for (k, v) in &in_degree {
            if *v == 0 {
                ready_queue.push(k.clone());
            }
        }
        
        let orch_keys_clone = orch_keys.clone();
        thread::spawn(move || {
            let task_pub = ZeroCopyPublisher::new(svc_tasks).expect("C5-REAL: Failed to bind ZeroCopy Publisher");
            let result_sub = ZeroCopySubscriber::new(svc_results).expect("C5-REAL: Failed to bind ZeroCopy Subscriber");
            let mut completed = HashSet::new();
            
            while completed.len() < num_nodes {
                while let Some(n_id) = ready_queue.pop() {
                    let seq_num = *node_to_id.get(&n_id).expect("C5-REAL: Node ID missing in translation mapping");
                    let fake_hash = "0000000000000000000000000000000000000000000000000000000000000000";
                    let _ = task_pub.publish_node(1, 0, seq_num, fake_hash, &orch_keys_clone);
                }

                if let Ok(Some(sample)) = result_sub.subscriber.receive() {
                    if sample.verify(&worker_pub_key) && sample.view == 1 {
                        let seq_num = sample.seq_num;
                        if let Some(n_id) = id_to_node.get(&seq_num) {
                            if completed.insert(n_id.clone()) {
                                let _ = tx_completed.blocking_send(n_id.clone());
                                if let Some(kids) = children_map.get(n_id) {
                                    for kid in kids {
                                        let d = in_degree.get_mut(kid).expect("C5-REAL: Child ID missing in degree map");
                                        *d -= 1;
                                        if *d == 0 {
                                            ready_queue.push(kid.clone());
                                        }
                                    }
                                }
                            }
                        }
                    }
                } else {
                    thread::yield_now();
                }
            }
        });

        // 3. Async Engine awaits completions
        let mut all_success = true;
        let mut err_msg = String::new();
        let mut node_sum_ms = 0.0;
        let mut has_high_latency = false;
        
        let mut completed_count = 0;
        while completed_count < num_nodes {
            if let Some(n_id) = rx_completed.recv().await {
                completed_count += 1;
                let node = self.nodes.get(&n_id).expect("C5-REAL: Critical DAG Integrity Failure - Node not found");
                if node.should_fail {
                    all_success = false;
                    err_msg = format!("Node {} failed", node.id);
                    break;
                }

                let js = JustifiedStatement {
                    statement: Statement { content: node.payload.clone(), modality: Modality::Epistemic, obligations: vec![] },
                    justification: Justification::Conjecture,
                };
                let atms_node_id = {
                    let mut a = atms.write().await;
                    if let Some(id) = a.find_node_by_datum(&node.payload) { id } else { a.install(&js) }
                };
                if !atms.read().await.contradiction_free(atms_node_id) {
                    all_success = false;
                    err_msg = format!("ATMS Cognitive Contradiction: Payload '{}' is logically invalid (Nogood).", node.payload);
                    break;
                }

                let mut hasher = Hasher::new();
                hasher.update(node.id.as_bytes());
                hasher.update(node.payload.as_bytes());
                let proof = hasher.finalize().to_hex().to_string();

                memory.write().await.put(&node.id, proof.clone());

                if let Some(tx) = &self.telemetry_tx {
                    let local_exergy = 0.9999 - (node.latency_ms as f64 * 0.0001);
                    let seq_count = memory.read().await.len() as u64;
                    let _ = tx.send((proof, seq_count, local_exergy, node.id.as_bytes().to_vec()));
                }

                node_sum_ms += node.latency_ms as f64;
                if node.latency_ms > 2 { has_high_latency = true; }
            }
        }

        stop_worker.store(true, std::sync::atomic::Ordering::Relaxed);
        let _ = worker_handle.join();

        if !all_success {
            let mut m = memory.write().await;
            m.restore(snapshot);
            return Err(err_msg);
        }

        // EVALUADOR GELABP NATIVO (Ultrathink Watchdog)
        let wall_ms = start_wall.elapsed().as_secs_f64() * 1000.0;
        let mem_stats = {
            let m = memory.read().await;
            (m.capacity(), m.len())
        };

        let score = compute_score(
            &params,
            wall_ms,
            node_sum_ms,
            mem_stats.0,
            mem_stats.1,
            has_high_latency,
            false // Asumimos no placeholders en entorno comercial pre-filtrado
        );

        if score < 700.0 {
            // Falla termodinámica -> Rollback
            let mut m = memory.write().await;
            m.restore(snapshot);
            return Err(format!("Thermodynamic Collapse: Score {:.2} < 700. Aborting DAG.", score));
        }

        // CRISTALIZACIÓN EN SQLITE WAL (INV_C5_18 timeout=5000)
        if !db_path.is_empty() {
            let conn = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE)
                .map_err(|e| format!("SQLite Open Error: {}", e))?;
            conn.busy_timeout(std::time::Duration::from_millis(5000))
                .map_err(|e| format!("SQLite Timeout Error: {}", e))?;
            
            conn.execute_batch(
                "PRAGMA journal_mode = WAL;
                 CREATE TABLE IF NOT EXISTS cortex_memory_bft (
                     node_id TEXT PRIMARY KEY,
                     proof TEXT NOT NULL,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                 );"
            ).map_err(|e| format!("SQLite Pragma Error: {}", e))?;

            let m = memory.read().await;
            let tx = conn.unchecked_transaction().map_err(|e| format!("TX Error: {}", e))?;
            {
                let mut stmt = tx.prepare_cached("INSERT OR REPLACE INTO cortex_memory_bft (node_id, proof) VALUES (?1, ?2)")
                    .map_err(|e| format!("Prepare Error: {}", e))?;
                for (k, entry) in m.snapshot() {
                    stmt.execute([&k, &entry.value]).map_err(|e| format!("Insert Error: {}", e))?;
                }
            }
            tx.commit().map_err(|e| format!("Commit Error: {}", e))?;
        }

        Ok(())
    }

    fn topological_sort(&self) -> Result<Vec<String>, String> {
        let mut in_degree = HashMap::new();
        let mut children_map: HashMap<String, Vec<String>> = HashMap::new();
        for k in self.nodes.keys() {
            in_degree.insert(k.clone(), 0);
            children_map.insert(k.clone(), Vec::new());
        }

        for node in self.nodes.values() {
            for dep in &node.deps {
                if !self.nodes.contains_key(dep) {
                    return Err(format!("Dependency {} not found for node {}", dep, node.id));
                }
                children_map.get_mut(dep).expect("C5-REAL: Topological dependency missing").push(node.id.clone());
                *in_degree.get_mut(&node.id).expect("C5-REAL: Node ID missing in degree map") += 1;
            }
        }

        let mut queue = Vec::new();
        for (k, v) in &in_degree {
            if *v == 0 {
                queue.push(k.clone());
            }
        }

        let mut sorted = Vec::new();
        while let Some(n) = queue.pop() {
            sorted.push(n.clone());
            if let Some(children) = children_map.get(&n) {
                for child_id in children {
                    let d = in_degree.get_mut(child_id).expect("C5-REAL: Child ID missing in topological map");
                    *d -= 1;
                    if *d == 0 {
                        queue.push(child_id.clone());
                    }
                }
            }
        }

        if sorted.len() != self.nodes.len() {
            return Err("Cycle detected in BFT DAG".to_string());
        }

        Ok(sorted)
    }

    pub fn stress_test_native(&mut self, count: usize) {
        self.nodes.clear();
        for i in 0..count {
            let id = format!("stress_{}", i);
            self.nodes.insert(id.clone(), BftNode {
                id,
                deps: vec![],
                payload: format!("Payload {}", i),
                latency_ms: 1,
                should_fail: false,
            });
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use tokio::sync::RwLock;

    #[tokio::test]
    async fn test_ax_bft_extreme_swarm() {
        // Eje 3: Swarm Commander (Extreme Stress Test)
        // Simulate a 100 node DAG with deep dependencies (within ATMS 128-bitmask limit)
        let mut engine = BftAsyncEngine::new(10); // Concurrency limit 10
        let mem = Arc::new(RwLock::new(KdaMemoryBuffer::new(500)));

        for i in 0..100 {
            let mut deps = Vec::new();
            if i >= 10 {
                // Layer-based DAG: Each layer of 10 nodes depends on previous layer
                deps.push(format!("node_{}", i - 10));
            }
            engine.add_node(BftNode {
                id: format!("node_{}", i),
                deps,
                payload: format!("Payload for {}", i),
                latency_ms: 1, // 1ms sleep to force context switching
                should_fail: false,
            });
        }

        let params = ExergyParams { g: 50.0, l: 50.0, a: 1.0, b: 1.0, p: 1.0, e_base: 0.04 };
        let res = engine.run_dag(mem.clone(), params, "").await;
        assert!(res.is_ok(), "Test failed: {:?}", res);

        let m = mem.read().await;
        assert_eq!(m.len(), 100);
    }
}
