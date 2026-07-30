use alloy::primitives::TxHash;
use alloy::providers::{Provider, ProviderBuilder};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc::Receiver;
use tokio::time::{sleep, Duration};
use crate::dashboard::Babylon60State;

// Monitor de salida: T+300s o Multiplicador 100x
pub async fn run_sell_monitor(
    mut bought_rx: Receiver<(String, TxHash)>,
    _private_key: &str,
    rpc_url: &str,
    state: Arc<Mutex<Babylon60State>>,
) {
    let provider = Arc::new(ProviderBuilder::new().connect_http(rpc_url.parse().unwrap()));

    println!(">>> [SELL MONITOR] Activo. Esperando confirmaciones de compra...");

    while let Some((ca, buy_tx_hash)) = bought_rx.recv().await {
        let state_clone = Arc::clone(&state);
        let provider_clone = Arc::clone(&provider);
        let ca_clone = ca.clone();

        tokio::spawn(async move {
            println!(">>> [MONITOR] Iniciando vigilancia para: {}", ca_clone);

            // 1. Esperar confirmación de la tx de compra
            let mut confirmed = false;
            for _ in 0..10 {
                if let Ok(Some(receipt)) = provider_clone.get_transaction_receipt(buy_tx_hash).await {
                    if receipt.status() {
                        confirmed = true;
                        break;
                    }
                }
                sleep(Duration::from_secs(2)).await;
            }

            if !confirmed {
                let mut s = state_clone.lock().unwrap();
                s.log.push(format!("[MONITOR❌] Compra fallida para {}", &ca_clone[..10]));
                return;
            }

            // 2. Loop de Vigilancia (Max 5 minutos)
            let start_time = std::time::Instant::now();
            let sell_after = Duration::from_secs(300); // 5 minutos

            loop {
                let elapsed = start_time.elapsed();

                // Simulación de chequeo de precio / PnL
                // En C5-REAL: llamar a uniswap_v2_router.getAmountsOut()
                let current_price_multiplier = 1.0 + (elapsed.as_secs_f64() * 0.5); // Simulación de pump

                if elapsed >= sell_after || current_price_multiplier >= 100.0 {
                    println!(">>> [MONITOR] GATILLO DE VENTA DETECTADO (T+5m o 100x). Ejecutando liquidación...");

                    // 3. Ejecutar Liquidación
                    // Nota: En producción llamamos a executor.liquidate()

                    let mut s = state_clone.lock().unwrap();
                    let profit = 0.05 * (current_price_multiplier - 1.0);
                    s.pnl_eth += profit;
                    s.log.push(format!("[VENDIDO💰] CA:{} Profit: {:.4} ETH", &ca_clone[..10], profit));
                    break;
                }

                // Honeypot Check (Simulado)
                // eth_call para ver si transfer() revierte

                sleep(Duration::from_secs(5)).await;
            }
        });
    }
}
