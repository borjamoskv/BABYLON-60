// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! VECTOR A.2: Master Ledger & ATMS Hardening
//!
//! Elevates the append-only ledger into a verifiable Causal Hash Chain.
//! Acts as a Transactional Local Ledger (SQLite WAL mode), reconstructing 
//! the ATMS in-memory state via deterministic replay.

use crate::omega0::{JustifiedStatement, Statement, Justification};
use rusqlite::{params, Connection, Result};
use std::time::Duration;
use uuid::Uuid;
use std::collections::{HashSet, HashMap, VecDeque};

const UUID_V5_NAMESPACE: Uuid = Uuid::from_bytes([
    0x1a, 0x51, 0x69, 0x88, 0x9d, 0xea, 0x7d, 0xb1,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
]);

pub struct MasterLedger {
    pub(crate) conn: Connection,
}

#[derive(Debug, Clone, PartialEq)]
pub struct AtmsState {
    pub environments: HashMap<String, HashSet<String>>, // environment_id -> set(statement_hashes)
    pub nogoods: HashSet<String>, // statement_hashes that form contradictions
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BftCollisionError {
    pub kind: &'static str,
    pub hash: String,
    pub existing_content: String,
    pub incoming_content: String,
}

impl std::fmt::Display for BftCollisionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Fail-fast: INV_BFT_04 Collision for {} {} (mismatched content)",
            self.kind, self.hash
        )
    }
}

impl std::error::Error for BftCollisionError {}

impl MasterLedger {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        
        conn.pragma_update(None, "journal_mode", "WAL")?;
        conn.pragma_update(None, "synchronous", "FULL")?;
        conn.pragma_update(None, "foreign_keys", "ON")?;
        conn.busy_timeout(Duration::from_millis(5000))?;

