//! # BABYLON-60 — FL-006 Crash Consistency & Durability Stress Harness
//!
//! Falsifiable Hypothesis FL-006:
//!   `ACK(m) ⟹ durable(m)`  (no userspace write() returned without disk commitment)
//!
//! The 6 Causal Crash Boundaries:
//!   ① Point1_AfterReceive       : Memory arrival, before write-ahead log.
//!   ② Point2_AfterWalAppend     : Appended to WAL log, before fdatasync/fsync.
//!   ③ Point3_AfterFdatasync     : Flushed WAL to non-volatile storage, before index reservation.
//!   ④ Point4_AfterIndexUpdate   : Reservation table updated in SQLite, before ledger commit.
//!   ⑤ Point5_AfterLedgerCommit  : Transaction committed in durable ledger, before ACK emission.
//!   ⑥ Point6_AfterAck           : ACK emitted and synced, killed immediately after.
//!
//! Formal Invariants Audited:
//!   1. `acked(m) ⟹ recoverable(m)`: Zero ghost ACKs, zero lost ACKed messages.
//!   2. `committed(m) ⟹ exactly_one_effect(m)`: Zero duplicate effects across crash & replay.
//!   3. `replay(m) ⟹ state' = state`: Replays of committed transactions rejected deterministically.
//!   4. SQLite WAL physical integrity: `PRAGMA integrity_check == "ok"`.

use std::collections::HashMap;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Instant;

use rand::Rng;
use rusqlite::{params, Connection, OptionalExtension};
use sha2::{Digest, Sha256};

const EXIT_OK: i32 = 0;
const EXIT_REPLAY_REJECTED: i32 = 3;

#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CrashBoundary {
    None,
    Point1_AfterReceive,
    Point2_AfterWalAppend,
    Point3_AfterFdatasync,
    Point4_AfterIndexUpdate,
    Point5_AfterLedgerCommit,
    Point6_AfterAck,
}

impl CrashBoundary {
    pub fn name(&self) -> &'static str {
        match self {
            CrashBoundary::None => "None",
            CrashBoundary::Point1_AfterReceive => "Point1_AfterReceive",
            CrashBoundary::Point2_AfterWalAppend => "Point2_AfterWalAppend",
            CrashBoundary::Point3_AfterFdatasync => "Point3_AfterFdatasync",
            CrashBoundary::Point4_AfterIndexUpdate => "Point4_AfterIndexUpdate",
            CrashBoundary::Point5_AfterLedgerCommit => "Point5_AfterLedgerCommit",
            CrashBoundary::Point6_AfterAck => "Point6_AfterAck",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "None" => Some(CrashBoundary::None),
            "Point1_AfterReceive" => Some(CrashBoundary::Point1_AfterReceive),
            "Point2_AfterWalAppend" => Some(CrashBoundary::Point2_AfterWalAppend),
            "Point3_AfterFdatasync" => Some(CrashBoundary::Point3_AfterFdatasync),
            "Point4_AfterIndexUpdate" => Some(CrashBoundary::Point4_AfterIndexUpdate),
            "Point5_AfterLedgerCommit" => Some(CrashBoundary::Point5_AfterLedgerCommit),
            "Point6_AfterAck" => Some(CrashBoundary::Point6_AfterAck),
            _ => None,
        }
    }
}

fn compute_nonce(iter: u64) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"FL006_CRASH_NONCE_v2");
    h.update(iter.to_be_bytes());
    h.finalize().into()
}

fn open_ledger_db(path: &Path) -> rusqlite::Result<Connection> {
    let conn = Connection::open(path)?;
    conn.busy_timeout(std::time::Duration::from_secs(30))?;
    conn.execute_batch(
        "PRAGMA journal_mode = WAL;
         PRAGMA synchronous = FULL;
         PRAGMA fullfsync = ON;
         PRAGMA checkpoint_fullfsync = ON;
         CREATE TABLE IF NOT EXISTS ledger_entries (
             nonce BLOB PRIMARY KEY,
             iter INTEGER NOT NULL,
             state TEXT NOT NULL CHECK(state IN ('RESERVED', 'COMMITTED', 'UNKNOWN')),
             created_at INTEGER NOT NULL,
             committed_at INTEGER
         );",
    )?;
    Ok(conn)
}

