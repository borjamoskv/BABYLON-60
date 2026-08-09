//! # Cortex Persist
//! Módulo de persistencia del SharedManifest (Cold Path) hacia SQLite WAL.
//! Incluye generación de Merkle Root para anclaje Bitcoin OP_RETURN.

use crate::manifest::SharedManifest;
use rusqlite::{params, Connection, Result};
use sha2::{Digest, Sha256};
use std::sync::atomic::Ordering;
use hex;

pub struct CortexPersister {
    conn: Connection,
}

impl CortexPersister {
    /// Inicializa la base de datos Cortex en disco.
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        
        // Optimización extrema: modo WAL y sin sincronicidad estricta para throughput
        conn.execute_batch(
            "PRAGMA journal_mode=WAL;
             PRAGMA synchronous=NORMAL;
             PRAGMA mmap_size=30000000000;
             CREATE TABLE IF NOT EXISTS ledger (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 epoch_id INTEGER NOT NULL,
                 seq INTEGER NOT NULL,
                 status_flag INTEGER NOT NULL,
                 payload_hash BLOB NOT NULL,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
             );"
        )?;
        
        Ok(Self { conn })
    }

    /// Lee un SharedManifest en memoria y lo inserta en SQLite.
    pub fn drain_manifest(&self, manifest: &SharedManifest) -> Result<()> {
        let epoch = manifest.epoch_id.load(Ordering::Acquire);
        let seq = manifest.seq.load(Ordering::Acquire);
        let status = manifest.status_flag.load(Ordering::Acquire);
        
        // El payload_hash son 4 AtomicU64 (32 bytes).
        let p0 = manifest.payload_hash[0].load(Ordering::Relaxed);
        let p1 = manifest.payload_hash[1].load(Ordering::Relaxed);
        let p2 = manifest.payload_hash[2].load(Ordering::Relaxed);
        let p3 = manifest.payload_hash[3].load(Ordering::Relaxed);
        
        let mut blob = Vec::with_capacity(32);
        blob.extend_from_slice(&p0.to_le_bytes());
        blob.extend_from_slice(&p1.to_le_bytes());
        blob.extend_from_slice(&p2.to_le_bytes());
        blob.extend_from_slice(&p3.to_le_bytes());

        self.conn.execute(
            "INSERT INTO ledger (epoch_id, seq, status_flag, payload_hash) VALUES (?1, ?2, ?3, ?4)",
            params![epoch, seq, status, blob],
        )?;

        Ok(())
    }

    /// Extrae los últimos N registros y genera el Hex string OP_RETURN para Bitcoin.
    pub fn generate_bitcoin_op_return(&self, limit: usize) -> Result<String> {
        let mut stmt = self.conn.prepare("SELECT payload_hash FROM ledger ORDER BY id DESC LIMIT ?1")?;
        
        let hash_iter = stmt.query_map([limit], |row| {
            let blob: Vec<u8> = row.get(0)?;
            Ok(blob)
        })?;

        let mut hasher = Sha256::new();
        for blob_result in hash_iter {
            if let Ok(blob) = blob_result {
                hasher.update(&blob);
            }
        }
        
        let merkle_root = hasher.finalize();
        let hex_root = hex::encode(merkle_root);
        
        // OP_RETURN máximo 80 bytes. Hex son 64 caracteres.
        Ok(format!("OP_RETURN {}", hex_root))
    }
}
