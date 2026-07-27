mod pfof_engine;
mod proxy;
mod router;

use axum::{
    routing::post,
    Router,
};
use std::sync::Arc;
use tracing::info;

use router::{handle_rpc, CartelState};
use pfof_engine::PfofEngine;
use proxy::UpstreamProxy;

// Dirección del nodo público o base
const UPSTREAM_NODE: &str = "http://127.0.0.1:8545"; // Ej. Anvil o Reth local
const BIND_ADDRESS: &str = "0.0.0.0:3000";

#[tokio::main]
async fn main() {
    // Inicialización del Logger
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();
        
    info!("Iniciando MOSKV-1 APEX RPC Cártel (PFOF Router)...");

    let state = Arc::new(CartelState {
        pfof: PfofEngine::new(),
        proxy: UpstreamProxy::new(UPSTREAM_NODE.to_string()),
    });

    let app = Router::new()
        .route("/", post(handle_rpc))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind(BIND_ADDRESS).await.unwrap();
    info!("Escuchando tráfico de la red en {}", BIND_ADDRESS);
    info!("Enrutamiento benigno apuntando a {}", UPSTREAM_NODE);
    
    axum::serve(listener, app).await.unwrap();
}
