// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
#[cfg(target_os = "linux")]
use inotify::{Inotify, WatchMask};
use rusqlite::{params, Connection};
use signal_hook::consts::signal::{SIGINT, SIGTERM};
#[cfg(not(target_os = "windows"))]
use signal_hook::iterator::Signals;
use std::env;
#[cfg(target_os = "linux")]
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;

/// Deriva una clave de 32 bytes determinista para MAC con BLAKE3
fn derive_bft_key(raw_key: &[u8]) -> [u8; 32] {
    blake3::derive_key("BABYLON-60 C5-REAL BFT INTERCEPTOR MAC KEY v1", raw_key)
}

/// Serialización Canónica (Length-Prefixed)
fn canonical_serialize(timestamp: u64, event: &str, payload: &str) -> Vec<u8> {
    let mut buf = Vec::new();
    buf.extend_from_slice(&timestamp.to_be_bytes());
    buf.extend_from_slice(&(event.len() as u32).to_be_bytes());
    buf.extend_from_slice(event.as_bytes());
    buf.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    buf.extend_from_slice(payload.as_bytes());
    buf
}

/// Hashea un nodo hoja con MAC (Domain Separation 0x00)
fn hash_leaf(key: &[u8; 32], prev_hash: &[u8], payload_bytes: &[u8]) -> Vec<u8> {
    let mut hasher = blake3::Hasher::new_keyed(key);
    hasher.update(&[0x00]); // Leaf domain prefix
    hasher.update(prev_hash);
    hasher.update(payload_bytes);
    hasher.finalize().as_bytes().to_vec()
}

/// Estructura compartida para el Ledger
struct BftLedger {
    conn: Connection,
    last_hash: Vec<u8>,
    key: [u8; 32],
    all_hashes: Vec<Vec<u8>>,
    logical_tick: u64,
}

impl BftLedger {
    fn insert(&mut self, event_type: &str, payload: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.logical_tick = self.logical_tick.checked_add(1).ok_or("Causal logical clock overflow")?;
        let ts = self.logical_tick;
        let canon = canonical_serialize(ts, event_type, payload);
        
        let new_hash = hash_leaf(&self.key, &self.last_hash, &canon);
        let prev_hex = hex::encode(&self.last_hash);
        let curr_hex = hex::encode(&new_hash);

        // Escritura Síncrona WAL
        self.conn.execute(
            "INSERT INTO transactions (timestamp, event_type, payload, prev_hash, curr_hash) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![ts as i64, event_type, payload, prev_hex, curr_hex],
        )?;

        self.last_hash = new_hash.clone();
        self.all_hashes.push(new_hash);
        Ok(())
    }

