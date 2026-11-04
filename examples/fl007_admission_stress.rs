use std::time::{Duration, Instant};
use std::sync::Arc;
use std::thread;

use babylon60::admission::AdmissionController;

/// FL-007 ADMISSION STRESS HARNESS
///
/// Goal: Prove that ACCEPTED != RECEIVED and that bounded liveness contract holds.
/// We set a capacity limit based on latency budgets and saturate it with concurrent workers.
fn main() {
    println!("╔══════════════════════════════════════════════════════════════════════════════╗");
    println!("║          BABYLON-60 · FL-007 · ADMISSION CONTROLLER STRESS HARNESS           ║");
    println!("╚══════════════════════════════════════════════════════════════════════════════╝");

    let num_workers = 50;
    let requests_per_worker = 1000;
    
    // We expect service time to be 10ms per item.
    // We strictly limit max latency to 100ms.
    // By Little's Law, maximum queue depth should be 10 (100ms / 10ms).
    let max_depth = 10;
    let expected_service_time = Duration::from_millis(10);
    let latency_budget = Duration::from_millis(100);

    let admission = Arc::new(AdmissionController::new(max_depth, latency_budget, expected_service_time));
    
    let mut handles = vec![];
    let start = Instant::now();

    for _w_idx in 0..num_workers {
        let adm = Arc::clone(&admission);
        handles.push(thread::spawn(move || {
            let mut accepted = 0;
            let mut rejected = 0;
            let mut violations = 0;

            for _ in 0..requests_per_worker {
                match adm.try_admit() {
                    Ok(_) => {
                        accepted += 1;
                        // Simulating actual bounded work
                        thread::sleep(Duration::from_millis(1)); // Processing time
                        adm.release();
                    }
                    Err(attempted_depth) => {
                        rejected += 1;
                        if attempted_depth <= max_depth {
                            // If we rejected but we were under max depth, that's a violation
                            // of work conservation unless latency budget caused it.
                            // But here expected_service_time * depth should be exact.
                            violations += 1;
                        }
                    }
                }
            }
            (accepted, rejected, violations)
        }));
    }

    let mut total_accepted = 0;
    let mut total_rejected = 0;
    let mut total_violations = 0;

    for h in handles {
        let (acc, rej, viol) = h.join().unwrap();
        total_accepted += acc;
        total_rejected += rej;
        total_violations += viol;
    }

    let duration = start.elapsed();
    let throughput = total_accepted as f64 / duration.as_secs_f64();

    println!("Total Requests:  {}", num_workers * requests_per_worker);
    println!("Accepted:        {}", total_accepted);
    println!("Rejected:        {}", total_rejected);
    println!("Contract Viol.:  {}", total_violations);
    println!("Throughput:      {:.2} req/sec", throughput);

    // FL-007 Law Verification
    // 1. Rejected must be > 0 (Proof that ACCEPTED != RECEIVED under saturation)
    // 2. Violations must be 0 (Bounded Liveness holding)
    assert!(total_rejected > 0, "FL-007 FALSIFIED: System accepted infinite capacity without backpressure!");
    assert_eq!(total_violations, 0, "FL-007 FALSIFIED: Capacity contract explicitly violated!");

    println!("Verdict: SUPPORTED_WITHIN_DOMAIN. Backpressure contract verified.");
}
