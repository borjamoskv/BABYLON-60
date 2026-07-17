/// VECTOR A.2: Master Ledger & ATMS Hardening
///
/// Elevates the append-only ledger into a verifiable Causal Hash Chain.
/// Acts as a Transactional Local Ledger (SQLite WAL mode), reconstructing 
/// the ATMS in-memory state via deterministic replay.

use crate::omega0::{JustifiedStatement, Statement, Justification};
use rusqlite::{params, Connection, Result};
use std::time::Duration;
use uuid::Uuid;
use std::collections::{HashSet, HashMap};

const UUID_V5_NAMESPACE: Uuid = Uuid::from_bytes([
    0x1a, 0x51, 0x69, 0x88, 0x9d, 0xea, 0x7d, 0xb1,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
]);

pub struct MasterLedger {
    conn: Connection,
}

#[derive(Debug, Clone, PartialEq)]
pub struct AtmsState {
    pub environments: HashMap<String, HashSet<String>>, // environment_id -> set(statement_hashes)
    pub nogoods: HashSet<String>, // statement_hashes that form contradictions
}

impl MasterLedger {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        
        conn.pragma_update(None, "journal_mode", "WAL")?;
        conn.pragma_update(None, "synchronous", "NORMAL")?;
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

    pub fn hash_statement(s: &Statement) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(s.content.as_bytes());
        hasher.update(format!("{:?}", s.modality).as_bytes());
        format!("STMT:{}", hasher.finalize().to_hex())
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
        let payload_json = serde_json::to_string(&js.justification).unwrap_or_else(|_| "{}".to_string());
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

        tx.execute(
            "INSERT OR IGNORE INTO statements (statement_hash, content, modality) VALUES (?1, ?2, ?3)",
            params![statement_hash, js.statement.content, format!("{:?}", js.statement.modality)],
        )?;

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

        tx.execute(
            "INSERT OR IGNORE INTO justifications (justification_hash, variant, payload_json) VALUES (?1, ?2, ?3)",
            params![justification_hash, variant, payload_json],
        )?;

        tx.execute(
            "INSERT INTO ledger_assertions (id, statement_hash, justification_hash, environment_id, lamport_t, prev_hash, cortex_taint) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![id, statement_hash, justification_hash, environment_id, lamport_t, prev_hash, cortex_taint],
        )?;

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

            expected_prev_hash = taint;
        }
        Ok(true)
    }

    /// Reconstructs the ATMS state purely from the causal event log.
    pub fn replay_to_atms_state(&self) -> Result<AtmsState> {
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

        Ok(state)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::Modality;

    #[test]
    fn test_hash_chain_and_atms_replay() {
        let mut ledger = MasterLedger::new(":memory:").unwrap();

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

        ledger.assert_knowledge(&js1, "master").unwrap();
        ledger.assert_knowledge(&js2, "master").unwrap();

        let s1_hash = MasterLedger::hash_statement(&js1.statement);
        ledger.assert_nogood(&s1_hash, "master").unwrap();

        // Verify chain
        assert!(ledger.verify_chain("master").is_ok());

        // Replay ATMS
        let state = ledger.replay_to_atms_state().unwrap();
        assert!(state.environments.get("master").unwrap().contains(&s1_hash));
        assert!(state.environments.get("master").unwrap().contains(&MasterLedger::hash_statement(&js2.statement)));
        assert!(state.nogoods.contains(&s1_hash));
    }
}
