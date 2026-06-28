use epistemic_engine::{epistemic, Inference, Transition};
use std::fs;
use std::path::PathBuf;

epistemic! {
    graph bft_consensus {
        RawTelemetry -> NodeValidation [0.99];
        NodeValidation -> QuorumAssertion [0.95];
        QuorumAssertion -> MerkleTreeCommit [1.0];
        MerkleTreeCommit -> StateFinality [1.0];
    }
}

fn main() {
    println!("[BFT] Initializing Byzantine Fault Tolerant Consensus...");
    let evidence = Inference::<states::RawTelemetry>::new("Incoming node state telemetry".to_string(), 1.0);
    
    let step1: Inference<states::NodeValidation> = evidence.apply();
    let step2: Inference<states::QuorumAssertion> = step1.apply();
    let step3: Inference<states::MerkleTreeCommit> = step2.apply();
    let final_node: Inference<states::StateFinality> = step3.apply();
    
    println!("Final Ledger State Confidence: {:.2}", final_node.confidence);

    let dot = states::CORTEX_SANEDRIN_DOT;
    let mut path = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
    path.push("target");
    let _ = fs::create_dir_all(&path);
    path.push("poc_bft.dot");
    fs::write(&path, dot).unwrap();
    println!("[BFT] Emitido: {}", path.display());
}
