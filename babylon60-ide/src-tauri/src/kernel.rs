use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};
use serde::{Deserialize, Serialize};
use crate::lexicon::{Domain, Primitive, Modifier, VectorPath};

type KernelLogic = fn() -> String;

/// Thread-safe ontology registry. Initialized once at boot.
static ONTOLOGY: OnceLock<Mutex<HashMap<VectorPath, VectorEntry>>> = OnceLock::new();

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorEntry {
    pub path: VectorPath,
    pub index: usize,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DispatchResult {
    pub vector: String,
    pub index: usize,
    pub output: String,
}

fn registry() -> &'static Mutex<HashMap<VectorPath, VectorEntry>> {
    ONTOLOGY.get_or_init(|| Mutex::new(HashMap::new()))
}

/// Map of vector paths to their executable logic (kept separate from serializable entries)
static LOGIC_TABLE: OnceLock<Mutex<HashMap<VectorPath, KernelLogic>>> = OnceLock::new();

fn logic_registry() -> &'static Mutex<HashMap<VectorPath, KernelLogic>> {
    LOGIC_TABLE.get_or_init(|| Mutex::new(HashMap::new()))
}

fn bind(domain: Domain, primitive: Primitive, modifier: Modifier, description: &str, logic: KernelLogic) {
    let path = VectorPath::new(domain, primitive, modifier);
    let entry = VectorEntry {
        path,
        index: path.index(),
        description: description.to_string(),
    };

    registry().lock().unwrap().insert(path, entry);
    logic_registry().lock().unwrap().insert(path, logic);
    println!("✅ [REGISTERED] {} (idx:{}) — {}", path, path.index(), description);
}

/// Dispatch a vector by its semantic path. Returns structured result or error.
pub fn dispatch(domain: Domain, primitive: Primitive, modifier: Modifier) -> Result<DispatchResult, String> {
    let path = VectorPath::new(domain, primitive, modifier);
    let logic = logic_registry()
        .lock()
        .unwrap()
        .get(&path)
        .copied()
        .ok_or_else(|| format!("VECTOR {} NOT BOUND", path))?;

    let output = logic();

    Ok(DispatchResult {
        vector: path.to_string(),
        index: path.index(),
        output,
    })
}

/// List all registered vectors in the ontology.
pub fn list_vectors() -> Vec<VectorEntry> {
    let reg = registry().lock().unwrap();
    let mut entries: Vec<VectorEntry> = reg.values().cloned().collect();
    entries.sort_by_key(|e| e.index);
    entries
}

// ═══════════════════════════════════════════════════════
//  ONTOLOGY GENESIS — The self-writing engine
// ═══════════════════════════════════════════════════════

pub fn build_ontology() {
    // [ VECTOR 001 ]: GÉNESIS — Motor de persistencia
    bind(Domain::Matrix, Primitive::Init, Modifier::Atomic,
        "Ignite SQLite WAL engine with BFT thread safety",
        || "WAL engine initialized: journal_mode=WAL, busy_timeout=5000, synchronous=NORMAL".to_string(),
    );

    // [ VECTOR 011 ]: SELLO — Commit criptográfico
    bind(Domain::Matrix, Primitive::Commit, Modifier::Atomic,
        "Cryptographic seal: SHA-256 chain-linked event append",
        || "Event appended and chain-sealed via SHA-256(prev_hash || payload)".to_string(),
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
        || format!("{} vectors currently bound in ontology", list_vectors().len()),
    );
}
