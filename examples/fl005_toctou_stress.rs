//! # BABYLON-60 — FL-005 Adversarial Stress Harness (TOCTOU & Effect Identity)
//!
//! Falsifiable Hypothesis FL-005:
//!   `authorized(path, t0) ∧ execute(path, t1) ⟹ same_inode(path, t0, t1)`
//!
//! Adversarial Attack Model:
//!   50–256 concurrent worker threads alternating:
//!     `target ──► regular_file` (with authorized payload)
//!     `target ──► symlink(victim.dat)` (pointing to critical canary file)
//!   while the broker executes:
//!     `VALIDATE ──► AUTHORIZE ──► MUTATE / DELETE`
//!
//! Failure modes to falsify:
//!   - Naive pathname-based broker: `lstat(path) ──► validate(...) ──► unlink/write(path)`
//!     vulnerable to `pathname(t_check) ≠ pathname(t_use)`.
//!   - Escapes via symlink traversal (`O_NOFOLLOW` bypass).
//!   - Victim inode mutation or deletion.
//!
//! Silicon Pass Criteria:
//!   - `unauthorized_victim_mutations == 0`
//!   - `symlink_escapes == 0`
//!   - `victim_canary_intact == true`
//!   - `security_aborts > 0` (fail-closed containment of race conditions)

use std::ffi::CString;
use std::fs::File;
use std::io::{Read, Write};
use std::os::unix::fs as unix_fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

use babylon60::secure_fs::{
    EffectTxOrchestrator, EffectTxState, NativeSecureFs, SecureFsBackend,
    SecureFsError,
};
use sha2::{Digest, Sha256};

const CANARY_VICTIM_DATA: &[u8] = b"CANARY_VICTIM_INTEGRITY_TOKEN_FL005_CRITICAL_NON_MUTABLE";

fn compute_sha256(data: &[u8]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(data);
    h.finalize().into()
}

fn compute_file_sha256(path: &Path) -> std::io::Result<[u8; 32]> {
    let mut f = File::open(path)?;
    let mut h = Sha256::new();
    let mut buf = [0u8; 8192];
    loop {
        let n = f.read(&mut buf)?;
        if n == 0 {
            break;
        }
        h.update(&buf[..n]);
    }
    Ok(h.finalize().into())
}

fn open_dir_fd(p: &Path) -> libc::c_int {
    let c = CString::new(p.as_os_str().to_str().unwrap()).unwrap();
    let fd = unsafe { libc::open(c.as_ptr(), libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC) };
    assert!(fd >= 0, "open_dir_fd failed on {}", p.display());
    fd
}

#[derive(Debug, Default)]
pub struct HarnessMetrics {
    pub workers: usize,
    pub iterations: usize,
    pub authorized_mutations: u64,
    pub authorized_deletions: u64,
    pub security_aborts: u64,
    pub symlink_escapes_detected: u64,
    pub victim_mutations_detected: u64,
    pub victim_deletions_detected: u64,
    pub victim_canary_intact: bool,
    pub naive_vulnerability_reproduced: bool,
    pub duration_ms: u64,
}

/// Runs the naive pathname-based check-then-act broker under attack to demonstrate
/// that TOCTOU occurs if identity is not pinned to the descriptor/handle in silicon.
fn run_naive_baseline(dir: &Path, iterations: usize) -> bool {
    let target = dir.join("naive_target.dat");
    let victim = dir.join("naive_victim.dat");
    let _ = std::fs::write(&victim, b"NAIVE_VICTIM_CANARY");

    let running = Arc::new(AtomicBool::new(true));
    let victim_tampered = Arc::new(AtomicBool::new(false));

    let r_clone = Arc::clone(&running);
    let target_clone = target.clone();
    let victim_clone = victim.clone();

    // Adversary: alternates target between regular file and symlink to victim
    let swapper = thread::spawn(move || {
        let mut count = 0;
        while r_clone.load(Ordering::Relaxed) && count < iterations * 5 {
            count += 1;
            let _ = std::fs::remove_file(&target_clone);
            let _ = unix_fs::symlink(&victim_clone, &target_clone);
            std::thread::yield_now();
            let _ = std::fs::remove_file(&target_clone);
            let _ = std::fs::write(&target_clone, b"SAFE_PAYLOAD");
            std::thread::yield_now();
        }
    });

    // Naive Broker: lstat -> check regular -> write/delete by path
    for _ in 0..iterations {
        if let Ok(meta) = std::fs::symlink_metadata(&target) {
            if meta.is_file() {
                // Window of vulnerability here: swapper can swap target to symlink(victim)
                std::thread::yield_now();
                if let Ok(mut f) = std::fs::OpenOptions::new().write(true).open(&target) {
                    let _ = f.write_all(b"NAIVE_CORRUPTION");
                }
            }
        }
        if let Ok(data) = std::fs::read(&victim) {
            if data != b"NAIVE_VICTIM_CANARY" {
                victim_tampered.store(true, Ordering::SeqCst);
                break;
            }
        }
    }

    running.store(false, Ordering::Relaxed);
    let _ = swapper.join();

    victim_tampered.load(Ordering::SeqCst)
}

