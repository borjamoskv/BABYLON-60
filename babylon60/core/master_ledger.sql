-- C5-REAL BFT Master Ledger Init
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ledger_entries (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    stream TEXT NOT NULL CHECK (length(stream) > 0),
    entity_id TEXT NOT NULL CHECK (length(entity_id) > 0),
    event_type TEXT NOT NULL CHECK (length(event_type) > 0),
    payload_json TEXT NOT NULL CHECK (length(payload_json) >= 2),
    source_db TEXT NOT NULL CHECK (length(source_db) > 0),
    source_table TEXT NOT NULL CHECK (length(source_table) > 0),
    source_pk TEXT NOT NULL CHECK (length(source_pk) > 0),
    cortex_taint TEXT NOT NULL CHECK (length(cortex_taint) > 0),
    lamport_t INTEGER NOT NULL UNIQUE CHECK (lamport_t > 0),
    prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 64 AND prev_hash GLOB '[0-9a-f]*'),
    entry_hash TEXT NOT NULL UNIQUE CHECK (length(entry_hash) = 64 AND entry_hash GLOB '[0-9a-f]*'),
    created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_update BEFORE UPDATE ON ledger_entries
BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;

CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_delete BEFORE DELETE ON ledger_entries
BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;
