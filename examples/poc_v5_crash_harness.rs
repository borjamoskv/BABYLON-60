//! # BABYLON-60 v5 — Arnés de crash real (multi-proceso, SIGKILL)
//!
//! Cada iteración lanza un proceso hijo que ejecuta una acción contra un ledger SQLite
//! en disco y un log de efectos en disco (fsync). En el punto de crash elegido el hijo
//! se bloquea y el padre lo mata con SIGKILL. Tras todas las iteraciones, el padre
//! relanza cada autorización archivada (replay byte a byte) en procesos nuevos y audita
//! invariantes contra el estado en disco.
//!
//! Alcance: muerte de proceso. NO simula pérdida de energía (la caché de páginas del
//! SO sobrevive a SIGKILL). La clave de autoridad es determinista y sólo de prueba.
//!
//! Uso: `poc_v5_crash_harness parent [--iterations N] [--dir PATH]`

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Instant;

use babylon60::executor::{
    AdmittedAuthority, AuthorityAlgorithm, AuthorizationPayload, CrashAction, CrashPoint,
    DurableExecutionStore, EffectAdapter, ExecutionError, IdempotencyContract, ProposedIntent,
    ReservationState, SecurityPolicy, SignedAuthorization, SovereignExecutor,
    PROTOCOL_VERSION,
};
use rand::Rng;
use sha2::{Digest, Sha256};

const INST: [u8; 32] = [0xA1; 32];
const EXEC: [u8; 32] = [0xE1; 32];
const TEST_ONLY_AUTHORITY_SEED: [u8; 32] = [0x07; 32];

const EXIT_OK: i32 = 0;
const EXIT_REPLAY_REJECTED: i32 = 3;
const EXIT_OTHER_ERROR: i32 = 4;

// ---------------------------------------------------------------------------
// Adaptador con efecto durable: log append-only + fsync
// ---------------------------------------------------------------------------

struct FileLogAdapter;

#[derive(Debug)]
struct FileLogError(String);
impl std::fmt::Display for FileLogError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

impl EffectAdapter for FileLogAdapter {
    type Resource = PathBuf;
    type Effect = ();
    type Output = ();
    type Error = FileLogError;

    fn parse_intent(&self, _intent: &ProposedIntent) -> Result<Self::Effect, Self::Error> {
        Ok(())
    }

    fn compute_precondition(&self, path: &PathBuf) -> Result<[u8; 32], FileLogError> {
        let content = match std::fs::read(path) {
            Ok(c) => c,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Vec::new(),
            Err(e) => return Err(FileLogError(e.to_string())),
        };
        let mut h = Sha256::new();
        h.update(b"BABYLON60/file-log/v1");
        h.update((content.len() as u64).to_be_bytes());
        h.update(&content);
        Ok(h.finalize().into())
    }

    /// Check-then-append no es atómico frente a escritores concurrentes; el arnés
    /// garantiza un único escritor (un hijo a la vez). Limitación declarada del adaptador.
    fn apply_effect(&mut self, path: &mut PathBuf, expected: &[u8; 32], nonce: &[u8; 32], _: &()) -> Result<(), FileLogError> {
        if &self.compute_precondition(path)? != expected {
            return Err(FileLogError("precondition mismatch".into()));
        }
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&*path)
            .map_err(|e| FileLogError(e.to_string()))?;
        writeln!(f, "{}", hex::encode(nonce)).map_err(|e| FileLogError(e.to_string()))?;
        f.sync_all().map_err(|e| FileLogError(e.to_string()))
    }

    fn idempotency_contract(&self) -> IdempotencyContract {
        IdempotencyContract::NonIdempotentExplicitIntervention
    }
}

// ---------------------------------------------------------------------------
// Fixture determinista
// ---------------------------------------------------------------------------

fn authority() -> (ed25519_dalek::SigningKey, Vec<u8>) {
    let sk = ed25519_dalek::SigningKey::from_bytes(&TEST_ONLY_AUTHORITY_SEED);
    let pk = sk.verifying_key().to_bytes().to_vec();
    (sk, pk)
}

