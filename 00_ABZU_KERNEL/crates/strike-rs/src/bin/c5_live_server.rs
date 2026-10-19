// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
use strike_rs::bft_engine::BftAsyncEngine;
use strike_rs::kda_memory::KdaMemoryBuffer;
use strike_rs::gelabp_calc::ExergyParams;
use std::sync::Arc;
use tokio::sync::RwLock;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("[Causal-Determinist] Initializing True BFT Engine & Telemetry Broadcast...");

    // Create the AI Telemetry channel (100 capacity)
    let (tx, rx) = tokio::sync::broadcast::channel(100);

    // Spawn the BFT DAG Engine
    tokio::spawn(async move {
        loop {
            let mut engine = BftAsyncEngine::new(10);
            engine.telemetry_tx = Some(tx.clone());

            // Load an extreme stress-test DAG (150 nodes)
            engine.stress_test_native(150);

            let mem = Arc::new(RwLock::new(KdaMemoryBuffer::new(500)));
            let params = ExergyParams { g: 12.0, l: 12.0, a: 1.0, b: 1.0, p: 1.0, e_base: 0.04 };

            println!("[Causal-Determinist] Executing DAG Collapse Cycle...");
            
            // Execute the DAG
            let _ = engine.run_dag(mem.clone(), params, "").await;

            // Wait 2 seconds before the next thermodynamic cycle
            tokio::time::sleep(std::time::Duration::from_millis(2000)).await;
        }
    });

    // Start the gRPC Bridge, passing the receiver
    println!("[Causal-Determinist] Starting gRPC Exergy Bridge on 127.0.0.1:50051...");
    strike_rs::sync_bridge::start_bridge("127.0.0.1:50051", rx).await?;

    Ok(())
}
