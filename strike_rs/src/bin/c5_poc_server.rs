#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("[C5-REAL POC] Inicializando Motor BFT...");
    
    // Iniciar el puente gRPC-Web en el puerto 50051
    strike_rs::sync_bridge::start_bridge("127.0.0.1:50051").await?;
    
    Ok(())
}
