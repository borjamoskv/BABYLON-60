/// SOVEREIGN EXECUTOR — BABYLON60 CSE ACTION DISPATCHER
/// Asimilado de paradigmxyz/artemis | Ley Ω₁ (Frontera Determinista)
/// Recibe SovereignAction y despacha al executor correcto.

use anyhow::Result;
use async_trait::async_trait;

use crate::types::{Executor, SovereignAction};
use crate::flashbots_executor::fire_genesis_snipe;
use crate::dashboard::Babylon60State;
use std::sync::{Arc, Mutex};

pub struct SovereignExecutor {
    pub private_key: String,
    pub flashbots_key: String,
    pub rpc_http_url: String,
    pub executor_contract: alloy::primitives::Address,
    pub state: Arc<Mutex<Babylon60State>>,
}

#[async_trait]
impl Executor<SovereignAction> for SovereignExecutor {
    async fn execute(&self, action: SovereignAction) -> Result<()> {
        match action {
            SovereignAction::FlashbotsSnipe { token_ca, amount_eth } => {
                tracing::info!("[EXECUTOR] SNIPE → CA:{token_ca} amount:{amount_eth}Ξ");

                match fire_genesis_snipe(
                    &self.private_key,
                    &self.flashbots_key,
                    &self.rpc_http_url,
                    self.executor_contract,
                    &token_ca,
                ).await {
                    Ok(tx_hash) => {
                        let mut st = self.state.lock().unwrap();
                        st.snipes_executed += 1;
                        st.log.push(format!("[SNIPE✅] CA:{} TX:{:?}", &token_ca[..10.min(token_ca.len())], tx_hash));
                        tracing::info!("[EXECUTOR] SNIPE confirmado. TX:{:?}", tx_hash);
                    },
                    Err(e) => {
                        let mut st = self.state.lock().unwrap();
                        st.log.push(format!("[SNIPE❌] {e}"));
                        tracing::error!("[EXECUTOR] SNIPE fallido: {e}");
                    }
                }
            },

            SovereignAction::StrikeExploit { ca, payload: _ } => {
                tracing::info!("[EXECUTOR][STRIKE] EXPLOIT → CA:{ca}");
                let mut st = self.state.lock().unwrap();
                st.log.push(format!("[STRIKE🔥] Atacando contrato vulnerable: {}", ca));

                // [Fase 7]: Despachar via Flashbots para evitar frontrunning
                // match fire_v4_strike(...)
            },

            SovereignAction::SellPosition { token_ca, tx_hash } => {
                // [Fase 3]: Implementar sell via Flashbots
                tracing::info!("[EXECUTOR] SELL → CA:{token_ca} (post TX:{tx_hash})");
            },

            SovereignAction::LogOnly(msg) => {
                tracing::info!("[EXECUTOR] {msg}");
                let mut st = self.state.lock().unwrap();
                st.log.push(msg);
            },
        }
        Ok(())
    }
}
