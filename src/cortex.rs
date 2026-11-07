//! # Cortex Persist
//! Módulo de persistencia del SharedManifest (Cold Path) hacia SQLite WAL.
//! Incluye un resumen secuencial SHA-256 para anclaje Bitcoin OP_RETURN.

use crate::manifest::SharedManifest;
use hex;
use rusqlite::{params, Connection, Result};
use sha2::{Digest, Sha256};

/// Persistidor de `SharedManifest` hacia SQLite en modo WAL.
///
/// Mantiene una conexión a la base de datos local y permite persistir
/// capturas del estado y calcular un resumen secuencial para anclaje Bitcoin OP_RETURN.
pub struct CortexPersister {
    conn: Connection,
}

impl CortexPersister {
    /// Inicializa la base de datos Cortex en disco.
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;

        // Durable WAL writes: acknowledge only after a FULL synchronization barrier.
        conn.execute_batch(
            "PRAGMA journal_mode=WAL;
             PRAGMA synchronous=FULL;
             PRAGMA mmap_size=30000000000;
             CREATE TABLE IF NOT EXISTS ledger (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 epoch_id INTEGER NOT NULL,
                 seq INTEGER NOT NULL,
                 status_flag INTEGER NOT NULL,
                 payload_hash BLOB NOT NULL,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
             );",
        )?;

        Ok(Self { conn })
    }

    /// Lee un `SharedManifest` en memoria de forma consistente e inserta el estado en SQLite.
    pub fn drain_manifest(&self, manifest: &SharedManifest) -> Result<()> {
        // Usar la lectura Nivel 5 Semantic Closure consistente
        let (status, seq, epoch, hash) =
            match crate::semantic_closure::read_consistent_state(manifest) {
                Some((st, sq, e, h)) => (st, sq, e, h),
                None => {
                    return Err(rusqlite::Error::QueryReturnedNoRows);
                }
            };

        let mut blob = Vec::with_capacity(32);
        blob.extend_from_slice(&hash[0].to_le_bytes());
        blob.extend_from_slice(&hash[1].to_le_bytes());
        blob.extend_from_slice(&hash[2].to_le_bytes());
        blob.extend_from_slice(&hash[3].to_le_bytes());

        self.conn.execute(
            "INSERT INTO ledger (epoch_id, seq, status_flag, payload_hash) VALUES (?1, ?2, ?3, ?4)",
            params![epoch as i64, seq, status, blob],
        )?;

        Ok(())
    }

    /// Genera OP_RETURN con el SHA-256 de los últimos `limit` hashes de 32 bytes,
    /// concatenados del registro más reciente al más antiguo (id descendente).
    ///
    /// Es un resumen secuencial, no una raíz de Merkle. Conserva el digest histórico
    /// para datos válidos; cero registros produce SHA-256 de la entrada vacía.
    /// Cualquier error de lectura o longitud inválida rechaza el resumen completo.
    pub fn generate_bitcoin_op_return(&self, limit: usize) -> Result<String> {
        let mut stmt = self
            .conn
            .prepare("SELECT payload_hash FROM ledger ORDER BY id DESC LIMIT ?1")?;

        let hash_iter = stmt.query_map([limit as i64], |row| row.get::<_, [u8; 32]>(0))?;

        let mut hasher = Sha256::new();
        for row_result in hash_iter {
            let record_hash = row_result?;
            hasher.update(record_hash);
        }

        let sequential_digest = hasher.finalize();
        let hex_digest = hex::encode(sequential_digest);

        // El digest son 32 bytes, representados por 64 caracteres hexadecimales.
        Ok(format!("OP_RETURN {}", hex_digest))
    }
}

#[cfg(test)]
mod security_tests {
    use super::*;
    #[test]
    fn security_cold_ledger_uses_full_synchronization() {
        let store = CortexPersister::new(":memory:").unwrap();
        let synchronous: u32 = store.conn.query_row("PRAGMA synchronous", [], |row| row.get(0)).unwrap();
        assert_eq!(synchronous, 2, "cold-ledger writes must use synchronous=FULL");
    }
}

#[cfg(test)]
mod tests {
    use super::CortexPersister;
    use rusqlite::{params, types::FromSqlError, Error};

    fn insert_record(persister: &CortexPersister, hash: &[u8]) {
        persister.conn.execute(
            "INSERT INTO ledger (epoch_id, seq, status_flag, payload_hash) VALUES (0, 0, 1, ?1)",
            params![hash],
        ).unwrap();
    }

