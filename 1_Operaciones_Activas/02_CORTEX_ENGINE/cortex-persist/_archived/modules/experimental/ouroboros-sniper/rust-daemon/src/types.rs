/// OUROBOROS SNIPER — BABYLON60 CSE TYPE LAYER
/// Asimilado de paradigmxyz/artemis | Ley Ω₄ (Soberanía Arquitectónica)
/// Collector → Strategy → Executor: O(1) event loop.

use anyhow::Result;
use async_trait::async_trait;
use std::pin::Pin;
use tokio_stream::Stream;

// ── Stream de eventos tipado ─────────────────────────────────────
pub type CollectorStream<'a, E> = Pin<Box<dyn Stream<Item = E> + Send + 'a>>;

// ── TRAIT: Collector ─────────────────────────────────────────────
/// Fuente de señales. Cada implementación es un vector de entrada:
/// mempool, hooks V4, Telegram, Discord, Github.
#[async_trait]
pub trait Collector<E>: Send + Sync {
    async fn get_event_stream(&self) -> Result<CollectorStream<'static, E>>;
}

// ── TRAIT: Strategy ──────────────────────────────────────────────
/// Lógica pura de decisión: Event → Vec<Action>.
/// Sin I/O. Determinista. Testeable en aislamiento.
#[async_trait]
pub trait Strategy<E, A>: Send + Sync {
    async fn sync_state(&mut self) -> Result<()>;
    async fn process_event(&mut self, event: E) -> Vec<A>;
}

// ── TRAIT: Executor ──────────────────────────────────────────────
/// Envío de acciones al mundo real: Flashbots, RPC, logs.
#[async_trait]
pub trait Executor<A>: Send + Sync {
    async fn execute(&self, action: A) -> Result<()>;
}

// ── EVENTOS DEL SISTEMA ──────────────────────────────────────────
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum SovereignEvent {
    /// Señal alpha cruda (Telegram, Discord, GitHub)
    AlphaSignal(String),
    /// Nuevo pool desplegado en Uniswap V4 (address del token)
    UniswapV4PoolCreated { token: String, pool_key: String },
    /// Transacción de wallet alpha detectada en mempool
    AlphaTxDetected { wallet: String, token: String, amount_eth: f64 },
    /// Contrato detectado con bytecode listo para análisis (VSA-SDM)
    ContractDetected { ca: String, bytecode: Vec<u8> },
    /// Nuevo bloque — trigger de reevaluación de posiciones
    NewBlock(u64),
}

// ── ACCIONES DEL SISTEMA ─────────────────────────────────────────
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum SovereignAction {
    /// Ejecutar snipe vía Flashbots (CA del token objetivo)
    FlashbotsSnipe { token_ca: String, amount_eth: f64 },
    /// Ejecutar strike contra vulnerabilidad (exploit atómico)
    StrikeExploit { ca: String, payload: Vec<u8> },
    /// Salir de posición (sell)
    SellPosition { token_ca: String, tx_hash: String },
    /// Loguear sin ejecutar (modo simulación)
    LogOnly(String),
}
