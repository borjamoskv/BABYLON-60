use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};
use rusqlite::{params, Connection, Result, OptionalExtension};
use std::sync::Mutex;

pub struct VoidLedger {
    conn: Mutex<Connection>,
    embedder: Mutex<TextEmbedding>,
}

impl VoidLedger {
    pub fn init() -> Result<Self> {
        let conn = Connection::open("cortex.db")?;
        
        // INV_BFT_02: WAL mode + busy_timeout=5000ms
        conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA synchronous = NORMAL;
             PRAGMA busy_timeout = 5000;
             
             CREATE TABLE IF NOT EXISTS events (
                 id TEXT PRIMARY KEY,
                 payload TEXT NOT NULL,
                 lamport_t INTEGER NOT NULL,
                 cortex_taint TEXT NOT NULL,
                 prev_hash TEXT UNIQUE
             );
             
             -- Ω11: MASTER LEDGER - RAISE(ABORT) on updates/deletes
             CREATE TRIGGER IF NOT EXISTS bft_no_update_events BEFORE UPDATE ON events 
             BEGIN SELECT RAISE(ABORT, 'C5-REAL: Immutability violation (UPDATE)'); END;
             
             CREATE TRIGGER IF NOT EXISTS bft_no_delete_events BEFORE DELETE ON events 
             BEGIN SELECT RAISE(ABORT, 'C5-REAL: Immutability violation (DELETE)'); END;
             
             CREATE TABLE IF NOT EXISTS vectors (
                 id TEXT PRIMARY KEY, 
                 vec BLOB NOT NULL,
                 FOREIGN KEY(id) REFERENCES events(id)
             );",
        )?;

        let embedder = TextEmbedding::try_new(InitOptions::new(EmbeddingModel::BGESmallENV15))
        .unwrap();

        Ok(Self {
            conn: Mutex::new(conn),
            embedder: Mutex::new(embedder),
        })
    }

    pub fn write(&self, payload: &str, causal_taint: &str) -> Result<()> {
        let mut embedder = self.embedder.lock().unwrap();
        let vec = &embedder.embed(vec![payload], None).unwrap()[0];
        let vec_bytes: Vec<u8> = vec.iter().flat_map(|f| f.to_le_bytes()).collect();

        let conn = self.conn.lock().unwrap();
        // Transaction for atomic write
        conn.execute("BEGIN IMMEDIATE", [])?;

        // Lamport ordering: MAX(lamport_t) + 1
        let mut stmt = conn.prepare("SELECT IFNULL(MAX(lamport_t), 0) FROM events")?;
        let max_lamport: i64 = stmt.query_row([], |row| row.get(0))?;
        let new_lamport = max_lamport + 1;

        // Get prev_hash (cortex_taint of the highest lamport_t)
        let mut stmt = conn.prepare("SELECT cortex_taint FROM events ORDER BY lamport_t DESC LIMIT 1")?;
        let prev_hash: Option<String> = stmt.query_row([], |row| row.get(0)).optional()?;

        // Calculate cortex_taint using blake3
        let mut hasher = blake3::Hasher::new();
        hasher.update(payload.as_bytes());
        hasher.update(causal_taint.as_bytes());
        if let Some(ref ph) = prev_hash {
            hasher.update(ph.as_bytes());
        }
        hasher.update(&new_lamport.to_le_bytes());
        
        // Include BFT key for HMAC-like signing (Ω25)
        let bft_key = std::env::var("CORTEX_BFT_KEY")
            .or_else(|_| std::env::var("CORTEX_VAULT_KEY"))
            .expect("FATAL: CORTEX_BFT_KEY or CORTEX_VAULT_KEY env var required for C5-REAL BFT HMAC signing. Zero static fallback permitted.");
        hasher.update(bft_key.as_bytes());
        
        let new_cortex_taint = hasher.finalize().to_hex().to_string();

        // INV_BFT_04: UUID v5 idempotency keys
        let id = uuid::Uuid::new_v5(&uuid::Uuid::NAMESPACE_OID, new_cortex_taint.as_bytes()).to_string();

        // Check idempotency: If ID exists, silently ignore and rollback
        let mut check_stmt = conn.prepare("SELECT 1 FROM events WHERE id = ?1")?;
        let exists: Option<i64> = check_stmt.query_row(params![id], |row| row.get(0)).optional()?;
        if exists.is_some() {
            conn.execute("ROLLBACK", [])?;
            return Ok(());
        }

        // Insert into events
        conn.execute(
            "INSERT INTO events (id, payload, lamport_t, cortex_taint, prev_hash) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![id, payload, new_lamport, new_cortex_taint, prev_hash],
        )?;

        // Insert into vectors
        conn.execute(
            "INSERT INTO vectors (id, vec) VALUES (?1, ?2)",
            params![id, vec_bytes],
        )?;

        conn.execute("COMMIT", [])?;

        Ok(())
    }
}
