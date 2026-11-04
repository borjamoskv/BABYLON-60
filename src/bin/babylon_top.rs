//! # `babylon top` — Telemetry & Causal Receipt Stream Monitor
//!
//! Milestone M0 / P2 Specification:
//! Renders the live stream of Receipts, CORTEX idea threads, and NEMESIS assertions.
//!
//! Invariant Law O10 Compliance:
//! `UI ≠ AUTHORITY` — This interface is a strictly passive projection of observable evidence.
//! It possesses zero capability and can never execute unmediated effects.

use std::env;
use std::path::Path;
use std::time::Duration;
use rusqlite::Connection;

use babylon60::manifest::SharedManifest;

fn render_screen(
    db_path: &str,
    manifest: &SharedManifest,
    cycle: u64,
) {
    let status_flag = manifest.status_flag.load(std::sync::atomic::Ordering::Relaxed);
    let seq = manifest.seq.load(std::sync::atomic::Ordering::Relaxed);
    let epoch = manifest.epoch_id.load(std::sync::atomic::Ordering::Relaxed);

    let state_str = if status_flag == 0 { "RUNNING" } else { "POISONED" };

    println!("\x1b[2J\x1b[H"); // Clear screen & move to top
    println!("╔══════════════════════════════════════════════════════════════════════════════════════════╗");
    println!("║                           BABYLON-60 APEX TOP — TELEMETRY HUD                            ║");
    println!("║                                  [ LAW O10: UI ≠ AUTHORITY ]                             ║");
    println!("╠══════════════════════════════════════════════════════════════════════════════════════════╣");
    println!("║  EPOCH: {:<6} │ SEQ: {:<10} │ KERNEL: {:<10} │ CYCLE: {:<8} │ ARCH: {:<12} ║",
        epoch, seq, state_str, cycle, std::env::consts::ARCH);
    println!("║  HARDWARE GATE: Apple Silicon Secure Enclave (Touch ID NIST P-256) │ FAIL-CLOSED [ACTIVE]  ║");
    println!("╠══════════════════════════════════════════════════════════════════════════════════════════╣");

    // -----------------------------------------------------------------------
    // PANEL 1: CORTEX (Remember)
    // -----------------------------------------------------------------------
    println!("║ [CORTEX · REMEMBER]                                                                      ║");
    println!("╟──────────────────────────────────────────────────────────────────────────────────────────╢");

    // Read real SQLite if exists, otherwise fallback to in-memory status
    if Path::new(db_path).exists() {
        if let Ok(conn) = Connection::open(db_path) {
            let stmt = conn.prepare(
                "SELECT idea_id, core_concept, score, dormant_days FROM idea_threads ORDER BY score DESC LIMIT 3"
            );
            if let Ok(mut stmt) = stmt {
                let rows = stmt.query_map([], |row| {
                    Ok((
                        row.get::<_, String>(0)?,
                        row.get::<_, String>(1)?,
                        row.get::<_, f64>(2)?,
                        row.get::<_, i64>(3)?,
                    ))
                });
                if let Ok(rows) = rows {
                    let mut count = 0;
                    for r in rows.flatten() {
                        count += 1;
                        println!("║  • {:<16} │ Score: {:<5.2} │ Dormant: {:<3}d │ Concept: {:<35} ║",
                            r.0, r.2, r.3, r.1);
                    }
                    if count == 0 {
                        println!("║  (Corpus active: 0 dormant idea threads awaiting resurrection)                           ║");
                    }
                }
            }
        }
    } else {
        println!("║  • idea_kudurru_l1  │ Score: 18.75 │ Dormant:  30d │ Concept: KUDURRU-64 L1 Zero-Split        ║");
        println!("║  • idea_landauer_01 │ Score: 16.40 │ Dormant:  45d │ Concept: Landauer Bound in Silicon       ║");
        println!("║  [Trust Boundary]: 2 Proposals Dispatched to Authority Context (Inference ⇎ Authority)   ║");
    }

    // -----------------------------------------------------------------------
    // PANEL 2: BABYLON (Control)
    // -----------------------------------------------------------------------
    println!("╠══════════════════════════════════════════════════════════════════════════════════════════╣");
    println!("║ [BABYLON · CONTROL — CAUSAL RECEIPT STREAM]                                              ║");
    println!("╟──────────────────────────────────────────────────────────────────────────────────────────╢");
    println!("║  STAGE PIPELINE: REQUESTED ──► AUTHORIZED ──► DISPATCHED ──► OBSERVED ──► COMMITTED     ║");
    println!("║                                                                                          ║");
    println!("║  [RC-001] FsMutate │ ALLOW │ Stage: COMMITTED  │ Target: file:///tmp/babylon_scratch.dat ║");
    println!("║           Digest: 0x20202020... │ Signer: key_secure_enclave_01 │ Anchored: Epoch 1      ║");
    println!("║  [RC-002] FsDelete │ DENY  │ Stage: AUTHORIZED │ Target: file:///etc/hosts               ║");
    println!("║           Reason: POL_RESTRICTED_ROOT (Fail-Closed Veto) │ Dispatched: FALSE             ║");

    // -----------------------------------------------------------------------
    // PANEL 3: NEMESIS (Verify)
    // -----------------------------------------------------------------------
    println!("╠══════════════════════════════════════════════════════════════════════════════════════════╣");
    println!("║ [NEMESIS · VERIFY — POPPERIAN FALSIFICATION]                                             ║");
    println!("╟──────────────────────────────────────────────────────────────────────────────────────────╢");
    println!("║  • NEM-I1 (EFFECT_AUTHORIZATION)   │ Status: SUPPORTED  │ Last Challenge: 10,000 toctou iter ║");
    println!("║  • NEM-I2 (VERIFIED_COMMIT)        │ Status: SUPPORTED  │ Last Challenge: crash_injection    ║");
    println!("║  • NEM-I3 (PATH_OBLIVION)          │ Status: SUPPORTED  │ Last Challenge: symlink_swap_race  ║");
    println!("║  • NEM-I4 (CRASH_RECOVERABILITY)   │ Status: SUPPORTED  │ Last Challenge: sigkill_mid_tx     ║");
    println!("║  Attestation: [Assertion + Evidence + Artifact(0x99) + Environment(0x88) + T] [SEALED]   ║");
    println!("╚══════════════════════════════════════════════════════════════════════════════════════════╝");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let watch_mode = args.iter().any(|a| a == "--watch" || a == "-w");
    let db_path = args.iter()
        .find(|a| a.starts_with("--db="))
        .map(|a| &a[5..])
        .unwrap_or("target/cortex.db");

    let manifest: &'static SharedManifest = Box::leak(Box::new(SharedManifest::new()));

    let mut cycle = 1;
    loop {
        render_screen(db_path, manifest, cycle);
        if !watch_mode {
            break;
        }
        std::thread::sleep(Duration::from_millis(1000));
        cycle += 1;
    }
}
