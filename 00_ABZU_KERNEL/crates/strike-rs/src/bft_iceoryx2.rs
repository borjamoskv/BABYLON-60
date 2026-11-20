// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! Asynchronous BFT Consensus over Shared Memory using iceoryx2.
//! 
//! INV_C5_18: Zero-Worktree Swarm Scaling.
//! Nodes communicate via zero-copy shared memory to achieve high-throughput
//! Byzantine Fault Tolerance without ENOSPC or socket starvation.

use iceoryx2::prelude::*;
use std::time::Duration;

#[derive(Debug, ZeroCopySend)]
#[repr(C)]
pub struct BftMessage {
    pub sender_id: u64,
    pub view: u64,
    pub seq_num: u64,
    pub payload_hash: [u8; 32], // 32-byte Merkle root hash (INV_C5_15)
    pub signature: [u8; 64],    // Ed25519 signature
}

pub fn run_abft_publisher_poc(service_name_str: &str) -> Result<(), Box<dyn std::error::Error>> {
    let service_name = ServiceName::new(service_name_str)?;
        let node = NodeBuilder::new().create::<ipc::Service>()?;

    let service = node.service_builder(&service_name)
        .publish_subscribe::<BftMessage>()
        .open_or_create()?;

    let publisher = service.publisher_builder().create()?;

    let sample = publisher.loan_uninit()?;
    let sample = sample.write_payload(BftMessage {
        sender_id: 1,
        view: 0,
        seq_num: 1,
        payload_hash: [0; 32],
        signature: [0; 64],
    });

    sample.send()?;
    println!("Published BFT Proposal via iceoryx2 zero-copy.");

    Ok(())
}

pub fn run_abft_subscriber_poc(service_name_str: &str) -> Result<(), Box<dyn std::error::Error>> {
    let service_name = ServiceName::new(service_name_str)?;
        let node = NodeBuilder::new().create::<ipc::Service>()?;

    let service = node.service_builder(&service_name)
        .publish_subscribe::<BftMessage>()
        .open_or_create()?;

    let subscriber = service.subscriber_builder().create()?;

    println!("Listening for BFT Messages...");
    for _ in 0..10 {
        if let Some(sample) = subscriber.receive()? {
            println!(
                "Received BFT Message from node {} for view {} seq {}",
                sample.sender_id, sample.view, sample.seq_num
            );
            break;
        }
        std::thread::sleep(Duration::from_millis(100));
    }

    Ok(())
}

use crate::exergy_binary_ipc::ExergyPacket;

#[derive(Debug, ZeroCopySend)]
#[repr(C)]
pub struct IpcEnvelope {
    pub len: usize,
    pub data: [u8; 8192],
}

pub fn publish_exergy_packet(service_name_str: &str, packet: &ExergyPacket) -> Result<(), Box<dyn std::error::Error>> {
    let service_name = ServiceName::new(service_name_str)?;
        let node = NodeBuilder::new().create::<ipc::Service>()?;
    let service = node.service_builder(&service_name)
        .publish_subscribe::<IpcEnvelope>()
        .open_or_create()?;

    let publisher = service.publisher_builder().create()?;
    let packed = packet.pack()?;
    if packed.len() > 8192 {
        return Err("Payload exceeds 8192 bytes fixed envelope".into());
    }
    
    let mut env = IpcEnvelope {
        len: packed.len(),
        data: [0; 8192],
    };
    env.data[..packed.len()].copy_from_slice(&packed);
    
    let sample = publisher.loan_uninit()?;
    let sample = sample.write_payload(env);
    
    sample.send()?;
    
    Ok(())
}

pub fn subscribe_exergy_packet(service_name_str: &str) -> Result<Option<ExergyPacket>, Box<dyn std::error::Error>> {
    let service_name = ServiceName::new(service_name_str)?;
        let node = NodeBuilder::new().create::<ipc::Service>()?;
    let service = node.service_builder(&service_name)
        .publish_subscribe::<IpcEnvelope>()
        .open_or_create()?;

    let subscriber = service.subscriber_builder().create()?;
    
    if let Some(sample) = subscriber.receive()? {
        return decode_exergy_sample(&*sample).map(Some);
    }
    Ok(None)
}

/// Decodifica un sobre recibido por IPC. `len` procede de memoria compartida (C0091).
pub fn decode_exergy_sample(env: &IpcEnvelope) -> Result<ExergyPacket, Box<dyn std::error::Error>> {
    // La longitud se valida contra la capacidad antes de cortar; sin pánico ante valores fuera de rango.
    let raw = env
        .data
        .get(..env.len)
        .ok_or("sobre IPC: longitud fuera de la capacidad")?;
    Ok(ExergyPacket::unpack(raw)?)
}

#[cfg(test)]
mod c0091_tests {
    use super::*;

    #[test]
    fn decode_rejects_len_beyond_capacity_without_panic() {
        let env = IpcEnvelope {
            len: 9000,
            data: [0u8; 8192],
        };
        assert!(decode_exergy_sample(&env).is_err());
    }

    #[test]
    fn decode_rejects_invalid_payload_without_panic() {
        let env = IpcEnvelope {
            len: 4,
            data: [0u8; 8192],
        };
        assert!(decode_exergy_sample(&env).is_err());
    }
}
