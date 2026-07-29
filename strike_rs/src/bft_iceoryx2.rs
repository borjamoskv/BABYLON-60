//! Asynchronous BFT Consensus over Shared Memory using iceoryx2.
//! 
//! INV_C5_18: Zero-Worktree Swarm Scaling.
//! Nodes communicate via zero-copy shared memory to achieve high-throughput
//! Byzantine Fault Tolerance without ENOSPC or socket starvation.

use iceoryx2::prelude::*;
use iceoryx2::node::NodeBuilder;
use iceoryx2::service::ipc;
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
    let node = NodeBuilder::new().create::<ipc::Service>()?;
    let service_name = ServiceName::new(service_name_str)?;

    // Create a pub-sub service
    let service = node.service_builder(&service_name)
        .publish_subscribe::<BftMessage>()
        .open_or_create()?;

    let publisher = service.publisher_builder().create()?;

    // Send a BFT Proposal
    let mut sample = publisher.loan_uninit()?;
    sample.write_payload(BftMessage {
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
    let node = NodeBuilder::new().create::<ipc::Service>()?;
    let service_name = ServiceName::new(service_name_str)?;

    let service = node.service_builder(&service_name)
        .publish_subscribe::<BftMessage>()
        .open_or_create()?;

    let subscriber = service.subscriber_builder().create()?;

    println!("Listening for BFT Messages...");
    // Poll for messages in this PoC
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
