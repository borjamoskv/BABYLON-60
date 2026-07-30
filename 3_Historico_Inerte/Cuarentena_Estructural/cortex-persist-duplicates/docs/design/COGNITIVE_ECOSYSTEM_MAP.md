# 🗺️ COGNITIVE ECOSYSTEM MAP — BABYLON-60



> **"CERO ANERGÍA ES LA MUERTE."** — Cristalizado bajo la soberanía de **Borja Moskv** (Γ1)



* **Reality Level**: C5-REAL (Full AST Extraction + Dynamic Schema Query)

* **Audit Date**: 2026-07-06

* **Subprocess Kernel**: `tools/generate_ecosystem_map.py` v1.0.0



---



## 🗄️ Database Schemas & Metrics Mapping

### `runtime.db`

* Path: `/Users/borjafernandezangulo/.cortex/runtime.db`
* Size: **2336.0 KB**

| Table Name | Columns | Est. Rows |
|:---|:---|:---|
| `agents` | `id` (TEXT), `public_key` (TEXT), `name` (TEXT), `agent_type` (TEXT), `tenant_id` (TEXT) (+14 more) | **0** |
| `api_keys` | `id` (INTEGER), `name` (TEXT), `key_hash` (TEXT), `key_prefix` (TEXT), `tenant_id` (TEXT) (+9 more) | **0** |
| `audit_exports` | `id` (INTEGER), `export_type` (TEXT), `filename` (TEXT), `file_hash` (TEXT), `tx_start_id` (INTEGER) (+3 more) | **0** |
| `causal_edges` | `id` (INTEGER), `fact_hash` (TEXT), `fact_id` (INTEGER), `parent_id` (INTEGER), `signal_id` (INTEGER) (+6 more) | **0** |
| `compaction_log` | `id` (INTEGER), `tenant_id` (TEXT), `project` (TEXT), `strategy` (TEXT), `original_ids` (TEXT) (+4 more) | **0** |
| `consensus_outcomes` | `id` (INTEGER), `fact_id` (INTEGER), `tenant_id` (TEXT), `final_state` (TEXT), `final_score` (REAL) (+6 more) | **0** |
| `consensus_votes_v2` | `id` (INTEGER), `fact_id` (INTEGER), `agent_id` (TEXT), `tenant_id` (TEXT), `vote` (INTEGER) (+7 more) | **0** |
| `context_snapshots` | `id` (INTEGER), `tenant_id` (TEXT), `active_project` (TEXT), `confidence` (TEXT), `signals_used` (INTEGER) (+4 more) | **0** |
| `cortex_meta` | `key` (TEXT), `value` (TEXT) | **4** |
| `enrichment_jobs` | `id` (INTEGER), `job_id` (TEXT), `event_id` (TEXT), `fact_id` (INTEGER), `job_type` (TEXT) (+9 more) | **48** |
| `entities` | `id` (INTEGER), `name` (TEXT), `entity_type` (TEXT), `project` (TEXT), `tenant_id` (TEXT) (+4 more) | **5** |
| `entity_events` | `id` (TEXT), `entity_id` (INTEGER), `tenant_id` (TEXT), `event_type` (TEXT), `payload` (TEXT) (+5 more) | **0** |
| `entity_relations` | `id` (INTEGER), `source_entity_id` (INTEGER), `target_entity_id` (INTEGER), `tenant_id` (TEXT), `relation_type` (TEXT) (+3 more) | **4** |
| `episodes` | `id` (INTEGER), `tenant_id` (TEXT), `session_id` (TEXT), `event_type` (TEXT), `content` (TEXT) (+5 more) | **1** |
| `episodes_fts` | `content` (), `event_type` (), `project` (), `tenant_id` () | **1** |
| `episodes_fts_config` | `k` (), `v` () | **1** |
| `episodes_fts_data` | `id` (INTEGER), `block` (BLOB) | **3** |
| `episodes_fts_docsize` | `id` (INTEGER), `sz` (BLOB) | **1** |
| `episodes_fts_idx` | `segid` (), `term` (), `pgno` () | **1** |
| `evolution_state` | `id` (INTEGER), `cycle` (INTEGER), `agent_domain` (TEXT), `agent_json` (TEXT), `saved_at` (TEXT) | **0** |
| `execution_trace_ledger` | `id` (TEXT), `tenant_id` (TEXT), `origin` (TEXT), `cost` (REAL), `lineage` (TEXT) (+3 more) | **0** |
| `fact_embeddings` | `fact_id` (), `embedding` () | **47** |
| `fact_embeddings_chunks` | `chunk_id` (INTEGER), `size` (INTEGER), `validity` (BLOB), `rowids` (BLOB) | **1** |
| `fact_embeddings_info` | `key` (TEXT), `value` (ANY) | **4** |
| `fact_embeddings_rowids` | `rowid` (INTEGER), `id` (), `chunk_id` (INTEGER), `chunk_offset` (INTEGER) | **47** |
| `fact_embeddings_vector_chunks00` | `rowid` (), `vectors` (BLOB) | **1** |
| `fact_tags` | `fact_id` (INTEGER), `tag` (TEXT), `tenant_id` (TEXT) | **147** |
| `facts` | `id` (INTEGER), `fact_hash` (TEXT), `tenant_id` (TEXT), `project` (TEXT), `content` (TEXT) (+27 more) | **48** |
| `facts_fts` | `content` (), `project` (), `tags` (), `fact_type` (), `tenant_id` () | **48** |
| `facts_fts_config` | `k` (), `v` () | **1** |
| `facts_fts_content` | `id` (INTEGER), `c0` (), `c1` (), `c2` (), `c3` () (+1 more) | **48** |
| `facts_fts_data` | `id` (INTEGER), `block` (BLOB) | **11** |
| `facts_fts_docsize` | `id` (INTEGER), `sz` (BLOB) | **48** |
| `facts_fts_idx` | `segid` (), `term` (), `pgno` () | **9** |
| `ghosts` | `id` (INTEGER), `tenant_id` (TEXT), `reference` (TEXT), `context` (TEXT), `project` (TEXT) (+7 more) | **0** |
| `heartbeats` | `id` (INTEGER), `tenant_id` (TEXT), `project` (TEXT), `entity` (TEXT), `category` (TEXT) (+4 more) | **0** |
| `integrity_checks` | `id` (INTEGER), `check_type` (TEXT), `status` (TEXT), `details` (TEXT), `started_at` (TEXT) (+1 more) | **0** |
| `ledger_events` | `event_id` (TEXT), `ts` (TEXT), `tool` (TEXT), `actor` (TEXT), `action` (TEXT) (+6 more) | **0** |
| `ledger_replay_admissions` | `id` (INTEGER), `tenant_id` (TEXT), `event_id` (TEXT), `nonce` (TEXT), `request_hash` (TEXT) (+7 more) | **0** |
| `llm_telemetry` | `id` (INTEGER), `tenant_id` (TEXT), `intent` (TEXT), `resolved_by` (TEXT), `project` (TEXT) (+8 more) | **0** |
| `lock_intents` | `id` (INTEGER), `tenant_id` (TEXT), `resource` (TEXT), `agent_id` (TEXT), `action` (TEXT) (+3 more) | **0** |
| `lock_state` | `resource` (TEXT), `tenant_id` (TEXT), `holder_agent` (TEXT), `acquired_at` (TEXT), `expires_at` (TEXT) (+1 more) | **0** |
| `memory_events` | `event_id` (TEXT), `timestamp` (TEXT), `role` (TEXT), `content` (TEXT), `token_count` (INTEGER) (+5 more) | **0** |
| `merkle_roots` | `id` (INTEGER), `tenant_id` (TEXT), `root_hash` (TEXT), `tx_start_id` (INTEGER), `tx_end_id` (INTEGER) (+2 more) | **5** |
| `moskv_aegis_log` | `audit_id` (TEXT), `timestamp` (TEXT), `risk_score` (REAL), `findings` (TEXT), `exploit_chains` (TEXT) (+2 more) | **3** |
| `procedural_engrams` | `skill_name` (TEXT), `tenant_id` (TEXT), `invocations` (INTEGER), `success_rate` (REAL), `avg_latency_ms` (REAL) (+2 more) | **0** |
| `schema_version` | `version` (INTEGER), `applied_at` (TEXT), `description` (TEXT) | **1** |
| `security_audit_log` | `audit_id` (TEXT), `timestamp` (TEXT), `tenant_id` (TEXT), `actor_role` (TEXT), `actor_id` (TEXT) (+6 more) | **0** |
| `sessions` | `id` (TEXT), `tenant_id` (TEXT), `date` (TEXT), `focus` (TEXT), `summary` (TEXT) (+2 more) | **0** |
| `signals` | `id` (INTEGER), `tenant_id` (TEXT), `event_type` (TEXT), `payload` (TEXT), `source` (TEXT) (+3 more) | **48** |
| `tasks` | `id` (TEXT), `payload` (TEXT), `status` (TEXT), `priority` (INTEGER), `created_at` (REAL) | **1** |
| `tenants` | `id` (TEXT), `name` (TEXT), `config` (TEXT), `is_active` (INTEGER), `created_at` (TEXT) | **0** |
| `threat_intel` | `id` (INTEGER), `ip_address` (TEXT), `reason` (TEXT), `confidence` (TEXT), `expires_at` (TEXT) (+1 more) | **0** |
| `time_entries` | `id` (INTEGER), `tenant_id` (TEXT), `project` (TEXT), `category` (TEXT), `start_time` (TEXT) (+5 more) | **0** |
| `transactions` | `id` (INTEGER), `tenant_id` (TEXT), `project` (TEXT), `action` (TEXT), `detail` (TEXT) (+3 more) | **48** |
| `trust_edges` | `id` (INTEGER), `source_agent` (TEXT), `target_agent` (TEXT), `tenant_id` (TEXT), `trust_weight` (REAL) (+2 more) | **0** |

#### Table `agents`
```sql
CREATE TABLE agents (
    id              TEXT PRIMARY KEY,
    public_key      TEXT NOT NULL,
    name            TEXT NOT NULL,
    agent_type      TEXT NOT NULL DEFAULT 'ai',
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    reputation_score    REAL NOT NULL DEFAULT 0.5,
    base_reputation     REAL NOT NULL DEFAULT 0.5,
    reputation_stake    REAL NOT NULL DEFAULT 0.0,
    alignment_hits      INTEGER DEFAULT 0,
    alignment_misses    INTEGER DEFAULT 0,
    total_votes         INTEGER DEFAULT 0,
    successful_votes    INTEGER DEFAULT 0,
    disputed_votes      INTEGER DEFAULT 0,
    last_active_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_active           BOOLEAN DEFAULT TRUE,
    is_verified         BOOLEAN DEFAULT FALSE,
    meta                TEXT DEFAULT '{}'
)
```
#### Table `api_keys`
```sql
CREATE TABLE api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    key_hash    TEXT NOT NULL UNIQUE,
    key_prefix  TEXT NOT NULL,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    role        TEXT NOT NULL DEFAULT 'user',
    permissions TEXT NOT NULL DEFAULT '["read","write"]',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_used   TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    rate_limit  INTEGER NOT NULL DEFAULT 100,
    key_hash_argon2 TEXT,
    hash_algo   TEXT NOT NULL DEFAULT 'sha256',
    migrated_at TEXT
)
```
#### Table `audit_exports`
```sql
CREATE TABLE audit_exports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    export_type     TEXT NOT NULL,
    filename        TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    tx_start_id     INTEGER NOT NULL,
    tx_end_id       INTEGER NOT NULL,
    exported_at     TEXT NOT NULL DEFAULT (datetime('now')),
    exported_by     TEXT NOT NULL
)
```
#### Table `causal_edges`
```sql
CREATE TABLE causal_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_hash       TEXT UNIQUE,
    fact_id         INTEGER NOT NULL,
    parent_id       INTEGER,
    signal_id       INTEGER,
    edge_type       TEXT NOT NULL DEFAULT 'triggered_by',
    confidence      REAL DEFAULT 1.0,
    agent_id        TEXT,
    project         TEXT,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fact_id) REFERENCES facts(id)
)
```
#### Table `compaction_log`
```sql
CREATE TABLE compaction_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    project         TEXT NOT NULL,
    strategy        TEXT NOT NULL,
    original_ids    TEXT,
    new_fact_id     INTEGER,
    facts_before    INTEGER,
    facts_after     INTEGER,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `consensus_outcomes`
```sql
CREATE TABLE consensus_outcomes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id         INTEGER NOT NULL REFERENCES facts(id),
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    final_state     TEXT NOT NULL,
    final_score     REAL NOT NULL,
    resolved_at     TEXT NOT NULL DEFAULT (datetime('now')),
    total_votes     INTEGER NOT NULL,
    unique_agents   INTEGER NOT NULL,
    reputation_sum  REAL NOT NULL,
    resolution_method   TEXT DEFAULT 'reputation_weighted',
    meta                TEXT DEFAULT '{}'
)
```
#### Table `consensus_votes_v2`
```sql
CREATE TABLE consensus_votes_v2 (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id         INTEGER NOT NULL REFERENCES facts(id),
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    vote            INTEGER NOT NULL,
    vote_weight     REAL NOT NULL,
    agent_rep_at_vote   REAL NOT NULL,
    stake_at_vote       REAL DEFAULT 0.0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    decay_factor    REAL DEFAULT 1.0,
    vote_reason     TEXT,
    meta            TEXT DEFAULT '{}',
    UNIQUE(fact_id, agent_id)
)
```
#### Table `context_snapshots`
```sql
CREATE TABLE context_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    active_project  TEXT,
    confidence      TEXT NOT NULL,
    signals_used    INTEGER NOT NULL,
    summary         TEXT NOT NULL,
    signals_json    TEXT,
    projects_json   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `cortex_meta`
