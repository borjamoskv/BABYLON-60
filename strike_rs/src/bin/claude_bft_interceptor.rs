use inotify::{Inotify, WatchMask};
use ring::hmac;
use rusqlite::{params, Connection};
use signal_hook::consts::signal::{SIGINT, SIGTERM};
use signal_hook::iterator::Signals;
use std::env;
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};

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

/// Hashea un nodo hoja (Domain Separation 0x00)
fn hash_leaf(key: &hmac::Key, prev_hash: &[u8], payload_bytes: &[u8]) -> Vec<u8> {
    let mut ctx = hmac::Context::with_key(key);
    ctx.update(&[0x00]); // Leaf domain prefix
    ctx.update(prev_hash);
    ctx.update(payload_bytes);
    ctx.sign().as_ref().to_vec()
}

/// Estructura compartida para el Ledger
struct BftLedger {
    conn: Connection,
    last_hash: Vec<u8>,
    key: hmac::Key,
    all_hashes: Vec<Vec<u8>>,
}

impl BftLedger {
    fn insert(&mut self, event_type: &str, payload: &str) -> Result<(), Box<dyn std::error::Error>> {
        let ts = SystemTime::now().duration_since(UNIX_EPOCH)?.as_nanos() as u64;
        let canon = canonical_serialize(ts, event_type, payload);
        
        let new_hash = hash_leaf(&self.key, &self.last_hash, &canon);
        let prev_hex = hex::encode(&self.last_hash);
        let curr_hex = hex::encode(&new_hash);

        // Escritura Síncrona WAL
        self.conn.execute(
            "INSERT INTO transactions (timestamp, event_type, payload, prev_hash, curr_hash) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![ts, event_type, payload, prev_hex, curr_hex],
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
                let mut ctx = hmac::Context::with_key(&self.key);
                ctx.update(&[0x01]); // Internal node domain prefix
                ctx.update(left);
                ctx.update(right);
                next_level.push(ctx.sign().as_ref().to_vec());
            }
            level = next_level;
        }
        hex::encode(&level[0])
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("█▄ [C5-REAL] CLAUDE CODE BFT INTERCEPTOR (HARDENED MCTS)");

    let ledger_path = "claude_bft_ledger.db";
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
    
    // Generar clave HMAC estática para demo (en prod vendría de HSM o env)
    let env_key = std::env::var("CORTEX_BFT_KEY").unwrap_or_else(|_| "CORTEX_BFT_KEY_2026_MASTER_LEDGER_FALLBACK".to_string());
    let key = hmac::Key::new(hmac::HMAC_SHA256, env_key.as_bytes());

    let ledger = Arc::new(Mutex::new(BftLedger {
        conn,
        last_hash: genesis,
        key,
        all_hashes: Vec::new(),
    }));

    let shutdown_flag = Arc::new(AtomicBool::new(false));

    // 1. Manejador de señales (Graceful SIGTERM/SIGINT)
    let mut signals = Signals::new(&[SIGINT, SIGTERM])?;
    let sf = Arc::clone(&shutdown_flag);
    thread::spawn(move || {
        for _sig in signals.forever() {
            sf.store(true, Ordering::SeqCst);
            break;
        }
    });

    // 2. Monitoreo inotify de ~/.claude
    let home = env::var("HOME").unwrap_or_else(|_| "/root".to_string());
    let claude_dir = format!("{}/.claude", home);
    
    let l_fs = Arc::clone(&ledger);
    let s_fs = Arc::clone(&shutdown_flag);
    
    if Path::new(&claude_dir).exists() {
        thread::spawn(move || {
            if let Ok(mut inotify) = Inotify::init() {
                let _ = inotify.watches().add(
                    Path::new(&claude_dir),
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

    // 3. Subproceso CLI (Bypass de recursión infinita)
    let real_cli = env::var("REAL_CLAUDE_PATH").unwrap_or_else(|_| "npx".to_string());
    let mut cmd = Command::new(&real_cli);
    if real_cli == "npx" {
        cmd.arg("-y").arg("@anthropic-ai/claude-code");
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
        println!("█▄ [C5-REAL] CIERRE CAUSAL EJECUTADO");
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
