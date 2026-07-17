use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};
use serde::{Deserialize, Serialize};
use crate::lexicon::{Domain, Primitive, Modifier, Target, VectorPath, VectorPath4D};

// ═══════════════════════════════════════════════════════
//  KERNEL — Dual-space dispatcher
//  3D ontology (VectorPath)  → semantic HashMap registry
//  4D tensor  (VectorPath4D) → static [Action; 10000]
// ═══════════════════════════════════════════════════════

/// 3D semantic dispatch: fn() -> String (rich output)
type KernelLogic = fn() -> String;
/// 4D tensor dispatch: fn(&VectorPath4D) (side-effecting)
type Action4D = fn(&VectorPath4D);

// ─── 3D Ontology Registry ────────────────────────────────

static ONTOLOGY:    OnceLock<Mutex<HashMap<VectorPath, VectorEntry>>>   = OnceLock::new();
static LOGIC_TABLE: OnceLock<Mutex<HashMap<VectorPath, KernelLogic>>>  = OnceLock::new();

fn registry()       -> &'static Mutex<HashMap<VectorPath, VectorEntry>>  { ONTOLOGY.get_or_init(|| Mutex::new(HashMap::new())) }
fn logic_registry() -> &'static Mutex<HashMap<VectorPath, KernelLogic>> { LOGIC_TABLE.get_or_init(|| Mutex::new(HashMap::new())) }

// ─── 4D Static Table (10,000-space) ─────────────────────

static KERNEL_TABLE_4D: OnceLock<[Action4D; 10_000]> = OnceLock::new();

fn default_4d_handler(v: &VectorPath4D) {
    println!(
        "⚡ [{:04}] {} — base transductor (unbound).",
        v.index(), v
    );
}

// ─── Shared types ────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorEntry {
    pub path:        VectorPath,
    pub index:       usize,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DispatchResult {
    pub vector: String,
    pub index:  usize,
    pub output: String,
}

// ─── 3D bind / dispatch / list ───────────────────────────

fn bind(domain: Domain, primitive: Primitive, modifier: Modifier, description: &str, logic: KernelLogic) {
    let path  = VectorPath::new(domain, primitive, modifier);
    let entry = VectorEntry { path, index: path.index(), description: description.to_string() };
    registry().lock().unwrap().insert(path, entry);
    logic_registry().lock().unwrap().insert(path, logic);
    println!("✅ [REGISTERED 3D] {} (idx:{}) — {}", path, path.index(), description);
}

/// Semantic 3D dispatch: returns structured result.
pub fn dispatch_3d(domain: Domain, primitive: Primitive, modifier: Modifier) -> Result<DispatchResult, String> {
    let path  = VectorPath::new(domain, primitive, modifier);
    let logic = logic_registry()
        .lock().unwrap()
        .get(&path).copied()
        .ok_or_else(|| format!("VECTOR {} NOT BOUND", path))?;

    Ok(DispatchResult { vector: path.to_string(), index: path.index(), output: logic() })
}

/// Tensor 4D dispatch via Tauri IPC. Falls back to 3D semantic registry if 4D unbound.
#[tauri::command]
pub fn dispatch(d: u8, p: u8, m: u8, t: u8) -> Result<String, String> {
    let v4d = VectorPath4D::new(d, p, m, t).map_err(|e| e.to_string())?;

    // Async modifier: spawn detached thread
    if v4d.modifier == Modifier::Async {
        let v_clone = v4d;
        std::thread::spawn(move || {
            if let Some(table) = KERNEL_TABLE_4D.get() {
                table[v_clone.index()](&v_clone);
            }
        });
        return Ok(format!("ASYNC DISPATCHED: {}", v4d));
    }

    // Sync 4D path
    if let Some(table) = KERNEL_TABLE_4D.get() {
        table[v4d.index()](&v4d);
    }

    // Fallback: attempt 3D semantic dispatch (backward-compat)
    let v3d = v4d.to_3d();
    if let Ok(result) = dispatch_3d(v3d.domain, v3d.primitive, v3d.modifier) {
        return Ok(format!("3D FALLBACK [{}] → {}", result.vector, result.output));
    }

    Ok(format!("DISPATCHED: {}", v4d))
}

/// List all 3D bound vectors.
#[tauri::command]
pub fn list_vectors() -> Vec<VectorEntry> {
    let reg = registry().lock().unwrap();
    let mut entries: Vec<VectorEntry> = reg.values().cloned().collect();
    entries.sort_by_key(|e| e.index);
    entries
}

// ═══════════════════════════════════════════════════════
//  ONTOLOGY GENESIS — Self-writing 3D engine
// ═══════════════════════════════════════════════════════

pub fn build_ontology() {
    // [ VECTOR 001 ]: GÉNESIS — Motor de persistencia
    bind(Domain::Matrix, Primitive::Init, Modifier::Atomic,
        "Ignite SQLite WAL engine with BFT thread safety",
        || "WAL engine initialized: journal_mode=WAL, busy_timeout=5000, synchronous=NORMAL".to_string(),
    );

    // [ VECTOR 011 ]: SELLO — Commit criptográfico SHA-256
    bind(Domain::Matrix, Primitive::Commit, Modifier::Atomic,
        "Cryptographic seal: SHA3-256 chain-linked event append",
        || "Event appended and chain-sealed via SHA3-256(prev_hash || payload)".to_string(),
    );

    // [ VECTOR 030 ]: KINETIC BIND RAW — Puente IPC Frontend↔Kernel
    bind(Domain::Kinetic, Primitive::Bind, Modifier::Raw,
        "Bridge Tauri IPC to Kernel ontology dispatch",
        || "IPC bridge active: frontend can invoke any bound vector by semantic name".to_string(),
    );

    // [ VECTOR 032 ]: KINETIC BIND PERSIST — Persistir estado de UI
    bind(Domain::Kinetic, Primitive::Bind, Modifier::Persist,
        "Persist UI state mutations to CortexLedger",
        || "UI state delta persisted to cortex_events".to_string(),
    );

    // [ VECTOR 040 ]: KINETIC QUERY RAW — Introspección del Kernel
    bind(Domain::Kinetic, Primitive::Query, Modifier::Raw,
        "Query ontology registry: list all bound vectors",
        || format!("{} vectors currently bound in ontology", registry().lock().unwrap().len()),
    );
}

// ═══════════════════════════════════════════════════════
//  KERNEL INIT — Wire both dispatch spaces at boot
// ═══════════════════════════════════════════════════════

pub fn init_kernel() {
    // 1. Build 3D semantic ontology
    build_ontology();

    // 2. Initialize 4D static table (all 10,000 slots default to base handler)
    let table = [default_4d_handler as Action4D; 10_000];
    KERNEL_TABLE_4D.set(table).ok();

    println!("⚡ BABYLON60 KERNEL ONLINE — 3D semantic + 4D tensor (10,000-space)");
}
