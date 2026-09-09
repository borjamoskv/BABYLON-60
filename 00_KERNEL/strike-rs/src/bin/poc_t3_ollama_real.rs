// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! PoC: Ollama Real Backend Integration
//!
//! Falsación Empírica para el Tier 3 local.
//! Conecta con `localhost:11434` e intenta usar el modelo `qwen2.5:0.5b` (o `llama3.2`).
//! Si falla (ej: Ollama no corre o no tiene el modelo), el Circuit Breaker debe manejarlo.

use std::sync::Arc;
use std::time::Instant;

use strike_rs::gateway::circuit_breaker::{CognitiveGateway, ManifoldRequest};
use strike_rs::gateway::tier3::Tier3Engine;
use strike_rs::gateway::tier3_ollama::OllamaBackend;

#[tokio::main]
async fn main() {
    println!("🚀 STRESS TEST: TIER 3 - OLLAMA REAL BACKEND");
    println!("═══════════════════════════════════════════════════════════════════");

    // 1. Initialize Backend
    // Adjust model name to one likely installed, e.g., "qwen2.5:0.5b" or "llama3.2"
    let model_name = "qwen2.5:0.5b"; 
    println!("[*] Intentando conectar con Ollama en localhost:11434 (Modelo: {})", model_name);
    
    let backend_result = OllamaBackend::new("http://localhost:11434", model_name);
    
    let engine = match backend_result {
        Ok(backend) => Arc::new(Tier3Engine::new(Arc::new(backend))),
        Err(e) => {
            println!("❌ Fallo al inicializar HTTP Client: {}", e);
            return;
        }
    };

    // 2. Gateway setup
    // Using short timeouts for T1/T2 to ensure T3 wins if it's healthy and fast.
    let gateway = CognitiveGateway::with_tier3(engine.clone());

    // Check health directly
    let health = engine.health().await;
    println!("[*] Estado de salud inicial de T3 (Ollama): {:?}", health);

    // 3. Dispatch real request
    let prompt = "Define 'entropía' en una sola frase breve.";
    let req = ManifoldRequest {
        payload_hash: 0xC5C5,
        complexity_score: 3,
        target_ring: 2, // Allowed for T3
        prompt: prompt.to_string(),
        max_tokens: 50,
    };

    println!("\n[*] Despachando prompt al Gateway: \"{}\"", prompt);
    let start = Instant::now();

    match gateway.execute_with_failover(req).await {
        Ok(response) => {
            let elapsed = start.elapsed().as_millis();
            println!("═══════════════════════════════════════════════════════════════════");
            println!("✅ INFERENCIA COMPLETADA EN {} ms", elapsed);
            println!("   Resuelto por : {}", response.resolved_by);
            println!("   Latencia int.: {} ms", response.latency_ms);
            println!("   BLAKE3 Hash  : {}", response.content_hash);
            println!("═══════════════════════════════════════════════════════════════════");
            println!("📝 OUTPUT:\n\n{}\n", response.content.trim());
            println!("═══════════════════════════════════════════════════════════════════");
        }
        Err(e) => {
            println!("❌ Fallo catastrófico (Circuit Breaker abierto): {}", e);
        }
    }
}
