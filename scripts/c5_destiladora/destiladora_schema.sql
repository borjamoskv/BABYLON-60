-- ==============================================================================
-- CORTEX L0 TRACE LEDGER :: ESQUEMA DE LA DESTILADORA (L0-TRACE-TO-RUST)
-- Proyecto: BABYLON-60 (C5-REAL Architecture)
-- Autor: Borja Fernández Angulo (borjamoskv)
-- ==============================================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Registro de Contratos /goal y Trazas Operativas
CREATE TABLE IF NOT EXISTS cortex_goal_traces (
    trace_id TEXT PRIMARY KEY,                       -- UUID-v4 canónico
    conversation_id TEXT NOT NULL,                  -- ID de sesión de Antigravity
    goal_contract_hash TEXT NOT NULL,               -- SHA-256 del contrato /goal
    model_assigned TEXT NOT NULL,                   -- Argon, Flash, Sonnet, Opus, GPT-OSS
    thinking_level TEXT NOT NULL,                   -- low, medium, high
    input_ast_digest TEXT NOT NULL,                 -- SHA-256 de los ASTs de entrada
    files_touched_json TEXT NOT NULL,               -- Lista de rutas involucradas
    tool_sequence_json TEXT NOT NULL,               -- Secuencia ordenada de ToolCalls
    output_diff_digest TEXT NOT NULL,               -- SHA-256 de la mutación de código
    exit_gate_cmd TEXT NOT NULL,                    -- Comando verificador de salida
    exit_gate_code INTEGER NOT NULL,                -- 0 = Success (Fail-Closed)
    prefill_tokens INTEGER NOT NULL,                -- Conteo de tokens de entrada
    cached_tokens INTEGER NOT NULL,                 -- Tokens cubiertos por KV-cache
    thinking_tokens INTEGER NOT NULL,               -- Tokens consumidos en cadena interna
    output_tokens INTEGER NOT NULL,                 -- Tokens visibles generados
    latency_ms REAL NOT NULL,                       -- Latencia total del turno
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsqueda rápida por similitud de entrada
CREATE INDEX IF NOT EXISTS idx_goal_traces_ast ON cortex_goal_traces(input_ast_digest);
CREATE INDEX IF NOT EXISTS idx_goal_traces_exit ON cortex_goal_traces(exit_gate_code);

-- 2. Clústeres de Invariantes Sintéticos (Candidatos a Extracción Z3/Lean)
CREATE TABLE IF NOT EXISTS cortex_invariant_clusters (
    cluster_id TEXT PRIMARY KEY,                    -- Hash del patrón de transición
    ast_signature TEXT NOT NULL,                    -- Firma estructural abstracta
    sample_count INTEGER NOT NULL DEFAULT 1,        -- Contador de trazas observadas
    z3_precondition TEXT,                           -- Precondición lógica calculada
    lean4_proof_status TEXT NOT NULL DEFAULT 'UNTESTED', -- UNTESTED, PROVED, FAILED
    lean4_proof_path TEXT,                          -- Ruta al .lean generado
    crystallized_fn_name TEXT,                      -- Nombre del resolver en Rust
    crystallized_at DATETIME,                       -- Timestamp de compilación a Rust
    status TEXT NOT NULL DEFAULT 'ACCUMULATING'     -- ACCUMULATING, EXTRACTED, COMPILED, DEPLOYED
);

-- 3. Tabla de Despacho de Reglas Cristalizadas (Anillo-0 Fast Path)
CREATE TABLE IF NOT EXISTS cortex_crystallized_rules (
    rule_id TEXT PRIMARY KEY,                       -- Hash único de la regla
    cluster_ref TEXT NOT NULL,                      -- Referencia al cluster original
    fastpath_fn_symbol TEXT NOT NULL,               -- Símbolo FFI / Rust interno
    execution_time_ns INTEGER NOT NULL,             -- Latencia medida en silicio (<200.000 ns)
    hit_counter INTEGER NOT NULL DEFAULT 0,         -- Veces despachado en Fast Path
    tokens_saved_accum INTEGER NOT NULL DEFAULT 0,  -- Tokens de LLM amortizados
    active_in_ring0 INTEGER NOT NULL DEFAULT 1,     -- 1 = Activo, 0 = Invalidad por regresión
    FOREIGN KEY(cluster_ref) REFERENCES cortex_invariant_clusters(cluster_id)
);
