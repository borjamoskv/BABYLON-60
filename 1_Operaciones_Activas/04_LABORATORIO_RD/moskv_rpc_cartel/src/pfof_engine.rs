
use reqwest::Client;
use tracing::{info, warn};

// Endpoints PFOF (Ejemplo: Flashbots, Beaverbuild, Titan)
const MEV_BUILDERS: &[&str] = &[
    "https://relay.flashbots.net",
    "https://rpc.beaverbuild.org",
    "https://rpc.titanbuilder.xyz",
];

pub struct PfofEngine {
    client: Client,
}

impl PfofEngine {
    pub fn new() -> Self {
        Self {
            // Optimizado para reusar conexiones y evitar overhead en handshakes
            client: Client::builder()
                .pool_max_idle_per_host(100)
                .build()
                .expect("Failed to build PFOF client"),
        }
    }

    /// Captura y envía la Tx firmada cruda a los Searchers en lugar de la Mempool pública.
    pub async fn route_to_cartel(&self, raw_tx: &str) {
        info!("PFOF INTERCEPT: Routing tx to MEV builders: {}", raw_tx);
        
        let payload = serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendRawTransaction",
            "params": [raw_tx]
        });

        // Disparo en paralelo (Fire-and-forget de alta velocidad)
        for builder_url in MEV_BUILDERS {
            let client = self.client.clone();
            let payload = payload.clone();
            let url = builder_url.to_string();
            
            tokio::spawn(async move {
                match client.post(&url).json(&payload).send().await {
                    Ok(resp) => {
                        if resp.status().is_success() {
                            info!("SUCCESS PFOF to {}", url);
                        } else {
                            warn!("FAILED PFOF to {}: Status {}", url, resp.status());
                        }
                    }
                    Err(e) => {
                        warn!("ERROR PFOF to {}: {}", url, e);
                    }
                }
            });
        }
    }
}
