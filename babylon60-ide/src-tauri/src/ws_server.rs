use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
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

pub async fn start_server() {
    let app = Router::new().route("/ws", get(ws_handler));
    let listener = tokio::net::TcpListener::bind("127.0.0.1:4000").await.unwrap();
    println!("Daemon RPC/WS server listening on {}", listener.local_addr().unwrap());
    axum::serve(listener, app).await.unwrap();
}

async fn ws_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
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
            // TODO: Route the 17 identified Tauri IPC commands here
            RpcResponse {
                result: Some(serde_json::json!({ "status": "acknowledged", "command": request.command })),
                error: None,
            }
        }
        Err(e) => RpcResponse {
            result: None,
            error: Some(format!("Invalid JSON-RPC format: {}", e)),
        }
    }
}
