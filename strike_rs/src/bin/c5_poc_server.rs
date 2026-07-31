#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("[Causal-Determinist POC] Inicializando Motor BFT...");
    
    let (_tx, rx) = tokio::sync::broadcast::channel(100);
    // Iniciar el puente gRPC-Web en el puerto 50051
    strike_rs::sync_bridge::start_bridge("127.0.0.1:50051", rx).await?;
    
    Ok(())
}
