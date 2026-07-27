/// UNISWAP V4 HOOK COLLECTOR — BABYLON60
/// Asimilado de Uniswap/v4-core | Ley Ω₄ (Soberanía Arquitectónica)
/// Escucha eventos Initialize (nuevos pools) y Swap de PoolManager V4.
/// Emite SovereignEvent::UniswapV4PoolCreated para la Strategy.

use anyhow::Result;
use async_trait::async_trait;
use alloy::sol;
use alloy::primitives::Address;
use alloy::providers::{ProviderBuilder, WsConnect};
use std::sync::Arc;
use tokio_stream::StreamExt;
use tokio_stream::wrappers::ReceiverStream;
use tokio::sync::mpsc;

use crate::types::{Collector, CollectorStream, SovereignEvent};

// ── PoolManager V4 ABI mínimo ──────────────────────────────────
// Evento: Initialize(PoolId indexed id, Currency indexed currency0, ...)
sol!(
    #[sol(rpc)]
    interface IPoolManagerV4 {
        event Initialize(bytes32 indexed id, address indexed currency0, address indexed currency1, uint24 fee, int24 tickSpacing, address hooks);
    }
);

/// Dirección del PoolManager de Uniswap V4 en Ethereum Mainnet.
/// Fuente: https://github.com/Uniswap/v4-core/blob/main/deployments.md
const POOL_MANAGER_V4_MAINNET: &str = "0x000000000004444c5dc75cB358380D2e3dE08A90";

pub struct UniswapV4HookCollector {
    ws_url: String,
    pool_manager: Address,
}

impl UniswapV4HookCollector {
    pub async fn new(ws_url: &str) -> Result<Self> {
        let pool_manager: Address = POOL_MANAGER_V4_MAINNET.parse()?;
        Ok(Self {
            ws_url: ws_url.to_string(),
            pool_manager,
        })
    }
}

#[async_trait]
impl Collector<SovereignEvent> for UniswapV4HookCollector {
    async fn get_event_stream(&self) -> Result<CollectorStream<'static, SovereignEvent>> {
        let (tx, rx) = mpsc::channel::<SovereignEvent>(256);

        let pool_manager    = self.pool_manager;
        let ws_url          = self.ws_url.clone();

        tokio::spawn(async move {
            let ws = WsConnect::new(&ws_url);
            let provider = match ProviderBuilder::new().connect_ws(ws).await {
                Ok(p) => Arc::new(p),
                Err(e) => {
                    tracing::error!("[V4 Collector] Error conectando WS: {e}");
                    return;
                }
            };
            let contract = IPoolManagerV4::new(pool_manager, provider);

            // Suscribir al evento Initialize — se emite al crear cada nuevo pool V4
            let filter = contract.Initialize_filter();
            let mut stream = match filter.subscribe().await {
                Ok(s) => s.into_stream(),
                Err(e) => {
                    tracing::error!("[V4 Collector] Error al suscribir a Initialize events: {e}");
                    return;
                }
            };

            tracing::info!("[V4 Collector] Escuchando nuevos pools en Uniswap V4 PoolManager...");

            while let Some(Ok((log, _meta))) = stream.next().await {
                let token = format!("{:?}", log.currency1); // currency1 (alloy sol! usa el nombre del parametro)
                let pool_key = format!("{:?}", log.id);

                tracing::info!("[V4 Collector] Nuevo pool: token={token} pool={pool_key}");

                let event = SovereignEvent::UniswapV4PoolCreated { token, pool_key };
                if tx.send(event).await.is_err() {
                    break; // Channel cerrado — apagar collector
                }
            }
        });

        Ok(Box::pin(ReceiverStream::new(rx)))
    }
}
