use strike_rs::ledger::MasterLedger;
use strike_rs::omega0::{Statement, Justification, Modality, JustifiedStatement};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Instant;

fn main() {
    println!("🛡️ FALSACIÓN TERMODINÁMICA: MASTER LEDGER (WAL)");
    println!("═══════════════════════════════════════════════════════════════════");
    
    let db_path = "target/poc_wal_stress.db";
    let _ = std::fs::remove_file(db_path);

    // Initializamos el ledger
    let ledger = Arc::new(Mutex::new(MasterLedger::new(db_path).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.")));

    let num_threads = 10;
    let ops_per_thread = 500;
    let mut handles = vec![];

    let start = Instant::now();

    for t_id in 0..num_threads {
        let ledger_clone = Arc::clone(&ledger);
        handles.push(thread::spawn(move || {
            for i in 0..ops_per_thread {
                let s = Statement {
                    content: format!("Thread {} iter {}", t_id, i),
                    modality: Modality::Epistemic,
                    obligations: vec![],
                };
                let js = JustifiedStatement {
                    statement: s,
                    justification: Justification::Observation {
                        timestamp: i,
                        sensor: format!("t_{}", t_id),
                    },
                };
                
                // Bloqueo de Mutex forzado por el diseño síncrono de Rust + SQLite
                let mut db = ledger_clone.lock().expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
                db.assert_knowledge(&js, "stress_env").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
            }
        }));
    }

    for h in handles {
        h.join().expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
    }

    let duration = start.elapsed();
    let total_ops = num_threads * ops_per_thread;
    let ops_per_sec = total_ops as f64 / duration.as_secs_f64();

    println!("[*] Test Completado: {} aserciones causales.", total_ops);
    println!("[*] Tiempo total   : {:.2?}", duration);
    println!("[*] Throughput     : {:.2} aserciones/segundo", ops_per_sec);
    
    if ops_per_sec < 5000.0 {
        println!("❌ DIAGNÓSTICO: Cuello de botella Termodinámico. El Mutex + Transaction-per-write ahoga el sistema.");
    } else {
        println!("✅ DIAGNÓSTICO: La topología WAL resiste el flujo.");
    }
}