    #[test]
    fn empty_ledger_preserves_sha256_of_empty_input() {
        let persister = CortexPersister::new(":memory:").unwrap();
        assert_eq!(
            persister.generate_bitcoin_op_return(100).unwrap(),
            "OP_RETURN e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    #[test]
    fn sequential_digest_preserves_latest_first_order_and_limit() {
        let persister = CortexPersister::new(":memory:").unwrap();
        for byte in [0x11, 0x22, 0x33] {
            insert_record(&persister, &[byte; 32]);
        }
        // Fixed vectors: SHA-256 of 32-byte records in descending ledger id order.
        for (limit, digest) in [
            (
                1,
                "deb0e38ced1e41de6f92e70e80c418d2d356afaaa99e26f5939dbc7d3ef4772a",
            ),
            (
                2,
                "75f81c145249f6df445708fe0bca5fdea71f6e7be44c4a67e0f4d70c52856308",
            ),
            (
                10,
                "46914cc6fab1147c21db7265090d894bb0d70b2eca7c8685a84c81b369df6f8d",
            ),
        ] {
            assert_eq!(
                persister.generate_bitcoin_op_return(limit).unwrap(),
                format!("OP_RETURN {digest}")
            );
        }
    }

    #[test]
    fn zero_limit_hashes_no_rows_even_when_ledger_contains_invalid_data() {
        let persister = CortexPersister::new(":memory:").unwrap();
        insert_record(&persister, &[0x11; 31]);
        assert_eq!(
            persister.generate_bitcoin_op_return(0).unwrap(),
            "OP_RETURN e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    #[test]
    fn intermediate_row_conversion_error_rejects_entire_digest() {
        let persister = CortexPersister::new(":memory:").unwrap();
        insert_record(&persister, &[0x11; 32]);
        persister.conn.execute(
            "INSERT INTO ledger (epoch_id, seq, status_flag, payload_hash) VALUES (0, 0, 1, 'invalid blob')",
            [],
        ).unwrap();
        insert_record(&persister, &[0x33; 32]);
        // The newest valid record must have been consumed before the bad row.
        assert!(persister.generate_bitcoin_op_return(1).is_ok());
        for limit in [2, 3] {
            assert!(matches!(
                persister.generate_bitcoin_op_return(limit),
                Err(Error::InvalidColumnType(0, _, _))
            ));
        }
    }

    #[test]
    fn invalid_blob_lengths_reject_entire_digest() {
        for length in [0, 1, 31, 33, 64] {
            let persister = CortexPersister::new(":memory:").unwrap();
            insert_record(&persister, &[0x11; 32]);
            insert_record(&persister, &vec![0x22; length]);
            insert_record(&persister, &[0x33; 32]);
            let error = persister.generate_bitcoin_op_return(3).unwrap_err();
            match error {
                Error::FromSqlConversionFailure(0, _, source) => {
                    assert!(matches!(source.downcast_ref::<FromSqlError>(),
                        Some(FromSqlError::InvalidBlobSize { expected_size: 32, blob_size })
                            if *blob_size == length));
                }
                other => panic!("unexpected error for blob length {length}: {other}"),
            }
        }
    }

    #[test]
    fn intermediate_sqlite_step_error_rejects_entire_digest() {
        let persister = CortexPersister::new(":memory:").unwrap();
        for byte in [0x11, 0x22, 0x33] {
            insert_record(&persister, &[byte; 32]);
        }
        // SQLite raises an integer overflow while stepping through the middle row.
        persister
            .conn
            .execute_batch(
                "ALTER TABLE ledger RENAME TO stored_ledger;
             CREATE VIEW ledger AS
             SELECT id, CASE WHEN id = 2 THEN abs(-9223372036854775808)
                        ELSE payload_hash END AS payload_hash
             FROM stored_ledger;",
            )
            .unwrap();
        let mut statement = persister
            .conn
            .prepare("SELECT payload_hash FROM ledger ORDER BY id DESC LIMIT 3")
            .unwrap();
        let mut rows = statement.query([]).unwrap();
        assert_eq!(
            rows.next().unwrap().unwrap().get::<_, [u8; 32]>(0).unwrap(),
            [0x33; 32]
        );
        assert!(matches!(rows.next(), Err(Error::SqliteFailure(_, _))));
        assert!(matches!(
            persister.generate_bitcoin_op_return(3),
            Err(Error::SqliteFailure(_, _))
        ));
    }
}
