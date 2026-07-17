use rusqlite::{Connection, Result, params};
use std::time::{SystemTime, UNIX_EPOCH};
use fastembed::{TextEmbedding, InitOptions, EmbeddingModel};

pub struct CortexLedger {
    conn: Connection,
    embedding_model: TextEmbedding,
}

impl CortexLedger {
    /// Ignición del motor de persistencia y embeddings locales
    pub fn ignite() -> Result<Self> {
        let conn = Connection::open("moskv_neural_memory.db")?;

        // PRAGMAs de alto rendimiento para escrituras masivas concurrentes
        conn.execute_batch(
            "
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            PRAGMA temp_store = MEMORY;
            PRAGMA cache_size = -64000;
            "
        )?;

        // 1. Tabla base para metadatos y payload
        conn.execute(
            "CREATE TABLE IF NOT EXISTS neural_events (
                event_id TEXT PRIMARY KEY,
                mutation_type TEXT NOT NULL, 
                payload JSON NOT NULL,
                timestamp INTEGER NOT NULL
            )",
            [],
        )?;

        // 2. Tabla para almacenar los vectores binarios (384 dimensiones para BGE-small)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS neural_vectors (
                event_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY(event_id) REFERENCES neural_events(event_id)
            )",
            [],
        )?;

        println!("🧠 CORTEX: Inicializando modelo de embeddings local (BGE-Small)...");
        
        // Inicialización del modelo FastEmbed
        let embedding_model = TextEmbedding::try_new(InitOptions {
            model_name: EmbeddingModel::BGESmallENV15,
            show_download_progress: false,
            ..Default::default()
        }).map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;

        println!("🧠 CortexLedger + Vector Engine instanciados correctamente.");
        Ok(Self { conn, embedding_model })
    }

    /// Método asíncrono/síncrono para sellar eventos y sus huellas vectoriales
    pub fn seal_event_vectorized(&self, mutation_type: &str, payload: &str, text_to_vectorize: &str) -> Result<()> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as i64;

        let event_id = format!("{}_{}", mutation_type, timestamp);

        // 1. Generar el embedding localmente en milisegundos
        let embeddings = self.embedding_model.embed(vec![text_to_vectorize], None)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;
        
        let vector = &embeddings[0]; // Extraemos el primer (y único) vector

        // Convertir Vec<f32> a Vec<u8> (Bytes crudos) para almacenamiento BLOB eficiente en SQLite
        let vector_bytes: Vec<u8> = vector.iter()
            .flat_map(|&f| f.to_le_bytes().to_vec())
            .collect();

        // 2. Inserción atómica mediante una transacción
        self.conn.execute(
            "INSERT INTO neural_events (event_id, mutation_type, payload, timestamp) 
             VALUES (?1, ?2, ?3, ?4)",
            params![&event_id, mutation_type, payload, &timestamp],
        )?;

        self.conn.execute(
            "INSERT INTO neural_vectors (event_id, embedding) VALUES (?1, ?2)",
            params![&event_id, vector_bytes],
        )?;

        println!("⚡ Evento criptosellado y vectorizado: {}", event_id);
        Ok(())
    }
}
