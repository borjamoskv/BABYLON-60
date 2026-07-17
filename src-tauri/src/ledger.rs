use fastembed::{EmbeddingModel, InitOptions, TextEmbedding};
use rusqlite::{params, Connection, Result};

pub struct CortexLedger {
    conn: Connection,
    embedder: TextEmbedding,
}

impl CortexLedger {
    pub fn init() -> Result<Self> {
        let conn = Connection::open("cortex.db")?;
        conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA synchronous = NORMAL;
             CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT);
             CREATE TABLE IF NOT EXISTS vectors (id TEXT PRIMARY KEY, vec BLOB);",
        )?;

        let embedder = TextEmbedding::try_new(InitOptions {
            model_name: EmbeddingModel::BGESmallENV15,
            ..Default::default()
        })
        .unwrap();

        Ok(Self { conn, embedder })
    }

    pub fn write(&self, id: &str, text: &str) -> Result<()> {
        let vec = &self.embedder.embed(vec![text], None).unwrap()[0];
        let vec_bytes: Vec<u8> = vec.iter().flat_map(|f| f.to_le_bytes()).collect();

        self.conn.execute(
            "INSERT INTO events (id, payload) VALUES (?1, ?2)",
            params![id, text],
        )?;
        self.conn.execute(
            "INSERT INTO vectors (id, vec) VALUES (?1, ?2)",
            params![id, vec_bytes],
        )?;
        Ok(())
    }
}