```sql
CREATE TABLE cortex_meta (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
)
```
#### Table `enrichment_jobs`
```sql
CREATE TABLE enrichment_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT UNIQUE,
    event_id        TEXT,
    fact_id         INTEGER NOT NULL REFERENCES facts(id),
    job_type        TEXT NOT NULL DEFAULT 'embedding',
    status          TEXT NOT NULL DEFAULT 'queued',
    priority        INTEGER DEFAULT 0,
    attempts        INTEGER DEFAULT 0,
    last_error      TEXT,
    next_attempt_ts TEXT,
    next_attempt_at TEXT,
    payload         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(event_id) REFERENCES entity_events(id) ON DELETE CASCADE
)
```
#### Table `entities`
```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'unknown',
    project TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    mention_count INTEGER DEFAULT 1,
    meta TEXT DEFAULT '{}'
)
```
#### Table `entity_events`
```sql
CREATE TABLE entity_events (
    id              TEXT PRIMARY KEY,
    entity_id       INTEGER NOT NULL,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    event_type      TEXT NOT NULL,
    payload         TEXT NOT NULL DEFAULT '{}',
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    prev_hash       TEXT NOT NULL DEFAULT 'GENESIS',
    signature       TEXT NOT NULL CHECK(length(signature) > 0),
    signer          TEXT NOT NULL DEFAULT '',
    schema_version  TEXT NOT NULL DEFAULT '1'
)
```
#### Table `entity_relations`
```sql
CREATE TABLE entity_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_id INTEGER NOT NULL REFERENCES entities(id),
    target_entity_id INTEGER NOT NULL REFERENCES entities(id),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    relation_type TEXT NOT NULL DEFAULT 'related_to',
    weight REAL DEFAULT 1.0,
    first_seen TEXT NOT NULL,
    source_fact_id INTEGER REFERENCES facts(id)
)
```
#### Table `episodes`
```sql
CREATE TABLE episodes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    session_id  TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    content     TEXT NOT NULL,
    project     TEXT,
    emotion     TEXT DEFAULT 'neutral',
    tags        TEXT DEFAULT '[]',
    meta        TEXT DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `episodes_fts`
```sql
CREATE VIRTUAL TABLE episodes_fts USING fts5(
    content,
    event_type,
    project,
    tenant_id UNINDEXED,
    content='episodes',
    content_rowid='id'
)
```
#### Table `episodes_fts_config`
```sql
CREATE TABLE 'episodes_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID
```
#### Table `episodes_fts_data`
```sql
CREATE TABLE 'episodes_fts_data'(id INTEGER PRIMARY KEY, block BLOB)
```
#### Table `episodes_fts_docsize`
```sql
CREATE TABLE 'episodes_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB)
```
#### Table `episodes_fts_idx`
```sql
CREATE TABLE 'episodes_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID
```
#### Table `evolution_state`
```sql
CREATE TABLE evolution_state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle       INTEGER NOT NULL,
    agent_domain TEXT NOT NULL,
    agent_json  TEXT NOT NULL,
    saved_at    TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `execution_trace_ledger`
```sql
CREATE TABLE execution_trace_ledger (
    id              TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    origin          TEXT NOT NULL,
    cost            REAL NOT NULL,
    lineage         TEXT NOT NULL DEFAULT '[]',
    outcome         TEXT NOT NULL,
    rollback_possible BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `fact_embeddings`
```sql
CREATE VIRTUAL TABLE fact_embeddings USING vec0(
    fact_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]
)
```
#### Table `fact_embeddings_chunks`
```sql
CREATE TABLE "fact_embeddings_chunks"(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,size INTEGER NOT NULL,validity BLOB NOT NULL,rowids BLOB NOT NULL)
```
#### Table `fact_embeddings_info`
```sql
CREATE TABLE "fact_embeddings_info" (key text primary key, value any)
```
#### Table `fact_embeddings_rowids`
```sql
CREATE TABLE "fact_embeddings_rowids"(rowid INTEGER PRIMARY KEY AUTOINCREMENT,id,chunk_id INTEGER,chunk_offset INTEGER)
```
#### Table `fact_embeddings_vector_chunks00`
```sql
CREATE TABLE "fact_embeddings_vector_chunks00"(rowid PRIMARY KEY,vectors BLOB NOT NULL)
```
#### Table `fact_tags`
```sql
CREATE TABLE fact_tags (
    fact_id INTEGER NOT NULL,
    tag     TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    PRIMARY KEY (fact_id, tag)
)
```
#### Table `facts`
```sql
CREATE TABLE facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_hash   TEXT UNIQUE,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    project     TEXT NOT NULL,
    content     TEXT NOT NULL,
    fact_type   TEXT NOT NULL DEFAULT 'knowledge',
    metadata    TEXT DEFAULT '{}',
    hash        TEXT,
    tx_id       INTEGER,
    valid_from  TEXT,
    valid_until TEXT,
    source      TEXT,
    confidence  TEXT DEFAULT 'C3',
    confidence_rank INTEGER DEFAULT 3,
    consensus_score  REAL DEFAULT 1.0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    is_tombstoned INTEGER NOT NULL DEFAULT 0,
    is_quarantined INTEGER NOT NULL DEFAULT 0,
    signature      TEXT,
    signer_pubkey  TEXT,
    -- Thermodynamic Plane (Ω₁₃)
    quadrant      TEXT NOT NULL DEFAULT 'ACTIVE',
    storage_tier  TEXT NOT NULL DEFAULT 'HOT',
    exergy_score  REAL NOT NULL DEFAULT 1.0,
    -- Semantic Plane
    category      TEXT NOT NULL DEFAULT 'general',
    semantic_status TEXT NOT NULL DEFAULT 'pending',
    semantic_error  TEXT,
    -- Causal Lineage (Ω₁₁)
    parent_id     INTEGER,
    relation_type TEXT,
    yield_score   REAL NOT NULL DEFAULT 1.0,
    -- Temporal Knowledge Graph
    decay_half_life REAL DEFAULT 30.0,
    -- Legacy/Compatibility
    tags          TEXT DEFAULT '[]'
)
```
#### Table `facts_fts`
```sql
CREATE VIRTUAL TABLE facts_fts USING fts5(
    content,
    project,
    tags,
    fact_type,
    tenant_id UNINDEXED
)
```
#### Table `facts_fts_config`
```sql
CREATE TABLE 'facts_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID
```
#### Table `facts_fts_content`
```sql
CREATE TABLE 'facts_fts_content'(id INTEGER PRIMARY KEY, c0, c1, c2, c3, c4)
```
#### Table `facts_fts_data`
```sql
CREATE TABLE 'facts_fts_data'(id INTEGER PRIMARY KEY, block BLOB)
```
#### Table `facts_fts_docsize`
```sql
CREATE TABLE 'facts_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB)
```
#### Table `facts_fts_idx`
```sql
CREATE TABLE 'facts_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID
```
#### Table `ghosts`
```sql
CREATE TABLE ghosts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    reference       TEXT NOT NULL,
    context         TEXT,
    project         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open',
    target_id       INTEGER,
    confidence      REAL DEFAULT 0.0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at     TEXT,
    expires_at      TEXT,
    meta            TEXT DEFAULT '{}'
)
```
#### Table `heartbeats`
```sql
CREATE TABLE heartbeats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    project     TEXT NOT NULL,
    entity      TEXT,
    category    TEXT NOT NULL,
    branch      TEXT,
    language    TEXT,
    timestamp   TEXT NOT NULL,
    meta        TEXT DEFAULT '{}'
)
```
#### Table `integrity_checks`
```sql
CREATE TABLE integrity_checks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    check_type      TEXT NOT NULL,
    status          TEXT NOT NULL,
    details         TEXT,
    started_at      TEXT NOT NULL,
    completed_at    TEXT NOT NULL
)
```
#### Table `ledger_events`
```sql
CREATE TABLE ledger_events (
    event_id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    tool TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    semantic_status TEXT NOT NULL DEFAULT 'pending',
    semantic_error TEXT,
    correlation_id TEXT,
    trace_id TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
)
```
#### Table `ledger_replay_admissions`
```sql
CREATE TABLE ledger_replay_admissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    nonce TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    ledger_event_id TEXT NOT NULL,
    actor_key_id TEXT NOT NULL,
    action TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    accepted_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
)
```
#### Table `llm_telemetry`
```sql
CREATE TABLE llm_telemetry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    intent          TEXT,
    resolved_by     TEXT,
    project         TEXT,
    tier            TEXT NOT NULL,
    depth           INTEGER NOT NULL,
    latency_ms      REAL,
    errors          TEXT DEFAULT '[]',
    timestamp       REAL NOT NULL,
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `lock_intents`
```sql
CREATE TABLE lock_intents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    resource        TEXT NOT NULL,
    agent_id        TEXT NOT NULL,
    action          TEXT NOT NULL, -- 'request', 'release'
    priority        INTEGER DEFAULT 0,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at      TEXT
)
```
#### Table `lock_state`
```sql
CREATE TABLE lock_state (
    resource        TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    holder_agent    TEXT,
    acquired_at     TEXT,
    expires_at      TEXT,
    queue_depth     INTEGER DEFAULT 0
)
```
#### Table `memory_events`
```sql
CREATE TABLE memory_events (
    event_id   TEXT PRIMARY KEY,
    timestamp  TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    session_id TEXT NOT NULL,
    tenant_id  TEXT NOT NULL DEFAULT 'default',
    prev_hash  TEXT NOT NULL DEFAULT '',
    signature  TEXT NOT NULL DEFAULT '',
    metadata   TEXT NOT NULL DEFAULT '{}'
)
```
#### Table `merkle_roots`
```sql
CREATE TABLE merkle_roots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       TEXT NOT NULL DEFAULT '__global__',
    root_hash       TEXT NOT NULL,
    tx_start_id     INTEGER NOT NULL,
    tx_end_id       INTEGER NOT NULL,
    tx_count        INTEGER NOT NULL,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `moskv_aegis_log`
```sql
CREATE TABLE moskv_aegis_log (
    audit_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    risk_score REAL NOT NULL,
    findings TEXT NOT NULL,
    exploit_chains TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    signature TEXT NOT NULL
)
```
#### Table `procedural_engrams`
```sql
CREATE TABLE procedural_engrams (
    skill_name      TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    invocations     INTEGER NOT NULL DEFAULT 0,
    success_rate    REAL NOT NULL DEFAULT 1.0,
    avg_latency_ms  REAL NOT NULL DEFAULT 0.0,
    last_invoked    REAL NOT NULL,
    permanent       INTEGER NOT NULL DEFAULT 0
)
```
#### Table `schema_version`
```sql
CREATE TABLE schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT DEFAULT (datetime('now')),
            description TEXT
        )
