-- ============================================================================
-- BABYLON-60 v5 — ESQUEMA L0 DE LINEALIZACIÓN ATÓMICA E INMUTABILIDAD CAUSAL
-- ============================================================================
-- Idempotente: usa IF NOT EXISTS en todas las DDL.
-- Requiere SQLite ≥ 3.37 (STRICT tables) y ≥ 3.8.11 (WITHOUT ROWID).
-- Este archivo es incluido en tiempo de compilación por `src/ring0.rs` via
-- `include_str!("../scripts/ring0_l0_schema.sql")`.
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;
PRAGMA trusted_schema = OFF;

-- ── 1. Tabla de Hechos Verificados (Entradas Ancladas en L0) ──────────────────
--
-- Cada fila representa un hecho externo verificado (oráculo, dato de entrada
-- certificado) que puede ser referenciado como fuente causal por una entrada
-- del ledger. La columna `anchored_tick` proporciona el orden temporal estricto.
CREATE TABLE IF NOT EXISTS l0_anchored_facts (
    fact_hash       BLOB PRIMARY KEY CHECK(length(fact_hash) = 32),
    anchored_tick   INTEGER NOT NULL CHECK(anchored_tick >= 0),
    domain_tag      INTEGER NOT NULL CHECK(domain_tag >= 0),
    payload_hash    BLOB NOT NULL CHECK(length(payload_hash) = 32)
) STRICT, WITHOUT ROWID;

-- Inmutabilidad: ningún hecho puede modificarse una vez anclado.
CREATE TRIGGER IF NOT EXISTS trg_facts_forbid_update
BEFORE UPDATE ON l0_anchored_facts
BEGIN
    SELECT RAISE(ABORT, '0xDEAD6060: L0_FACTS_IMMUTABLE_UPDATE_FORBIDDEN');
END;

CREATE TRIGGER IF NOT EXISTS trg_facts_forbid_delete
BEFORE DELETE ON l0_anchored_facts
BEGIN
    SELECT RAISE(ABORT, '0xDEAD6060: L0_FACTS_IMMUTABLE_DELETE_FORBIDDEN');
END;

-- ── 2. Ledger Causal de Efectos Irreversibles (Anillo-0) ──────────────────────
--
-- Tabla append-only que registra cada transición de estado autorizada por el
-- silicio. Tres invariantes se verifican en el trigger de INSERT:
--   A) Monotonía contigua: `logical_tick = MAX(logical_tick) + 1`.
--   B) Enlace Merkle: `prev_merkle_root = curr_merkle_root[tick-1]`.
--   C) Precedencia causal: `source_fact_hash` existe en `l0_anchored_facts`
--      con `anchored_tick < logical_tick`.
CREATE TABLE IF NOT EXISTS l0_causal_ledger (
    logical_tick        INTEGER PRIMARY KEY CHECK(logical_tick >= 1),
    prev_merkle_root    BLOB NOT NULL CHECK(length(prev_merkle_root) = 32),
    source_fact_hash    BLOB NOT NULL CHECK(length(source_fact_hash) = 32),
    effect_payload_hash BLOB NOT NULL CHECK(length(effect_payload_hash) = 32),
    curr_merkle_root    BLOB NOT NULL UNIQUE CHECK(length(curr_merkle_root) = 32),
    token_count         INTEGER NOT NULL CHECK(token_count >= 0 AND token_count <= 150),
    attestation_tier    INTEGER NOT NULL CHECK(attestation_tier IN (1, 2)),
    hw_signature        BLOB NOT NULL CHECK(length(hw_signature) = 64),
    hw_pubkey_id        BLOB NOT NULL CHECK(length(hw_pubkey_id) = 32),
    hw_measurement      BLOB NOT NULL CHECK(length(hw_measurement) = 32)
) STRICT;

-- Inmutabilidad absoluta — Append-Only estricto.
CREATE TRIGGER IF NOT EXISTS trg_ledger_forbid_update
BEFORE UPDATE ON l0_causal_ledger
BEGIN
    SELECT RAISE(ABORT, '0xDEAD6060: L0_LEDGER_IMMUTABLE_UPDATE_FORBIDDEN');
END;

CREATE TRIGGER IF NOT EXISTS trg_ledger_forbid_delete
BEFORE DELETE ON l0_causal_ledger
BEGIN
    SELECT RAISE(ABORT, '0xDEAD6060: L0_LEDGER_IMMUTABLE_DELETE_FORBIDDEN');
END;

-- Verificación de las tres invariantes causales en cada INSERT.
-- Actúa como barrera defensiva secundaria tras la verificación a nivel Rust.
CREATE TRIGGER IF NOT EXISTS trg_ledger_enforce_causal_invariants
BEFORE INSERT ON l0_causal_ledger
BEGIN
    -- Invariante A: Monotonía estricta sin huecos
    SELECT CASE
        WHEN NEW.logical_tick != COALESCE(
            (SELECT MAX(logical_tick) FROM l0_causal_ledger), 0
        ) + 1
        THEN RAISE(ABORT, '0xDEAD6060: L0_NON_CONTIGUOUS_LOGICAL_TICK')
    END;

    -- Invariante B: Enlace criptográfico con la raíz de Merkle anterior
    SELECT CASE
        WHEN NEW.logical_tick > 1 AND NEW.prev_merkle_root != (
            SELECT curr_merkle_root
            FROM l0_causal_ledger
            WHERE logical_tick = NEW.logical_tick - 1
        )
        THEN RAISE(ABORT, '0xDEAD6060: L0_BROKEN_MERKLE_CHAIN')
    END;

    -- Invariante C: Precedencia causal del hecho fuente
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM l0_anchored_facts
            WHERE fact_hash = NEW.source_fact_hash
              AND anchored_tick < NEW.logical_tick
        )
        THEN RAISE(ABORT, '0xDEAD6060: L0_UNANCHORED_OR_FUTURE_CAUSAL_FACT')
    END;
END;

-- ── 3. Vista de auditoría (read-only) ─────────────────────────────────────────
--
-- Permite inspeccionar el estado del ledger sin riesgo de escritura accidental.
CREATE VIEW IF NOT EXISTS v_l0_audit AS
SELECT
    e.logical_tick,
    hex(e.prev_merkle_root)    AS prev_merkle_root_hex,
    hex(e.source_fact_hash)    AS source_fact_hash_hex,
    hex(e.effect_payload_hash) AS effect_payload_hash_hex,
    hex(e.curr_merkle_root)    AS curr_merkle_root_hex,
    e.token_count,
    e.attestation_tier,
    hex(e.hw_signature)        AS hw_signature_hex,
    hex(e.hw_pubkey_id)        AS hw_pubkey_id_hex,
    hex(e.hw_measurement)      AS hw_measurement_hex,
    f.anchored_tick            AS fact_anchored_tick,
    f.domain_tag               AS fact_domain_tag
FROM l0_causal_ledger e
LEFT JOIN l0_anchored_facts f ON f.fact_hash = e.source_fact_hash
ORDER BY e.logical_tick;
