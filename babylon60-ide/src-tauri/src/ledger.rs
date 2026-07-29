use rusqlite::{Connection, Result, params};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use chrono::Utc;

#[derive(Debug, Serialize, Deserialize)]
pub struct CortexEvent {
    pub id: Option<i64>,
    pub timestamp: String,
    pub event_type: String,
    pub payload: String,
    pub prev_hash: String,
    pub event_hash: String,
}

pub struct CortexLedger {
    conn: Connection,
}

impl CortexLedger {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;

        // Ω10 · Concurrencia Confiable de DB: busy_timeout=5000ms and WAL mode
        conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA busy_timeout = 5000;
             PRAGMA synchronous = NORMAL;"
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS cortex_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload JSON NOT NULL,
                prev_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE
            )",
            [],
        )?;

        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM cortex_events",
            [],
            |row| row.get(0),
        )?;

        if count == 0 {
            let genesis_hash = Self::compute_hash("0", "GENESIS", "{}", "0");
            conn.execute(
                "INSERT INTO cortex_events (timestamp, event_type, payload, prev_hash, event_hash)
                 VALUES (?1, ?2, ?3, ?4, ?5)",
                params![
                    Utc::now().to_rfc3339(),
                    "GENESIS",
                    "{}",
                    "0",
                    genesis_hash
                ],
            )?;
        }

        Ok(Self { conn })
    }

    fn compute_hash(timestamp: &str, event_type: &str, payload: &str, prev_hash: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(timestamp.as_bytes());
        hasher.update(event_type.as_bytes());
        hasher.update(payload.as_bytes());
        hasher.update(prev_hash.as_bytes());
        hex::encode(hasher.finalize())
    }

    pub fn get_latest_hash(&self) -> Result<String> {
        self.conn.query_row(
            "SELECT event_hash FROM cortex_events ORDER BY id DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
    }

    pub fn append_event(&self, event_type: &str, payload: &serde_json::Value) -> Result<CortexEvent> {
        let prev_hash = self.get_latest_hash()?;
        let timestamp = Utc::now().to_rfc3339();
        let payload_str = payload.to_string();
        let event_hash = Self::compute_hash(&timestamp, event_type, &payload_str, &prev_hash);

        self.conn.execute(
            "INSERT INTO cortex_events (timestamp, event_type, payload, prev_hash, event_hash)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                timestamp,
                event_type,
                payload_str,
                prev_hash,
                event_hash
            ],
        )?;

        Ok(CortexEvent {
            id: Some(self.conn.last_insert_rowid()),
            timestamp,
            event_type: event_type.to_string(),
            payload: payload_str,
            prev_hash,
            event_hash,
        })
    }

    pub fn get_events(&self, limit: u32) -> Result<Vec<CortexEvent>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, timestamp, event_type, payload, prev_hash, event_hash
             FROM cortex_events ORDER BY id DESC LIMIT ?1"
        )?;

        let event_iter = stmt.query_map(params![limit], |row| {
            Ok(CortexEvent {
                id: row.get(0)?,
                timestamp: row.get(1)?,
                event_type: row.get(2)?,
                payload: row.get(3)?,
                prev_hash: row.get(4)?,
                event_hash: row.get(5)?,
            })
        })?;

        let mut events = Vec::new();
        for event in event_iter {
            events.push(event?);
        }

        events.reverse();
        Ok(events)
    }
}