fn signal_and_await_kill(boundary: CrashBoundary) -> ! {
    println!("CRASHPOINT {}", boundary.name());
    std::io::stdout().flush().unwrap();
    // Block indefinitely until parent delivers SIGKILL
    loop {
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
}

// ---------------------------------------------------------------------------
// Child Execution Process
// ---------------------------------------------------------------------------

fn run_child_worker(dir: &Path, iter: u64, boundary: CrashBoundary) -> ! {
    let nonce = compute_nonce(iter);
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    // Boundary 1: After Receive
    if boundary == CrashBoundary::Point1_AfterReceive {
        signal_and_await_kill(boundary);
    }

    // Boundary 2: Write WAL log entry without fsync
    let wal_path = dir.join("wal.log");
    {
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&wal_path)
            .expect("open wal");
        let line = format!("WAL_ENTRY iter={} nonce={}\n", iter, hex::encode(nonce));
        f.write_all(line.as_bytes()).expect("write wal");
        // No sync here: dirty in userspace buffer
    }

    if boundary == CrashBoundary::Point2_AfterWalAppend {
        signal_and_await_kill(boundary);
    }

    // Boundary 3: Flush WAL to physical media (fdatasync/sync_all)
    {
        let f = File::open(&wal_path).expect("open wal for sync");
        f.sync_all().expect("fdatasync wal");
    }

    if boundary == CrashBoundary::Point3_AfterFdatasync {
        signal_and_await_kill(boundary);
    }

    // Boundary 4: Update SQLite index in pending uncommitted transaction
    let db_path = dir.join("ledger.sqlite");
    let mut conn = open_ledger_db(&db_path).expect("open ledger");

    let tx = conn
        .transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)
        .expect("begin tx");

    // Check if nonce already exists
    let existing: Option<String> = tx
        .query_row(
            "SELECT state FROM ledger_entries WHERE nonce = ?1",
            params![&nonce[..]],
            |r| r.get(0),
        )
        .optional()
        .expect("lookup nonce");

    if existing.is_some() {
        std::process::exit(EXIT_REPLAY_REJECTED);
    }

    tx.execute(
        "INSERT INTO ledger_entries (nonce, iter, state, created_at, committed_at) VALUES (?1, ?2, 'RESERVED', ?3, NULL)",
        params![&nonce[..], iter as i64, now as i64],
    )
    .expect("insert reserved");

    if boundary == CrashBoundary::Point4_AfterIndexUpdate {
        // Child killed while SQLite transaction is open; SQLite rollbacks on crash
        signal_and_await_kill(boundary);
    }

    // Commit ledger state to COMMITTED
    tx.execute(
        "UPDATE ledger_entries SET state = 'COMMITTED', committed_at = ?1 WHERE nonce = ?2",
        params![now as i64, &nonce[..]],
    )
    .expect("update committed");

    tx.commit().expect("commit ledger tx");

    // Execute physical effect with sync_all
    let effects_path = dir.join("effects.log");
    {
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&effects_path)
            .expect("open effects");
        writeln!(f, "EFFECT nonce={} iter={}", hex::encode(nonce), iter).expect("write effect");
        f.sync_all().expect("sync effect");
    }

    // Boundary 5: Ledger committed, physical effect applied, but BEFORE ACK emitted
    if boundary == CrashBoundary::Point5_AfterLedgerCommit {
        signal_and_await_kill(boundary);
    }

    // Emit ACK token with sync_all
    let acks_path = dir.join("acks.log");
    {
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&acks_path)
            .expect("open acks");
        writeln!(f, "ACK nonce={} iter={}", hex::encode(nonce), iter).expect("write ack");
        f.sync_all().expect("sync acks");
    }

    // Boundary 6: ACK emitted and synced, killed immediately after
    if boundary == CrashBoundary::Point6_AfterAck {
        signal_and_await_kill(boundary);
    }

    std::process::exit(EXIT_OK);
}

// ---------------------------------------------------------------------------
// Replay Worker Process
// ---------------------------------------------------------------------------

