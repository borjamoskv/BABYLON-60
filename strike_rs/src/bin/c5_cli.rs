use c5real::exergy_bridge_client::ExergyBridgeClient;
use c5real::LedgerRequest;
use tonic::transport::Channel;

pub mod c5real {
    tonic::include_proto!("c5real"); // Generado en tiempo de compilación por build.rs
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!(">>> [AI EXCLUSIVE USE] C5-REAL CLI Watcher Initiated");
    
    // Conectar a la interfaz nativa gRPC (sin pasar por envoy ni grpc-web proxy)
    // Nota: Aunque el servidor acepta gRPC-Web (HTTP/1.1), Tonic-Client negocia gRPC nativo por defecto,
    // o simplemente funciona si exponemos grpc en el servidor.
    // wait, el servidor Tonic tiene `accept_http1(true)` y `tonic_web::enable()`, lo que permite ambos!
    let url = "http://127.0.0.1:50051";
    let mut client = ExergyBridgeClient::connect(url).await?;
    
    println!(">>> Connected to BFT Kernel at {}", url);
    println!(">>> Streaming Exergy Telemetry...");

    let request = tonic::Request::new(LedgerRequest {
        from_sequence: 0,
    });

    let mut stream = client.stream_ledger(request).await?.into_inner();

    while let Some(state) = stream.message().await? {
        // Formato estructurado para parseo por el agente IA
        println!(
            "{{\"event\": \"bft_block\", \"sequence\": {}, \"hash\": \"{}\", \"exergy\": {:.5}}}",
            state.sequence_id, state.block_hash, state.exergy_level
        );
    }

    Ok(())
}
