#![cfg(feature = "cortex-persist")]

use babylon60::cortex::CortexPersister;
use babylon60::manifest::{SharedManifest, RUNNING};
use std::fs;
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::time::Instant;

fn new_manifest() -> &'static SharedManifest {
    let m = Box::new(SharedManifest {
        status_flag: AtomicU32::new(RUNNING),
        seq: AtomicU32::new(0),
        epoch_id: AtomicU64::new(0),
        payload_hash: [
            AtomicU64::new(0),
            AtomicU64::new(0),
            AtomicU64::new(0),
            AtomicU64::new(0),
        ],
        _padding: [0; 16],
    });
    Box::leak(m)
}

#[test]
fn test_cortex_persist_stress() {
    let tmp = std::env::temp_dir();
    let db_file = tmp.join("test_cortex.db");
    let db_path = db_file.to_str().unwrap();
    let clean_db = |path: &str| {
        let _ = fs::remove_file(path);
        let _ = fs::remove_file(format!("{}-wal", path));
        let _ = fs::remove_file(format!("{}-shm", path));
    };
    clean_db(db_path); // Limpiar tests previos
    
    let persister = CortexPersister::new(db_path).expect("No se pudo inicializar Cortex");
    let manifest = new_manifest();
    
    let total_ops = 10_000;
    
    let start_time = Instant::now();
    
    for i in 1..=total_ops {
        // Simulamos el productor escribiendo
        manifest.seq.store((i * 2) as u32, Ordering::Release);
        manifest.epoch_id.store(i as u64, Ordering::Release);
        manifest.payload_hash[0].store(0xDEADBEEF + i as u64, Ordering::Relaxed);
        
        // El consumidor (Cortex) drena al disco
        persister.drain_manifest(manifest).unwrap();
    }
    
    let elapsed = start_time.elapsed();
    
    println!("============================================================");
    println!("CORTEX PERSIST STRESS TEST: {} operaciones", total_ops);
    println!("Tiempo de persistencia a disco (SQLite WAL): {:?}", elapsed);
    println!("Throughput: {:.2} ops/sec", total_ops as f64 / elapsed.as_secs_f64());
    
    // Generar ancla Bitcoin de los últimos 100 registros
    let btc_anchor = persister.generate_bitcoin_op_return(100).unwrap();
    println!("Ancla Termodinámica Bitcoin generada:");
    println!("{}", btc_anchor);
    println!("============================================================");
    
    assert!(btc_anchor.starts_with("OP_RETURN "));
    // Limpiar al final
    clean_db(db_path);
}