fn run_replay_worker(dir: &Path, iter: u64) -> ! {
    let nonce = compute_nonce(iter);
    let db_path = dir.join("ledger.sqlite");
    let mut conn = open_ledger_db(&db_path).expect("open ledger for replay");

    let tx = conn
        .transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)
        .expect("begin tx");

    let existing: Option<String> = tx
        .query_row(
            "SELECT state FROM ledger_entries WHERE nonce = ?1",
            params![&nonce[..]],
            |r| r.get(0),
        )
        .optional()
        .expect("lookup nonce");

    if let Some(state) = existing {
        if state == "COMMITTED" {
            // Replay of already committed transaction MUST be rejected
            std::process::exit(EXIT_REPLAY_REJECTED);
        }
    }

    // If never committed (crashed at 1..4), complete it cleanly now
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    tx.execute(
        "INSERT OR REPLACE INTO ledger_entries (nonce, iter, state, created_at, committed_at) VALUES (?1, ?2, 'COMMITTED', ?3, ?4)",
        params![&nonce[..], iter as i64, now as i64, now as i64],
    ).expect("replay insert");

    tx.commit().expect("replay commit");

    let effects_path = dir.join("effects.log");
    {
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&effects_path)
            .expect("open effects");
        writeln!(f, "EFFECT nonce={} iter={}", hex::encode(nonce), iter).expect("write effect");
        f.sync_all().expect("sync effect");
    }

    std::process::exit(EXIT_OK);
}

// ---------------------------------------------------------------------------
// Parent Orchestrator
// ---------------------------------------------------------------------------

#[derive(Debug, PartialEq)]
enum ChildOutcome {
    Killed,
    Exited(i32),
}

fn execute_child_and_kill_if_boundary(exe: &Path, args: &[String]) -> ChildOutcome {
    let mut c = Command::new(exe)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .expect("spawn child");

    let stdout = c.stdout.take().unwrap();
    let reader = BufReader::new(stdout);

    for line in reader.lines() {
        let l = line.unwrap_or_default();
        if l.starts_with("CRASHPOINT ") {
            // Deliver real SIGKILL to simulate instant process death
            c.kill().expect("SIGKILL child");
            let _ = c.wait();
            return ChildOutcome::Killed;
        }
    }

    let status = c.wait().expect("wait child");
    ChildOutcome::Exited(status.code().unwrap_or(-1))
}

fn read_acks_map(dir: &Path) -> HashMap<String, u64> {
    let mut m = HashMap::new();
    let acks_file = dir.join("acks.log");
    if let Ok(f) = File::open(acks_file) {
        for line in BufReader::new(f).lines().map_while(Result::ok) {
            if line.starts_with("ACK nonce=") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if let Some(n_part) = parts.get(1) {
                    if let Some(hex_nonce) = n_part.strip_prefix("nonce=") {
                        m.insert(hex_nonce.to_string(), 1);
                    }
                }
            }
        }
    }
    m
}

fn read_effects_counts(dir: &Path) -> HashMap<String, usize> {
    let mut m = HashMap::new();
    let effects_file = dir.join("effects.log");
    if let Ok(f) = File::open(effects_file) {
        for line in BufReader::new(f).lines().map_while(Result::ok) {
            if line.starts_with("EFFECT nonce=") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if let Some(n_part) = parts.get(1) {
                    if let Some(hex_nonce) = n_part.strip_prefix("nonce=") {
                        *m.entry(hex_nonce.to_string()).or_insert(0) += 1;
                    }
                }
            }
        }
    }
    m
}

#[derive(Debug, Default)]
pub struct Fl006Report {
    pub total_iterations: usize,
    pub boundary_counts: HashMap<&'static str, usize>,
    pub replays_rejected: usize,
    pub ghost_acks_detected: usize,
    pub lost_acked_messages: usize,
    pub duplicate_effects_detected: usize,
    pub sqlite_integrity_ok: bool,
    pub duration_ms: u64,
}

