# VECTOR A — Master Ledger & ATMS Persistence · Diseño

> Estado: **CONSTRUIDO — C5-REAL (2026-07-18).** `ledger.rs` compila y pasa tests.
> Prueba: `cargo clippy --all-targets -- -D warnings` limpio + `cargo test` 37/37
> verde (rustc 1.95, edition 2024). Condición de promoción C4-SIM→C5-REAL satisfecha.
> BFT real (réplicas + consenso) permanece trabajo futuro (§1).

## 0. Qué YA es C5-REAL (esta iteración)

- `omega0.rs` endurecido (H1/H2/H3) — 11 unit + 7 leyes proptest verdes.
- `atms.rs` — runtime ATMS in-memory (Environments/Labels/Nogoods/DDB) — 9 unit + 4 leyes proptest verdes.
- El ATMS vive en RAM. El Vector A le da **disco tamper-evidente**.

## 1. Alcance honesto: "BFT-SQLite"

El briefing pide "BFT-SQLite". Precisión termodinámica: SQLite en un solo nodo
**no puede** ser Byzantine-Fault-*Tolerant* — la tolerancia bizantina exige N≥3f+1
réplicas y consenso. Lo que sí es alcanzable y valioso en un nodo es:

- **Append-only tamper-EVIDENT** (cadena BLAKE3 CORTEX-TAINT): cualquier edición
  de una fila rompe el hash de todas las filas posteriores → detectable en O(n).
- **Linealizable** vía WAL + escritor único (el Orchestrator del Vector B).
- **Idempotente** vía direccionamiento por contenido (INSERT OR IGNORE).

BFT real = trabajo futuro (réplicas + Raft/PBFT). No lo llamemos BFT hasta entonces.

## 2. Esquema SQLite (WAL)

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;      -- WAL: durable en checkpoint, rápido en fast-loop
PRAGMA foreign_keys=ON;

-- Statement⟨M⟩, direccionado por contenido (id = BLAKE3 canónico)
CREATE TABLE statement (
  id           TEXT PRIMARY KEY,          -- blake3(content ‖ modality ‖ Σobligations)
  content      TEXT NOT NULL,
  modality     TEXT NOT NULL CHECK (modality IN ('Epistemic','Deontic')),
  obligations  TEXT NOT NULL              -- JSON array ordenado (canónico)
);

-- Justification (incluye la variante Derived con su tier — H1)
CREATE TABLE justification (
  id      TEXT PRIMARY KEY,               -- blake3 del término canónico
  kind    TEXT NOT NULL,                  -- FormalProof|StatisticalInference|...|Derived
  tier    TEXT NOT NULL,                  -- Provisional|Exogenous|Testimonial|Empirical|Deductive
  fields  TEXT NOT NULL                   -- JSON por-variante (confidence, premises, ...)
);

-- Belief = (S,J) materializado, con eslabón de la cadena causal
CREATE TABLE belief (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  stmt_id      TEXT NOT NULL REFERENCES statement(id),
  just_id      TEXT NOT NULL REFERENCES justification(id),
  parent_taint TEXT NOT NULL,             -- CORTEX-TAINT de la fila previa
  cortex_taint TEXT NOT NULL UNIQUE,      -- blake3(parent_taint ‖ canonical(row))
  created_at   INTEGER NOT NULL,          -- unix ms (inyectado por el runtime, no por el kernel)
  UNIQUE(stmt_id, just_id)                -- idempotencia
);

-- ── Proyección persistente del ATMS ──────────────────────────────
CREATE TABLE assumption (
  id        INTEGER PRIMARY KEY,          -- AssumptionId
  belief_id INTEGER NOT NULL REFERENCES belief(id)
);

CREATE TABLE environment (
  id           TEXT PRIMARY KEY,          -- blake3(sorted assumption ids)
  assumptions  TEXT NOT NULL              -- JSON array ordenado de AssumptionId
);

-- label(node) = conjunto de environments (relación N:M)
CREATE TABLE label (
  belief_id INTEGER NOT NULL REFERENCES belief(id),
  env_id    TEXT    NOT NULL REFERENCES environment(id),
  PRIMARY KEY (belief_id, env_id)
);

CREATE TABLE nogood (
  env_id       TEXT PRIMARY KEY REFERENCES environment(id),
  cortex_taint TEXT NOT NULL UNIQUE,
  created_at   INTEGER NOT NULL
);

-- Soporte ATMS: consequent ⇐ antecedents
CREATE TABLE support (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  consequent  INTEGER NOT NULL REFERENCES belief(id),
  antecedents TEXT NOT NULL                -- JSON array de belief_id
);
```

## 3. Invariante CORTEX-TAINT (el eslabón causal)

Reusa `TaintEngine` (lib.rs, BLAKE3 + toposort de Kahn). Cada fila que muta disco:

```
taint(rowₙ) = BLAKE3( taint(rowₙ₋₁) ‖ canonical_bytes(rowₙ) )
taint(row₀) = BLAKE3( "GENESIS:C5_REAL" )
```

- `canonical_bytes` = serialización determinista (campos en orden fijo, sin floats
  crudos: los `f64` de confidence/quorum se codifican con `to_bits()` para evitar
  no-determinismo de formato).
- **Boot check**: `verify_chain()` recomputa el fold sobre `belief` en orden de `id`
  y compara con `head_taint`. Mismatch → `abort()` (la doctrina "sin hash no existe"
  aplicada en la capa de almacenamiento).

## 4. API Rust (a implementar en `ledger.rs`)

```rust
pub struct Ledger { conn: rusqlite::Connection, head: String }

impl Ledger {
    pub fn open(path: &Path) -> Result<Self, LedgerError>;      // aplica PRAGMAs + verify_chain
    pub fn append_belief(&mut self, js: &omega0::JustifiedStatement) -> Result<BeliefId, LedgerError>;
    pub fn record_nogood(&mut self, env: &atms::Environment)      -> Result<(), LedgerError>;
    pub fn upsert_label(&mut self, node: BeliefId, env: &atms::Environment) -> Result<(), LedgerError>;
    pub fn load_atms(&self) -> Result<atms::Atms, LedgerError>;   // reconstruye el TMS al arrancar
    pub fn head_taint(&self) -> &str;
    pub fn verify_chain(&self) -> Result<(), LedgerError>;        // O(n) tamper check
}
```

## 5. Tests que lo harían C5-REAL (obligatorios antes de cantar victoria)

1. `append` es idempotente: dos `append_belief` del mismo (S,J) → 1 fila, mismo taint.
2. `verify_chain` verde tras N appends; y ROJO si se muta una fila a mano (tamper).
3. round-trip: `load_atms(persist(atms)) ≈ atms` (labels y nogoods preservados).
4. property: el `env_id` (blake3 de asunciones ordenadas) es estable ante permutación.
5. crash-safety: matar el proceso a mitad de un append (WAL) no corrompe la cadena.

## 6. Orden de colapso sugerido

1. `ledger.rs` con `statement`/`justification`/`belief` + cadena taint (+ tests 1,2).
2. Proyección ATMS (`environment`/`label`/`nogood`/`support`) + `load_atms` (+ tests 3,4).
3. Integrar `Obligation::Freshness` real aquí (timestamp vs. horizonte = obligación runtime, H2).
4. Recién entonces Vector B (Scheduler) escribe contra este ledger con escritor único.
