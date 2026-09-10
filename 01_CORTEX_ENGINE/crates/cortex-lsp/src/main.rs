//! cortex-lsp: Sovereign LSP Paracortex Server for BABYLON-60 & CORTEX.
//! Zero-DOM, Zero-Node, Stdin/Stdout JSON-RPC 2.0 Daemon.

mod actions;
mod diagnostics;
mod protocol;

use actions::ActionEngine;
use diagnostics::DiagnosticEngine;
use protocol::*;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::sync::Mutex;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    eprintln!("[🛡️ cortex-lsp] Inicializando Sovereign Paracortex Server...");

    let stdin = tokio::io::stdin();
    let stdout = tokio::io::stdout();
    let mut reader = BufReader::new(stdin);
    let writer = Arc::new(Mutex::new(stdout));

    // Cache of open documents (URI -> Content)
    let documents: Arc<Mutex<HashMap<String, String>>> = Arc::new(Mutex::new(HashMap::new()));

    loop {
        // Read Content-Length header
        let mut line = String::new();
        let bytes_read = reader.read_line(&mut line).await?;
        if bytes_read == 0 {
            break; // EOF
        }

        let line = line.trim();
        if !line.starts_with("Content-Length:") {
            continue;
        }

        let length_str = line.trim_start_matches("Content-Length:").trim();
        let content_length: usize = match length_str.parse() {
            Ok(len) => len,
            Err(_) => continue,
        };

        // Read empty delimiter line (\r\n)
        let mut delimiter = String::new();
        reader.read_line(&mut delimiter).await?;

        // Read payload exact bytes
        let mut buffer = vec![0u8; content_length];
        reader.read_exact(&mut buffer).await?;

        let body_str = match String::from_utf8(buffer) {
            Ok(s) => s,
            Err(_) => continue,
        };

        // Handle JSON-RPC message
        let request: JsonRpcRequest = match serde_json::from_str(&body_str) {
            Ok(req) => req,
            Err(_) => continue,
        };

        let method = request.method.as_str();
        let writer_clone = writer.clone();
        let docs_clone = documents.clone();

        match method {
            "initialize" => {
                let response = JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    id: request.id,
                    result: Some(serde_json::json!({
                        "capabilities": {
                            "textDocumentSync": 1, // Full document sync
                            "codeActionProvider": true,
                            "executeCommandProvider": {
                                "commands": [
                                    "c5.biometricSignOff",
                                    "c5.auditLedger"
                                ]
                            }
                        },
                        "serverInfo": {
                            "name": "cortex-lsp",
                            "version": "4.0.0-sovereign"
                        }
                    })),
                    error: None,
                };
                send_response(writer_clone, &response).await?;
            }

            "initialized" => {
                eprintln!("[✓ cortex-lsp] Handshake completado con el editor.");
            }

            "textDocument/didOpen" => {
                if let Some(params) = request.params {
                    if let Some(text_doc) = params.get("textDocument") {
                        if let (Some(uri), Some(text)) = (text_doc.get("uri").and_then(|u| u.as_str()), text_doc.get("text").and_then(|t| t.as_str())) {
                            docs_clone.lock().await.insert(uri.to_string(), text.to_string());
                            publish_diagnostics(writer_clone, uri, text).await?;
                        }
                    }
                }
            }

            "textDocument/didChange" => {
                if let Some(params) = request.params {
                    if let (Some(text_doc), Some(changes)) = (params.get("textDocument"), params.get("contentChanges")) {
                        if let (Some(uri), Some(change_list)) = (text_doc.get("uri").and_then(|u| u.as_str()), changes.as_array()) {
                            if let Some(last_change) = change_list.last() {
                                if let Some(new_text) = last_change.get("text").and_then(|t| t.as_str()) {
                                    docs_clone.lock().await.insert(uri.to_string(), new_text.to_string());
                                    publish_diagnostics(writer_clone, uri, new_text).await?;
                                }
                            }
                        }
                    }
                }
            }

            "textDocument/codeAction" => {
                let mut actions = Vec::new();
                if let Some(params) = request.params {
                    if let Some(uri) = params.get("textDocument").and_then(|t| t.get("uri")).and_then(|u| u.as_str()) {
                        actions = ActionEngine::get_code_actions(uri);
                    }
                }
                let response = JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    id: request.id,
                    result: Some(serde_json::to_value(actions)?),
                    error: None,
                };
                send_response(writer_clone, &response).await?;
            }

            "workspace/executeCommand" => {
                let id = request.id.clone();
                let params = request.params.clone();
                tokio::spawn(async move {
                    let cmd_name = params
                        .as_ref()
                        .and_then(|p| p.get("command"))
                        .and_then(|c| c.as_str())
                        .unwrap_or_default()
                        .to_string();

                    let args = params
                        .as_ref()
                        .and_then(|p| p.get("arguments"))
                        .and_then(|a| serde_json::from_value(a.clone()).ok());

                    match ActionEngine::execute_command(&cmd_name, args).await {
                        Ok(res) => {
                            let resp = JsonRpcResponse {
                                jsonrpc: "2.0".to_string(),
                                id,
                                result: Some(res),
                                error: None,
                            };
                            let _ = send_response(writer_clone, &resp).await;
                        }
                        Err(err_msg) => {
                            let resp = JsonRpcResponse {
                                jsonrpc: "2.0".to_string(),
                                id,
                                result: None,
                                error: Some(JsonRpcError {
                                    code: -32000,
                                    message: err_msg,
                                    data: None,
                                }),
                            };
                            let _ = send_response(writer_clone, &resp).await;
                        }
                    }
                });
            }

            "shutdown" => {
                let response = JsonRpcResponse {
                    jsonrpc: "2.0".to_string(),
                    id: request.id,
                    result: Some(serde_json::Value::Null),
                    error: None,
                };
                send_response(writer_clone, &response).await?;
            }

            "exit" => {
                eprintln!("[🛡️ cortex-lsp] Cerrando conexión.");
                break;
            }

            _ => {
                // Ignore unhandled notifications or return empty response for unhandled requests
                if request.id.is_some() {
                    let response = JsonRpcResponse {
                        jsonrpc: "2.0".to_string(),
                        id: request.id,
                        result: Some(serde_json::Value::Null),
                        error: None,
                    };
                    send_response(writer_clone, &response).await?;
                }
            }
        }
    }

    Ok(())
}

