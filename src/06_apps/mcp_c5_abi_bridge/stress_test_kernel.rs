// C5-REAL EXERGY CERTIFIED - KERNEL C-ABI STRESS TEST
// file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/06_apps/mcp_c5_abi_bridge/stress_test_kernel.rs

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

#[repr(C, align(64))]
pub struct SharedManifestBuffer {
    pub sequence_epoch: AtomicU64,
    pub payload_size: AtomicU64,
    pub status_code: AtomicU64,
    pub sha3_digest: [AtomicU64; 4], // 32 bytes split across 4 AtomicU64s for thread safety
    pub payload: [u8; 4096],
}

impl SharedManifestBuffer {
    pub fn new() -> Self {
        Self {
            sequence_epoch: AtomicU64::new(0),
            payload_size: AtomicU64::new(0),
            status_code: AtomicU64::new(0),
            sha3_digest: [
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
            ],
            payload: [0u8; 4096],
        }
    }

    pub fn write_optimistic(&self, status: u64, text: &str) {
        let _seq = self.sequence_epoch.fetch_add(1, Ordering::Acquire);

        let bytes = text.as_bytes();
        let len = bytes.len().min(4096);
        self.payload_size.store(len as u64, Ordering::Relaxed);
        self.status_code.store(status, Ordering::Relaxed);

        // Update surrogate digest
        let mut d = [0u64; 4];
        for (i, &b) in bytes[..len].iter().enumerate() {
            d[i % 4] = d[i % 4].wrapping_add(b as u64);
        }
        for i in 0..4 {
            self.sha3_digest[i].store(d[i], Ordering::Relaxed);
        }

        self.sequence_epoch.fetch_add(1, Ordering::Release);
    }

    pub fn read_optimistic(&self) -> Option<(u64, u64)> {
        let seq1 = self.sequence_epoch.load(Ordering::Acquire);
        if seq1 % 2 != 0 {
            return None;
        }

        let size = self.payload_size.load(Ordering::Relaxed);
        let status = self.status_code.load(Ordering::Relaxed);

        let seq2 = self.sequence_epoch.load(Ordering::Acquire);
        if seq1 == seq2 {
            Some((size, status))
        } else {
            None
        }
    }
}

fn main() {
    println!("=== STRESS TEST: KERNEL C-ABI SEQLOCK ===");
    let num_threads = 8;
    let ops_per_thread = 200_000;
    let total_ops = num_threads * ops_per_thread;

    let buffer = Arc::new(SharedManifestBuffer::new());
    let start = Instant::now();

    let mut handles = vec![];
    for t in 0..num_threads {
        let buf = Arc::clone(&buffer);
        let handle = thread::spawn(move || {
            let mut retries = 0;
            let mut reads = 0;
            for i in 0..ops_per_thread {
                if i % 2 == 0 {
                    let msg = format!("THREAD_{}_MSG_{}", t, i);
                    buf.write_optimistic(200, &msg);
                } else {
                    reads += 1;
                    if buf.read_optimistic().is_none() {
                        retries += 1;
                    }
                }
            }
            (reads, retries)
        });
        handles.push(handle);
    }

    let mut total_reads = 0;
    let mut total_retries = 0;
    for h in handles {
        let (r, ret) = h.join().unwrap();
        total_reads += r;
        total_retries += ret;
    }

    let elapsed = start.elapsed();
    let ops_per_sec = (total_ops as f64) / elapsed.as_secs_f64();
    let ns_per_op = (elapsed.as_nanos() as f64) / (total_ops as f64);

    println!("Threads Concurrentes: {}", num_threads);
    println!("Operaciones Totales: {}", total_ops);
    println!("Tiempo Transcurrido: {:.2?}", elapsed);
    println!("Rendimiento (Throughput): {:.2} ops/sec", ops_per_sec);
    println!("Latencia Media por Op: {:.2} ns", ns_per_op);
    println!("Lecturas Exitosas: {}", total_reads - total_retries);
    println!("Re-intentos por Contención: {} ({:.2}%)", total_retries, (total_retries as f64 / total_reads as f64) * 100.0);
}