    fn compute_merkle_root(&self) -> String {
        if self.all_hashes.is_empty() {
            return "EMPTY_LEDGER".to_string();
        }
        let mut level = self.all_hashes.clone();
        while level.len() > 1 {
            let mut next_level = Vec::new();
            for chunk in level.chunks(2) {
                let left = &chunk[0];
                let right = if chunk.len() > 1 { &chunk[1] } else { left };
                let mut hasher = blake3::Hasher::new_keyed(&self.key);
                hasher.update(&[0x01]); // Internal node domain prefix
                hasher.update(left);
                hasher.update(right);
                next_level.push(hasher.finalize().as_bytes().to_vec());
            }
            level = next_level;
        }
        hex::encode(&level[0])
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("█▄ [Causal-Determinist] AGENT CODE BFT INTERCEPTOR (HARDENED MCTS)");

    let ledger_path = "agent_bft_ledger.db";
    let conn = Connection::open(ledger_path)?;
    conn.execute_batch(
        "PRAGMA journal_mode = WAL;
         PRAGMA synchronous = FULL;
         CREATE TABLE IF NOT EXISTS transactions (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             timestamp INTEGER NOT NULL,
             event_type TEXT NOT NULL,
             payload TEXT NOT NULL,
             prev_hash TEXT NOT NULL,
             curr_hash TEXT NOT NULL
         );",
    )?;

    // Recuperar estado previo (simulado como Genesis para esta corrida)
    let genesis = vec![0u8; 32];
    
    // Generar clave MAC desde entorno (en prod/Causal-Determinist vendría de HSM o env obligatorio)
    let env_key = std::env::var("CORTEX_BFT_KEY")
        .or_else(|_| std::env::var("CORTEX_VAULT_KEY"))
        .expect("FATAL: CORTEX_BFT_KEY or CORTEX_VAULT_KEY env var required for Causal-Determinist BFT MAC signing. Zero static fallback permitted.");
    let key = derive_bft_key(env_key.as_bytes());

    let ledger = Arc::new(Mutex::new(BftLedger {
        conn,
        last_hash: genesis,
        key,
        all_hashes: Vec::new(),
        logical_tick: 0,
    }));

    let shutdown_flag = Arc::new(AtomicBool::new(false));

    // 1. Manejador de señales (Graceful SIGTERM/SIGINT)
    #[cfg(not(target_os = "windows"))]
    {
        let mut signals = Signals::new([SIGINT, SIGTERM])?;
        let sf = Arc::clone(&shutdown_flag);
        thread::spawn(move || {
            if signals.forever().next().is_some() {
                sf.store(true, Ordering::SeqCst);
            }
        });
    }

    // 2. Monitoreo inotify de ~/.agent_persist (Linux)
    #[cfg(target_os = "linux")]
    {
        let home = env::var("HOME").unwrap_or_else(|_| "/root".to_string());
        let agent_dir = format!("{}/.agent_persist", home);
        
        let l_fs = Arc::clone(&ledger);
        let s_fs = Arc::clone(&shutdown_flag);
        
        if Path::new(&agent_dir).exists() {
            thread::spawn(move || {
                if let Ok(mut inotify) = Inotify::init() {
                    let _ = inotify.watches().add(
                        Path::new(&agent_dir),
                        WatchMask::MODIFY | WatchMask::CREATE | WatchMask::DELETE,
                    );
                    
                    let mut buffer = [0; 1024];
                    while !s_fs.load(Ordering::SeqCst) {
                        if let Ok(events) = inotify.read_events(&mut buffer) {
                            for event in events {
                                if let Some(name) = event.name {
                                    let payload = name.to_string_lossy().to_string();
                                    if let Ok(mut l) = l_fs.lock() {
                                        let _ = l.insert("FS_EVENT", &payload);
                                    }
                                }
                            }
                        }
                        thread::sleep(std::time::Duration::from_millis(50));
                    }
                }
            });
        }
    }

    // 3. Subproceso CLI (Bypass de recursión infinita)
    let real_cli = env::var("REAL_AGENT_PATH").unwrap_or_else(|_| "npx".to_string());
    let mut cmd = Command::new(&real_cli);
    if real_cli == "npx" {
        cmd.arg("-y").arg("@agent-ai/agent-code");
    }
    
    let mut child = cmd
        .arg("--print-updates=false")
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()?;

    // Espera activa controlada para manejar shutdown
    while !shutdown_flag.load(Ordering::SeqCst) {
        if let Ok(Some(_status)) = child.try_wait() {
            shutdown_flag.store(true, Ordering::SeqCst);
            break;
        }
        thread::sleep(std::time::Duration::from_millis(100));
    }

    // Cierre Causal
    if let Ok(mut l) = ledger.lock() {
        let root = l.compute_merkle_root();
        let _ = l.insert("CLOSURE_SEAL", &format!("ROOT:{}", root));
        println!("█▄ [Causal-Determinist] CIERRE CAUSAL EJECUTADO");
        println!("MERKLE ROOT: {}", root);
    }

    Ok(())
}

#[allow(dead_code)]
fn hex_encode(data: &[u8]) -> String {
    data.iter().map(|b| format!("{:02x}", b)).collect()
}
// Stub para evitar dependencias extra si no usamos el crate hex
#[allow(dead_code)]
mod hex {
    pub fn encode(data: &[u8]) -> String {
        data.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_canonical_serialize() {
        let buf = canonical_serialize(123456789, "TEST_EVENT", "payload_data");
        assert_eq!(&buf[0..8], &123456789u64.to_be_bytes());
        assert_eq!(&buf[8..12], &10u32.to_be_bytes());
        assert_eq!(&buf[12..22], b"TEST_EVENT");
    }

    #[test]
    fn test_hash_leaf_domain_separation() {
        let key = derive_bft_key(&[0x41; 32]);
        let h1 = hash_leaf(&key, &[0u8; 32], b"data_1");
        let h2 = hash_leaf(&key, &[0u8; 32], b"data_2");
        assert_ne!(h1, h2);
        assert_eq!(h1.len(), 32);
    }

    #[test]
    fn test_bft_ledger_merkle_root() {
        let key = derive_bft_key(&[0x42; 32]);
        let conn = Connection::open_in_memory().expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        conn.execute_batch(
            "CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                curr_hash TEXT NOT NULL
            );"
        ).expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");

        let mut ledger = BftLedger {
            conn,
            last_hash: vec![0u8; 32],
            key,
            all_hashes: Vec::new(),
            logical_tick: 0,
        };

        assert_eq!(ledger.compute_merkle_root(), "EMPTY_LEDGER");

        ledger.insert("EVENT_A", "payload_A").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert_ne!(ledger.compute_merkle_root(), "EMPTY_LEDGER");
        let root_1 = ledger.compute_merkle_root();

        ledger.insert("EVENT_B", "payload_B").expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        let root_2 = ledger.compute_merkle_root();
        assert_ne!(root_1, root_2);
        assert_eq!(ledger.logical_tick, 2);
    }
}
