//! Tipos y estructuras del protocolo de inferencia local para ERIDU-INFER.
//! Wire-format extraído de LM Studio (`lms_communication`), API REST OpenAI y descriptores UMA.

use serde::{Deserialize, Serialize};

/// Mensajes multiplexados del protocolo WebSocket de LM Studio (`lms_communication`).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum LmsWireMessage {
    #[serde(rename = "channelCreate")]
    ChannelCreate {
        #[serde(rename = "channelId")]
        channel_id: u32,
        endpoint: String,
        namespace: String,
        #[serde(rename = "creationParameter")]
        creation_parameter: serde_json::Value,
    },
    #[serde(rename = "channelSend")]
    ChannelSend {
        #[serde(rename = "channelId")]
        channel_id: u32,
        message: serde_json::Value,
    },
    #[serde(rename = "channelClose")]
    ChannelClose {
        #[serde(rename = "channelId")]
        channel_id: u32,
    },
    #[serde(rename = "channelError")]
    ChannelError {
        #[serde(rename = "channelId")]
        channel_id: u32,
        error: ChannelErrorPayload,
    },
    #[serde(rename = "rpcCall")]
    RpcCall {
        #[serde(rename = "callId")]
        call_id: u32,
        endpoint: String,
        namespace: String,
        parameter: serde_json::Value,
    },
    #[serde(rename = "rpcResult")]
    RpcResult {
        #[serde(rename = "callId")]
        call_id: u32,
        result: serde_json::Value,
    },
    #[serde(rename = "rpcError")]
    RpcError {
        #[serde(rename = "callId")]
        call_id: u32,
        error: ChannelErrorPayload,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChannelErrorPayload {
    pub cause: String,
}

/// Respuesta devuelta en el endpoint de sondeo HTTP `GET /lms-status`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LmsStatusResponse {
    pub package: String,
    pub version: String,
}

// ==========================================
// Tipos de la API REST Compatible con OpenAI
// ==========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatCompletionRequest {
    pub model: String,
    pub messages: Vec<ChatMessage>,
    #[serde(default)]
    pub stream: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatChoice {
    pub index: u32,
    pub message: ChatMessage,
    pub finish_reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageInfo {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatCompletionResponse {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<ChatChoice>,
    pub usage: UsageInfo,
    /// Hash criptográfico WORM de BABYLON-60 sellando la inferencia
    pub babylon_attestation_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelItem {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub owned_by: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelListResponse {
    pub object: String,
    pub data: Vec<ModelItem>,
}

// ==========================================
// Descriptores UMA y GGUF
// ==========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UmaTensorDescriptor {
    pub name: String,
    pub dims: Vec<u64>,
    pub tensor_type: u32,
    pub offset: u64,
    pub byte_size: usize,
}
