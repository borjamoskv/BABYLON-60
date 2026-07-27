use rusqlite::{params, Connection, Result as SqlResult};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpistemicFailure {
    pub attempted_code: String,
    pub compiler_rejection: String,
}

pub struct MemoryStore {
    conn: Connection,
}

impl MemoryStore {
    /// Inicializa el almacenamiento de memoria epistémica en la base de datos local SQLite.
    pub fn new<P: AsRef<Path>>(db_path: P) -> SqlResult<Self> {
        let conn = Connection::open(db_path)?;
        conn.execute(
            "CREATE TABLE IF NOT EXISTS epistemic_failures (
                id INTEGER PRIMARY KEY,
                causal_hash TEXT NOT NULL,
                attempted_code TEXT NOT NULL,
                compiler_rejection TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        // Índice para acelerar la búsqueda por hash causal
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_causal_hash ON epistemic_failures (causal_hash)",
            [],
        )?;
        Ok(Self { conn })
    }

    /// Inicia el almacén en memoria (útil para tests).
    pub fn in_memory() -> SqlResult<Self> {
        let conn = Connection::open_in_memory()?;
        conn.execute(
            "CREATE TABLE epistemic_failures (
                id INTEGER PRIMARY KEY,
                causal_hash TEXT NOT NULL,
                attempted_code TEXT NOT NULL,
                compiler_rejection TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        Ok(Self { conn })
    }

    /// Genera el Causal Hash determinista (Firma AST).
    pub fn compute_causal_hash(error_code: &str, file_path: &Path, ast_scope: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(error_code.as_bytes());
        hasher.update(b":");
        hasher.update(file_path.to_string_lossy().as_bytes());
        hasher.update(b":");
        hasher.update(ast_scope.as_bytes());
        let result = hasher.finalize();
        hex::encode(result)
    }

    /// Registra un fallo en el Ledger Epistémico (Ramas muertas).
    pub fn log_failure(
        &self,
        error_code: &str,
        file_path: &Path,
        ast_scope: &str,
        attempted_code: &str,
        compiler_rejection: &str,
    ) -> SqlResult<()> {
        let hash = Self::compute_causal_hash(error_code, file_path, ast_scope);
        self.conn.execute(
            "INSERT INTO epistemic_failures (causal_hash, attempted_code, compiler_rejection)
             VALUES (?1, ?2, ?3)",
            params![hash, attempted_code, compiler_rejection],
        )?;
        Ok(())
    }

    /// Recupera las últimas `limit` ramas muertas para un contexto dado, acotando el ruido histórico.
    pub fn retrieve_failures(
        &self,
        error_code: &str,
        file_path: &Path,
        ast_scope: &str,
        limit: usize,
    ) -> SqlResult<Vec<EpistemicFailure>> {
        let hash = Self::compute_causal_hash(error_code, file_path, ast_scope);
        let mut stmt = self.conn.prepare(
            "SELECT attempted_code, compiler_rejection
             FROM epistemic_failures
             WHERE causal_hash = ?1
             ORDER BY timestamp DESC
             LIMIT ?2",
        )?;

        let failure_iter = stmt.query_map(params![hash, limit as i64], |row| {
            Ok(EpistemicFailure {
                attempted_code: row.get(0)?,
                compiler_rejection: row.get(1)?,
            })
        })?;

        let mut failures = Vec::new();
        for f in failure_iter {
            failures.push(f?);
        }
        Ok(failures)
    }
}