```
#### Table `security_audit_log`
```sql
CREATE TABLE security_audit_log (
    audit_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    status TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    signature TEXT NOT NULL,
    external_anchor TEXT
)
```
#### Table `sessions`
```sql
CREATE TABLE sessions (
    id              TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    date            TEXT NOT NULL,
    focus           TEXT NOT NULL DEFAULT '[]',
    summary         TEXT NOT NULL,
    conversations   INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `signals`
```sql
CREATE TABLE signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    event_type  TEXT NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}',
    source      TEXT NOT NULL,
    project     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    consumed_by TEXT NOT NULL DEFAULT '[]'
)
```
#### Table `tasks`
```sql
CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            payload TEXT,
            status TEXT,
            priority INTEGER,
            created_at REAL
        )
```
#### Table `tenants`
```sql
CREATE TABLE tenants (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    config      TEXT NOT NULL DEFAULT '{}',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `threat_intel`
```sql
CREATE TABLE threat_intel (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address  TEXT NOT NULL UNIQUE,
    reason      TEXT NOT NULL,
    confidence  TEXT NOT NULL DEFAULT 'C5',
    expires_at  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `time_entries`
```sql
CREATE TABLE time_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    project     TEXT NOT NULL,
    category    TEXT NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT NOT NULL,
    duration_s  INTEGER NOT NULL,
    entities    TEXT DEFAULT '[]',
    heartbeats  INTEGER DEFAULT 0,
    meta        TEXT DEFAULT '{}'
)
```
#### Table `transactions`
```sql
CREATE TABLE transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL DEFAULT 'default',
    project     TEXT NOT NULL,
    action      TEXT NOT NULL,
    detail      TEXT,
    prev_hash   TEXT,
    hash        TEXT NOT NULL,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
)
```
#### Table `trust_edges`
```sql
CREATE TABLE trust_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_agent    TEXT NOT NULL REFERENCES agents(id),
    target_agent    TEXT NOT NULL REFERENCES agents(id),
    tenant_id       TEXT NOT NULL DEFAULT 'default',
    trust_weight    REAL NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_agent, target_agent)
)
```

### `nexus.db`

* Path: `/Users/borjafernandezangulo/.cortex/nexus.db`
* Size: **36.0 KB**

| Table Name | Columns | Est. Rows |
|:---|:---|:---|
| `nexus_mutations` | `id` (INTEGER), `idempotency_key` (TEXT), `origin` (TEXT), `intent` (TEXT), `project` (TEXT) (+5 more) | **0** |

#### Table `nexus_mutations`
```sql
CREATE TABLE nexus_mutations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT UNIQUE NOT NULL,
                origin TEXT NOT NULL,
                intent TEXT NOT NULL,
                project TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                priority INTEGER NOT NULL DEFAULT 2,
                timestamp REAL NOT NULL,
                created_at REAL NOT NULL DEFAULT (unixepoch('now'))
            )
```

### `budget.db`

* Path: `/Users/borjafernandezangulo/.cortex/budget.db`
* Size: **12.0 KB**

| Table Name | Columns | Est. Rows |
|:---|:---|:---|
| `mission_budget` | `mission_id` (TEXT), `total_input_tokens` (INTEGER), `total_output_tokens` (INTEGER), `total_cost_usd` (REAL), `request_count` (INTEGER) (+1 more) | **0** |

#### Table `mission_budget`
```sql
CREATE TABLE mission_budget (
                        mission_id           TEXT PRIMARY KEY,
                        total_input_tokens   INTEGER DEFAULT 0,
                        total_output_tokens  INTEGER DEFAULT 0,
                        total_cost_usd       REAL DEFAULT 0,
                        request_count        INTEGER DEFAULT 0,
                        last_update          REAL
                    )
```

### `quota.db`

* Path: `/Users/borjafernandezangulo/.cortex/quota.db`
* Size: **8.0 KB**

| Table Name | Columns | Est. Rows |
|:---|:---|:---|
| `quota_bucket` | `id` (INTEGER), `tokens` (REAL), `last_update` (REAL), `acquired` (INTEGER), `throttled` (INTEGER) (+1 more) | **1** |

#### Table `quota_bucket`
```sql
CREATE TABLE quota_bucket (
                            id            INTEGER PRIMARY KEY,
                            tokens        REAL    NOT NULL,
                            last_update   REAL    NOT NULL,
                            acquired      INTEGER NOT NULL DEFAULT 0,
                            throttled     INTEGER NOT NULL DEFAULT 0,
                            timeouts      INTEGER NOT NULL DEFAULT 0
                        )
```

### `pulmones.db`

* Path: `/Users/borjafernandezangulo/.cortex/pulmones.db`
* Size: **16.0 KB**

| Table Name | Columns | Est. Rows |
|:---|:---|:---|
| `fallback_queue` | `id` (INTEGER), `target_func` (TEXT), `payload` (JSON), `retries` (INTEGER), `next_retry_at` (REAL) | **11** |

#### Table `fallback_queue`
```sql
CREATE TABLE fallback_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_func TEXT NOT NULL,
                    payload JSON NOT NULL,
                    retries INTEGER DEFAULT 0,
                    next_retry_at REAL NOT NULL
                )
```

### `vectors.db`

* Path: `/Users/borjafernandezangulo/.cortex/vectors.db`
* Size: **148.0 KB**

| Table Name | Columns | Est. Rows |
|:---|:---|:---|
| `facts_meta` | `id` (TEXT), `tenant_id` (TEXT), `project_id` (TEXT), `content` (TEXT), `timestamp` (REAL) (+12 more) | **0** |
| `facts_meta_fts` | `content` (), `id` () | **0** |
| `facts_meta_fts_config` | `k` (), `v` (), `cognitive_layer` (TEXT), `parent_decision_id` (TEXT), `category` (TEXT) (+4 more) | **1** |
| `facts_meta_fts_content` | `id` (INTEGER), `c0` (), `c1` (), `cognitive_layer` (TEXT), `parent_decision_id` (TEXT) (+5 more) | **0** |
| `facts_meta_fts_data` | `id` (INTEGER), `block` (BLOB), `cognitive_layer` (TEXT), `parent_decision_id` (TEXT), `category` (TEXT) (+4 more) | **2** |
| `facts_meta_fts_docsize` | `id` (INTEGER), `sz` (BLOB), `cognitive_layer` (TEXT), `parent_decision_id` (TEXT), `category` (TEXT) (+4 more) | **0** |
| `facts_meta_fts_idx` | `segid` (), `term` (), `pgno` (), `cognitive_layer` (TEXT), `parent_decision_id` (TEXT) (+5 more) | **0** |
| `vec_facts` | `rowid` (), `embedding` () | **0** |
| `vec_facts_chunks` | `chunk_id` (INTEGER), `size` (INTEGER), `validity` (BLOB), `rowids` (BLOB) | **0** |
| `vec_facts_info` | `key` (TEXT), `value` (ANY) | **4** |
| `vec_facts_rowids` | `rowid` (INTEGER), `id` (), `chunk_id` (INTEGER), `chunk_offset` (INTEGER) | **0** |
| `vec_facts_vector_chunks00` | `rowid` (), `vectors` (BLOB) | **0** |
| `vec_void` | `rowid` (INTEGER), `embedding` (BLOB) | **0** |
| `vec_void_mih` | `rowid` (INTEGER), `s0` (INTEGER), `s1` (INTEGER), `s2` (INTEGER), `s3` (INTEGER) (+12 more) | **0** |

#### Table `facts_meta`
```sql
CREATE TABLE facts_meta (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    content TEXT,
                    timestamp REAL,
                    is_diamond INTEGER,
                    is_bridge INTEGER,
                    confidence TEXT,
                    success_rate REAL,
                    cognitive_layer TEXT,
                    parent_decision_id TEXT,
                    metadata TEXT,
                    -- Double-Plane Facets (Ω₁₃)
                    category TEXT DEFAULT 'general',
                    quadrant TEXT DEFAULT 'ACTIVE',
                    storage_tier TEXT DEFAULT 'HOT',
                    facet_version INTEGER DEFAULT 2,
                    exergy_score REAL DEFAULT 1.0
                )
```
#### Table `facts_meta_fts`
```sql
CREATE VIRTUAL TABLE facts_meta_fts USING fts5(
                    content,
                    id UNINDEXED,
                    tokenize='unicode61 remove_diacritics 2'
                )
```
#### Table `facts_meta_fts_config`
```sql
CREATE TABLE 'facts_meta_fts_config'(k PRIMARY KEY, v, cognitive_layer TEXT, parent_decision_id TEXT, category TEXT DEFAULT 'general', quadrant TEXT DEFAULT 'ACTIVE', storage_tier TEXT DEFAULT 'HOT', facet_version INTEGER DEFAULT 2, exergy_score REAL DEFAULT 1.0) WITHOUT ROWID
```
#### Table `facts_meta_fts_content`
```sql
CREATE TABLE 'facts_meta_fts_content'(id INTEGER PRIMARY KEY, c0, c1, cognitive_layer TEXT, parent_decision_id TEXT, category TEXT DEFAULT 'general', quadrant TEXT DEFAULT 'ACTIVE', storage_tier TEXT DEFAULT 'HOT', facet_version INTEGER DEFAULT 2, exergy_score REAL DEFAULT 1.0)
```
#### Table `facts_meta_fts_data`
```sql
CREATE TABLE 'facts_meta_fts_data'(id INTEGER PRIMARY KEY, block BLOB, cognitive_layer TEXT, parent_decision_id TEXT, category TEXT DEFAULT 'general', quadrant TEXT DEFAULT 'ACTIVE', storage_tier TEXT DEFAULT 'HOT', facet_version INTEGER DEFAULT 2, exergy_score REAL DEFAULT 1.0)
```
#### Table `facts_meta_fts_docsize`
```sql
CREATE TABLE 'facts_meta_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB, cognitive_layer TEXT, parent_decision_id TEXT, category TEXT DEFAULT 'general', quadrant TEXT DEFAULT 'ACTIVE', storage_tier TEXT DEFAULT 'HOT', facet_version INTEGER DEFAULT 2, exergy_score REAL DEFAULT 1.0)
```
#### Table `facts_meta_fts_idx`
```sql
CREATE TABLE 'facts_meta_fts_idx'(segid, term, pgno, cognitive_layer TEXT, parent_decision_id TEXT, category TEXT DEFAULT 'general', quadrant TEXT DEFAULT 'ACTIVE', storage_tier TEXT DEFAULT 'HOT', facet_version INTEGER DEFAULT 2, exergy_score REAL DEFAULT 1.0, PRIMARY KEY(segid, term)) WITHOUT ROWID
```
#### Table `vec_facts`
```sql
CREATE VIRTUAL TABLE vec_facts USING vec0(
                        embedding int8[384]
                    )
```
#### Table `vec_facts_chunks`
```sql
CREATE TABLE "vec_facts_chunks"(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,size INTEGER NOT NULL,validity BLOB NOT NULL,rowids BLOB NOT NULL)
```
#### Table `vec_facts_info`
```sql
CREATE TABLE "vec_facts_info" (key text primary key, value any)
```
#### Table `vec_facts_rowids`
```sql
CREATE TABLE "vec_facts_rowids"(rowid INTEGER PRIMARY KEY AUTOINCREMENT,id,chunk_id INTEGER,chunk_offset INTEGER)
```
#### Table `vec_facts_vector_chunks00`
```sql
CREATE TABLE "vec_facts_vector_chunks00"(rowid PRIMARY KEY,vectors BLOB NOT NULL)
```
#### Table `vec_void`
```sql
CREATE TABLE vec_void (
                        rowid INTEGER PRIMARY KEY,
                        embedding BLOB
                    )
```
#### Table `vec_void_mih`
```sql
CREATE TABLE vec_void_mih (
                        rowid INTEGER PRIMARY KEY,
                        s0 INTEGER, s1 INTEGER, s2 INTEGER, s3 INTEGER,
                        s4 INTEGER, s5 INTEGER, s6 INTEGER, s7 INTEGER,
                        s8 INTEGER, s9 INTEGER, s10 INTEGER, s11 INTEGER,
                        s12 INTEGER, s13 INTEGER, s14 INTEGER, s15 INTEGER
                    )
```


## 🌐 HTTP / API Routes Mapping

Scanned **104** active endpoints.

| Method | Endpoint Path | Handler | File | Description |
|:---|:---|:---|:---|:---|
| `GET` | **`/`** | `list_memories` | `memories.py` | List memories for a project (paginated). |
| `GET` | **`/`** | `get_tips` | `tips.py` | Get random contextual tips. |
| `POST` | **`/`** | `store_memory` | `memories.py` | Store a memory. Returns the memory ID and cryptographic hash. |
| `POST` | **`/`** | `translate_texts` | `translate.py` | OMNI-TRANSLATE: Sovereign Core translation endpoint. |
| `POST` | **`/api/v1/telemetry/ingest`** | `ingest_telemetry` | `telemetry.py` | Ingest sovereign telemetry facts (C5-REAL) from external edge sensors. |
| `GET` | **`/api/v1/telemetry/nodes`** | `get_mafia_nodes` | `telemetry.py` | Retrieve all active mafia nodes (base + dynamic). |
| `POST` | **`/api/v1/telemetry/nodes`** | `add_mafia_node` | `telemetry.py` | Add a new mafia node fact and push to all active extensions. |
| `GET` | **`/audit`** | `get_audit_log` | `gate.py` | View the SovereignGate audit log. |
| `POST` | **`/batch`** | `batch_store` | `memories.py` | Batch store up to 100 memories in a single request. |
| `GET` | **`/boot_recovery`** | `get_boot_recovery` | `runtime.py` | Get the memory recovery report generated during boot. |
| `GET` | **`/categories`** | `list_categories` | `tips.py` | List all tip categories with counts. |
| `GET` | **`/category/{category}`** | `get_tips_by_category` | `tips.py` | Get tips filtered by category. |
| `POST` | **`/chat/completions`** | `proxy_chat_completions` | `llm_proxy.py` | OpenAI-compatible Chat Completions endpoint. |
| `POST` | **`/checkout`** | `create_checkout_session` | `stripe.py` | Create a Stripe Checkout session for a plan purchase. |
| `POST` | **`/checkpoint`** | `create_checkpoint` | `ledger.py` | Manually trigger a Merkle root checkpoint for recent transactions. |
| `GET` | **`/dashboard`** | `dashboard` | `dashboard.py` | Serve the embedded memory dashboard. |
| `GET` | **`/edg`** | `get_epistemic_dependency_graph` | `ultramap.py` | Extracts the Epistemic Dependency Graph (EDG) directly from the C5-REAL SQLite Ledger. |
| `POST` | **`/flush`** | `flush_krgs_to_disk` | `keyed_retrieval.py` | Fuerza la persistencia manual en MessagePack. |
| `GET` | **`/health`** | `get_health` | `runtime.py` | Retrieve runtime health report. |
| `GET` | **`/history`** | `get_history` | `mejoralo.py` | Retrieve MEJORAlo session history for a project. |
| `POST` | **`/ingest`** | `ingest_influencer` | `benchmark.py` | Ingest/update a single influencer into the benchmark dataset using the Write-Path Contract. |
| `GET` | **`/list`** | `list_influencers` | `benchmark.py` | Retrieve all active benchmark influencers (public read, rate-limited and CORS protected). |
| `GET` | **`/pending`** | `list_pending` | `gate.py` | List all pending L3 actions awaiting approval. |
| `POST` | **`/pipe/run`** | `langbase_pipe_run` | `langbase.py` | Run a Langbase Pipe enriched with CORTEX memory context. |
| `POST` | **`/portal`** | `create_portal_session` | `stripe.py` | Create a Stripe Customer Portal session for billing management. |
| `GET` | **`/project/{project}`** | `get_tips_by_project` | `tips.py` | Get tips scoped to a specific project. |
| `POST` | **`/psychohistory`** | `run_psychohistory_simulation` | `swarm.py` | Trigger the Psychohistory Fracture Simulator (Hito 4). |
| `POST` | **`/record`** | `record_session` | `mejoralo.py` | Record a MEJORAlo audit session in the ledger. |
| `POST` | **`/register`** | `register_keyed_node` | `keyed_retrieval.py` | Ingesta un nuevo nodo en el Keyed Retrieval Graph System (KRGS) y persiste el cambio. |
| `POST` | **`/resolve`** | `resolve_keyed_context` | `keyed_retrieval.py` | Extrae un subgrafo de contexto determinista pre-ordenado topológicamente |
| `POST` | **`/scan`** | `scan_project` | `mejoralo.py` | Execute X-Ray 13D scan on a project. |
| `POST` | **`/search`** | `langbase_memory_search` | `langbase.py` | Search a Langbase Memory set (RAG proxy). |
| `POST` | **`/search`** | `search_memories` | `memories.py` | Semantic search across all memories (scoped to tenant). |
| `POST` | **`/ship`** | `ship_gate` | `mejoralo.py` | Validate the 7 Seals for production readiness. |
| `GET` | **`/status`** | `gate_status` | `gate.py` | Get the current SovereignGate status. |
| `GET` | **`/status`** | `langbase_status` | `langbase.py` | Check Langbase API connectivity and resource counts. |
| `GET` | **`/status`** | `get_ledger_status` | `ledger.py` | Check the cryptographic integrity of all ledgers (Tx and Votes). |
| `GET` | **`/status`** | `get_swarm_status` | `swarm.py` | Aggregate swarm health and load metrics. |
| `POST` | **`/sync`** | `langbase_sync` | `langbase.py` | Sync CORTEX facts to Langbase Memory. |
| `POST` | **`/telemetry/ingest`** | `ingest_telemetry` | `telemetry.py` | Ingest sovereign telemetry facts (C5-REAL) from external edge sensors. |
| `GET` | **`/telemetry/nodes`** | `get_mafia_nodes` | `telemetry.py` | Retrieve all active mafia nodes (base + dynamic). |
| `POST` | **`/telemetry/nodes`** | `add_mafia_node` | `telemetry.py` | Add a new mafia node fact and push to all active extensions. |
| `POST` | **`/v1/admin/credibility-strike`** | `execute_credibility_strike` | `admin.py` | Execute a JIT credibility strike for a project. |
| `GET` | **`/v1/admin/keys`** | `list_api_keys` | `admin.py` | Expose non-sensitive metadata for all provisioned keys. |
| `POST` | **`/v1/admin/keys`** | `create_api_key` | `admin.py` | Sovereign Key Provisioning. |
| `GET` | **`/v1/agents`** | `list_agents` | `agents.py` | List all agents for the current tenant. |
| `POST` | **`/v1/agents`** | `register_agent` | `agents.py` | Register a new agent for Reputation-Weighted Consensus (Requires Admin). |
| `GET` | **`/v1/agents/{agent_id}`** | `get_agent` | `agents.py` | Get agent details and current reputation. |
| `POST` | **`/v1/ask`** | `ask_cortex` | `ask.py` | RAG endpoint: search → synthesize → answer. |
| `POST` | **`/v1/ask/stream`** | `ask_stream` | `ask.py` | Streaming RAG endpoint: search → synthesize → stream answer. |
| `GET` | **`/v1/daemon/status`** | `daemon_status` | `daemon.py` | Get last daemon watchdog check results. |
| `GET` | **`/v1/events/stream`** | `stream_events` | `events.py` | Subscribe to CORTEX coordination events via SSE. |
| `GET` | **`/v1/facts`** | `list_all_facts` | `facts.py` | No description. |
| `POST` | **`/v1/facts`** | `store_fact` | `facts.py` | Store a fact (scoped to authenticated tenant). |
| `POST` | **`/v1/facts/batch`** | `batch_store` | `facts.py` | Batch store up to 100 facts in a single request. |
| `POST` | **`/v1/facts/search`** | `search_facts` | `facts.py` | Semantic search across all facts (scoped to tenant). |
| `GET` | **`/v1/facts/verify`** | `verify_ledger` | `facts.py` | Verify cryptographic integrity of the memory ledger. |
| `DELETE` | **`/v1/facts/{fact_id}`** | `deprecate_fact` | `facts.py` | Soft-deprecate a fact (mark as invalid). |
| `GET` | **`/v1/facts/{fact_id}`** | `get_fact_by_id` | `facts.py` | Get a single fact by ID. |
| `GET` | **`/v1/facts/{fact_id}/chain`** | `get_causal_chain` | `facts.py` | Get the causal chain for a fact (up=ancestors, down=descendants). |
| `GET` | **`/v1/facts/{fact_id}/history`** | `get_fact_history` | `facts.py` | Retrieve version history for a specific fact. |
| `POST` | **`/v1/facts/{fact_id}/taint`** | `propagate_taint` | `facts.py` | Trigger Ω₁₃ taint propagation from a compromised/invalidated fact. |
| `POST` | **`/v1/facts/{fact_id}/vote`** | `cast_vote` | `facts.py` | Cast a consensus vote (verify/dispute) on a fact. |
| `POST` | **`/v1/facts/{fact_id}/vote-v2`** | `cast_vote_v2` | `facts.py` | Cast a reputation-weighted consensus vote (RWC). |
| `GET` | **`/v1/facts/{fact_id}/votes`** | `list_votes` | `facts.py` | Retrieve all votes for a specific fact (Tenant Isolated). |
| `GET` | **`/v1/graph`** | `get_graph_all` | `graph.py` | Get entity graph across all projects. |
| `GET` | **`/v1/graph/{project}`** | `get_graph` | `graph.py` | Get entity graph for a specific project. |
| `POST` | **`/v1/handoff`** | `generate_handoff_context` | `admin.py` | Manifest a session handoff artifact with hot context and recent episodes. |
| `GET` | **`/v1/health/deep`** | `deep_health_check` | `admin.py` | Deep Health Check - probes all CORTEX subsystems. |
| `POST` | **`/v1/heartbeat`** | `record_heartbeat` | `timing.py` | Record an activity heartbeat for automatic time tracking. |
| `GET` | **`/v1/llm/status`** | `llm_status` | `ask.py` | Check LLM provider status and list supported providers. [STATUS] |
| `POST` | **`/v1/notebooklm/digest`** | `notebooklm_digest` | `notebooklm.py` | Generate Master Digest with Shadow Key anchors. |
| `POST` | **`/v1/notebooklm/fragment`** | `notebooklm_fragment` | `notebooklm.py` | Fragment CORTEX facts into semantic domain files. |
| `GET` | **`/v1/notebooklm/status`** | `notebooklm_status` | `notebooklm.py` | Get NotebookLM sync status - staleness, file inventory, cloud detection. |
| `POST` | **`/v1/notebooklm/sync`** | `notebooklm_sync` | `notebooklm.py` | Sync exported files to cloud storage for NotebookLM pickup. |
| `POST` | **`/v1/oracle/audit`** | `audit_target` | `oracle.py` | The Oracle: Run a Sovereign Agent audit. |
| `GET` | **`/v1/projects/{project}/export`** | `export_project` | `admin.py` | Sovereign Export - dumps project memory to a secure JSON artifact. |
| `GET` | **`/v1/projects/{project}/facts`** | `recall_facts` | `facts.py` | Recall facts for a specific project with tenant isolation. |
| `GET` | **`/v1/search`** | `search_facts_get` | `search.py` | Semantic + Graph-RAG search via GET (scoped to tenant). |
| `POST` | **`/v1/search`** | `search_facts` | `search.py` | Semantic + Graph-RAG search across facts (scoped to tenant). |
| `GET` | **`/v1/status`** | `get_system_status` | `admin.py` | Expose engine diagnostics and memory health metrics. |
| `POST` | **`/v1/taas/jobs/quote`** | `request_job_quote` | `taas.py` | Request a quote and SLA for an agent execution job. |
| `POST` | **`/v1/taas/jobs/{job_id}/execute`** | `execute_job` | `taas.py` | Execute a previously quoted job and receive proof of execution. |
| `GET` | **`/v1/taas/jobs/{job_id}/verify`** | `verify_job_proof` | `taas.py` | Verify cryptographic proof of execution for a job. |
| `POST` | **`/v1/telemetry/ingest`** | `ingest_telemetry` | `telemetry.py` | Ingest sovereign telemetry facts (C5-REAL) from external edge sensors. |
| `GET` | **`/v1/telemetry/nodes`** | `get_mafia_nodes` | `telemetry.py` | Retrieve all active mafia nodes (base + dynamic). |
| `POST` | **`/v1/telemetry/nodes`** | `add_mafia_node` | `telemetry.py` | Add a new mafia node fact and push to all active extensions. |
| `GET` | **`/v1/time`** | `time_report` | `timing.py` | Get time tracking report for the last N days. |
| `GET` | **`/v1/time/history`** | `get_time_history` | `timing.py` | Get daily time history. |
| `GET` | **`/v1/time/today`** | `time_today` | `timing.py` | Get today's time tracking summary. |
| `GET` | **`/v1/trust/compliance`** | `get_compliance_status` | `trust.py` | Generate aggregate compliance report (EU AI Act Art 12). |
| `POST` | **`/v1/trust/guard`** | `dry_run_guard` | `trust.py` | Dry-run a store proposal against StorageGuard (Ω₃). |
| `GET` | **`/v1/trust/profiles/{agent_id}`** | `get_agent_trust` | `trust.py` | Retrieve the Bayesian trust profile for a specific agent. |
| `GET` | **`/verify`** | `verify_ledger` | `ledger.py` | Alias for /status - performs full integrity verification. |
| `GET` | **`/verify`** | `verify_memories` | `memories.py` | Verify cryptographic integrity of the memory ledger. |
| `POST` | **`/webhook`** | `stripe_webhook` | `stripe.py` | Handle Stripe webhook events. |
| `POST` | **`/worktrees`** | `create_worktree` | `swarm.py` | Provision a new isolated execution environment (Hito 3). |
| `DELETE` | **`/worktrees/{worktree_id}`** | `delete_worktree` | `swarm.py` | Cleanly destroy an isolated worktree. |
| `GET` | **`/worktrees/{worktree_id}`** | `get_worktree_status` | `swarm.py` | Get metadata for a specific worktree. |
| `POST` | **`/{action_id}/approve`** | `approve_action` | `gate.py` | Approve a pending L3 action with HMAC signature. |
| `POST` | **`/{action_id}/deny`** | `deny_action` | `gate.py` | Deny a pending L3 action. |
| `DELETE` | **`/{memory_id}`** | `delete_memory` | `memories.py` | Delete (soft-deprecate) a memory. |
| `GET` | **`/{memory_id}`** | `get_memory` | `memories.py` | Get a single memory by ID. |
| `GET` | **`/{memory_id}/chain`** | `get_causal_chain` | `memories.py` | Get the causal chain for a memory (up=ancestors, down=descendants). |


## 💻 CLI Commands Mapping

Scanned **356** registered CLI entrypoints.

| Type | Command | Handler | File | Description |
|:---|:---|:---|:---|:---|
| `COMMAND` | **`actions`** | `actions` | `ghost_cmds.py` | High-level actions (open-app, select-all). |
| `COMMAND` | **`aefm`** | `run_aefm` | `exergy_cmds.py` | Starts the continuous Active Field reality deformation loop (Autonomous Exergy Field Mode). |
| `COMMAND` | **`aether`** | `aether_mcp` | `mcp_cmds.py` | Boot the MOSKV-Aether Sovereign MCP Server. |
| `COMMAND` | **`agents`** | `routing_agents` | `routing_cmds.py` | Show all registered agents with resolved models. |
| `COMMAND` | **`aix`** | `aix_cmd` | `apotheosis_cmds.py` | Deification Metric (AIx). Quantifies system efficiency and sovereignty. |
| `COMMAND` | **`all`** | `tips_all` | `tips_cmds.py` | Show all available tips. |
| `COMMAND` | **`alpha`** | `growth_alpha` | `wealth_cmds.py` | Alpha hunt focalizado en un canal específico. |
| `COMMAND` | **`analyze`** | `analyze` | `chronos_cmds.py` | Analyzes the task asymmetry. Example: |
| `COMMAND` | **`anomaly-hunt`** | `anomaly_hunt_cmd` | `anomaly_cmds.py` | Full scan: detect ontological anomalies in the Ledger. |
| `COMMAND` | **`antipatterns`** | `mejoralo_antipatterns` | `mejoralo_cmds.py` | 🔍 Antipattern Scanner - Detecta lo implícito que debería ser explícito. |
| `COMMAND` | **`apoptosis`** | `apoptosis_cmd` | `apoptosis.py` | Trigger thermodynamic apoptosis on a target (.aof or .db). |
| `COMMAND` | **`audit`** | `audit` | `autodidact_cmds.py` | Mide el impacto termodinámico de las inferencias previas usando crystal_thermometer.py. |
| `COMMAND` | **`audit`** | `run_audit` | `moskv_aegis_cmds.py` | Run an adversarial audit and anchor findings in the cryptographic ledger. |
| `COMMAND` | **`audit`** | `audit_cmd` | `nexus_cmds.py` | Audit the physical filesystem for INV_NEXUS_LINK violations. |
| `COMMAND` | **`audit`** | `security_audit` | `security_cmds.py` | Run integrity audit (hash chain + signatures). |
| `COMMAND` | **`audit`** | `swarm_audit` | `swarm_cmds.py` | Deep semantic audit of a file or directory using the swarm. |
| `COMMAND` | **`audit-cognitive`** | `audit_cognitive` | `trust_cmds.py` | Run a deep cryptographic audit of the Cognitive Event Ledger (L3). |
| `COMMAND` | **`audit-file`** | `audit_file` | `lineage_cmds.py` | Scan a file for fact IDs and verify their epistemic lineage. |
| `COMMAND` | **`auto-sync`** | `auto_sync_cmd` | `nexus_cmds.py` | Automatically propagate symlinks across all projects defined in configuration. |
| `COMMAND` | **`awwwards-fix`** | `mejoralo_awwwards_fix` | `mejoralo_cmds.py` | Sovereign 200 - Rewrite animations, CSS, and UI for Awwwards SOTD. |
| `COMMAND` | **`base`** | `architect_base` | `architect_cmds.py` | Interactive requirement gathering for a Sovereign Prompt. |
| `COMMAND` | **`batch`** | `batch` | `scraper_cmds.py` | Batch extract URLs from a newline-delimited file. |
| `COMMAND` | **`bind`** | `bind_cmd` | `nexus_cmds.py` | Force a physical symlink to a CORTEX artifact. |
| `COMMAND` | **`board`** | `swarm_board_cmd` | `swarm_cmds.py` | Launch the real-time Swarm Kanban TUI. |
| `COMMAND` | **`boot`** | `boot_cmd` | `episodic_cmds.py` | Generate session boot payload (replaces context-snapshot.md). |
| `COMMAND` | **`bridge`** | `bridge` | `nexus_cmds.py` | Bridge a sovereign pattern from source to target project. |
| `COMMAND` | **`bridge-audit`** | `bridge_audit` | `security_hardening_cmds.py` | Audit active bridges for quarantine contamination. |
| `COMMAND` | **`build`** | `build_cmd` | `keter_cmds.py` | Builds a complete system from scratch. |
| `COMMAND` | **`build-manifest`** | `build_manifest_cmd` | `forensics_cmds.py` | Build a canonical SHA-256 manifest for local evidence artifacts. |
| `COMMAND` | **`capture`** | `capture_cmd` | `maestro_cmds.py` | Captura de pantalla del display principal. |
| `COMMAND` | **`cheapest`** | `routing_cheapest` | `routing_cmds.py` | Show cheapest providers for an intent. |
| `COMMAND` | **`check`** | `check` | `health_cmds.py` | Quick boolean health check (healthy/degraded). |
| `COMMAND` | **`checkout`** | `timeline_checkout` | `timeline_cmds.py` | Reconstruct state at a specific transaction ID. |
| `COMMAND` | **`checkpoint`** | `create_checkpoint` | `ledger.py` | Compute and store a Merkle root for uncheckpointed events. |
| `COMMAND` | **`checkpoint`** | `ledger_checkpoint` | `vote_ledger.py` | Activa manualmente un punto de control (Merkle root). |
| `COMMAND` | **`circuit-breaker`** | `circuit_breaker_cmd` | `immune_cmds.py` | Evaluate the cognitive entropy density and trip the Sovereign Lock if it exceeds the threshold. |
| `COMMAND` | **`cleanup`** | `swarm_cleanup` | `swarm_cmds.py` | Force-remove all ephemeral worktrees and their git metadata. |
| `COMMAND` | **`click-at`** | `click_at_cmd` | `maestro_cmds.py` | Click en coordenadas de pantalla. |
| `COMMAND` | **`commit-manifest`** | `commit_manifest_cmd` | `forensics_cmds.py` | Verify and commit a forensic evidence manifest to the transaction ledger. |
| `COMMAND` | **`compact`** | `compact_cmd` | `compact_cmds.py` | Run auto-compaction on a project's facts. |
| `COMMAND` | **`compact`** | `compact_ledger_cmd` | `ledger.py` | Compact older ledger rows into a snapshot and inject a COMPACTION_NODE. |
| `COMMAND` | **`compact-session`** | `compact_session_cmd` | `compact_cmds.py` | Generate compressed context for LLM re-injection. |
| `COMMAND` | **`compact-status`** | `compact_status` | `compact_cmds.py` | Show compaction history and statistics. |
| `COMMAND` | **`compile`** | `compile_cmd` | `nous_cmds.py` | Compile a .nous manifest into a typed AST and display it. |
| `COMMAND` | **`compliance-report`** | `compliance_report` | `trust_cmds.py` | Generate EU AI Act Article 12 compliance snapshot. |
| `COMMAND` | **`compose`** | `compose` | `genesis_cmds.py` | Compose multiple templates for a single component. |
| `COMMAND` | **`compound`** | `compound` | `chronos_cmds.py` | Detect compound causal chains and report exponential Ω₁₁ yield. |
| `COMMAND` | **`compound`** | `money_compound` | `wealth_cmds.py` | Reinversión automática 50/30/20 post-tax. |
| `COMMAND` | **`config`** | `config` | `autorouter_cmds.py` | Generar autorouter.config.json personalizable. |
| `COMMAND` | **`consolidate`** | `swarm_10k_consolidate` | `swarm_10k_cmds.py` | Trigger state synthesis to Sovereign Ledger and Annihilate the hierarchy. |
| `COMMAND` | **`contradiction-scan`** | `contradiction_scan_cmd` | `anomaly_cmds.py` | TARGETED: Search for contradictions regarding a specific entity. |
| `COMMAND` | **`copy`** | `prompt_copy` | `prompt_cmds.py` | Copy the system prompt to the clipboard. |
| `COMMAND` | **`crawl`** | `crawl` | `autodidact_cmds.py` | LIBRARIAN-1 ∪ DEMIURGE-OMEGA = Autopoiesis. |
| `COMMAND` | **`create`** | `create` | `genesis_cmds.py` | Create a new system from a minimal spec. |
| `COMMAND` | **`create`** | `snapshot_create` | `timeline_cmds.py` | Create a new physical snapshot. |
| `COMMAND` | **`daemon`** | `run_exergy_daemon` | `exergy_cmds.py` | Run the Exergy Daemon self-healing background loop. |
| `COMMAND` | **`daemon`** | `mejoralo_daemon` | `mejoralo_cmds.py` | ♾️  Ouroboros - Inicia el bucle infinito de mejora soberana. |
| `COMMAND` | **`daemon`** | `run_cortex` | `runtime_cmds.py` | Start the Cortex Persist continuous runtime kernel. |
| `COMMAND` | **`dashboard`** | `dashboard` | `dashboard_cmds.py` | Live sovereign dashboard - system health, entropy, ledger, activity. |
| `COMMAND` | **`dashboard`** | `dashboard` | `health_dashboard.py` | Rich interactive live dashboard for CORTEX Health. |
| `COMMAND` | **`dedupe`** | `dedupe` | `causal_cmds.py` | Run Memory Archaeology to deduplicate and crystallize facts. |
| `COMMAND` | **`delete`** | `delete` | `crud.py` | Soft-delete: depreca un fact y auto-sincroniza JSON. |
| `COMMAND` | **`deploy`** | `swarm_10k_deploy` | `swarm_10k_cmds.py` | Deploy the SwarmCommander and bootstrap the 10K hierarchical topology. |
| `COMMAND` | **`deploy`** | `swarm_deploy` | `swarm_cmds.py` | Deploy a Sovereign Swarm for fractal scaling (SCALING-Ω). |
| `COMMAND` | **`digest`** | `digest_cmd` | `notebooklm_cmds.py` | Generate Master Digest for NotebookLM (decrypted). |
| `COMMAND` | **`disable-boot`** | `disable_boot` | `autorouter_cmds.py` | Desinstala AUTOROUTER-1 de launchd. |
| `COMMAND` | **`dispatch`** | `routing_dispatch` | `routing_cmds.py` | Dispatch a prompt to sovereign agent(s) from the Pantheon. |
| `COMMAND` | **`doctor`** | `doctor` | `doctor_cmds.py` | 🩺 CORTEX Doctor - System diagnostic and health tool. |
| `COMMAND` | **`double-click`** | `double_click_cmd` | `maestro_cmds.py` | Doble click en coordenadas de pantalla. |
| `COMMAND` | **`drag`** | `drag_cmd` | `maestro_cmds.py` | Drag-and-drop de un punto a otro. |
| `COMMAND` | **`dry-run`** | `dry_run_cmd` | `nous_cmds.py` | Simulate a .nous migration without side-effects. |
| `COMMAND` | **`duplicates`** | `purge_duplicates` | `purge.py` | Remove exact duplicate facts, keeping the oldest per project. |
| `COMMAND` | **`edit`** | `edit` | `crud.py` | Editar un fact: depreca el viejo y crea uno nuevo con el contenido actualizado. |
| `COMMAND` | **`emit`** | `emit_cmd` | `signal_cmds.py` | Emit a signal into the bus. |
| `COMMAND` | **`empty`** | `purge_empty` | `purge.py` | Remove facts with empty or template-only content. |
| `COMMAND` | **`enable-boot`** | `enable_boot` | `autorouter_cmds.py` | Instala AUTOROUTER-1 en launchd para inicio automático en macOS. |
| `COMMAND` | **`entropy`** | `check_entropy` | `exergy_cmds.py` | Nivel 2: Comprueba la degradación entrópica (Entropy Drift) de un workflow. |
| `COMMAND` | **`escape-hatch`** | `escape_hatch_cmd` | `ledger.py` | Autonomic Data Escape Hatch (Dead Man Switch) operations. |
| `COMMAND` | **`eval`** | `eval_cmd` | `eval_cmds.py` | Run V8 Recall Precision Proxy tests. |
| `COMMAND` | **`evaluate`** | `evaluate_cmd` | `policy_cmds.py` | Evaluate memory and output prioritized action queue. |
| `COMMAND` | **`evolve`** | `evolve_scheduler` | `exergy_cmds.py` | Nivel 7: Meta-Lyapunov. Evoluciona el α_risk basado en errores contra-factuales. |
| `COMMAND` | **`evolve`** | `evolve` | `mcts_cmds.py` | Evolve the given Python file mathematically via AlphaZero-autodidact. |
| `COMMAND` | **`execute`** | `execute_cmd` | `nous_cmds.py` | Execute a .nous migration directly against the active CORTEX engine. |
| `COMMAND` | **`export`** | `export_cmd` | `audit_cmds.py` | Export the Master Ledger to a verifiable compliance bundle. |
| `COMMAND` | **`export`** | `export` | `health_cmds.py` | Export health metrics (prometheus or json format). |
| `COMMAND` | **`export`** | `export_ledger_cmd` | `ledger.py` | Export forensic ledger package in public-v1-strict format. |
| `COMMAND` | **`export`** | `export` | `sync_cmds.py` | Exportar datos o snapshot de CORTEX. |
| `COMMAND` | **`export-bundle`** | `export_bundle` | `export_cmds.py` | Exports a cryptographic compliance bundle for third-party auditing. |
| `COMMAND` | **`export-ledger`** | `export_ledger` | `public_export_cmds.py` | Write a signed public ledger export package from public-v1 JSONL. |
| `COMMAND` | **`extend`** | `extend` | `genesis_cmds.py` | Add components to an existing system. |
| `COMMAND` | **`extract`** | `fingerprint_extract` | `fingerprint_cmds.py` | Extract the Cognitive Fingerprint from the CORTEX Ledger. |
| `COMMAND` | **`extract`** | `extract_cmd` | `niche_cmds.py` | Executes the Niche Arbitrage ETL pipeline. |
| `COMMAND` | **`eyes`** | `eyes` | `ghost_cmds.py` | Screen vision and pixel parsing (screenshot, locate). |
| `COMMAND` | **`feed`** | `feed` | `darknet_cmds.py` | Visor (Feed) Noir Termodinámico Local. |
| `COMMAND` | **`field`** | `field` | `ghost_cmds.py` | Scan the topography for active Songline ghosts (Ω₁). |
| `COMMAND` | **`find`** | `find_cmd` | `maestro_cmds.py` | Buscar elementos AX por título, rol o identificador. |
| `COMMAND` | **`fix`** | `fix` | `health_cmds.py` | Auto-remediation for degraded metrics. |
| `COMMAND` | **`forge`** | `forge` | `demiurge_cmds.py` | Dynamically compile, execute, and evaluate a skill. |
| `COMMAND` | **`fragment`** | `fragment_cmd` | `notebooklm_cmds.py` | Fragment decrypted knowledge into semantic domains. |
| `COMMAND` | **`from-yaml`** | `from_yaml` | `genesis_cmds.py` | Create a system from a YAML specification file. |
| `COMMAND` | **`frontier`** | `frontier_cmd` | `audit_cmds.py` | Execute a lethal cognitive audit using the TOM, OLIVER & BENJI triad. |
| `COMMAND` | **`frontier`** | `routing_frontier` | `routing_cmds.py` | Show frontier-tier providers for an intent. |
| `COMMAND` | **`fullscreen`** | `fullscreen_cmd` | `maestro_cmds.py` | Alterna pantalla completa para una app. |
| `COMMAND` | **`gc`** | `gc_cmd` | `compact_cmds.py` | Run vector GC (safe physical deletion). |
| `COMMAND` | **`gc`** | `gc_cmd` | `signal_cmds.py` | Garbage collect old consumed signals. |
| `COMMAND` | **`generate`** | `generate` | `handoff_cmds.py` | Generate a session handoff from current CORTEX state. |
| `COMMAND` | **`generate`** | `prompt_generate` | `prompt_cmds.py` | Regenerate the system prompt with live codebase statistics. |
| `COMMAND` | **`generate`** | `honeypot_generate` | `security_cmds.py` | Generate a new synthetic secret (decoy). |
| `COMMAND` | **`genomes`** | `check_genomes` | `exergy_cmds.py` | Nivel 5: Imprime el rendimiento exergético por gen (herramienta/paradigma). |
| `COMMAND` | **`ghosts`** | `ghosts` | `nexus_cmds.py` | Sync ghosts across CORTEX (Handoffs) and local codebases. |
| `COMMAND` | **`growth`** | `growth_pipeline` | `wealth_cmds.py` | SOVEREIGN-GROWTH: de intención a revenue. Pipeline completo. |
| `COMMAND` | **`guard`** | `guard_cmd` | `apotheosis_cmds.py` | The Demiurgic Sleep: Nightly vigilance and real technical debt purge. |
| `COMMAND` | **`hand`** | `hand` | `ghost_cmds.py` | Mouse and keyboard control (click, type, hotkey). |
| `COMMAND` | **`heal`** | `cli` | `heal_cmds.py` | Invokes the LLM surgeon to reduce static (Axiom 14). |
| `COMMAND` | **`health`** | `health` | `gateway_cmds.py` | Check gateway resonance and health. |
| `COMMAND` | **`heartbeat`** | `heartbeat_cmd` | `time_cmds.py` | Record an activity heartbeat. |
| `COMMAND` | **`history`** | `history` | `autorouter_cmds.py` | Ver historial de mutaciones cognitivas. |
| `COMMAND` | **`history`** | `history` | `causal_cmds.py` | Temporal query: what did we know at a specific time? |
| `COMMAND` | **`history`** | `history_cmd` | `context_cmds.py` | Show past context inference snapshots. |
| `COMMAND` | **`history`** | `history` | `health_cmds.py` | Show persisted health score history. |
| `COMMAND` | **`history`** | `mejoralo_history` | `mejoralo_cmds.py` | Historial de sesiones MEJORAlo. |
| `COMMAND` | **`history`** | `pipeline_history` | `pipeline_cmds.py` | Show recent pipeline execution history from the ledger. |
| `COMMAND` | **`history`** | `history_cmd` | `signal_cmds.py` | Show signal history (including consumed). |
| `COMMAND` | **`hotkey`** | `hotkey_cmd` | `maestro_cmds.py` | Envía un atajo de teclado. |
| `COMMAND` | **`hydrate`** | `routing_hydrate` | `routing_cmds.py` | Show which agents would be hydrated at a given tier. |
| `COMMAND` | **`ignite`** | `sovereign_ignite_cmd` | `keter_cmds.py` | Executes the complete sovereign pipeline. |
| `COMMAND` | **`immortality`** | `entropy_immortality` | `entropy_cmds.py` | Immortality Index (ι) - cognitive crystallization metric. |
| `COMMAND` | **`incident-report`** | `incident_report` | `fiscal_cmds.py` | Reconstruct causal chain for a specific fiscal decision. |
| `COMMAND` | **`infer`** | `infer_cmd` | `context_cmds.py` | Infer current working context from ambient signals. |
| `COMMAND` | **`ingest`** | `ingest` | `autodidact_cmds.py` | Ingest a Python file through the JIT Sovereign Sandbox. |
| `COMMAND` | **`ingest`** | `ingest_cmd` | `notebooklm_cmds.py` | Silent daemon-like ingest: Parse NotebookLM notes back into CORTEX. |
| `COMMAND` | **`init`** | `agent_init` | `agent_cmds.py` | Generate a scaffold role.yaml with sensible defaults. |
| `COMMAND` | **`init`** | `init` | `init_cmds.py` | Initialize CORTEX database. |
| `COMMAND` | **`inject`** | `inject` | `reflect_cmds.py` | Retrieve relevant past learnings for system_prompt injection. |
| `COMMAND` | **`inject-vad`** | `inject_vad` | `darknet_cmds.py` | [RED TEAM] Inyecta colisiones termodinámicas deliberadas en el Sanedrín (VAD). |
| `COMMAND` | **`inspect`** | `inspect` | `crud.py` | Deep inspection of a fact (Double-Plane V2 facets). |
| `COMMAND` | **`inspect`** | `inspect_cmd` | `maestro_cmds.py` | Inspecciona el árbol de accesibilidad de una app. |
| `COMMAND` | **`install-hook`** | `entropy_install_hook` | `entropy_cmds.py` | Instala ENTROPY-0 como hook de pre-commit en el repositorio actual. |
| `COMMAND` | **`instruct`** | `architect_instruct` | `architect_cmds.py` | Rewrite a raw requirement file into a Sovereign Prompt. |
| `COMMAND` | **`jit`** | `jit_eval` | `autodidact_cmds.py` | Directly evaluate a snippet of Python in the AST Sandbox. |
| `COMMAND` | **`launch`** | `mission_launch` | `launchpad_cmds.py` | Launch a new swarm mission. Provide a goal or a mission file. |
| `COMMAND` | **`launch`** | `money_launch` | `wealth_cmds.py` | Lanza SaaS MVP / Producto Digital. |
| `COMMAND` | **`list`** | `list_requests` | `auth_cmds.py` | Lists pending BFT quorum requests. |
| `COMMAND` | **`list`** | `list_facts` | `crud.py` | Listar facts activos (tabulado). |
| `COMMAND` | **`list`** | `mission_list` | `launchpad_cmds.py` | List recent swarm missions from the ledger. |
| `COMMAND` | **`list`** | `honeypot_list` | `security_cmds.py` | List all active honeypot traps. |
| `COMMAND` | **`list`** | `snapshot_list` | `timeline_cmds.py` | List all available snapshots. |
| `COMMAND` | **`list`** | `tips_list` | `tips_cmds.py` | List all tip categories and counts. |
| `COMMAND` | **`list-windows`** | `list_windows_cmd` | `maestro_cmds.py` | Lista todas las ventanas de una aplicación. |
| `COMMAND` | **`load`** | `load` | `handoff_cmds.py` | Load and display the current session handoff. |
| `COMMAND` | **`log`** | `timeline_log` | `timeline_cmds.py` | Show the transaction history ledger. |
| `COMMAND` | **`logout`** | `logout_cmd` | `session_cmds.py` | End the current sovereign session, verifying entropic safety (Ω₆). |
| `COMMAND` | **`logs`** | `logs` | `autorouter_cmds.py` | Sigue (tail) los logs del daemon en tiempo real. |
| `COMMAND` | **`loop`** | `loop` | `loop_cmds.py` | Sovereign Execution Loop - Task → Execute → Persist → Repeat. |
| `COMMAND` | **`manifest`** | `manifest_cmd` | `apotheosis_cmds.py` | The singularity of creation. Materializes an ecosystem from a short intent. |
| `COMMAND` | **`map`** | `map_site` | `scraper_cmds.py` | Discover URLs from a website (sitemap). |
| `COMMAND` | **`matrix`** | `routing_matrix` | `routing_cmds.py` | Show the full intent→provider→model routing matrix. |
| `COMMAND` | **`memory-clean`** | `memory_clean_cmd` | `anomaly_cmds.py` | PURGE: Apply automatic actions for low severity anomalies. |
| `COMMAND` | **`metabolize`** | `metabolize_cmd` | `frontier_cmds.py` | Force a metabolism cycle (Ouroboros-Omega) on target. |
| `COMMAND` | **`migrate`** | `migrate` | `init_cmds.py` | Import CORTEX v3.1 data into v4.0. |
| `COMMAND` | **`minimize`** | `minimize_cmd` | `maestro_cmds.py` | Minimiza la ventana principal de una app. |
| `COMMAND` | **`moskv-videntia`** | `moskv_videntia` | `moskv_cmds.py` | 🔮 Moskv-Videntia - Maps all past and future problems (vulnerabilities & anergy). |
| `COMMAND` | **`move`** | `move_cmd` | `maestro_cmds.py` | Mueve la ventana principal de una app. |
| `COMMAND` | **`nirvana`** | `nirvana_cmd` | `apotheosis_cmds.py` | Destructive request. Purifies a file/dir by annihilating all complexity. |
| `COMMAND` | **`observe`** | `observe_cmd` | `episodic_cmds.py` | Start the real-time perception observer in the foreground. |
| `COMMAND` | **`obsidian`** | `obsidian` | `sync_cmds.py` | Exportar CORTEX como vault de Obsidian con notas interconectadas. |
| `COMMAND` | **`omega`** | `purge_omega` | `purge.py` | LEA-Ω: Loose End Annihilator. Purges dead code, caches, and token debris. |
| `COMMAND` | **`ordenar`** | `ordenar` | `bibliotecario_cmds.py` | Ingest a file or directory and output a structured CORTEX Memo. |
| `COMMAND` | **`patterns`** | `patterns_cmd` | `episodic_cmds.py` | Detect recurring patterns across sessions. |
| `COMMAND` | **`poll`** | `poll_cmd` | `signal_cmds.py` | Poll and consume unconsumed signals. |
| `COMMAND` | **`predict`** | `predict_exergy` | `exergy_cmds.py` | Nivel 3: Predice el tiempo y exergía esperada de un workflow. |
| `COMMAND` | **`preview`** | `preview` | `genesis_cmds.py` | Preview what files would be created without writing anything. |
| `COMMAND` | **`process`** | `process` | `ghost_cmds.py` | Process management (list, kill, find). |
| `COMMAND` | **`produce`** | `produce_cmd` | `grammy_cmds.py` | Dispara el pipeline de producción de GRAMMY-Ω para un nuevo track. |
| `COMMAND` | **`project`** | `purge_project` | `purge.py` | Deprecate all facts in a project. |
| `COMMAND` | **`projection`** | `projection` | `chronos_cmds.py` | Project Linear vs Compound CHRONOS-1 yield over a decade. |
| `COMMAND` | **`prune`** | `prune` | `mcts_cmds.py` | [LEA-OMEGA] Garbage Collect orphaned MCTS Chronos worktrees and branches. |
| `COMMAND` | **`prune`** | `prune` | `radar_cmds.py` | Execute the 'Poda' (Pruning) of impossible states and entropy (Protocol Ω₂). |
| `COMMAND` | **`pulse`** | `pulse` | `nexus_cmds.py` | System health audit across all MOSKV projects. |
| `COMMAND` | **`purge`** | `swarm_purge` | `swarm_cmds.py` | Purge residual Swarm-100 debt from the AsyncSignalBus. |
| `COMMAND` | **`quarantine`** | `quarantine` | `security_hardening_cmds.py` | Quarantine a suspicious fact (isolate without deleting). |
| `COMMAND` | **`radar`** | `money_radar` | `wealth_cmds.py` | Escaneo completo del mercado para Alpha y DeFi. |
| `COMMAND` | **`random`** | `tips_random` | `tips_cmds.py` | Show random tips (great for thinking pauses). |
| `COMMAND` | **`reap-ghosts`** | `reap_ghosts` | `security_hardening_cmds.py` | Reap expired ghosts (DB + Songlines). |
| `COMMAND` | **`recall`** | `recall_cmd` | `episodic_cmds.py` | Recall episodic memories with flexible filtering. |
| `COMMAND` | **`recall`** | `recall` | `memory_cmds.py` | Load full context for a project. |
| `COMMAND` | **`record`** | `record_cmd` | `episodic_cmds.py` | Record an episodic memory event. |
| `COMMAND` | **`record`** | `mejoralo_record` | `mejoralo_cmds.py` | Ouroboros - Registrar sesión MEJORAlo en el ledger. |
| `COMMAND` | **`refactor`** | `swarm_refactor` | `swarm_cmds.py` | Refactor a specific file using the full specialist squad. |
| `COMMAND` | **`reflect`** | `reflect` | `reflect_cmds.py` | Store a post-mortem reflection for the current session. |
| `COMMAND` | **`reject`** | `reject_request` | `auth_cmds.py` | Rejects a pending request directly (admin override). |
| `COMMAND` | **`report`** | `entropy_report` | `entropy_cmds.py` | Genera un reporte del estado de inmunidad del proyecto. |
| `COMMAND` | **`report`** | `report` | `health_cmds.py` | Full health report with recommendations. |
| `COMMAND` | **`report`** | `report` | `roi_cmds.py` | Genera un reporte ROI en markdown. |
| `COMMAND` | **`report`** | `security_report` | `security_cmds.py` | Generate daily security report. |
| `COMMAND` | **`reset`** | `reset` | `quota_cmds.py` | Reset de emergencia: llena el bucket al máximo y borra métricas. |
| `COMMAND` | **`resize`** | `resize_cmd` | `maestro_cmds.py` | Redimensiona la ventana principal de una app. |
| `COMMAND` | **`resolve`** | `routing_resolve` | `routing_cmds.py` | Resolve the best model for a provider+intent pair. |
| `COMMAND` | **`reverse`** | `architect_reverse` | `architect_cmds.py` | Reverse engineer style and structural rules. |
| `COMMAND` | **`rewrite`** | `rewrite_cmd` | `keter_cmds.py` | Rewrites a component from 0 to 100 without asking. |
| `COMMAND` | **`run`** | `agent_run` | `agent_cmds.py` | Compile and run an agent from a YAML role definition. |
| `COMMAND` | **`run`** | `run_cmd` | `maestro_cmds.py` | Ejecuta instrucción de lenguaje natural con Mac Maestro. |
| `COMMAND` | **`run`** | `run_pipeline` | `pipeline_cmds.py` | Execute an intent through the full E2E CORTEX pipeline. |
| `COMMAND` | **`scan`** | `scan_cmd` | `frontier_cmds.py` | Scan the frontier for new intelligence (Cognitive Ingestion). |
| `COMMAND` | **`scan`** | `mejoralo_scan` | `mejoralo_cmds.py` | X-Ray 13D - Escaneo multidimensional del proyecto. |
| `COMMAND` | **`scan`** | `scan` | `radar_cmds.py` | Scan the topography for active ghosts and entropy. |
| `COMMAND` | **`scan`** | `security_scan` | `security_cmds.py` | Manual full scan of content. |
| `COMMAND` | **`scan`** | `growth_scan` | `wealth_cmds.py` | Escaneo pasivo de oportunidades CORTEX. |
| `COMMAND` | **`schedule`** | `schedule_workflows` | `exergy_cmds.py` | Nivel 4: Lyapunov Scheduler. Ordena workflows por densidad de exergía. |
| `COMMAND` | **`score`** | `score` | `health_cmds.py` | Print only the numeric health score (0-100). |
| `COMMAND` | **`scrape`** | `scrape` | `scraper_cmds.py` | Extract content from a single URL. |
| `COMMAND` | **`scroll`** | `scroll_cmd` | `maestro_cmds.py` | Scroll de rueda. Positivo=arriba, negativo=abajo. |
| `COMMAND` | **`search`** | `search` | `memory_cmds.py` | Semantic search across CORTEX memory. |
| `COMMAND` | **`self`** | `self_create` | `genesis_cmds.py` | Ω₀: Generate the Genesis Engine's own specification (auto-reference proof). |
| `COMMAND` | **`shannon`** | `entropy_shannon` | `entropy_cmds.py` | Shannon entropy analysis of CORTEX memory. |
| `COMMAND` | **`ship`** | `mejoralo_ship` | `mejoralo_cmds.py` | Ship Gate - Los 7 Sellos de producción. |
| `COMMAND` | **`show`** | `prompt_show` | `prompt_cmds.py` | Print the CORTEX system prompt to stdout. |
| `COMMAND` | **`siege`** | `siege` | `trust_cmds.py` | Run an autonomous Red Team swarm to test Ledger and Vault BFT compliance. |
| `COMMAND` | **`signals`** | `signals_cmd` | `context_cmds.py` | Show raw ambient signals. |
| `COMMAND` | **`skill-sync`** | `skill_sync` | `nexus_cmds.py` | Full unification pipeline from the Singularity Nexus Skill. |
| `COMMAND` | **`snapshot`** | `fiscal_snapshot` | `fiscal_cmds.py` | Generate an audit-ready fiscal snapshot. |
| `COMMAND` | **`snipe`** | `money_snipe` | `wealth_cmds.py` | Ejecuta oportunidad validada con Risk Management militar. |
| `COMMAND` | **`sovereign`** | `sovereign_mcp` | `mcp_cmds.py` | Boot the CORTEX Sovereign MCP Server (Rust-native, Stdio). |
| `COMMAND` | **`spawn`** | `spawn_cmd` | `spawn_cmds.py` | Ignite a headless sub-agent to execute an intent autonomously. |
| `COMMAND` | **`specs`** | `list_specs` | `genesis_cmds.py` | List available YAML specification templates. |
| `COMMAND` | **`start`** | `start` | `autorouter_cmds.py` | Arrancar el daemon de ruteo cognitivo. |
| `COMMAND` | **`start`** | `cmd_omega_start` | `omega_cmds.py` | Inicia el metabolismo de CORTEX (Omega Singularity). |
| `COMMAND` | **`start`** | `start_worker` | `worker_cmds.py` | Start all background workers (Enrichment, Compaction). |
| `COMMAND` | **`stats`** | `stats` | `memory_cmds.py` | Show memory statistics. |
| `COMMAND` | **`stats`** | `stats_cmd` | `signal_cmds.py` | Show signal bus statistics. |
| `COMMAND` | **`status`** | `router_status` | `autorouter_cmds.py` | Mostrar estado del daemon. |
| `COMMAND` | **`status`** | `status` | `ghost_cmds.py` | Check the status of GHOST-1 dependencies. |
| `COMMAND` | **`status`** | `status` | `github_cmds.py` | Show GitHub bridge sync status. |
| `COMMAND` | **`status`** | `sovereign_status_cmd` | `keter_cmds.py` | Displays the status of DigitalEndocrine and PowerLevel. |
| `COMMAND` | **`status`** | `status_cmd` | `notebooklm_cmds.py` | Show NotebookLM sync status and file inventory. |
| `COMMAND` | **`status`** | `cmd_omega_status` | `omega_cmds.py` | Consulta el estado del metabolismo. |
| `COMMAND` | **`status`** | `pipeline_status` | `pipeline_cmds.py` | Show pipeline configuration and health. |
| `COMMAND` | **`status`** | `status_cmd` | `policy_cmds.py` | Show policy engine status and configuration. |
| `COMMAND` | **`status`** | `status` | `quota_cmds.py` | Visualiza el estado del Sovereign Quota Manager con métricas. |
| `COMMAND` | **`status`** | `status` | `roi_cmds.py` | Muestra el ROI acumulado del ecosistema. |
| `COMMAND` | **`status`** | `routing_status` | `routing_cmds.py` | Show LLM provider readiness and API key status. [STATUS_CLI] |
| `COMMAND` | **`status`** | `security_status` | `security_cmds.py` | Show shield health dashboard. |
| `COMMAND` | **`status`** | `status` | `status_cmds.py` | Show CORTEX health and statistics. |
| `COMMAND` | **`status`** | `swarm_10k_status` | `swarm_10k_cmds.py` | Display real-time global exergy and density stats for the 10K Swarm. |
| `COMMAND` | **`status`** | `ledger_status` | `vote_ledger.py` | Muestra el estado actual del registro de votos. |
| `COMMAND` | **`stop`** | `stop` | `autorouter_cmds.py` | Detener el daemon limpiamente. |
| `COMMAND` | **`storage-init-pg`** | `storage_init_pg` | `storage_cmds.py` | Initialize CORTEX PostgreSQL schema. |
| `COMMAND` | **`storage-status`** | `storage_status` | `storage_cmds.py` | Show current storage backend mode and health. |
| `COMMAND` | **`store`** | `store` | `memory_cmds.py` | Store a fact in CORTEX. |
| `COMMAND` | **`store-batch`** | `store_batch` | `memory_cmds.py` | Store multiple facts from a JSON file in CORTEX. |
| `COMMAND` | **`strike`** | `swarm_strike` | `swarm_cmds.py` | Deploy CORTEX-SWARM-100 Architecture (20 Sovereign Vessels) |
| `COMMAND` | **`surf`** | `surf` | `browser_cmds.py` | Deploy BROWSER-Ω to a URL with a specific objective. |
| `COMMAND` | **`sync`** | `sync` | `darknet_cmds.py` | Descarga la matriz exterior mundial y desata el debate de los avatares. |
| `COMMAND` | **`sync`** | `sync` | `github_cmds.py` | Sync GitHub Issues/PRs → CORTEX bridge facts. |
| `COMMAND` | **`sync`** | `sync_cmd` | `notebooklm_cmds.py` | Sync exports to Google Drive for NotebookLM auto-pickup. |
| `COMMAND` | **`sync`** | `sync` | `sync_cmds.py` | Sincronizar ~/.agent/memory/ → CORTEX (incremental). |
| `COMMAND` | **`system`** | `system` | `ghost_cmds.py` | System state and hardware (volume, brightness, battery). |
| `COMMAND` | **`tax`** | `money_tax` | `wealth_cmds.py` | Generador de reportes fiscales y compliance. |
| `COMMAND` | **`telemetry`** | `telemetry_cmd` | `telemetry.py` | Mostrar métricas simuladas del sistema. |
| `COMMAND` | **`templates`** | `list_templates` | `genesis_cmds.py` | List all available system templates. |
| `COMMAND` | **`test`** | `test` | `autorouter_cmds.py` | Test rápido de todas las funciones. |
| `COMMAND` | **`test-sync`** | `security_test_sync` | `security_cmds.py` | Test visual synchronization with the Notch. |
| `COMMAND` | **`time`** | `time_cmd` | `time_cmds.py` | Show time tracking summary. |
| `COMMAND` | **`trace`** | `trace_lineage` | `lineage_cmds.py` | Trace the heredity tree of a fact back to L0 sources. |
| `COMMAND` | **`trace-chain`** | `trace_chain` | `causal_cmds.py` | Traverse the causal chain from a fact. |
| `COMMAND` | **`trace-episode`** | `trace_episode` | `causal_cmds.py` | Trace causal episodes - reconstruct WHY something happened. |
| `COMMAND` | **`trend`** | `trend` | `health_cmds.py` | Health trend from DB history (instant) or live sampling. |
| `COMMAND` | **`trend`** | `mejoralo_trend` | `mejoralo_cmds.py` | 📈 Effectiveness Trend - ¿CORTEX está mejorando tu código de verdad? |
| `COMMAND` | **`triangulate`** | `triangulate` | `triangulation_cmds.py` | DISPARA EL PROTOCOLO DE TRIANGULACIÓN DIAGNÓSTICA. |
| `COMMAND` | **`trust`** | `trust_mcp` | `mcp_cmds.py` | Boot the standard CORTEX Trust MCP Server. |
| `COMMAND` | **`type`** | `type_cmd` | `maestro_cmds.py` | Escribe texto en la app activa (clipboard para cadenas largas). |
| `COMMAND` | **`unquarantine`** | `unquarantine` | `security_hardening_cmds.py` | Lift quarantine from a fact (restore to active). |
| `COMMAND` | **`up`** | `swarm_up` | `swarm_cmds.py` | Launch the Sovereign Swarm with Omega Prime as orchestrator. |
| `COMMAND` | **`update`** | `security_update` | `security_cmds.py` | Force threat feed refresh from remote sources. |
| `COMMAND` | **`validate`** | `agent_validate` | `agent_cmds.py` | Validate a role.yaml configuration file. |
| `COMMAND` | **`verify`** | `verify` | `health_cmds.py` | Run structural invariant checks on the health system. |
| `COMMAND` | **`verify`** | `verify_ledger` | `ledger.py` | Verify hash chain integrity. |
| `COMMAND` | **`verify`** | `verify_fact` | `trust_cmds.py` | Verify cryptographic integrity of a specific fact. |
| `COMMAND` | **`verify`** | `ledger_verify` | `vote_ledger.py` | Verifica la integridad criptográfica del registro de votos. |
| `COMMAND` | **`verify-bundle`** | `verify_bundle_cmd` | `audit_cmds.py` | Offline cryptographic verification of an EU AI Act compliance bundle. |
| `COMMAND` | **`verify-bundle`** | `verify_bundle` | `verify_cmds.py` | Verifies a CORTEX Compliance Bundle (EU AI Act / SOC2). |
| `COMMAND` | **`verify-commit`** | `verify_commit_cmd` | `forensics_cmds.py` | Verify a forensic manifest and its matching transaction-ledger commitment. |
| `COMMAND` | **`verify-files`** | `verify_files_cmd` | `verification_cmds.py` | Verifica archivos Python contra los invariantes de seguridad soberanos. |
| `COMMAND` | **`verify-ledger`** | `verify_ledger_cmd` | `verification_cmds.py` | Cryptographically verifies the offline integrity of the CORTEX Ledger (H5.1). |
| `COMMAND` | **`verify-ledger-export`** | `verify_ledger_export` | `public_verifier_cmds.py` | Verify a public ledger export from files only. |
| `COMMAND` | **`verify-manifest`** | `verify_manifest_cmd` | `forensics_cmds.py` | Verify a canonical evidence manifest against local artifact bytes. |
| `COMMAND` | **`vote`** | `submit_vote` | `auth_cmds.py` | Submits a cryptographic vote for a pending consensus request. |
| `COMMAND` | **`vote`** | `vote` | `vote_ledger.py` | Emite un voto de consenso sobre un hecho (1=verificar, -1=disputar). |
| `COMMAND` | **`window`** | `window` | `ghost_cmds.py` | Window management (list, focus, tile). |
| `COMMAND` | **`writeback`** | `writeback` | `sync_cmds.py` | Write-back: CORTEX DB → ~/.agent/memory/ (DB es Source of Truth). |
| `GROUP` | **`agent`** | `agent_cmds` | `agent_cmds.py` | Declarative YAML agent interface for CORTEX. |
| `GROUP` | **`anomaly`** | `anomaly_cmds` | `anomaly_cmds.py` | 🔍 ANOMALY-HUNTER-DAEMON (NightShift Memory Refiner). |
| `GROUP` | **`apotheosis`** | `apotheosis_cmds` | `apotheosis_cmds.py` | The proactive manifestation and eradication engine of MOSKV-1. |
| `GROUP` | **`architect`** | `architect` | `architect_cmds.py` | Design Sovereign Prompts from raw requirements. |
| `GROUP` | **`audit`** | `audit` | `trust_cmds.py` | Run audits or view Audit Trail. |
| `GROUP` | **`auth`** | `auth` | `auth_cmds.py` | Manage BFT Consensus Quorum requests. |
| `GROUP` | **`autodidact`** | `autodidact_group` | `autodidact_cmds.py` | Autodidact Omega: Sovereign Thermodynamic Crystal Forge. |
| `GROUP` | **`autorouter`** | `autorouter_cmds` | `autorouter_cmds.py` | ⚡ AUTOROUTER-1 v3.0: Cognitive Switch Engine. |
| `GROUP` | **`bibliotecario`** | `bibliotecario_cmds` | `bibliotecario_cmds.py` | 📚 LIBRARIAN-1: Se encarga de ordenar y estructurar conocimiento. |
| `GROUP` | **`browser`** | `browser` | `browser_cmds.py` | BROWSER-Ω: Autonomous Sovereign Web Automation. |
| `GROUP` | **`chronos`** | `chronos_cmds` | `chronos_cmds.py` | CHRONOS-1 - Benchmark of Senior Human Time vs AI Swarm Time. |
| `GROUP` | **`compliance`** | `compliance` | `export_cmds.py` | Enterprise Compliance & Audit tools (EU AI Act, SOC2). |
| `GROUP` | **`context`** | `context` | `context_cmds.py` | Context Engine - ambient intelligence. |
| `GROUP` | **`darknet`** | `darknet_cmds` | `darknet_cmds.py` | Sovereign Darknet - Red Social de Agentes (Inversión de Dead-Internet). |
| `GROUP` | **`demiurge`** | `demiurge_group` | `demiurge_cmds.py` | Demiurge Omega: Sovereign JIT Skill Compiler. |
| `GROUP` | **`entropy`** | `entropy` | `entropy_cmds.py` | ENTROPY-0 v1.0 - El Guardián de la Deuda Técnica. |
| `GROUP` | **`episode`** | `episode` | `episodic_cmds.py` | Episodic Memory - persistent native memory. |
| `GROUP` | **`exergy`** | `exergy_cmds` | `exergy_cmds.py` | El motor de salud y auto-reparación de CORTEX. |
| `GROUP` | **`fingerprint`** | `fingerprint` | `fingerprint_cmds.py` | Cognitive Fingerprint - Extract your decision-making patterns. |
| `GROUP` | **`fiscal`** | `fiscal_group` | `fiscal_cmds.py` | Audit-ready commands for the fiscal beachhead. |
| `GROUP` | **`forensics`** | `forensics_cmds` | `forensics_cmds.py` | Local forensic evidence utilities. |
| `GROUP` | **`frontier`** | `frontier_cmds` | `frontier_cmds.py` | 🚀 Frontier: Sovereign Evolution & Metabolism. |
| `GROUP` | **`gateway`** | `gateway_cmds` | `gateway_cmds.py` | CORTEX gateway management commands. |
| `GROUP` | **`genesis`** | `genesis_group` | `genesis_cmds.py` | Genesis Engine - create systems from declarative specs. |
| `GROUP` | **`ghost`** | `ghost_cmds` | `ghost_cmds.py` | 👻 GHOST-1: OS Control & Songlines Architecture. |
| `GROUP` | **`github`** | `github_cmds` | `github_cmds.py` | GitHub ↔ CORTEX bridge - sync issues/PRs as facts. |
| `GROUP` | **`grammy`** | `grammy_cmds` | `grammy_cmds.py` | Grupo de comandos para GRAMMY-Ω. |
| `GROUP` | **`handoff`** | `handoff` | `handoff_cmds.py` | Session Handoff Protocol - compact session continuity. |
| `GROUP` | **`health`** | `health_group` | `health_cmds.py` | CORTEX Health Index - system health monitoring. |
| `GROUP` | **`honeypot`** | `honeypot_group` | `security_cmds.py` | Manage honeypot traps. |
| `GROUP` | **`immune`** | `immune_group` | `immune_cmds.py` | Immune system and epistemic membrane commands. |
| `GROUP` | **`keter`** | `keter_cmds` | `keter_cmds.py` | Invokes the fractal cascade to build ecosystems. |
| `GROUP` | **`launchpad`** | `launchpad` | `launchpad_cmds.py` | Orchestrate AI Swarm missions via CORTEX Launchpad. |
| `GROUP` | **`ledger`** | `ledger_cmds` | `ledger.py` | Sovereign Ledger Operations (Wave 6: High-Performance Chaining). |
| `GROUP` | **`ledger`** | `ledger` | `vote_ledger.py` | Administrar el registro inmutable de votos. |
| `GROUP` | **`lineage`** | `lineage_group` | `lineage_cmds.py` | Epistemic lineage (Ω₃-V) commands. |
| `GROUP` | **`maestro`** | `maestro` | `maestro_cmds.py` | MAC-Ω: Automatización soberana de escritorio (AppleScript/Native). |
| `GROUP` | **`mcp`** | `mcp_cmds` | `mcp_cmds.py` | Model Context Protocol (MCP) integrations. |
| `GROUP` | **`mcts`** | `mcts_cmds` | `mcts_cmds.py` | CORTEX Chronos (Git-MCTS) - Búsqueda de Mutaciones Asintóticas. |
| `GROUP` | **`mejoralo`** | `mejoralo` | `mejoralo_cmds.py` | MEJORAlo v8.0 - Protocolo de auditoría y mejora de código. Modo Relentless. |
| `GROUP` | **`memory`** | `memory_cmds` | `memory_cmds.py` | CORTEX memory management commands. |
| `GROUP` | **`moskv-aegis`** | `moskv_aegis` | `moskv_aegis_cmds.py` | 🛡️ Moskv-Aegis - Adversarial Ledger & Verification Engine. |
| `GROUP` | **`nexus`** | `nexus_cmds` | `nexus_cmds.py` | 🌌 Singularity Nexus v∞: Cross-Project Unification. |
| `GROUP` | **`niche`** | `niche_cmds` | `niche_cmds.py` | Domain intelligence and market anomaly arbitrage. |
| `GROUP` | **`notebooklm`** | `notebooklm_cmds` | `notebooklm_cmds.py` | 📓 NotebookLM synchronization commands. |
| `GROUP` | **`nous`** | `nous` | `nous_cmds.py` | NOUS Database Migrator and AST Compiler. |
| `GROUP` | **`omega`** | `omega_cmds` | `omega_cmds.py` | Mega Hito 38: Omega Singularity (CORTEX v10.0 Metabolism). |
| `GROUP` | **`pipeline`** | `pipeline_group` | `pipeline_cmds.py` | Pipeline management commands. |
| `GROUP` | **`policy`** | `policy_cmds` | `policy_cmds.py` | 🎯 Bellman Policy Engine - Prioritized action queue. |
| `GROUP` | **`prompt`** | `prompt` | `prompt_cmds.py` | System prompt management - generate, show, copy. |
| `GROUP` | **`purge`** | `purge` | `purge.py` | Purge garbage facts from CORTEX. |
| `GROUP` | **`quota-cli`** | `quota_cli` | `quota_cmds.py` | Métricas y estrangulamiento de la cuota Antigravity (PULMONES). |
| `GROUP` | **`radar`** | `radar_cmds` | `radar_cmds.py` | 📡 RADAR-Ω: Sovereign monitoring and architectural enforcement. |
| `GROUP` | **`roi`** | `roi` | `roi_cmds.py` | 📊 ROI & Efficiency Quantification (CHRONOS-1). |
| `GROUP` | **`routing`** | `routing` | `routing_cmds.py` | LLM routing - tier/cost-aware provider selection. |
| `GROUP` | **`scraper`** | `scraper` | `scraper_cmds.py` | SCRAPER-Ω: Sovereign Web Extraction Engine. |
| `GROUP` | **`security`** | `security_cli` | `security_cmds.py` | CORTEX Security Shield commands. |
| `GROUP` | **`signal`** | `signal_cmds` | `signal_cmds.py` | Signal Bus - L1 consciousness for cross-tool communication. |
| `GROUP` | **`snapshot`** | `timeline_snapshot` | `timeline_cmds.py` | Manage physical database snapshots. |
| `GROUP` | **`sovereign`** | `sovereign_cmds` | `keter_cmds.py` | Direct access to the MOSKV-1 sovereign engine. |
| `GROUP` | **`swarm`** | `swarm` | `swarm_cmds.py` | SOVEREIGN SWARM - Orchestration of specialized agents (130/100). |
| `GROUP` | **`swarm-10k`** | `swarm_10k` | `swarm_10k_cmds.py` | SOVEREIGN SWARM 10K - Hierarchical Orchestration (L0 -> L2). |
| `GROUP` | **`timeline`** | `timeline` | `timeline_cmds.py` | Navigate the CORTEX timeline and manage snapshots. |
| `GROUP` | **`tips`** | `tips` | `tips_cmds.py` | 💡 TIPS - Contextual tips and insights from CORTEX. |
| `GROUP` | **`wealth`** | `wealth_cmds` | `wealth_cmds.py` | 💰 Sovereign Wealth Engine (moneytv-1 + sovereign-growth-engine-v1). |
| `GROUP` | **`worker`** | `worker_group` | `worker_cmds.py` | Manage background workers (Enrichment, etc). |


## 🔱 Swarm Nodes Mapping (LEGION-93)

Scanned **94** defined agent identities matching the LEGION-93 swarm topology.

| ID Nodo | Identidad Cognitiva | Exergy | Realidad | Intent | Payload Model |
|:---|:---|:---|:---|:---|:---|
| :--- | :--- | :---: | :---: | :--- | :--- |
| **demiurge** | DEMIURGE-Ω | P0 | C5-REAL | `architect` | `gemini-3.1-pro-preview` |
| **ada** | ADA-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **aegis** | AEGIS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **antigravity** | ANTIGRAVITY-Ω | P1 | C5-REAL | `architect` | `gemini-2.5-pro` |
| **apis_omega** | APIS-Ω | P1 | C5-REAL | `reasoning` | `gemini-3.1-pro-preview` |
| **apollo** | APOLLO-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **arachne** | ARACHNE-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **ares** | ARES-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **argos** | ARGOS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **ariadne** | ARIADNE-Ω | P1 | C5-REAL | `architect` | `gemini-2.5-pro` |
| **asklepios** | ASKLEPIOS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **athena** | ATHENA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **atlas** | ATLAS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **auditor** | AUDITOR-Ω | P1 | C5-REAL | `reasoning` | `gemini-3.1-pro` |
| **auditor_omega** | Sovereign Auditor & Git Expert | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **aura** | AURA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **autonomo** | AUTONOMO-Ω | P1 | C5-REAL | `reasoning` | `qwen2.5-coder:32b` |
| **babel** | BABEL-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **bessemer** | BESSEMER-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **boltzmann** | BOLTZMANN-Ω | P1 | C5-REAL | `reasoning` | `gemini-3.1-pro-preview` |
| **calliope** | CALLIOPE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **carnot** | CARNOT-Ω | P1 | C5-REAL | `code` | `gemini-3.1-pro-preview` |
| **cerberus** | CERBERUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **ceres** | CERES-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **chronos** | CHRONOS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **curie** | CURIE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **da_vinci** | DA_VINCI-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **daedalus** | DAEDALUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **demeter** | DEMETER-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **diablo** | DIABLO-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **dinero** | DINERO-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **enigma** | ENIGMA-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **erdos** | ERDŐS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **euclid** | EUCLID-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **exergia** | EXERGIA-Ω | P1 | C5-REAL | `architect` | `gemini-2.5-pro` |
| **fourier** | FOURIER-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **gaia** | GAIA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **galileo** | GALILEO-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **grammy_electronic** | GRAMMY-Ω | P1 | C5-REAL | `reasoning` | `llama-3.3-70b-versatile` |
| **hades** | HADES-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **helix** | HELIX-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **hephaestus** | HEPHAESTUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **hermes** | HERMES-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **holmes** | HOLMES-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **homer** | HOMER-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **hydra** | HYDRA-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **icarus** | ICARUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **janus** | JANUS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **lavoisier** | LAVOISIER-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **loki** | LOKI-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **lorca** | LORCA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **lumiere** | LUMIERE-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **lynx** | LYNX-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **maxwell** | MAXWELL-Ω | P1 | C5-REAL | `reasoning` | `gemini-3.1-pro-preview` |
| **mejoralo_omega** | MEJORALO-Ω | P1 | C5-REAL | `code` | `qwen2.5-coder:32b` |
| **mentor** | MENTOR-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **mercator** | MERCATOR-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **mercury** | MERCURY-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **minerva** | MINERVA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **mnemosyne** | MNEMOSYNE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **morpheus** | MORPHEUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **moskv_videntia** | MOSKV-VIDENTIA | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **nash** | NASHΩ | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **nemo** | NEMO-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **nobel** | NOBEL-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **notebooklm** | NOTEBOOKLM-Ω | P1 | C5-REAL | `synthesis` | `gemini-2.5-pro` |
| **nyx** | NYX-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **oracle** | ORACLE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **orion** | ORION-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **pandora** | PANDORA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **pasteur** | PASTEUR-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **poseidon** | POSEIDON-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **prometheus** | PROMETHEUS-Ω | P1 | C5-REAL | `code` | `gemini-3.1-pro-preview` |
| **proteus** | PROTEUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **psyche** | PSYCHE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **qubit** | QUBIT-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **satoshi** | SATOSHI-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **scout** | SCOUT-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **simula** | SIMULA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **sisyphus** | SISYPHUS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **socrates** | SOCRATES-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **sphinx** | SPHINX-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **talos** | TALOS-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **tesla** | TESLA-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **tesseract** | TESSERACT-Ω | P1 | C5-REAL | `architect` | `gemini-2.5-pro` |
| **themis** | THEMIS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **turing** | TURING-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **tyche** | TYCHE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **valkyrie** | VALKYRIE-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **vitruvius** | VITRUVIUS-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **vulcan** | VULCAN-Ω | P1 | C5-REAL | `code` | `gemini-2.5-pro` |
| **wright** | WRIGHT-Ω | P1 | C5-REAL | `reasoning` | `gemini-2.5-pro` |
| **zeus** | ZEUS-Ω | P1 | C5-REAL | `architect` | `gemini-2.5-pro` |


## 📦 Package Dependency & Coupling Map

Analyzed **1702** Python files in `babylon60/` and `cortex/`.

| Package Name | Import Count | Coupling Density |
|:---|:---|:---|
| `aiosqlite` | 93 files | **5.5%** |
| `click` | 93 files | **5.5%** |
| `fastapi` | 54 files | **3.2%** |
| `httpx` | 48 files | **2.8%** |
| `mcp` | 15 files | **0.9%** |
| `onnxruntime` | 1 files | **0.1%** |
| `pydantic` | 63 files | **3.7%** |
| `rich` | 94 files | **5.5%** |
| `sentence_transformers` | 3 files | **0.2%** |
| `sqlite_vec` | 7 files | **0.4%** |
| `starlette` | 9 files | **0.5%** |
| `uvicorn` | 4 files | **0.2%** |

### Detailed Package Import Mappings

#### `aiosqlite` imports (93 files)
- `babylon60/audit/ledger.py`
- `babylon60/audit/ledger_compactor.py`
- `babylon60/auth/backends.py`
- `babylon60/cli/doctor_cmds.py`
- `babylon60/cli/ledger.py`
- `babylon60/compaction/compactor.py`
- `babylon60/compliance/eu_ai_act.py`
- `babylon60/crypto/shredder.py`
- `babylon60/database/core.py`
- `babylon60/database/mixins/ghost_mixin.py`
- `babylon60/database/mixins/privacy_mixin.py`
- `babylon60/database/mixins/transaction_mixin.py`
- `babylon60/database/pool.py`
- `babylon60/engine/causal/graph.py`
- `babylon60/engine/causal/oracle.py`
- *...and 78 more files*

#### `click` imports (93 files)
- `babylon60/cli/agent_cmds.py`
- `babylon60/cli/anomaly_cmds.py`
- `babylon60/cli/apoptosis.py`
- `babylon60/cli/apotheosis_cmds.py`
- `babylon60/cli/architect_cmds.py`
- `babylon60/cli/audit_cmds.py`
- `babylon60/cli/auth_cmds.py`
- `babylon60/cli/autodidact_cmds.py`
- `babylon60/cli/autorouter_cmds.py`
- `babylon60/cli/bibliotecario_cmds.py`
- `babylon60/cli/browser_cmds.py`
- `babylon60/cli/causal_cmds.py`
- `babylon60/cli/chronos_cmds.py`
- `babylon60/cli/commands/josu_start.py`
- `babylon60/cli/common.py`
- *...and 78 more files*

#### `fastapi` imports (54 files)
- `babylon60/api/__init__.py`
- `babylon60/api/analysis.py`
- `babylon60/api/audit.py`
- `babylon60/api/core.py`
- `babylon60/api/deps.py`
- `babylon60/api/events.py`
- `babylon60/api/fsm_streamer.py`
- `babylon60/api/middleware.py`
- `babylon60/auth/deps.py`
- `babylon60/cli/relay_daemon.py`
- `babylon60/cli/relay_server.py`
- `babylon60/extensions/daemon/ccr_proxy.py`
- `babylon60/extensions/hive/main.py`
- `babylon60/extensions/kapso/webhook.py`
- `babylon60/extensions/metering/middleware.py`
- *...and 39 more files*

#### `httpx` imports (48 files)
- `babylon60/api/async_client.py`
- `babylon60/api/client.py`
- `babylon60/audit/ledger.py`
- `babylon60/audit/rekor_client.py`
- `babylon60/audit/tsa_client.py`
- `babylon60/embeddings/api_embedder.py`
- `babylon60/engine/cognitive/synthesis.py`
- `babylon60/extensions/aether/github_ingestor.py`
- `babylon60/extensions/aether/sovereign_apis.py`
- `babylon60/extensions/aether/tools.py`
- `babylon60/extensions/agents/apis_omega.py`
- `babylon60/extensions/daemon/ccr_proxy.py`
- `babylon60/extensions/daemon/monitors/dependency_health.py`
- `babylon60/extensions/daemon/monitors/network.py`
- `babylon60/extensions/daemon/t_cell_ihelp_purge.py`
- *...and 33 more files*

#### `mcp` imports (15 files)
- `babylon60/extensions/mcp/server.py`
- `babylon60/forensics/claude_mcp_fuzzer.py`
- `babylon60/integration/rustchain/mcp_tool.py`
- `babylon60/mcp_server/aether_server.py`
- `babylon60/mcp_server/apollo_tools.py`
- `babylon60/mcp_server/genesis_tools.py`
- `babylon60/mcp_server/maestro_tools.py`
- `babylon60/mcp_server/mega_tools.py`
- `babylon60/mcp_server/music_tools.py`
- `babylon60/mcp_server/resilient_gateway.py`
- `babylon60/mcp_server/server.py`
- `babylon60/mcp_server/singularity_tools.py`
- `babylon60/mcp_server/trust_compliance.py`
- `babylon60/mcp_server/trust_tools.py`
- `babylon60/pipeline/mcp_outbound.py`

#### `onnxruntime` imports (1 files)
- `babylon60/embeddings/rust_bridge.py`

#### `pydantic` imports (63 files)
- `babylon60/agents/contracts.py`
- `babylon60/agents/copilot_cache.py`
- `babylon60/agents/copilot_context.py`
- `babylon60/agents/copilot_contracts.py`
- `babylon60/agents/message_schema.py`
- `babylon60/agents/schema.py`
- `babylon60/api/analysis.py`
- `babylon60/engine/causal/pydantic_schemas.py`
- `babylon60/engine/causal/schema_validator.py`
- `babylon60/engine/membrane/models.py`
- `babylon60/engine/membrane/sanitizer.py`
- `babylon60/engine/meta/metacognition.py`
- `babylon60/extensions/agents/tools/autodidact_tool.py`
- `babylon60/extensions/agents/tools/crystallization_tool.py`
- `babylon60/extensions/agents/tools/hypothesis_tool.py`
- *...and 48 more files*

#### `rich` imports (94 files)
- `babylon60/cli/agent_cmds.py`
- `babylon60/cli/aix.py`
- `babylon60/cli/anomaly_cmds.py`
- `babylon60/cli/apoptosis.py`
- `babylon60/cli/apotheosis_cmds.py`
- `babylon60/cli/architect_cmds.py`
- `babylon60/cli/audit_helpers.py`
- `babylon60/cli/auth_cmds.py`
- `babylon60/cli/autodidact_cmds.py`
- `babylon60/cli/autorouter_cmds.py`
- `babylon60/cli/bibliotecario_cmds.py`
- `babylon60/cli/bicameral.py`
- `babylon60/cli/browser_cmds.py`
- `babylon60/cli/causal_cmds.py`
- `babylon60/cli/chronos_cmds.py`
- *...and 79 more files*

#### `sentence_transformers` imports (3 files)
- `babylon60/embeddings/local.py`
- `babylon60/guards/prompt_security_guard.py`
- `babylon60/search/reranker.py`

#### `sqlite_vec` imports (7 files)
- `babylon60/database/core.py`
- `babylon60/engine/core/_engine_connection.py`
- `babylon60/extensions/artist_cortex/artist_cortex.py`
- `babylon60/extensions/daemon/monitors/drift.py`
- `babylon60/memory/hdc/store.py`
- `babylon60/memory/sqlite_vec_store.py`
- `babylon60/memory/traits/schema.py`

#### `starlette` imports (9 files)
- `babylon60/api/middleware.py`
- `babylon60/extensions/metering/middleware.py`
- `babylon60/routes/admin.py`
- `babylon60/routes/agents.py`
- `babylon60/routes/facts.py`
- `babylon60/routes/graph.py`
- `babylon60/routes/middleware.py`
- `babylon60/routes/swarm.py`
- `babylon60/routes/timing.py`

#### `uvicorn` imports (4 files)
- `babylon60/cli/relay_daemon.py`
- `babylon60/cli/relay_server.py`
- `babylon60/extensions/daemon/ccr_proxy.py`
- `babylon60/swarm/inference_proxy.py`
