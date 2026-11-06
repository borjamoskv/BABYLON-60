-- Explicit init-only migration: multiple independent facts may precede one effect.
-- Preserve every original fact byte and tick; never run during approval.
BEGIN IMMEDIATE;
-- Temporarily disable schema rewriting for this name-preserving table rebuild.
PRAGMA legacy_alter_table = ON;
CREATE TABLE l0_anchored_facts_migrating (
    fact_hash BLOB PRIMARY KEY CHECK(length(fact_hash) = 32),
    anchored_tick INTEGER NOT NULL CHECK(anchored_tick >= 0),
    domain_tag INTEGER NOT NULL CHECK(domain_tag >= 0),
    payload_hash BLOB NOT NULL CHECK(length(payload_hash) = 32)
) STRICT, WITHOUT ROWID;
INSERT INTO l0_anchored_facts_migrating SELECT * FROM l0_anchored_facts;
DROP TABLE l0_anchored_facts;
ALTER TABLE l0_anchored_facts_migrating RENAME TO l0_anchored_facts;
PRAGMA legacy_alter_table = OFF;
CREATE TRIGGER trg_facts_forbid_update BEFORE UPDATE ON l0_anchored_facts
BEGIN SELECT RAISE(ABORT, '0xDEAD6060: L0_FACTS_IMMUTABLE_UPDATE_FORBIDDEN'); END;
CREATE TRIGGER trg_facts_forbid_delete BEFORE DELETE ON l0_anchored_facts
BEGIN SELECT RAISE(ABORT, '0xDEAD6060: L0_FACTS_IMMUTABLE_DELETE_FORBIDDEN'); END;
COMMIT;