fn policy(pk: &[u8]) -> SecurityPolicy {
    SecurityPolicy {
        policy_id: [0x50; 32],
        allowed_action: "APPEND_EFFECT".into(),
        max_allowed_uses: 1,
        admitted_authority_key: pk.to_vec(),
    }
}

fn intent(iter: u64) -> ProposedIntent {
    let mut id = [0u8; 32];
    id[..8].copy_from_slice(&iter.to_be_bytes());
    ProposedIntent {
        intent_id: id,
        target_resource: "effects.log".into(),
        action_name: "APPEND_EFFECT".into(),
        parameters: iter.to_be_bytes().to_vec(),
    }
}

fn nonce_for(iter: u64) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"harness-nonce");
    h.update(iter.to_be_bytes());
    h.finalize().into()
}

fn now() -> u64 {
    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs()
}

fn executor(dir: &Path, pk: &[u8]) -> Result<SovereignExecutor<FileLogAdapter>, ExecutionError> {
    let mut store = DurableExecutionStore::open(dir.join("ledger.sqlite").to_str().unwrap())?;
    store.reconcile_on_startup()?; // semántica de reinicio del executor
    Ok(SovereignExecutor::new(
        INST,
        EXEC,
        1,
        vec![AdmittedAuthority { public_key: pk.to_vec(), algorithm: AuthorityAlgorithm::Ed25519 }],
        store,
        FileLogAdapter,
    ))
}

fn write_synced(path: &Path, bytes: &[u8]) -> std::io::Result<()> {
    let mut f = std::fs::File::create(path)?;
    f.write_all(bytes)?;
    f.sync_all()?;
    std::fs::File::open(path.parent().unwrap())?.sync_all()
}

fn auth_path(dir: &Path, iter: u64) -> PathBuf {
    dir.join("auths").join(format!("{:06}.bin", iter))
}

// ---------------------------------------------------------------------------
// Hijo: ejecutar o reproducir
// ---------------------------------------------------------------------------

fn exit_for(res: Result<(), ExecutionError>) -> ! {
    match res {
        Ok(()) => std::process::exit(EXIT_OK),
        Err(ExecutionError::NonceAlreadyConsumed(_)) => std::process::exit(EXIT_REPLAY_REJECTED),
        Err(ExecutionError::PreconditionMismatch) => std::process::exit(EXIT_REPLAY_REJECTED),
        Err(e) => {
            eprintln!("child error: {:?}", e);
            std::process::exit(EXIT_OTHER_ERROR)
        }
    }
}

fn child(dir: &Path, iter: u64, crash: CrashPoint) -> ! {
    let (sk, pk) = authority();
    let pol = policy(&pk);
    let it = intent(iter);
    let mut log = dir.join("effects.log");
    let res = (|| {
        let ex = executor(dir, &pk)?;
        let pre = ex.adapter.compute_precondition(&log).map_err(|e| ExecutionError::EffectExecutionFailed(e.0))?;
        let payload = AuthorizationPayload {
            protocol_version: PROTOCOL_VERSION,
            installation_id: INST,
            executor_id: EXEC,
            intent_digest: it.compute_digest(),
            policy_digest: pol.compute_digest(),
            resource_precondition_digest: pre,
            nonce: nonce_for(iter),
            authority_epoch: 1,
            expires_at: now() + 3600,
            max_uses: 1,
        };
        let signer = babylon60::receipt::Ed25519Signer::from_signing_key(sk);
        let auth = SignedAuthorization::new_cose(&payload, &signer).unwrap();
        let blob = auth.cose_bytes.clone();
        // Archivar la autorización ANTES de ejecutar: el replay usará estos bytes exactos.
        write_synced(&auth_path(dir, iter), &blob).map_err(|e| ExecutionError::StorageError(e.to_string()))?;
        let mut ex = ex.with_crash(crash, CrashAction::SignalAndAwaitKill);
        ex.execute_action(&auth, &it, &pol, &mut log, now())
    })();
    exit_for(res)
}

