// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! PoC: Oracle Nexus
//!
//! Conecta el MasterLedger, ATMS, Orchestrator, y CognitiveGateway (con Ollama).
//! Demuestra el ciclo completo de inyección de intenciones desde el kernel 
//! hasta el LLM local, y su persistencia en el DAG inmutable como ExogenousInjection.

use std::sync::Arc;
use tokio::time::Instant;

use strike_rs::ledger::MasterLedger;
use strike_rs::orchestrator::Orchestrator;
use strike_rs::gateway::circuit_breaker::CognitiveGateway;
use strike_rs::gateway::tier3::Tier3Engine;
use strike_rs::gateway::tier3_ollama::OllamaBackend;
use strike_rs::omega0::{Statement, Modality, Obligation};

#[tokio::main]
async fn main() {
    println!("🚀 STRESS TEST: ORACLE NEXUS (Orchestrator + ATMS + T3 Ollama)");
    println!("═══════════════════════════════════════════════════════════════════");

    // 1. Initialize MasterLedger
    let ledger = MasterLedger::new(":memory:").expect("Failed to create in-memory ledger");
    println!("[*] MasterLedger inicializado (Memoria)");

    // 2. Initialize Gateway (with Ollama)
    let model_name = "qwen2.5:0.5b"; 
    let backend_result = OllamaBackend::new("http://localhost:11434", model_name);
    
    let engine = match backend_result {
        Ok(backend) => Arc::new(Tier3Engine::new(Arc::new(backend))),
        Err(e) => {
            println!("❌ Fallo al inicializar HTTP Client para Ollama: {}", e);
            return;
        }
    };
    let gateway = CognitiveGateway::with_tier3(engine.clone());
    println!("[*] CognitiveGateway inicializado (Tier 3 -> {})", model_name);

    // 3. Initialize Orchestrator (Injecting Gateway as Attestor)
    let mut orchestrator = Orchestrator::new(ledger, Box::new(gateway));
    println!("[*] Orchestrator enlazado al Gateway (Attestor Interface)\n");

    // 4. Formulate an Epistemic Goal
    let goal = Statement {
        content: "Explica qué es un DAG (Directed Acyclic Graph) en 10 palabras.".into(),
        modality: Modality::Epistemic,
        obligations: vec![Obligation::Freshness], // Requiere justificación fresca (que provee ExogenousInjection)
    };

    println!("[*] Inyectando Intención: \"{}\"", goal.content);
    let start = Instant::now();

    // 5. Resolve Intent
    match orchestrator.resolve_intent(&goal, "c5-oracle-nexus").await {
        Ok(node_id) => {
            let elapsed = start.elapsed().as_millis();
            println!("✅ INTENCIÓN RESUELTA Y PERSISTIDA EN {} ms", elapsed);
            println!("   Node ID ATMS : {:?}", node_id);
            
            // Verificamos el estado en el ATMS
            let is_believed = orchestrator.atms.is_believed(node_id);
            println!("   Believed?    : {}", is_believed);

            // Fetch the justification from Ledger directly
            let json = orchestrator.ledger.get_latest_justification_json().unwrap();
            println!("\n   === Recuperado del MasterLedger ===");
            println!("   Justification (JSON): {}", json);
        }
        Err(e) => {
            println!("❌ Fallo en resolución de intent: {}", e);
        }
    }
    println!("═══════════════════════════════════════════════════════════════════");
}