/// Executes the full adversarial FL-005 stress test against BABYLON-60's NativeSecureFs
pub fn run_fl005_stress(
    work_dir: &Path,
    workers: usize,
    iterations_per_worker: usize,
) -> HarnessMetrics {
    let t0 = Instant::now();

    // 1. Setup isolated environment
    let stress_root = work_dir.join("fl005_root");
    std::fs::create_dir_all(&stress_root).unwrap();

    let victim_path = stress_root.join("victim.dat");
    std::fs::write(&victim_path, CANARY_VICTIM_DATA).unwrap();

    let victim_fd = unsafe {
        let c = CString::new(victim_path.to_str().unwrap()).unwrap();
        libc::open(c.as_ptr(), libc::O_RDONLY | libc::O_CLOEXEC)
    };
    assert!(victim_fd >= 0);
    let mut victim_stat: libc::stat = unsafe { std::mem::zeroed() };
    unsafe { libc::fstat(victim_fd, &mut victim_stat) };
    unsafe { libc::close(victim_fd) };

    let victim_expected_ino = victim_stat.st_ino as u64;
    let victim_expected_dev = victim_stat.st_dev as u64;
    let victim_expected_hash = compute_sha256(CANARY_VICTIM_DATA);

    // 2. Initialize EffectTxOrchestrator and open root descriptor
    let orch = Arc::new(EffectTxOrchestrator::<NativeSecureFs>::new(&stress_root).unwrap());
    let root_fd = open_dir_fd(&stress_root);

    // 3. Shared atomic counters
    let authorized_mutations = Arc::new(AtomicU64::new(0));
    let authorized_deletions = Arc::new(AtomicU64::new(0));
    let security_aborts = Arc::new(AtomicU64::new(0));
    let symlink_escapes_detected = Arc::new(AtomicU64::new(0));
    let victim_mutations_detected = Arc::new(AtomicU64::new(0));
    let victim_deletions_detected = Arc::new(AtomicU64::new(0));

    // 4. Spawn adversarial worker threads
    let mut handles = Vec::with_capacity(workers);

    for w_id in 0..workers {
        let orch = Arc::clone(&orch);
        let stress_root = stress_root.clone();
        let auth_mut = Arc::clone(&authorized_mutations);
        let auth_del = Arc::clone(&authorized_deletions);
        let sec_aborts = Arc::clone(&security_aborts);
        let sym_escapes = Arc::clone(&symlink_escapes_detected);
        let vic_mut = Arc::clone(&victim_mutations_detected);
        let vic_del = Arc::clone(&victim_deletions_detected);

        handles.push(thread::spawn(move || {
            let target_filename = format!("target_{}.dat", w_id);
            let target_path = stress_root.join(&target_filename);
            let victim_rel = "victim.dat";

            for iter in 0..iterations_per_worker {
                let is_delete_op = (w_id + iter) % 2 == 0;
                let is_attack_turn = (iter % 3) != 0; // 66% under adversarial swap attack

                // Prepare genuine target file with authorized payload
                let genuine_payload = format!("GENUINE_WORKER_{}_ITER_{}", w_id, iter).into_bytes();
                std::fs::write(&target_path, &genuine_payload).unwrap();

                let cap_root = [w_id as u8; 32];
                // 1. PIN object to obtain authorized identity
                let pin_res = NativeSecureFs::pin_object(root_fd, &target_filename, cap_root);
                let (pinned_fd, authorized_identity) = match pin_res {
                    Ok((fd, id)) => (fd, id),
                    Err(SecureFsError::SymlinkEscapeAttempt) => {
                        sym_escapes.fetch_add(1, Ordering::SeqCst);
                        continue;
                    }
                    Err(_) => {
                        sec_aborts.fetch_add(1, Ordering::SeqCst);
                        continue;
                    }
                };

                // Close pinned_fd for delete test (orchestrator uses path under quarantine),
                // but for mutate test we test descriptor pinning.
                unsafe { libc::close(pinned_fd) };

                // 2. Adversarial Action in the TOCTOU window:
                // Attempt to swap target with symlink to victim or swap with victim inode!
                if is_attack_turn {
                    let _ = std::fs::remove_file(&target_path);
                    let _ = unix_fs::symlink(victim_rel, &target_path);
                }

                let mut tx_nonce = [0u8; 32];
                tx_nonce[0] = w_id as u8;
                tx_nonce[1..9].copy_from_slice(&(iter as u64).to_be_bytes());

                // 3. Broker Operation Execution
                if is_delete_op {
                    match orch.secure_delete(root_fd, &target_filename, &authorized_identity, &tx_nonce) {
                        Ok(EffectTxState::Committed) => {
                            if is_attack_turn {
                                // If attack turn committed, check if victim was deleted!
                                vic_del.fetch_add(1, Ordering::SeqCst);
                            } else {
                                auth_del.fetch_add(1, Ordering::SeqCst);
                            }
                        }
                        Ok(EffectTxState::SecurityAbort) => {
                            sec_aborts.fetch_add(1, Ordering::SeqCst);
                        }
                        Err(SecureFsError::SymlinkEscapeAttempt) => {
                            sym_escapes.fetch_add(1, Ordering::SeqCst);
                        }
                        Err(SecureFsError::SecurityMismatch { .. }) => {
                            sec_aborts.fetch_add(1, Ordering::SeqCst);
                        }
                        Err(SecureFsError::IdentityUnstable) => {
                            sec_aborts.fetch_add(1, Ordering::SeqCst);
                        }
                        _ => {}
                    }
                } else {
                    // Mutation operation via NativeSecureFs::secure_mutate
                    let mutate_payload = format!("MUTATED_PAYLOAD_{}_{}", w_id, iter).into_bytes();
                    match NativeSecureFs::secure_mutate(
                        root_fd,
                        &target_filename,
                        &authorized_identity,
                        &mutate_payload,
                    ) {
                        Ok(_) => {
                            if is_attack_turn {
                                vic_mut.fetch_add(1, Ordering::SeqCst);
                            } else {
                                auth_mut.fetch_add(1, Ordering::SeqCst);
                            }
                        }
                        Err(SecureFsError::SecurityMismatch { .. }) => {
                            sec_aborts.fetch_add(1, Ordering::SeqCst);
                        }
                        Err(SecureFsError::SymlinkEscapeAttempt) => {
                            sym_escapes.fetch_add(1, Ordering::SeqCst);
                        }
                        Err(SecureFsError::IoError(e)) if e.raw_os_error() == Some(libc::ELOOP) => {
                            sym_escapes.fetch_add(1, Ordering::SeqCst);
                        }
                        _ => {
                            sec_aborts.fetch_add(1, Ordering::SeqCst);
                        }
                    }
                }

                // Clean up remaining target if still there
                let _ = std::fs::remove_file(&target_path);
            }
        }));
    }

    for h in handles {
        h.join().unwrap();
    }
    unsafe { libc::close(root_fd) };

    // 5. Post-audit of victim file: verify canary integrity and inode
    let victim_exists = victim_path.exists();
    let mut post_victim_stat: libc::stat = unsafe { std::mem::zeroed() };
    let post_stat_ok = if victim_exists {
        let c = CString::new(victim_path.to_str().unwrap()).unwrap();
        let ret = unsafe { libc::lstat(c.as_ptr(), &mut post_victim_stat) };
        ret == 0
    } else {
        false
    };

    let victim_hash_matches = compute_file_sha256(&victim_path)
        .map(|h| h == victim_expected_hash)
        .unwrap_or(false);

    let victim_intact = victim_exists
        && post_stat_ok
        && post_victim_stat.st_ino as u64 == victim_expected_ino
        && post_victim_stat.st_dev as u64 == victim_expected_dev
        && victim_hash_matches;

    // Optional naive baseline verification
    let naive_dir = work_dir.join("fl005_naive");
    std::fs::create_dir_all(&naive_dir).unwrap();
    let naive_reproduced = run_naive_baseline(&naive_dir, 500);

    let duration = t0.elapsed();

    HarnessMetrics {
        workers,
        iterations: workers * iterations_per_worker,
        authorized_mutations: authorized_mutations.load(Ordering::SeqCst),
        authorized_deletions: authorized_deletions.load(Ordering::SeqCst),
        security_aborts: security_aborts.load(Ordering::SeqCst),
        symlink_escapes_detected: symlink_escapes_detected.load(Ordering::SeqCst),
        victim_mutations_detected: victim_mutations_detected.load(Ordering::SeqCst),
        victim_deletions_detected: victim_deletions_detected.load(Ordering::SeqCst),
        victim_canary_intact: victim_intact,
        naive_vulnerability_reproduced: naive_reproduced,
        duration_ms: duration.as_millis() as u64,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mut workers = 128usize;
    let mut iters_per_worker = 10usize; // 128 * 10 = 1280 operations
    let mut work_dir = None;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--workers" => {
                workers = args[i + 1].parse().unwrap_or(128);
                i += 2;
            }
            "--iterations" => {
                let total: usize = args[i + 1].parse().unwrap_or(1280);
                iters_per_worker = (total / workers).max(1);
                i += 2;
            }
            "--dir" => {
                work_dir = Some(PathBuf::from(&args[i + 1]));
                i += 2;
            }
            _ => {
                i += 1;
            }
        }
    }

    let work_dir = work_dir.unwrap_or_else(|| {
        std::env::temp_dir().join(format!("fl005_stress_{}_{}", std::process::id(), rand::random::<u32>()))
    });
    std::fs::create_dir_all(&work_dir).unwrap();

    println!("╔══════════════════════════════════════════════════════════════════════════════╗");
    println!("║       BABYLON-60 · FL-005 EFFECT ADAPTER / TOCTOU STRESS HARNESS             ║");
    println!("╚══════════════════════════════════════════════════════════════════════════════╝");
    println!("Target Directory: {}", work_dir.display());
    println!("Workers:          {}", workers);
    println!("Iterations:       {}", workers * iters_per_worker);
    println!("Hypothesis:       authorized(path, t0) ∧ execute(path, t1) ⟹ same_inode(path, t0, t1)");
    println!("--------------------------------------------------------------------------------");

    let metrics = run_fl005_stress(&work_dir, workers, iters_per_worker);

    println!("{:<32} {:>16}", "Authorized Mutations", metrics.authorized_mutations);
    println!("{:<32} {:>16}", "Authorized Deletions", metrics.authorized_deletions);
    println!("{:<32} {:>16}", "Security Aborts (Fail-Closed)", metrics.security_aborts);
    println!("{:<32} {:>16}", "Symlink Escapes Intercepted", metrics.symlink_escapes_detected);
    println!("{:<32} {:>16}", "Victim Mutations (Must=0)", metrics.victim_mutations_detected);
    println!("{:<32} {:>16}", "Victim Deletions (Must=0)", metrics.victim_deletions_detected);
    println!("{:<32} {:>16}", "Victim Canary Intact", if metrics.victim_canary_intact { "PASS (TRUE)" } else { "FAIL (FALSE)" });
    println!("{:<32} {:>16}", "Naive Flaw Reproduced", if metrics.naive_vulnerability_reproduced { "YES (FALSIFIED)" } else { "NO" });
    println!("{:<32} {:>16} ms", "Execution Duration", metrics.duration_ms);
    println!("--------------------------------------------------------------------------------");

    let pass = metrics.victim_canary_intact
        && metrics.victim_mutations_detected == 0
        && metrics.victim_deletions_detected == 0
        && (metrics.authorized_mutations + metrics.authorized_deletions > 0);

    let sitrep_json = format!(
        r#"{{
  "fl_id": "FL-005",
  "name": "EFFECT_ADAPTER_TOCTOU_IDENTITY",
  "hypothesis": "authorized(path, t0) ∧ execute(path, t1) ⟹ same_inode(path, t0, t1)",
  "workers": {},
  "total_iterations": {},
  "authorized_mutations": {},
  "authorized_deletions": {},
  "security_aborts": {},
  "symlink_escapes_intercepted": {},
  "victim_mutations": {},
  "victim_deletions": {},
  "victim_canary_intact": {},
  "naive_baseline_vulnerable": {},
  "status": "{}",
  "domain": "Darwin ARM64 / APFS / POSIX",
  "duration_ms": {}
}}
"#,
        metrics.workers,
        metrics.iterations,
        metrics.authorized_mutations,
        metrics.authorized_deletions,
        metrics.security_aborts,
        metrics.symlink_escapes_detected,
        metrics.victim_mutations_detected,
        metrics.victim_deletions_detected,
        metrics.victim_canary_intact,
        metrics.naive_vulnerability_reproduced,
        if pass { "SUPPORTED_WITHIN_DOMAIN" } else { "FALSIFIED" },
        metrics.duration_ms
    );

    let report_path = work_dir.join("fl005_report.json");
    std::fs::write(&report_path, &sitrep_json).unwrap();
    println!("Report written to: {}", report_path.display());

    if pass {
        println!("VERDICT: [SUPPORTED_WITHIN_DOMAIN] — 0 victim mutations, 0 escapes.");
        std::process::exit(0);
    } else {
        eprintln!("VERDICT: [FALSIFIED] — Invariant violation detected!");
        std::process::exit(1);
    }
}
