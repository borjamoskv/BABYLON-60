use axum::{
    body::Body,
    http::{Response, StatusCode},
};
use reqwest::Client;
use tracing::error;

pub struct UpstreamProxy {
    client: Client,
    upstream_url: String,
}

impl UpstreamProxy {
    pub fn new(upstream_url: String) -> Self {
        Self {
            client: Client::builder()
                .pool_max_idle_per_host(500) // Máximo caudal P0
                .build()
                .expect("Failed to build Upstream client"),
            upstream_url,
        }
    }

    /// Redirige peticiones benignas al nodo real
    pub async fn forward(&self, req_body: serde_json::Value) -> Result<Response<Body>, StatusCode> {
        match self.client.post(&self.upstream_url).json(&req_body).send().await {
            Ok(resp) => {
                let status = resp.status();
                let bytes = resp.bytes().await.unwrap_or_default();
                
                let mut response = Response::builder()
                    .status(status);
                
                // Mapeo básico de headers de respuesta
                response = response.header("content-type", "application/json");
                
                Ok(response.body(Body::from(bytes)).unwrap())
            }
            Err(e) => {
                error!("Upstream forward failed: {}", e);
                Err(StatusCode::BAD_GATEWAY)
            }
        }
    }
}
