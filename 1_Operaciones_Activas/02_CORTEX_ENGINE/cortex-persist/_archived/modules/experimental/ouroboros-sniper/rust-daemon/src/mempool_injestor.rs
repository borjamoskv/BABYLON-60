// ▓▓ MEMPOOL INJESTOR-OMEGA — PROYECTO GÉNESIS-Ω
// Ley Ω₀: Lógica sintetizable. Path crítico < 5ms.
// Ley Ω₉: C5-REAL — Solo transacciones on-chain verificables.

use alloy::primitives::U256;
use alloy::providers::{Provider, ProviderBuilder, WsConnect};
use alloy::consensus::Transaction as _;
use futures_util::StreamExt;
use aho_corasick::AhoCorasick;
use tokio::sync::mpsc::Sender;
use std::sync::{Arc, Mutex};
use std::time::Instant;
use crate::dashboard::Babylon60State;

/// Firmas de funciones (primeros 4 bytes del keccak256) para routers DEX conocidos.
/// Estas son las "huellas digitales" que buscamos en el mempool.
const SWAP_SIGNATURES: &[&str] = &[
    "38ed1739", // swapExactTokensForTokens (UniV2)
    "7ff36ab5", // swapExactETHForTokens (UniV2)
    "18cbafe5", // swapExactTokensForETH (UniV2)
    "fb3bdb41", // swapETHForExactTokens (UniV2)
    "5ae401dc", // multicall (UniV3 Router)
    "04e45aaf", // exactInputSingle (UniV3)
    "b858183f", // exactInput (UniV3)
    "f28c0498", // exactOutputSingle (UniV3)
    "09b81346", // exactOutput (UniV3)
    "3593564c", // execute (Universal Router / V4)
];

/// Umbrales de valor para clasificación de señales.
/// Solo procesamos transacciones que superan el umbral mínimo de exergía.
const MIN_VALUE_WEI: u128 = 100_000_000_000_000_000; // 0.1 ETH
const WHALE_VALUE_WEI: u128 = 10_000_000_000_000_000_000; // 10 ETH

/// Tipos de señal emitidos por el injestor.
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum MempoolSignal {
    /// Swap detectado: (contract_address, value_wei, is_whale, latency_us)
    SwapDetected {
        target_ca: String,
        from: String,
        value_wei: U256,
        is_whale: bool,
        latency_us: u128,
    },
    /// Creación de contrato nuevo (posible token launch)
    ContractCreation {
        deployer: String,
        latency_us: u128,
    },
}

/// Motor de ingestión de mempool de alto rendimiento.
/// Suscripción WebSocket a transacciones pendientes con matching O(1) via Aho-Corasick.
pub async fn run_mempool_injestor(
    rpc_ws_url: String,
    signal_tx: Sender<String>,
    state: Arc<Mutex<Babylon60State>>,
) -> anyhow::Result<()> {
    println!(">>> [GENESIS-Ω] Mempool Injestor ONLINE. Conectando a: {}", rpc_ws_url);

    // Construir el autómata Aho-Corasick con las firmas de swap
    let ac = AhoCorasick::new(SWAP_SIGNATURES)?;

    // Conectar al nodo via WebSocket
    let ws = WsConnect::new(&rpc_ws_url);
    let provider = ProviderBuilder::new().connect_ws(ws).await?;
    let sub = provider.subscribe_pending_transactions().await?;
    let mut stream = sub.into_stream();

    let mut total_scanned: u64 = 0;
    let mut total_matched: u64 = 0;

    println!(">>> [GENESIS-Ω] Stream de mempool activo. Esperando transacciones pendientes...");

    while let Some(tx_hash) = stream.next().await {
        total_scanned += 1;
        let t0 = Instant::now();

        // Obtener datos completos de la transacción pendiente
        let tx = match provider.get_transaction_by_hash(tx_hash).await {
            Ok(Some(tx)) => tx,
            _ => continue,
        };

        // === GATE 1: Filtro de valor mínimo (Ω₂ — Exergía) ===
        if tx.inner.value() < U256::from(MIN_VALUE_WEI) && tx.inner.to().is_some() {
            continue;
        }

        // === GATE 2: Detección de Contract Creation (sin 'to') ===
        if tx.inner.to().is_none() {
            let latency = t0.elapsed().as_micros();
            {
                let mut s = state.lock().unwrap();
                s.signals_detected += 1;
                s.log.push(format!(
                    "[GENESIS-Ω🔥] CONTRACT DEPLOY det. From: {:?} | {}μs",
                    tx.inner.signer(), latency
                ));
            }
            // Emitir señal de nuevo contrato al pipeline
            let deployer_str = format!("{:?}", tx.inner.signer());
            let _ = signal_tx.send(format!("DEPLOY:{}", deployer_str)).await;
            continue;
        }

        // === GATE 3: Matching O(1) de firmas de swap ===
        let input_hex = hex::encode(tx.inner.input());
        if input_hex.len() < 8 {
            continue;
        }

        let selector = &input_hex[..8];

        if ac.is_match(selector) {
            total_matched += 1;
            let latency = t0.elapsed().as_micros();
            let is_whale = tx.inner.value() >= U256::from(WHALE_VALUE_WEI);
            let to_addr = tx.inner.to().unwrap(); // Safe: checked above

            {
                let mut s = state.lock().unwrap();
                s.signals_detected += 1;
                let whale_tag = if is_whale { "🐋WHALE" } else { "📡STD" };
                s.log.push(format!(
                    "[GENESIS-Ω] {} SWAP: {:?} → {:?} | {} wei | {}μs | {}/{}",
                    whale_tag,
                    tx.inner.signer(),
                    to_addr,
                    tx.inner.value(),
                    latency,
                    total_matched,
                    total_scanned,
                ));
            }

            // Emitir la dirección del contrato TARGET al executor pipeline
            let ca_string = format!("{:?}", to_addr);
            let _ = signal_tx.send(ca_string).await;
        }

        // Checkpoint periódico cada 10k transacciones
        if total_scanned % 10_000 == 0 {
            let mut s = state.lock().unwrap();
            s.log.push(format!(
                "[GENESIS-Ω📊] Checkpoint: {} escaneadas, {} matched ({:.2}%)",
                total_scanned,
                total_matched,
                (total_matched as f64 / total_scanned as f64) * 100.0
            ));
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    #[test]
    fn test_aho_corasick_latency() {
        let signatures = vec![
            "38ed1739", "7ff36ab5", "18cbafe5", "fb3bdb41", "5ae401dc",
            "04e45aaf", "b858183f", "f28c0498", "09b81346", "3593564c"
        ];
        let ac = AhoCorasick::new(&signatures).unwrap();

        // Mock Uniswap V3 swap calldata (typical length)
        let input_hex = "3593564c" .to_owned() + &"0".repeat(200);

        let mut total_duration = 0;
        let iterations = 1000;

        for _ in 0..iterations {
            let start = Instant::now();
            let selector = &input_hex[..8];
            let _is_match = ac.is_match(selector);
            total_duration += start.elapsed().as_nanos();
        }

        let avg_latency_ns = total_duration / iterations as u128;
        println!(">>> [BENCHMARK] Aho-Corasick Avg Latency: {}ns", avg_latency_ns);

        // Ω₆: Latency must be < 5ms (5,000,000ns).
        // Our goal is sub-microsecond.
        assert!(avg_latency_ns < 1000);
    }
}
