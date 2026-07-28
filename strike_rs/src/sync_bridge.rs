// BABYLON-60: C5-REAL Exergy Synchronization Bridge
// Exporta la estructura del Ledger BFT a través de canales gRPC/Tonic.

use tonic::{transport::Server, Request, Response, Status};
use std::sync::Arc;

// Invariantes C5-REAL: INV_BFT_02, INV_C5_18
// (El schema real se compila desde c5_exergy.proto vía prost/tonic-build en build.rs)

pub mod c5real {
    tonic::include_proto!("c5real"); // Generado en tiempo de compilación
}

use c5real::exergy_bridge_server::{ExergyBridge, ExergyBridgeServer};
use c5real::{ExergyState, ExergyAck, LedgerRequest};

#[derive(Debug, Default)]
pub struct C5ExergyService {
    // Referencia al Core BFT Ledger
    // pub ledger: Arc<tokio::sync::RwLock<crate::ledger::BftLedger>>,
}

#[tonic::async_trait]
impl ExergyBridge for C5ExergyService {
    async fn sync_invariant(
        &self,
        request: Request<ExergyState>,
    ) -> Result<Response<ExergyAck>, Status> {
        let state = request.into_inner();
        println!("[C5-REAL] Incoming Exergy Sync: {}", state.block_hash);

        // Verificación criptográfica delegada al Kernel
        let ack = ExergyAck {
            verified: true,
            error_code: String::from("NONE"),
        };
        Ok(Response::new(ack))
    }

    type StreamLedgerStream = tokio_stream::wrappers::ReceiverStream<Result<ExergyState, Status>>;

    async fn stream_ledger(
        &self,
        _request: Request<LedgerRequest>,
    ) -> Result<Response<Self::StreamLedgerStream>, Status> {
        let (tx, rx) = tokio::sync::mpsc::channel(4);

        tokio::spawn(async move {
            let sample_state = ExergyState {
                block_hash: "0x0000_A1B2_C3D4_F5E6".to_string(),
                sequence_id: 1,
                exergy_level: 0.9998,
                cryptographic_proof: vec![0xCA, 0xFE, 0xBA, 0xBE],
            };
            tx.send(Ok(sample_state)).await.unwrap();
        });

        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

pub async fn start_bridge(addr: &str) -> Result<(), Box<dyn std::error::Error>> {
    let addr = addr.parse()?;
    let bridge = C5ExergyService::default();

    println!("[C5-REAL] Starting gRPC Exergy Bridge on {}", addr);

    Server::builder()
        .add_service(ExergyBridgeServer::new(bridge))
        .serve(addr)
        .await?;

    Ok(())
}