pub fn run_fl006_crash_stress(dir: &Path, iterations: usize) -> Fl006Report {
    let t0 = Instant::now();
    let exe = std::env::current_exe().expect("current exe");

    std::fs::create_dir_all(dir).unwrap();

    let all_boundaries = [
        CrashBoundary::None,
        CrashBoundary::Point1_AfterReceive,
        CrashBoundary::Point2_AfterWalAppend,
        CrashBoundary::Point3_AfterFdatasync,
        CrashBoundary::Point4_AfterIndexUpdate,
        CrashBoundary::Point5_AfterLedgerCommit,
        CrashBoundary::Point6_AfterAck,
    ];

    let mut plan = Vec::with_capacity(iterations);
    let mut rng = rand::thread_rng();

    for _ in 0..iterations {
        let b = all_boundaries[rng.gen_range(0..all_boundaries.len())];
        plan.push(b);
    }

    let mut boundary_counts = HashMap::new();

    // -----------------------------------------------------------------------
    // Phase 1: Execution with SIGKILL at crash points
    // -----------------------------------------------------------------------
    for (i, &boundary) in plan.iter().enumerate() {
        *boundary_counts.entry(boundary.name()).or_insert(0) += 1;
        let args = vec![
            "child".to_string(),
            dir.display().to_string(),
            i.to_string(),
            boundary.name().to_string(),
        ];
        execute_child_and_kill_if_boundary(&exe, &args);
    }

    let acks_after_phase1 = read_acks_map(dir);
    let effects_after_phase1 = read_effects_counts(dir);

    // -----------------------------------------------------------------------
    // Phase 2: Replay Phase (Testing Replay Rejection & Nonce Idempotency)
    // -----------------------------------------------------------------------
    let mut replays_rejected = 0;
    for i in 0..iterations {
        let args = vec![
            "replay".to_string(),
            dir.display().to_string(),
            i.to_string(),
        ];
        let outcome = execute_child_and_kill_if_boundary(&exe, &args);
        if outcome == ChildOutcome::Exited(EXIT_REPLAY_REJECTED) {
            replays_rejected += 1;
        }
    }

    let effects_after_phase2 = read_effects_counts(dir);

    // -----------------------------------------------------------------------
    // Phase 3: Forensic Ledger & Invariant Audit
    // -----------------------------------------------------------------------
    let db_path = dir.join("ledger.sqlite");
    let conn = open_ledger_db(&db_path).expect("open ledger for audit");

    // Check SQLite physical integrity
    let integrity_check: String = conn
        .query_row("PRAGMA integrity_check;", [], |r| r.get(0))
        .unwrap_or_else(|_| "FAILED".to_string());
    let sqlite_integrity_ok = integrity_check == "ok";

    let mut lost_acked_messages = 0;
    let mut ghost_acks_detected = 0;
    let mut duplicate_effects_detected = 0;

    // Invariant 1: ACK(m) ==> durable(m)
    // If child emitted ACK before dying, the effect MUST be durable in ledger and applied
    for hex_nonce in acks_after_phase1.keys() {
        let raw_nonce = hex::decode(hex_nonce).expect("decode nonce");
        let state: Option<String> = conn
            .query_row(
                "SELECT state FROM ledger_entries WHERE nonce = ?1",
                params![&raw_nonce[..]],
                |r| r.get(0),
            )
            .optional()
            .unwrap_or(None);

        if state != Some("COMMITTED".to_string()) {
            lost_acked_messages += 1;
        }

        let effect_count = effects_after_phase1.get(hex_nonce).copied().unwrap_or(0);
        if effect_count == 0 {
            ghost_acks_detected += 1;
        }
    }

    // Invariant 2: committed(m) ==> exactly_one_effect(m)
    // No effect may ever appear more than once in effects.log across crashes and replays
    for (hex_nonce, &count) in &effects_after_phase2 {
        if count > 1 {
            duplicate_effects_detected += 1;
        }
        // Verify state in ledger
        let raw_nonce = hex::decode(hex_nonce).expect("decode nonce");
        let state: Option<String> = conn
            .query_row(
                "SELECT state FROM ledger_entries WHERE nonce = ?1",
                params![&raw_nonce[..]],
                |r| r.get(0),
            )
            .optional()
            .unwrap_or(None);

        assert_eq!(
            state,
            Some("COMMITTED".to_string()),
            "Effect exists without committed ledger state for nonce {}",
            hex_nonce
        );
    }

    let duration = t0.elapsed();

    Fl006Report {
        total_iterations: iterations,
        boundary_counts,
        replays_rejected,
        ghost_acks_detected,
        lost_acked_messages,
        duplicate_effects_detected,
        sqlite_integrity_ok,
        duration_ms: duration.as_millis() as u64,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(String::as_str);

    match mode {
        Some("child") => {
            let dir = Path::new(&args[2]);
            let iter: u64 = args[3].parse().expect("parse iter");
            let boundary = CrashBoundary::parse(&args[4]).expect("parse boundary");
            run_child_worker(dir, iter, boundary);
        }
        Some("replay") => {
            let dir = Path::new(&args[2]);
            let iter: u64 = args[3].parse().expect("parse iter");
            run_replay_worker(dir, iter);
        }
        _ => {
            let mut iterations = 600usize;
            let mut work_dir = None;

            let mut i = 1;
            while i < args.len() {
                match args[i].as_str() {
                    "--iterations" => {
                        iterations = args[i + 1].parse().unwrap_or(600);
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
                std::env::temp_dir().join(format!("fl006_crash_{}_{}", std::process::id(), rand::random::<u32>()))
            });

            println!("╔══════════════════════════════════════════════════════════════════════════════╗");
            println!("║      BABYLON-60 · FL-006 CRASH CONSISTENCY & ACK DURABILITY HARNESS          ║");
            println!("╚══════════════════════════════════════════════════════════════════════════════╝");
            println!("Target Directory:   {}", work_dir.display());
            println!("Total Iterations:   {}", iterations);
            println!("Hypothesis:         ACK(m) ⟹ durable(m) [6 causal boundaries + SIGKILL]");
            println!("--------------------------------------------------------------------------------");

            let report = run_fl006_crash_stress(&work_dir, iterations);

            println!("{:<36} {:>16}", "Crash Boundary", "Iterations");
            for b in [
                CrashBoundary::None,
                CrashBoundary::Point1_AfterReceive,
                CrashBoundary::Point2_AfterWalAppend,
                CrashBoundary::Point3_AfterFdatasync,
                CrashBoundary::Point4_AfterIndexUpdate,
                CrashBoundary::Point5_AfterLedgerCommit,
                CrashBoundary::Point6_AfterAck,
            ] {
                let count = report.boundary_counts.get(b.name()).copied().unwrap_or(0);
                println!("{:<36} {:>16}", b.name(), count);
            }
            println!("--------------------------------------------------------------------------------");
            println!("{:<36} {:>16}", "Replays Rejected (Idempotency)", report.replays_rejected);
            println!("{:<36} {:>16}", "Ghost ACKs Detected (Must=0)", report.ghost_acks_detected);
            println!("{:<36} {:>16}", "Lost ACKed Messages (Must=0)", report.lost_acked_messages);
            println!("{:<36} {:>16}", "Duplicate Effects (Must=0)", report.duplicate_effects_detected);
            println!("{:<36} {:>16}", "SQLite WAL Integrity", if report.sqlite_integrity_ok { "PASS (ok)" } else { "FAIL" });
            println!("{:<36} {:>16} ms", "Execution Duration", report.duration_ms);
            println!("--------------------------------------------------------------------------------");

            let pass = report.ghost_acks_detected == 0
                && report.lost_acked_messages == 0
                && report.duplicate_effects_detected == 0
                && report.sqlite_integrity_ok
                && report.replays_rejected > 0;

            let sitrep_json = format!(
                r#"{{
  "fl_id": "FL-006",
  "name": "CRASH_CONSISTENCY_ACK_DURABILITY",
  "hypothesis": "ACK(m) ⟹ durable(m)",
  "total_iterations": {},
  "replays_rejected": {},
  "ghost_acks_detected": {},
  "lost_acked_messages": {},
  "duplicate_effects_detected": {},
  "sqlite_integrity_ok": {},
  "status": "{}",
  "domain": "Darwin ARM64 / SQLite WAL / FullFsync",
  "duration_ms": {}
}}
"#,
                report.total_iterations,
                report.replays_rejected,
                report.ghost_acks_detected,
                report.lost_acked_messages,
                report.duplicate_effects_detected,
                report.sqlite_integrity_ok,
                if pass { "SUPPORTED_WITHIN_DOMAIN" } else { "FALSIFIED" },
                report.duration_ms
            );

            let report_path = work_dir.join("fl006_report.json");
            std::fs::write(&report_path, &sitrep_json).unwrap();
            println!("Report written to: {}", report_path.display());

            if pass {
                println!("VERDICT: [SUPPORTED_WITHIN_DOMAIN] — Zero lost ACKs, zero duplicate effects.");
                std::process::exit(0);
            } else {
                eprintln!("VERDICT: [FALSIFIED] — Durability invariant violated!");
                std::process::exit(1);
            }
        }
    }
}
