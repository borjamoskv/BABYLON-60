# 🗂️ VECTOR A — Master Ledger & ATMS Persistence · Diseño

Revisión 2026-10-24: **diseño con resultados históricos NO_REVALIDADOS**. Las cifras 37/37, 11+7 y 9+4 tests, versiones y compilaciones se conservan como referencias históricas sin atribuirles una ejecución actual. El axioma genérico de validez documental se retira. [Auditoría y alcance](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 0. Objetivo de diseño

Persistir creencias y dependencias ATMS con integridad, idempotencia y recuperación. No se certifica la implementación vigente ni se ejecutan tests Rust en esta revisión documental.

## 1. Límites de persistencia y BFT

SQLite en un nodo no acredita tolerancia bizantina distribuida. La cota N ≥ 3f+1 corresponde a ciertos protocolos y supuestos; Raft es un protocolo de tolerancia a fallos por parada, no reemplazo de PBFT para atacantes bizantinos.

Una cadena hash permite detectar modificaciones respecto a un ancla confiable: quien puede recomputar todo el historial o truncarlo y sustituir el ancla puede eludir una comprobación local. WAL + escritor único no prueban automáticamente linealizabilidad de toda la API. Idempotencia exige validar que una colisión de identidad conserva el mismo payload; `INSERT OR IGNORE` por sí solo no basta.

El esquema siguiente es una propuesta, no una migración ejecutada. Conforme al contrato del proyecto, los commits persistentes usan `synchronous=FULL` y hashes canónicos basados en `logical_tick`, no reloj de pared. [Documentación oficial de SQLite](https://www.sqlite.org/pragma.html#pragma_synchronous): WAL con NORMAL puede perder commits ante fallo de alimentación; FULL sincroniza el WAL en commit bajo las garantías de la plataforma.

## 2. 📌 Esquema SQLite (WAL)

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;        -- requisito de durabilidad; verificar plataforma y recuperación
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
  logical_tick INTEGER NOT NULL,          -- reloj lógico para consenso y hashes canónicos
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
  logical_tick INTEGER NOT NULL
);

-- Soporte ATMS: consequent ⇐ antecedents
CREATE TABLE support (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  consequent  INTEGER NOT NULL REFERENCES belief(id),
  antecedents TEXT NOT NULL                -- JSON array de belief_id
);
```

## 3. 📌 Invariante CORTEX-TAINT (el eslabón causal)

Reusa `[OBSOLETO: TaintEngine]` (lib.rs, BLAKE3 + toposort de Kahn). Cada fila que muta disco:

```
taint(rowₙ) = BLAKE3( taint(rowₙ₋₁) ‖ canonical_bytes(rowₙ) )
taint(row₀) = BLAKE3( "GENESIS:C5_REAL" )
```

- `[OBSOLETO: canonical_bytes]` = serialización determinista (campos en orden fijo, sin floats
  crudos: los `f64` de confidence/quorum se codifican con `to_bits()` para fijar una representación; además deben especificarse NaNs, ceros con signo y equivalencias semánticas).
- **Boot check**: `verify_chain()` recomputa el fold sobre `[OBSOLETO: belief]` en orden de `id`
  y compara con `[OBSOLETO: head_taint]`. Mismatch → rechazo según el contrato del componente (una política propuesta, pendiente de probar en la implementación).

## 4. 📌 API Rust (a implementar en `ledger.rs`)

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

## 5. 📌 Tests que lo harían Causal-Determinist (obligatorios antes de cantar victoria)

1. `append` es idempotente: dos `[OBSOLETO: append_belief]` del mismo (S,J) → 1 fila, mismo taint.
2. `[OBSOLETO: verify_chain]` verde tras N appends; y ROJO si se muta una fila a mano (tamper).
3. round-trip: `load_atms(persist(atms)) ≈ atms` (labels y nogoods preservados).
4. property: el `[OBSOLETO: env_id]` (blake3 de asunciones ordenadas) es estable ante permutación.
5. crash-safety: matar el proceso a mitad de un append (WAL) no corrompe la cadena.

## 6. 📌 Orden de colapso sugerido

1. `ledger.rs` con `statement`/`[OBSOLETO: justification]`/`[OBSOLETO: belief]` + cadena taint (+ tests 1,2).
2. Proyección ATMS (`[OBSOLETO: environment]`/`label`/`[OBSOLETO: nogood]`/`[OBSOLETO: support]`) + `[OBSOLETO: load_atms]` (+ tests 3,4).
3. Integrar `Obligation::Freshness` real aquí (timestamp vs. horizonte = obligación runtime, H2).
4. Recién entonces Vector B (Scheduler) escribe contra este ledger con escritor único.


## 7. Estado científico y aceptación pendiente

El esquema SQL y las firmas Rust ilustran una API propuesta; no se presentan como programa completo compilable. Las comprobaciones enumeradas son criterios futuros, no pruebas ejecutadas. Una propiedad de integridad requiere además amenazas, anclas, atomicidad y casos de rechazo; una garantía de durabilidad necesita recuperación ante fallos. No se deducen energía física, verdad del contenido ni seguridad total de la cadena hash.
