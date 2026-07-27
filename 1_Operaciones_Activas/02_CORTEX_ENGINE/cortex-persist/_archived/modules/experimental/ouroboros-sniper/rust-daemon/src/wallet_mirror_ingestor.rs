use alloy::primitives::Address;
use alloy::providers::{Provider, ProviderBuilder, WsConnect};
use alloy::consensus::Transaction as _;
use futures_util::StreamExt;
use tokio::sync::mpsc::Sender;
use std::sync::{Arc, Mutex};
use crate::dashboard::Babylon60State;

/// Ingestor de clonado de billeteras (Mirroring).
/// Escucha el mempool en busca de transacciones de "Smart Money".
pub async fn run_wallet_mirror_ingestor(
    rpc_ws_url: String,
    alpha_wallets: Vec<Address>,
    signal_tx: Sender<String>,
    state: Arc<Mutex<Babylon60State>>,
) -> anyhow::Result<()> {
    println!(">>> [MIRROR] Iniciando ingestor de clonado. Alpha Wallets: {}", alpha_wallets.len());

    let ws = WsConnect::new(&rpc_ws_url);
    let provider = ProviderBuilder::new().connect_ws(ws).await?;
    let sub = provider.subscribe_pending_transactions().await?;
    let mut stream = sub.into_stream();

    while let Some(tx_hash) = stream.next().await {
        // Obtener detalle de la transacción pendiente
        if let Ok(Some(tx)) = provider.get_transaction_by_hash(tx_hash).await {
            // Verificar si el remitente (from) está en nuestra lista Alpha
            if alpha_wallets.contains(&tx.inner.signer()) {
                // Extraer el Address del contrato objetivo (Target CA)
                // Usualmente es 'to' si es una interacción directa o está embebido en el input
                if let Some(to_addr) = tx.inner.to() {
                    {
                        let mut s = state.lock().unwrap();
                        s.signals_detected += 1;
                        s.log.push(format!("[MIRROR🎯] Whale det: {:?}", tx.inner.signer()));
                    }

                    println!(">>> [MIRROR] ALPHA DETECTADO: Remitente: {:?} -> Destino: {:?}", tx.inner.signer(), to_addr);

                    // Enviamos el CA al oráculo/ejecutor
                    let ca_string = format!("{:?}", to_addr);
                    let _ = signal_tx.send(ca_string).await;
                }
            }
        }
    }

    Ok(())
}
