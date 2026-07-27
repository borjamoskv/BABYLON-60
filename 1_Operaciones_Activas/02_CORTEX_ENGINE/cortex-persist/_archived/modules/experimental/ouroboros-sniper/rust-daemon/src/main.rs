mod github_ingestor;
mod discord_ingestor;
mod dashboard;
mod sell_monitor;
mod flashbots_executor;
mod persistence;
mod telegram_ingestor;
mod ai_oracle;
mod wallet_mirror_ingestor;
// ── CSE LAYER (Asimilado de Paradigm/Artemis) ───────────────────
mod types;
mod strategy;
mod uniswap_v4_collector;
mod sovereign_executor;
mod mempool_injestor;
mod vsa_memory;

use alloy::primitives::{Address, TxHash};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use dashboard::{Babylon60State, run_dashboard};
use telegram_ingestor::run_telegram_ingestor;
use sell_monitor::run_sell_monitor;
use wallet_mirror_ingestor::run_wallet_mirror_ingestor;
use dotenv::dotenv;
use std::env;
// CSE imports
use types::{Collector, Executor, Strategy, SovereignEvent};
use strategy::{SovereignAlphaStrategy, StrategyConfig};
use uniswap_v4_collector::UniswapV4HookCollector;
use sovereign_executor::SovereignExecutor;
use vsa_memory::VsaMemory;

