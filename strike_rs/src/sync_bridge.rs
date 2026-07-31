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

pub struct C5ExergyService {
    pub telemetry_rx: tokio::sync::Mutex<tokio::sync::broadcast::Receiver<(String, u64, f64, Vec<u8>)>>,
}

#[tonic::async_trait]
impl ExergyBridge for C5ExergyService {
    async fn sync_invariant(
        &self,
        request: Request<ExergyState>,
    ) -> Result<Response<ExergyAck>, Status> {
        let state = request.into_inner();
        println!("[C5-REAL] Incoming Exergy Sync: {}", state.block_hash);

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
        let (tx, rx) = tokio::sync::mpsc::channel(100);
        
        let mut bcast_rx = {
            let mut guard = self.telemetry_rx.lock().await;
            guard.resubscribe()
        };

        tokio::spawn(async move {
            loop {
                match bcast_rx.recv().await {
                    Ok((hash, seq, exergy, proof)) => {
                        let state = ExergyState {
                            block_hash: hash,
                            sequence_id: seq,
                            exergy_level: exergy,
                            cryptographic_proof: proof,
                        };
                        if tx.send(Ok(state)).await.is_err() {
                            break;
                        }
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Lagged(_)) => {
                        continue;
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Closed) => {
                        break;
                    }
                }
            }
        });

        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

pub async fn start_bridge(addr: &str, telemetry_rx: tokio::sync::broadcast::Receiver<(String, u64, f64, Vec<u8>)>) -> Result<(), Box<dyn std::error::Error>> {
    let addr = addr.parse()?;
    let bridge = C5ExergyService {
        telemetry_rx: tokio::sync::Mutex::new(telemetry_rx),
    };

    println!("[C5-REAL] Starting gRPC Exergy Bridge on {}", addr);

    let service = tonic_web::enable(ExergyBridgeServer::new(bridge));

    Server::builder()
        .accept_http1(true) // Required for tonic-web to accept HTTP/1.1 requests
        .add_service(service)
        .serve(addr)
        .await?;

    Ok(())
}
