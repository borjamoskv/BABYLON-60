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

#[derive(Debug)]
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

    let service = zero_copy::Service::new(&service_name)
        .publish_subscribe()
        .open_or_create::<BftMessage>()?;

    let publisher = service.publisher().create()?;

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

    let service = zero_copy::Service::new(&service_name)
        .publish_subscribe()
        .open_or_create::<BftMessage>()?;

    let subscriber = service.subscriber().create()?;

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

#[derive(Debug)]
#[repr(C)]
pub struct IpcEnvelope {
    pub len: usize,
    pub data: [u8; 8192],
}

pub fn publish_exergy_packet(service_name_str: &str, packet: &ExergyPacket) -> Result<(), Box<dyn std::error::Error>> {
    let service_name = ServiceName::new(service_name_str)?;
    let service = zero_copy::Service::new(&service_name)
        .publish_subscribe()
        .open_or_create::<IpcEnvelope>()?;

    let publisher = service.publisher().create()?;
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
    let service = zero_copy::Service::new(&service_name)
        .publish_subscribe()
        .open_or_create::<IpcEnvelope>()?;

    let subscriber = service.subscriber().create()?;
    
    if let Some(sample) = subscriber.receive()? {
        let env = &*sample;
        let unpacked = ExergyPacket::unpack(&env.data[..env.len])?;
        return Ok(Some(unpacked));
    }
    Ok(None)
}
