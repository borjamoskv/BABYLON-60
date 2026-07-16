use rusqlite::{params, Connection, Result};
use std::path::Path;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Instant;
use std::{env, fs};
use chrono::Utc;
use sha2::{Sha256, Digest};
use rand::Rng;
use crossbeam::channel;

const DEFAULT_TOTAL_REQUESTS: usize = 100_000_000; // 100 Millones
const BATCH_SIZE: usize = 10_000;
const DB_PATH: &str = "../../ledger/stress_test_100M.db";

struct Payload {
    worker_id: usize,
    payload_hash: String,
    timestamp: String,
}

fn main() -> Result<()> {
    println!("[*] Initializing CORTEX_SIEGE_100M (C5-REAL Rust BFT Engine)...");

    let args: Vec<String> = env::args().collect();
    let total_requests = if args.len() > 1 {
        args[1].parse::<usize>().unwrap_or(DEFAULT_TOTAL_REQUESTS)
    } else {
        DEFAULT_TOTAL_REQUESTS
    };

    let num_workers = num_cpus::get(); // Utilizar todos los cores físicos
    println!("[*] Target: {} requests", total_requests);
    println!("[*] Workers: {}", num_workers);
    println!("[*] Batch Size: {}", BATCH_SIZE);

    // Preparar DB
    let db_path = Path::new(DB_PATH);
    if let Some(parent) = db_path.parent() {
        fs::create_dir_all(parent).unwrap_or(());
    }
    if db_path.exists() {
        let _ = fs::remove_file(db_path);
    }

    let mut conn = Connection::open(db_path)?;
    conn.execute_batch(
        "PRAGMA journal_mode = WAL;
         PRAGMA synchronous = NORMAL;
         PRAGMA busy_timeout = 15000;
         PRAGMA temp_store = MEMORY;
         PRAGMA mmap_size = 30000000000;
         CREATE TABLE stress_log (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             timestamp TEXT NOT NULL,
             payload_hash TEXT NOT NULL,
             worker_id INTEGER NOT NULL
         );",
    )?;

    // Canal MPSC limitado para no explotar la memoria RAM
    let (tx, rx) = channel::bounded::<Payload>(BATCH_SIZE * 4);
    
    let start_time = Instant::now();
    let requests_generated = Arc::new(AtomicUsize::new(0));

    // Desplegar Workers (Productores de Entropía)
    crossbeam::scope(|s| {
        for worker_id in 0..num_workers {
            let tx_clone = tx.clone();
            let req_count = Arc::clone(&requests_generated);
            s.spawn(move |_| {
                let mut rng = rand::thread_rng();
                loop {
                    let current = req_count.fetch_add(1, Ordering::Relaxed);
                    if current >= total_requests {
                        break;
                    }

                    let val: f64 = rng.gen();
                    let payload_str = format!("worker_{}_{}", worker_id, val);
                    let mut hasher = Sha256::new();
                    hasher.update(payload_str.as_bytes());
                    let payload_hash = format!("{:x}", hasher.finalize());
                    let timestamp = Utc::now().to_rfc3339();

                    let payload = Payload {
                        worker_id,
                        payload_hash,
                        timestamp,
                    };

                    if tx_clone.send(payload).is_err() {
                        break; // Canal cerrado
                    }
                }
            });
        }

        // Eliminar la referencia original de tx para que rx termine cuando los workers terminen
        drop(tx);

        // Escritor Físico (Transductor a Disco)
        let mut total_written = 0;
        let mut batch_latencies = Vec::new();
        
        loop {
            let mut batch = Vec::with_capacity(BATCH_SIZE);
            for _ in 0..BATCH_SIZE {
                if let Ok(payload) = rx.recv() {
                    batch.push(payload);
                } else {
                    break;
                }
            }

            if batch.is_empty() {
                break;
            }

            let batch_start = Instant::now();
            let tx_db = conn.transaction().unwrap();
            {
                let mut stmt = tx_db.prepare_cached(
                    "INSERT INTO stress_log (timestamp, payload_hash, worker_id) VALUES (?, ?, ?)"
                ).unwrap();
                
                for p in &batch {
                    stmt.execute(params![p.timestamp, p.payload_hash, p.worker_id]).unwrap();
                }
            }
            tx_db.commit().unwrap();
            
            batch_latencies.push(batch_start.elapsed().as_millis() as f64);
            total_written += batch.len();

            if total_written % (BATCH_SIZE * 10) == 0 {
                println!("  ... Escritos: {} / {}", total_written, total_requests);
            }
        }

        let total_duration = start_time.elapsed();
        let throughput = (total_written as f64) / total_duration.as_secs_f64();
        
        // Calcular percentiles (Rule Σ15)
        batch_latencies.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let p50 = percentile(&batch_latencies, 50.0);
        let p90 = percentile(&batch_latencies, 90.0);
        let p95 = percentile(&batch_latencies, 95.0);
        let p99 = percentile(&batch_latencies, 99.0);

        println!("\nEXECUTIVE BRIEFING — RUST CORTEX_SIEGE_100M");
        println!("==========================================");
        println!("Total Requests: {}", total_written);
        println!("Total Duration: {:.3} s", total_duration.as_secs_f64());
        println!("Throughput:     {:.2} writes/s", throughput);
        println!("\nBatch Latency Percentiles ({} rows/batch):", BATCH_SIZE);
        println!("  p50:  {:.2} ms", p50);
        println!("  p90:  {:.2} ms", p90);
        println!("  p95:  {:.2} ms", p95);
        println!("  p99:  {:.2} ms", p99);
        println!("\nOutcome Matrix:");
        println!("  SUCCESS (Exergy): {}", total_written);
        let anergy = total_requests.saturating_sub(total_written);
        println!("  FAILURES (Anergia): {}", anergy);
        
        if anergy > 0 {
            println!("\n[!] STRESS TEST INCOMPLETE: Some writes dropped.");
            std::process::exit(1);
        } else {
            println!("\n[+] STRESS TEST PASS: C5-REAL SQLite batch insertion is anentropic.");
        }
    }).unwrap();

    Ok(())
}

fn percentile(sorted: &[f64], p: f64) -> f64 {
    if sorted.is_empty() {
        return 0.0;
    }
    let k = (sorted.len() - 1) as f64 * (p / 100.0);
    let f = k.floor();
    let c = k.ceil();
    if f == c {
        sorted[k as usize]
    } else {
        let d0 = sorted[f as usize] * (c - k);
        let d1 = sorted[c as usize] * (k - f);
        d0 + d1
    }
}