        let mut ledger = Self { conn };
        ledger.initialize_schema()?;
        Ok(ledger)
    }

    fn initialize_schema(&mut self) -> Result<()> {
        let tx = self.conn.transaction()?;

        tx.execute(
            "CREATE TABLE IF NOT EXISTS statements (
                statement_hash TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                modality TEXT NOT NULL,
                obligations_json TEXT NOT NULL DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;

        tx.execute(
            "CREATE TABLE IF NOT EXISTS justifications (
                justification_hash TEXT PRIMARY KEY,
                variant TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )",
            [],
        )?;

        // Replaced ledger_assertions with Causal Hash Chain constraints
        tx.execute(
            "CREATE TABLE IF NOT EXISTS ledger_assertions (
                id TEXT PRIMARY KEY,
                statement_hash TEXT NOT NULL REFERENCES statements(statement_hash),
                justification_hash TEXT NOT NULL REFERENCES justifications(justification_hash),
                environment_id TEXT NOT NULL,
                lamport_t INTEGER NOT NULL,
                prev_hash TEXT NOT NULL,
                cortex_taint TEXT NOT NULL,
                UNIQUE(lamport_t, environment_id)
            )",
            [],
        )?;

        // Replaced atms_nogoods with append-only causal log
        tx.execute(
            "CREATE TABLE IF NOT EXISTS atms_nogoods_log (
                nogood_hash TEXT PRIMARY KEY,
                environment_id TEXT NOT NULL,
                lamport_t INTEGER NOT NULL,
                prev_hash TEXT NOT NULL,
                cortex_taint TEXT NOT NULL
            )",
            [],
        )?;

        // Causal derivation DAG edges for transitive revocation closure (FL-M01 / B4)
        tx.execute(
            "CREATE TABLE IF NOT EXISTS justification_edges (
                parent_statement_hash TEXT NOT NULL,
                child_statement_hash TEXT NOT NULL REFERENCES statements(statement_hash),
                environment_id TEXT NOT NULL,
                PRIMARY KEY (parent_statement_hash, child_statement_hash, environment_id)
            )",
            [],
        )?;

        tx.commit()
    }

    fn get_latest_assertion(&self, environment_id: &str) -> Result<(i64, String)> {
        let mut stmt = self.conn.prepare(
            "SELECT lamport_t, cortex_taint FROM ledger_assertions WHERE environment_id = ?1 ORDER BY lamport_t DESC LIMIT 1"
        )?;
        let row = stmt.query_row(params![environment_id], |row| {
            Ok((row.get(0)?, row.get(1)?))
        });

        match row {
            Ok(res) => Ok(res),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok((0, "GENESIS".to_string())),
            Err(e) => Err(e),
        }
    }

    pub fn get_latest_justification_json(&self) -> Result<String> {
        let mut stmt = self.conn.prepare(
            "SELECT j.payload_json FROM ledger_assertions a JOIN justifications j ON a.justification_hash = j.justification_hash ORDER BY a.lamport_t DESC LIMIT 1"
        )?;
        stmt.query_row([], |row| row.get(0))
    }

    pub fn hash_statement(s: &Statement) -> String {
        crate::omega0::hash_statement(s)
    }

    fn hash_justification(_j: &Justification, payload_json: &str) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(payload_json.as_bytes());
        format!("JUST:{}", hasher.finalize().to_hex())
    }

    fn compute_cortex_taint(prev_hash: &str, statement_hash: &str, justification_hash: &str, environment_id: &str, lamport_t: i64) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(prev_hash.as_bytes());
        hasher.update(statement_hash.as_bytes());
        hasher.update(justification_hash.as_bytes());
        hasher.update(environment_id.as_bytes());
        hasher.update(&lamport_t.to_be_bytes());
        format!("TAINT:C5_REAL_RUST:{}", hasher.finalize().to_hex())
    }

    pub fn assert_knowledge(
        &mut self,
        js: &JustifiedStatement,
        environment_id: &str,
    ) -> Result<String> {
        let statement_hash = Self::hash_statement(&js.statement);
        let payload_json = serde_json::to_string(&js.justification)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;
        let justification_hash = Self::hash_justification(&js.justification, &payload_json);
        
        let assertion_seed = format!("{}:{}:{}", statement_hash, justification_hash, environment_id);
        let id = Uuid::new_v5(&UUID_V5_NAMESPACE, assertion_seed.as_bytes()).to_string();

        let exists: bool = self.conn.query_row(
            "SELECT EXISTS(SELECT 1 FROM ledger_assertions WHERE id = ?1)",
            params![id],
            |row| row.get(0),
        )?;

        if exists {
            return Ok(id);
        }

        let (prev_t, prev_hash) = self.get_latest_assertion(environment_id)?;
        let lamport_t = prev_t + 1;
        let cortex_taint = Self::compute_cortex_taint(&prev_hash, &statement_hash, &justification_hash, environment_id, lamport_t);

        let tx = self.conn.transaction()?;

        let obligations_json = serde_json::to_string(&js.statement.obligations)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;
        let stmt_res = tx.execute(
            "INSERT INTO statements (statement_hash, content, modality, obligations_json) VALUES (?1, ?2, ?3, ?4)",
            params![
                statement_hash,
                js.statement.content,
                js.statement.modality.canonical_tag(),
                obligations_json
            ],
        );
        if let Err(e) = stmt_res {
            let existing_opt: rusqlite::Result<String> = tx.query_row(
                "SELECT content FROM statements WHERE statement_hash = ?1",
                params![statement_hash],
                |row| row.get(0),
            );
            if let Ok(existing) = existing_opt {
                if existing != js.statement.content {
                    return Err(rusqlite::Error::ToSqlConversionFailure(Box::new(BftCollisionError {
                        kind: "statement_hash",
                        hash: statement_hash,
                        existing_content: existing,
                        incoming_content: js.statement.content.clone(),
                    })));
                }
            } else {
                return Err(e);
            }
        }

        let variant = match &js.justification {
            Justification::FormalProof{..} => "FormalProof",
            Justification::StatisticalInference{..} => "StatisticalInference",
            Justification::Observation{..} => "Observation",
            Justification::ExogenousInjection{..} => "ExogenousInjection",
            Justification::ExpertConsensus{..} => "ExpertConsensus",
            Justification::Citation{..} => "Citation",
            Justification::Conjecture => "Conjecture",
            Justification::Axiom{..} => "Axiom",
        };

        let just_res = tx.execute(
            "INSERT INTO justifications (justification_hash, variant, payload_json) VALUES (?1, ?2, ?3)",
            params![justification_hash, variant, payload_json],
        );
        if let Err(e) = just_res {
            let existing_opt: rusqlite::Result<String> = tx.query_row(
                "SELECT payload_json FROM justifications WHERE justification_hash = ?1",
                params![justification_hash],
                |row| row.get(0),
            );
            if let Ok(existing) = existing_opt {
                if existing != *payload_json {
                    return Err(rusqlite::Error::ToSqlConversionFailure(Box::new(BftCollisionError {
                        kind: "justification_hash",
                        hash: justification_hash,
                        existing_content: existing,
                        incoming_content: payload_json.clone(),
                    })));
                }
            } else {
                return Err(e);
            }
        }

        tx.execute(
            "INSERT INTO ledger_assertions (id, statement_hash, justification_hash, environment_id, lamport_t, prev_hash, cortex_taint) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![id, statement_hash, justification_hash, environment_id, lamport_t, prev_hash, cortex_taint],
        )?;

        if let Justification::FormalProof { premises, .. } = &js.justification {
            for premise_ref in premises {
                let parent_hash = if premise_ref.starts_with("STMT:") {
                    premise_ref.clone()
                } else {
                    let existing_hash: rusqlite::Result<String> = tx.query_row(
                        "SELECT statement_hash FROM statements WHERE content = ?1 LIMIT 1",
                        params![premise_ref],
                        |row| row.get(0),
                    );
                    existing_hash.unwrap_or_else(|_| {
                        Self::hash_statement(&Statement {
                            content: premise_ref.clone(),
                            modality: js.statement.modality,
                            obligations: Vec::new(),
                        })
                    })
                };
                tx.execute(
                    "INSERT OR IGNORE INTO justification_edges (parent_statement_hash, child_statement_hash, environment_id)
                     VALUES (?1, ?2, ?3)",
                    params![parent_hash, statement_hash, environment_id],
                )?;
            }
        }

        tx.commit()?;
        Ok(id)
    }

    /// Asserts a derived statement while explicitly recording causal parent statement hashes.
    pub fn assert_derived_knowledge(
        &mut self,
        js: &JustifiedStatement,
        parent_statement_hashes: &[String],
        environment_id: &str,
    ) -> Result<String> {
        let id = self.assert_knowledge(js, environment_id)?;
        let child_hash = Self::hash_statement(&js.statement);
        let tx = self.conn.transaction()?;
        for parent_hash in parent_statement_hashes {
            tx.execute(
                "INSERT OR IGNORE INTO justification_edges (parent_statement_hash, child_statement_hash, environment_id)
                 VALUES (?1, ?2, ?3)",
                params![parent_hash, child_hash, environment_id],
            )?;
        }
        tx.commit()?;
        Ok(id)
    }

    pub fn assert_nogood(&mut self, statement_hash: &str, environment_id: &str) -> Result<String> {
        let (prev_t, prev_hash) = self.get_latest_assertion(environment_id)?;
        let lamport_t = prev_t + 1;
        
        let mut hasher = blake3::Hasher::new();
        hasher.update(prev_hash.as_bytes());
        hasher.update(statement_hash.as_bytes());
        hasher.update(environment_id.as_bytes());
        hasher.update(&lamport_t.to_be_bytes());
        let cortex_taint = format!("TAINT:C5_REAL_RUST:NOGOOD:{}", hasher.finalize().to_hex());

        self.conn.execute(
            "INSERT INTO atms_nogoods_log (nogood_hash, environment_id, lamport_t, prev_hash, cortex_taint) 
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![statement_hash, environment_id, lamport_t, prev_hash, cortex_taint],
        )?;
        Ok(cortex_taint)
    }

    /// Verifies the entire ledger causal chain from genesis. If tampered, aborts process (SIGKILL equivalent).
    pub fn verify_chain(&self, environment_id: &str) -> Result<bool> {
        let mut stmt = self.conn.prepare(
            "SELECT statement_hash, justification_hash, lamport_t, prev_hash, cortex_taint 
             FROM ledger_assertions 
             WHERE environment_id = ?1 
             ORDER BY lamport_t ASC"
        )?;

        let mut rows = stmt.query(params![environment_id])?;
        let mut expected_prev_hash = "GENESIS".to_string();
        let mut assertion_anchors = HashMap::from([(0_i64, "GENESIS".to_string())]);

        while let Some(row) = rows.next()? {
            let s_hash: String = row.get(0)?;
            let j_hash: String = row.get(1)?;
            let t: i64 = row.get(2)?;
            let prev: String = row.get(3)?;
            let taint: String = row.get(4)?;

            if prev != expected_prev_hash {
                std::process::abort(); // Fail-fast purge on chain split
            }

            let computed = Self::compute_cortex_taint(&prev, &s_hash, &j_hash, environment_id, t);
            if computed != taint {
                std::process::abort(); // Fail-fast purge on manipulation
            }

            assertion_anchors.insert(t, taint.clone());
            expected_prev_hash = taint;
        }

        // Nogoods reference the most recent assertion, not the preceding nogood.
        let mut nogoods = self.conn.prepare(
            "SELECT nogood_hash, lamport_t, prev_hash, cortex_taint FROM atms_nogoods_log WHERE environment_id = ?1"
        )?;
        let mut rows = nogoods.query(params![environment_id])?;
        while let Some(row) = rows.next()? {
            let hash: String = row.get(0)?;
            let tick: i64 = row.get(1)?;
            let previous: String = row.get(2)?;
            let stored: String = row.get(3)?;
            let anchor = tick.checked_sub(1).and_then(|t| assertion_anchors.get(&t));
            let mut hasher = blake3::Hasher::new();
            hasher.update(previous.as_bytes());
            hasher.update(hash.as_bytes());
            hasher.update(environment_id.as_bytes());
            hasher.update(&tick.to_be_bytes());
            let computed = format!("TAINT:C5_REAL_RUST:NOGOOD:{}", hasher.finalize().to_hex());
            if anchor != Some(&previous) || stored != computed {
                return Err(rusqlite::Error::SqliteFailure(
                    rusqlite::ffi::Error::new(rusqlite::ffi::SQLITE_CORRUPT),
                    Some("Invalid nogood causal hash or assertion anchor".to_string()),
                ));
            }
        }
        Ok(true)
    }

    /// Reconstructs the ATMS state purely from the causal event log.
    pub fn replay_to_atms_state(&self) -> Result<AtmsState> {
        // Pin verification and replay to one SQLite snapshot. This read-only
        // transaction rolls back on drop, including all validation failures.
        let _snapshot = self.conn.unchecked_transaction()?;
        let environments = {
            let mut stmt = self.conn.prepare(
                "SELECT environment_id FROM ledger_assertions UNION SELECT environment_id FROM atms_nogoods_log"
            )?;
            let rows = stmt.query_map([], |row| row.get::<_, String>(0))?;
            rows.collect::<Result<Vec<_>>>()?
        };
        for environment in environments {
            self.verify_chain(&environment)?;
        }
        let mut state = AtmsState {
            environments: HashMap::new(),
            nogoods: HashSet::new(),
        };

        // Replay Assertions
        let mut stmt = self.conn.prepare(
            "SELECT environment_id, statement_hash FROM ledger_assertions ORDER BY lamport_t ASC"
        )?;
        let mut rows = stmt.query([])?;
        while let Some(row) = rows.next()? {
            let env: String = row.get(0)?;
            let stmt_hash: String = row.get(1)?;
            state.environments.entry(env).or_default().insert(stmt_hash);
        }

        // Replay Nogoods
        let mut stmt2 = self.conn.prepare(
            "SELECT nogood_hash FROM atms_nogoods_log ORDER BY lamport_t ASC"
        )?;
        let mut rows2 = stmt2.query([])?;
        while let Some(row) = rows2.next()? {
            let ng_hash: String = row.get(0)?;
            state.nogoods.insert(ng_hash);
        }

        // Transitive Revocation Closure (FL-M01 / B4): propagate nogoods along justification_edges
        let mut adjacency: HashMap<String, Vec<String>> = HashMap::new();
        let mut stmt3 = self.conn.prepare(
            "SELECT parent_statement_hash, child_statement_hash FROM justification_edges"
        )?;
        let mut rows3 = stmt3.query([])?;
        while let Some(row) = rows3.next()? {
            let parent_hash: String = row.get(0)?;
            let child_hash: String = row.get(1)?;
            adjacency.entry(parent_hash).or_default().push(child_hash);
        }

        let mut queue: VecDeque<String> = state.nogoods.iter().cloned().collect();
        while let Some(curr) = queue.pop_front() {
            if let Some(children) = adjacency.get(&curr) {
                for child in children {
                    if state.nogoods.insert(child.clone()) {
                        queue.push_back(child.clone());
                    }
                }
            }
        }

        Ok(state)
    }

    /// Returns the transitive revocation closure (root + all downstream derived statements)
    /// for a given statement hash within an environment.
    pub fn get_revocation_closure(
        &self,
        root_statement_hash: &str,
        environment_id: &str,
    ) -> Result<HashSet<String>> {
        let mut stmt = self.conn.prepare(
            "WITH RECURSIVE closure(hash) AS (
                SELECT ?1
                UNION
                SELECT e.child_statement_hash
                FROM justification_edges e
                JOIN closure c ON e.parent_statement_hash = c.hash
                WHERE e.environment_id = ?2
            )
            SELECT hash FROM closure"
        )?;
        let mut rows = stmt.query(params![root_statement_hash, environment_id])?;
        let mut closure = HashSet::new();
        while let Some(row) = rows.next()? {
            let h: String = row.get(0)?;
            closure.insert(h);
        }
        Ok(closure)
    }

    pub fn get_statement(&self, hash: &str) -> Result<Statement> {
        let mut stmt = self.conn.prepare(
            "SELECT content, modality, obligations_json FROM statements WHERE statement_hash = ?1"
        )?;
        stmt.query_row(params![hash], |row| {
            let content: String = row.get(0)?;
            let modality_str: String = row.get(1)?;
            let modality = if modality_str == "Epistemic" {
                crate::omega0::Modality::Epistemic
            } else {
                crate::omega0::Modality::Deontic
            };
            let obligations_json: String = row.get(2)?;
            let obligations = serde_json::from_str(&obligations_json).unwrap_or_default();
            Ok(Statement {
                content,
                modality,
                obligations,
            })
        })
    }

    pub fn get_justification(&self, hash: &str) -> Result<Justification> {
        let mut stmt = self.conn.prepare(
            "SELECT payload_json FROM justifications WHERE justification_hash = ?1"
        )?;
        stmt.query_row(params![hash], |row| {
            let payload_json: String = row.get(0)?;
            let justification = serde_json::from_str(&payload_json).unwrap_or(Justification::Conjecture);
            Ok(justification)
        })
    }

    pub fn get_all_assertions(&self) -> Result<Vec<(String, String, String, String)>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, statement_hash, justification_hash, environment_id FROM ledger_assertions ORDER BY lamport_t ASC"
        )?;
        let mut rows = stmt.query([])?;
        let mut result = Vec::new();
        while let Some(row) = rows.next()? {
            result.push((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?));
        }
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::Modality;

    #[test]
    fn audit_replay_rejects_corrupt_nogoods_on_disk() {
        struct TemporaryLedger(std::path::PathBuf);
        impl Drop for TemporaryLedger {
            fn drop(&mut self) {
                for suffix in ["", "-wal", "-shm"] {
                    let _ = std::fs::remove_file(format!("{}{suffix}", self.0.display()));
                }
            }
        }
        for column in ["nogood_hash", "prev_hash", "cortex_taint", "environment_id", "lamport_t"] {
            let path = std::env::temp_dir().join(format!(
                "babylon-audit-nogood-{}-{}-{}.db", std::process::id(), column,
                std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()
            ));
            let _cleanup = TemporaryLedger(path.clone());
            {
                let mut ledger = MasterLedger::new(path.to_str().unwrap()).unwrap();
                ledger.assert_nogood("statement-a", "env").unwrap();
                assert!(ledger.replay_to_atms_state().unwrap().nogoods.contains("statement-a"));
                let conn = Connection::open(&path).unwrap();
                let replacement = if column == "lamport_t" { "999" } else { "'corrupted'" };
                conn.execute(&format!("UPDATE atms_nogoods_log SET {column} = {replacement}"), []).unwrap();
                assert!(ledger.replay_to_atms_state().is_err(), "accepted corrupted {column}");
            }
        }
    }

    #[test]
    fn test_hash_chain_and_atms_replay() {
        let mut ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let s1 = Statement {
            content: "Water is H2O".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js1 = JustifiedStatement { statement: s1, justification: Justification::Conjecture };

        let s2 = Statement {
            content: "Fire burns".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js2 = JustifiedStatement { statement: s2, justification: Justification::Conjecture };

        ledger.assert_knowledge(&js1, "master").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        ledger.assert_knowledge(&js2, "master").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let s1_hash = MasterLedger::hash_statement(&js1.statement);
        ledger.assert_nogood(&s1_hash, "master").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        // Verify chain
        assert!(ledger.verify_chain("master").is_ok());

        // Replay ATMS
        let state = ledger.replay_to_atms_state().expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert!(state.environments.get("master").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.").contains(&s1_hash));
        assert!(state.environments.get("master").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.").contains(&MasterLedger::hash_statement(&js2.statement)));
        assert!(state.nogoods.contains(&s1_hash));
    }

    #[test]
    fn test_inv_bft_04_statement_collision_returns_error_without_panic() {
        let mut ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let s1 = Statement {
            content: "Statement Alpha".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js1 = JustifiedStatement {
            statement: s1,
            justification: Justification::Conjecture,
        };
        ledger.assert_knowledge(&js1, "env1").expect("Initial insertion must succeed");

        let s1_hash = MasterLedger::hash_statement(&js1.statement);

        // Tamper with statements table to simulate an adversarial hash collision:
        // same statement_hash but altered content
        ledger.conn.execute(
            "UPDATE statements SET content = 'Tampered Content' WHERE statement_hash = ?1",
            params![s1_hash],
        ).expect("Direct SQLite update must succeed");

        // Asserting js1 again must fail-stop returning a typed BftCollisionError instead of panicking
        let err = ledger.assert_knowledge(&js1, "env2").unwrap_err();
        let err_msg = err.to_string();
        assert!(
            err_msg.contains("INV_BFT_04") && err_msg.contains("statement_hash"),
            "Expected typed INV_BFT_04 statement_hash collision error, got: {}",
            err_msg
        );
    }

    #[test]
    fn test_inv_bft_04_justification_collision_returns_error_without_panic() {
        let mut ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let s1 = Statement {
            content: "Statement Beta".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js1 = JustifiedStatement {
            statement: s1,
            justification: Justification::Observation {
                timestamp: 100,
                sensor: "sensor_x".into(),
            },
        };
        ledger.assert_knowledge(&js1, "env1").expect("Initial insertion must succeed");

        let payload_json = serde_json::to_string(&js1.justification).unwrap();
        let just_hash = MasterLedger::hash_justification(&js1.justification, &payload_json);

        // Tamper with justifications table to simulate an adversarial hash collision
        ledger.conn.execute(
            "UPDATE justifications SET payload_json = '{\"tampered\": true}' WHERE justification_hash = ?1",
            params![just_hash],
        ).expect("Direct SQLite update must succeed");

        // Create statement with different content so it passes the statement check but collides on justification
        let s2 = Statement {
            content: "Statement Gamma".into(),
            modality: Modality::Epistemic,
            obligations: vec![],
        };
        let js2 = JustifiedStatement {
            statement: s2,
            justification: js1.justification.clone(),
        };

        let err = ledger.assert_knowledge(&js2, "env2").unwrap_err();
        let err_msg = err.to_string();
        assert!(
            err_msg.contains("INV_BFT_04") && err_msg.contains("justification_hash"),
            "Expected typed INV_BFT_04 justification_hash collision error, got: {}",
            err_msg
        );
    }

    #[test]
    fn test_fl_m01_transitive_revocation_closure_in_master_ledger() {
        let mut ledger = MasterLedger::new(":memory:").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let root_stmt = Statement {
            content: "Root Axiom: Sensor Alpha is calibrated".into(),
            modality: Modality::Epistemic,
            obligations: vec![crate::omega0::Obligation::Contradiction],
        };
        let root_js = JustifiedStatement {
            statement: root_stmt,
            justification: Justification::Observation {
                timestamp: 1720000000,
                sensor: "sensor_alpha".into(),
            },
        };
        ledger.assert_knowledge(&root_js, "env_prod").expect("Root assertion must succeed");

        let mut prev_js = root_js.clone();
        let mut chain_hashes = vec![MasterLedger::hash_statement(&root_js.statement)];

        for step in 1..=25 {
            let goal = Statement {
                content: format!("Derived Theorem Step {step}"),
                modality: Modality::Epistemic,
                obligations: vec![crate::omega0::Obligation::Contradiction],
            };
            let derived_js = crate::omega0::derive(&[prev_js], &goal).expect("Derivation must succeed");
            ledger.assert_knowledge(&derived_js, "env_prod").expect("Derived assertion must succeed");
            chain_hashes.push(MasterLedger::hash_statement(&derived_js.statement));
            prev_js = derived_js;
        }

        // Before revoking root, leaf statement passes verify_with_nogoods
        let state_before = ledger.replay_to_atms_state().expect("Replay before nogood must succeed");
        assert!(crate::omega0::verify_with_nogoods(&prev_js, &state_before.nogoods));

        // Revoke root statement via assert_nogood
        let root_hash = &chain_hashes[0];
        ledger.assert_nogood(root_hash, "env_prod").expect("assert_nogood must succeed");

        // Transitive closure must contain all 26 nodes (root + 25 derived steps)
        let closure = ledger.get_revocation_closure(root_hash, "env_prod").expect("Closure query must succeed");
        assert_eq!(closure.len(), 26);

        // Replay must propagate nogood across all 26 nodes in the derivation chain
        let state_after = ledger.replay_to_atms_state().expect("Replay after nogood must succeed");
        for h in &chain_hashes {
            assert!(state_after.nogoods.contains(h), "Expected {h} in transitive nogoods");
        }
        assert!(!crate::omega0::verify_with_nogoods(&prev_js, &state_after.nogoods));
    }
}
