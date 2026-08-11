use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    routing::get,
    Router,
};
use futures_util::{sink::SinkExt, stream::StreamExt};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Deserialize, Debug)]
struct RpcRequest {
    command: String,
    args: Option<Value>,
}

#[derive(Serialize, Debug)]
struct RpcResponse {
    result: Option<Value>,
    error: Option<String>,
}

/// A browser attacker page always carries a real cross-site `Origin` header
/// (browsers forbid scripts from spoofing it), so an Origin allowlist here is
/// the correct defense against cross-site WebSocket hijacking (CSWSH).
/// Native Tauri/CLI clients send no Origin at all.
fn origin_allowed(origin: Option<&str>) -> bool {
    match origin {
        None => true, // native, non-browser client (Tauri webview / CLI)
        Some(o) => {
            o == "tauri://localhost"
                || o == "https://tauri.localhost"
                || o.starts_with("http://localhost")
                || o.starts_with("http://127.0.0.1")
        }
    }
}

pub async fn start_server() {
    let app = Router::new().route("/ws", get(ws_handler));
    let listener = tokio::net::TcpListener::bind("127.0.0.1:4000").await.unwrap();
    println!("Daemon RPC/WS server listening on {}", listener.local_addr().unwrap());
    axum::serve(listener, app).await.unwrap();
}

async fn ws_handler(headers: HeaderMap, ws: WebSocketUpgrade) -> Response {
    // Anti-CSWSH gate: reject cross-site browser origins before upgrading.
    let origin = headers.get("origin").and_then(|v| v.to_str().ok());
    if !origin_allowed(origin) {
        return (StatusCode::FORBIDDEN, "ORIGIN_NOT_ALLOWED").into_response();
    }
    ws.on_upgrade(handle_socket).into_response()
}

async fn handle_socket(mut socket: WebSocket) {
    while let Some(Ok(msg)) = socket.next().await {
        if let Message::Text(text) = msg {
            let res = process_rpc(&text).await;
            if let Ok(json_res) = serde_json::to_string(&res) {
                let _ = socket.send(Message::Text(json_res)).await;
            }
        }
    }
}

async fn process_rpc(text: &str) -> RpcResponse {
    let req: Result<RpcRequest, _> = serde_json::from_str(text);
    match req {
        Ok(request) => {
            // SECURITY (do this BEFORE wiring the 17 Tauri IPC commands):
            // browser WebSocket clients cannot set custom headers, so gate every
            // fs/exec-bearing command with an app-level token carried in `args`,
            // compared in constant time against CORTEX_BFT_KEY — mirroring the
            // auth_token check already enforced in src-tauri/src/llm_bridge.rs.
            RpcResponse {
                result: Some(serde_json::json!({ "status": "acknowledged", "command": request.command })),
                error: None,
            }
        }
        Err(e) => RpcResponse {
            result: None,
            error: Some(format!("Invalid JSON-RPC format: {}", e)),
        },
    }
}