#[allow(dead_code)]
const RPC_WS_URL: &str = "ws://127.0.0.1:8546";

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenv().ok();

    let api_id: i32      = env::var("TG_API_ID")?.parse()?;
    let api_hash         = env::var("TG_API_HASH")?;
    let private_key      = env::var("SOVEREIGN_PRIVATE_KEY")?;
    let executor_addr: Address = env::var("EXECUTOR_CONTRACT")?.parse()?;
    let flashbots_key    = env::var("FLASHBOTS_AUTH_KEY")?;
    let rpc_url          = env::var("RPC_HTTP_URL")?;
    let rpc_ws_url       = env::var("RPC_WS_URL").unwrap_or_else(|_| "ws://127.0.0.1:8546".to_string());

    let alpha_wallets_env = env::var("ALPHA_WALLETS").unwrap_or_default();
    let alpha_wallets: Vec<Address> = alpha_wallets_env
        .split(',')
        .filter_map(|s| s.trim().parse().ok())
        .collect();

    let state = Arc::new(Mutex::new(Babylon60State::default()));

    // Canal central: Eventos (Collector) → Strategy
    let (event_tx, mut event_rx) = mpsc::channel::<SovereignEvent>(1024);

    // Canal: MEV Executor → Sell Monitor
    let (bought_tx, bought_rx) = mpsc::channel::<(String, TxHash)>(64);

    // ── HILO 1: TELEGRAM MTProto ─────────────────────────────────────────────
    {
        let tx    = event_tx.clone();
        let s     = Arc::clone(&state);
        tokio::spawn(async move {
            let groups = vec!["AlphaCallsCrypto".to_string()];
            // Adaptador: signal String -> SovereignEvent
            let (inner_tx, mut inner_rx) = mpsc::channel::<String>(100);
            let tx_clone = tx.clone();
            tokio::spawn(async move {
                while let Some(msg) = inner_rx.recv().await {
                    let _ = tx_clone.send(SovereignEvent::AlphaSignal(msg)).await;
                }
            });
            let _ = run_telegram_ingestor(api_id, api_hash, groups, inner_tx, s).await;
        });
    }

    // ── HILO 1.1: GITHUB MONITOR ─────────────────────────────────────────────
    {
        let token = env::var("GH_TOKEN").unwrap_or_default();
        let tx    = event_tx.clone();
        let s     = Arc::clone(&state);
        tokio::spawn(async move {
            if !token.is_empty() {
                let targets = vec!["Uniswap/v2-core".to_string()];
                // Adaptador inline
                let (inner_tx, mut inner_rx) = mpsc::channel::<String>(100);
                let tx_clone = tx.clone();
                tokio::spawn(async move {
                    while let Some(msg) = inner_rx.recv().await {
                        let _ = tx_clone.send(SovereignEvent::AlphaSignal(msg)).await;
                    }
                });
                let _ = github_ingestor::run_github_monitor(token, targets, inner_tx, s).await;
            }
        });
    }

    // ── HILO 1.2: DISCORD MONITOR ────────────────────────────────────────────
    {
        let token = env::var("DISCORD_TOKEN").unwrap_or_default();
        let tx    = event_tx.clone();
        let s     = Arc::clone(&state);
        tokio::spawn(async move {
            if !token.is_empty() {
                let (inner_tx, mut inner_rx) = mpsc::channel::<String>(100);
                let tx_clone = tx.clone();
                tokio::spawn(async move {
                    while let Some(msg) = inner_rx.recv().await {
                        let _ = tx_clone.send(SovereignEvent::AlphaSignal(msg)).await;
                    }
                });
                let _ = discord_ingestor::run_discord_monitor(token, inner_tx, s).await;
            }
        });
    }

    // ── HILO 1.3: WALLET MIRRORING (Alpha Cloning) ──────────────────────────
    {
        let ws_url = rpc_ws_url.clone();
        let tx     = event_tx.clone();
        let s      = Arc::clone(&state);
        let wallets = alpha_wallets.clone();
        tokio::spawn(async move {
            let (inner_tx, mut inner_rx) = mpsc::channel::<String>(100);
            let tx_clone = tx.clone();
            tokio::spawn(async move {
                while let Some(msg) = inner_rx.recv().await {
                    let _ = tx_clone.send(SovereignEvent::AlphaSignal(msg)).await;
                }
            });
            let _ = run_wallet_mirror_ingestor(ws_url, wallets, inner_tx, s).await;
        });
    }

    // ── HILO 1.4: GÉNESIS-Ω MEMPOOL INJESTOR (O(1) Alpha Detection) ────
    {
        let ws_url = rpc_ws_url.clone();
        let tx     = event_tx.clone();
        let s      = Arc::clone(&state);
        tokio::spawn(async move {
            let (inner_tx, mut inner_rx) = mpsc::channel::<String>(100);
            let tx_clone = tx.clone();
            tokio::spawn(async move {
                while let Some(msg) = inner_rx.recv().await {
                    let _ = tx_clone.send(SovereignEvent::AlphaSignal(msg)).await;
                }
            });
            let _ = mempool_injestor::run_mempool_injestor(ws_url, inner_tx, s).await;
        });
    }

    // Nota: El HILO 2 (Executor) ahora vive dentro del CSE Loop central (Hilo 5).
    // Se elimina el bucle manual de signal_rx para centralizar la lógica en Strategy.

    // ── HILO 3: SELL MONITOR (T+5min / 100x) ────────────────────────────────
    {
        let pk   = private_key.clone();
        let rpc  = rpc_url.clone();
        let s    = Arc::clone(&state);

        tokio::spawn(async move {
            run_sell_monitor(bought_rx, &pk, &rpc, s).await;
        });
    }

    // ── HILO 3.1: PERSISTENCIA (Ledger Soberano) ──────────────────────────────
    {
        let s = Arc::clone(&state);
        tokio::spawn(async move {
            persistence::run_persistence_task("ledger.jsonl".to_string(), s).await;
        });
    }

    // ── HILO 4: DASHBOARD TUI — Thread OS bloqueante (no Tokio) ─────────────
    // CRÍTICO: run_dashboard es síncrono (crossterm). Debe correr en std::thread,
    // NO en tokio::spawn, para no bloquear el runtime async.
    {
        let s = Arc::clone(&state);
        std::thread::spawn(move || {
            let _ = run_dashboard(s);
        });
    }

    {
        let s            = Arc::clone(&state);
        let pk           = private_key.clone();
        let fb_key       = flashbots_key.clone();
        let rpc          = rpc_url.clone();
        let exec_addr    = executor_addr;
        let ws_url       = rpc_ws_url.clone();
        let _btx          = bought_tx.clone();

        tokio::spawn(async move {
            // 1. Configurar Estrategia + VSA Memory
            let memory = VsaMemory::new(Arc::clone(&s));
            let mut strategy = SovereignAlphaStrategy::new(StrategyConfig {
                snipe_amount_eth: 0.05,
                min_sell_multiplier: 3.0,
                blacklist: vec![],
                dry_run: true,
            }, memory);
            let _ = strategy.sync_state().await;

            let executor = SovereignExecutor {
                private_key: pk,
                flashbots_key: fb_key,
                rpc_http_url: rpc,
                executor_contract: exec_addr,
                state: s,
            };

            // 2. Conectar stream de Uniswap V4 (Collector)
            // Usamos un stream fusionado para el loop central
            let mut v4_stream = match UniswapV4HookCollector::new(&ws_url).await {
                Ok(c) => match c.get_event_stream().await {
                    Ok(s) => Some(s),
                    Err(_) => None,
                },
                Err(_) => None,
            };

            tracing::info!("[OUROBOROS-CSE] Cluster activado. Orquestación Soberana activa.");

            // 3. Bucle Central de Eventos
            loop {
                tokio::select! {
                    // [SIMULACIÓN] Inyectar un "Vulnerable Hook" para demostrar el Strike
                    _ = tokio::time::sleep(tokio::time::Duration::from_secs(10)), if env::args().any(|arg| arg == "--simulation") => {
                        let mock_ca = "0xFEEDFACE00000000000000000000000000000000".to_string();
                        let mock_bytecode = vec![0x60, 0x80, 0x60, 0x40, 0x52]; // Bytecode "vulnerable" simplificado

                        // Entrenamos la memoria para que reconozca este patrón como vulnerable
                        strategy.vsa_memory.add_vulnerability_pattern(&mock_bytecode);

                        let event = SovereignEvent::ContractDetected {
                            ca: mock_ca,
                            bytecode: mock_bytecode,
                        };
                        let _ = event_rx.recv().await; // Limpiar canal (opcional)
                        let actions = strategy.process_event(event).await;
                        for action in actions {
                            let _ = executor.execute(action).await;
                        }
                    }

                    // Eventos de Ingestors (Telegram/GitHub/etc)
                    Some(event) = event_rx.recv() => {
                        let actions = strategy.process_event(event).await;
                        for action in actions {
                            let _ = executor.execute(action).await;
                        }
                    }

                    // Eventos de Uniswap V4 (si el stream está activo)
                    Some(v4_event) = async {
                        if let Some(ref mut s) = v4_stream {
                            tokio_stream::StreamExt::next(s).await
                        } else {
                            std::future::pending().await
                        }
                    } => {
                        let actions = strategy.process_event(v4_event).await;
                        for action in actions {
                            let _ = executor.execute(action).await;
                        }
                    }
                }
            }
        });
    }

    // Mantener el runtime vivo hasta señal del OS
    tokio::signal::ctrl_c().await?;
    println!("\n>>> [BABYLON60] SHUTDOWN SIGNAL. Cerrando clúster.");
    Ok(())
}