fn replay(dir: &Path, iter: u64) -> ! {
    let (_, pk) = authority();
    let pol = policy(&pk);
    let it = intent(iter);
    let mut log = dir.join("effects.log");
    let res = (|| {
        let blob = std::fs::read(auth_path(dir, iter)).map_err(|e| ExecutionError::StorageError(e.to_string()))?;
        let auth = SignedAuthorization { cose_bytes: blob };
        let mut ex = executor(dir, &pk)?;
        ex.execute_action(&auth, &it, &pol, &mut log, now())
    })();
    exit_for(res)
}

// ---------------------------------------------------------------------------
// Padre: orquestación SIGKILL + auditoría
// ---------------------------------------------------------------------------

#[derive(Debug, PartialEq)]
enum ChildOutcome {
    Killed,
    Exited(i32),
}

fn run_child(exe: &Path, args: &[String]) -> ChildOutcome {
    let mut c = Command::new(exe)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .expect("spawn child");
    let stdout = c.stdout.take().unwrap();
    for line in BufReader::new(stdout).lines() {
        let line = line.unwrap_or_default();
        if line.starts_with("CRASHPOINT ") {
            c.kill().expect("SIGKILL child"); // Child::kill = SIGKILL en Unix
            c.wait().unwrap();
            return ChildOutcome::Killed;
        }
    }
    ChildOutcome::Exited(c.wait().unwrap().code().unwrap_or(-1))
}

fn effect_counts(dir: &Path) -> HashMap<String, usize> {
    let mut m = HashMap::new();
    if let Ok(s) = std::fs::read_to_string(dir.join("effects.log")) {
        for l in s.lines().filter(|l| !l.is_empty()) {
            *m.entry(l.to_string()).or_insert(0) += 1;
        }
    }
    m
}