async fn publish_diagnostics(writer: Arc<Mutex<tokio::io::Stdout>>, uri: &str, text: &str) -> anyhow::Result<()> {
    let diags = DiagnosticEngine::audit_document(uri, text);
    let notification = JsonRpcNotification {
        jsonrpc: "2.0".to_string(),
        method: "textDocument/publishDiagnostics".to_string(),
        params: Some(serde_json::to_value(PublishDiagnosticsParams {
            uri: uri.to_string(),
            diagnostics: diags,
        })?),
    };
    send_notification(writer, &notification).await
}

async fn send_response(writer: Arc<Mutex<tokio::io::Stdout>>, response: &JsonRpcResponse) -> anyhow::Result<()> {
    let payload = serde_json::to_string(response)?;
    let message = format!("Content-Length: {}\r\n\r\n{}", payload.len(), payload);
    let mut lock = writer.lock().await;
    lock.write_all(message.as_bytes()).await?;
    lock.flush().await?;
    Ok(())
}

async fn send_notification(writer: Arc<Mutex<tokio::io::Stdout>>, notification: &JsonRpcNotification) -> anyhow::Result<()> {
    let payload = serde_json::to_string(notification)?;
    let message = format!("Content-Length: {}\r\n\r\n{}", payload.len(), payload);
    let mut lock = writer.lock().await;
    lock.write_all(message.as_bytes()).await?;
    lock.flush().await?;
    Ok(())
}
