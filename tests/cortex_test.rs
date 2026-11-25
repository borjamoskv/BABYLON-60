#![cfg(feature = "cortex-persist")]

use babylon60::cortex::CortexPersister;
use babylon60::manifest::SharedManifest;
use std::sync::atomic::Ordering;
use std::time::Instant;

fn persist_records(persister: &CortexPersister, total: u32) {
    let manifest = SharedManifest::new();
    for i in 1..=total {
        manifest.seq.store(i * 2, Ordering::Release);
        manifest.epoch_id.store(u64::from(i), Ordering::Release);
        manifest.payload_hash[0].store(0xDEADBEEF + u64::from(i), Ordering::Relaxed);
        persister.drain_manifest(&manifest).unwrap();
    }
}

#[test]
fn test_cortex_persist_stress() {
    // Isolated in-memory warmup: no leaked manifest or SQLite WAL files.
    let warmup = CortexPersister::new(":memory:").unwrap();
    persist_records(&warmup, 128);
    assert!(warmup.generate_bitcoin_op_return(100).is_ok());
    drop(warmup);

    let persister = CortexPersister::new(":memory:").unwrap();
    let total_ops = 10_000;
    let start_time = Instant::now();
    persist_records(&persister, total_ops);
    let elapsed = start_time.elapsed();

    println!("Cortex in-memory stress: {total_ops} records in {elapsed:?}");
    // SHA-256 of the final 100 records, latest first, with each u64 little-endian.
    assert_eq!(
        persister.generate_bitcoin_op_return(100).unwrap(),
        "OP_RETURN f1e313a035c0e563aa54920b3dfa1ae9428f6591d08fadabb28199a76a6a7597"
    );
}