fn parent(dir: PathBuf, iterations: u64) -> ! {
    std::fs::create_dir_all(dir.join("auths")).unwrap();
    let exe = std::env::current_exe().unwrap();
    let mut rng = rand::rngs::OsRng;
    let mut plan: Vec<CrashPoint> = Vec::with_capacity(iterations as usize);
    let mut violations: Vec<String> = Vec::new();
    let t0 = Instant::now();

    // Fase 1: ejecución con SIGKILL
    for i in 0..iterations {
        let cp = match rng.gen_range(0..10u8) {
            0 | 1 => CrashPoint::AfterReservationBeforeDispatch,
            2 | 3 => CrashPoint::AfterDispatchBeforeEffect,
            4 | 5 => CrashPoint::AfterEffectBeforeCompletion,
            _ => CrashPoint::None,
        };
        plan.push(cp);
        let out = run_child(&exe, &["child".into(), dir.display().to_string(), i.to_string(), cp.name().into()]);
        let expected = if cp == CrashPoint::None { ChildOutcome::Exited(EXIT_OK) } else { ChildOutcome::Killed };
        if out != expected {
            violations.push(format!("iter {} crash={} outcome={:?} expected={:?}", i, cp.name(), out, expected));
        }
    }
    let phase1 = t0.elapsed();
    let effects_before_replay = effect_counts(&dir);

    // Fase 2: replay byte a byte de cada autorización archivada, en procesos nuevos
    let mut replay_rejected = 0u64;
    for i in 0..iterations {
        match run_child(&exe, &["replay".into(), dir.display().to_string(), i.to_string()]) {
            ChildOutcome::Exited(EXIT_REPLAY_REJECTED) => replay_rejected += 1,
            other => violations.push(format!("replay iter {} not rejected: {:?}", i, other)),
        }
    }
    let effects_after_replay = effect_counts(&dir);
    if effects_after_replay != effects_before_replay {
        violations.push("replay phase changed the effect log".into());
    }

    // Fase 3: auditoría contra disco
    let mut store = DurableExecutionStore::open(dir.join("ledger.sqlite").to_str().unwrap()).unwrap();
    store.reconcile_on_startup().unwrap();
    if store.count_by_state(ReservationState::Dispatched).unwrap() != 0 {
        violations.push("DISPATCHED rows survive reconciliation".into());
    }
    let mut tally: HashMap<&'static str, (u64, u64)> = HashMap::new(); // (iteraciones, con efecto)
    for (i, cp) in plan.iter().enumerate() {
        let n = nonce_for(i as u64);
        let key = hex::encode(n);
        let applied = *effects_after_replay.get(&key).unwrap_or(&0);
        if applied > 1 {
            violations.push(format!("iter {} effect applied {} times", i, applied));
        }
        let state = store.get_record(&n).unwrap().map(|r| r.state);
        let (exp_state, exp_effect) = match cp {
            CrashPoint::None => (ReservationState::Executed, 1),
            CrashPoint::AfterReservationBeforeDispatch => (ReservationState::Reserved, 0),
            CrashPoint::AfterDispatchBeforeEffect => (ReservationState::Unknown, 0),
            CrashPoint::AfterEffectBeforeCompletion => (ReservationState::Unknown, 1),
        };
        if state != Some(exp_state) || applied != exp_effect {
            violations.push(format!(
                "iter {} crash={} state={:?} effects={} expected {:?}/{}",
                i, cp.name(), state, applied, exp_state, exp_effect
            ));
        }
        let e = tally.entry(cp.name()).or_insert((0, 0));
        e.0 += 1;
        e.1 += applied as u64;
    }

    let total = t0.elapsed();
    println!("BABYLON-60 v5 crash harness  dir={}", dir.display());
    println!("iterations={} phase1={:.2?} total={:.2?}", iterations, phase1, total);
    println!("{:<34} {:>10} {:>16} {:>16}", "crash point", "iters", "effects applied", "final state");
    for cp in [
        CrashPoint::None,
        CrashPoint::AfterReservationBeforeDispatch,
        CrashPoint::AfterDispatchBeforeEffect,
        CrashPoint::AfterEffectBeforeCompletion,
    ] {
        let (n, e) = tally.get(cp.name()).copied().unwrap_or((0, 0));
        let st = match cp {
            CrashPoint::None => "EXECUTED",
            CrashPoint::AfterReservationBeforeDispatch => "RESERVED",
            _ => "UNKNOWN",
        };
        println!("{:<34} {:>10} {:>16} {:>16}", cp.name(), n, e, st);
    }
    println!("replays rejected (NonceAlreadyConsumed): {}/{}", replay_rejected, iterations);
    println!(
        "UNKNOWN with effect applied: {}  UNKNOWN without effect: {}",
        tally.get("AfterEffectBeforeCompletion").map(|t| t.1).unwrap_or(0),
        tally.get("AfterDispatchBeforeEffect").map(|t| t.0).unwrap_or(0)
    );
    println!("violations: {}", violations.len());
    for v in violations.iter() {
        println!("  VIOLATION {}", v);
    }
    let report = format!(
        "{{\"iterations\":{},\"replays_rejected\":{},\"violations\":{},\"scope\":\"process-kill (SIGKILL); not power-loss\"}}\n",
        iterations,
        replay_rejected,
        violations.len()
    );
    std::fs::write(dir.join("report.json"), report).unwrap();
    std::process::exit(if violations.is_empty() { 0 } else { 1 })
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(String::as_str);
    match mode {
        Some("child") => child(Path::new(&args[2]), args[3].parse().unwrap(), CrashPoint::parse(&args[4]).unwrap()),
        Some("replay") => replay(Path::new(&args[2]), args[3].parse().unwrap()),
        _ => {
            let mut iterations = 1000u64;
            let mut dir = None;
            let mut i = if mode == Some("parent") { 2 } else { 1 };
            while i < args.len() {
                match args[i].as_str() {
                    "--iterations" => { iterations = args[i + 1].parse().unwrap(); i += 2; }
                    "--dir" => { dir = Some(PathBuf::from(&args[i + 1])); i += 2; }
                    _ => { i += 1; }
                }
            }
            let dir = dir.unwrap_or_else(|| {
                std::env::temp_dir().join(format!("b60_crash_harness_{}_{}", std::process::id(), now()))
            });
            if dir.join("ledger.sqlite").exists() {
                eprintln!("refusing to reuse existing ledger at {}", dir.display());
                std::process::exit(2);
            }
            parent(dir, iterations)
        }
    }
}
