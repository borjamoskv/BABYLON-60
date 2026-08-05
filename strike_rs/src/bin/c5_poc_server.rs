// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("[Causal-Determinist POC] Inicializando Motor BFT...");
    
    let (_tx, rx) = tokio::sync::broadcast::channel(100);
    // Iniciar el puente gRPC-Web en el puerto 50051
    strike_rs::sync_bridge::start_bridge("127.0.0.1:50051", rx).await?;
    
    Ok(())
}
