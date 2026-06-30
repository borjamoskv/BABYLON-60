use epistemic_engine::{epistemic, Inference, Transition};
use std::fs;
use std::path::PathBuf;

epistemic! {
    graph zero_day_discovery {
        // Causal Chain for Zero-Day Exploit Validation
        RawTraffic -> PacketInspection [0.99];
        PacketInspection -> SignatureBypass [0.85];
        SignatureBypass -> SandboxExecution [0.95];
        SandboxExecution -> MemoryCorruption [0.90];
        MemoryCorruption -> ZeroDayConfirmed [1.0];
    }
}

fn main() {
    println!("[CORTEX] Initializing Zero-Day Discovery Epistemic Graph...");
    
    // 1. Initial State: We captured anomalous raw traffic
    let initial_evidence = Inference::<states::RawTraffic>::new(
        "Encrypted payload with non-standard SSL handshake".to_string(), 
        1.0
    );
    println!("Step 0: [{}] Confidence: {:.2}", initial_evidence.value, initial_evidence.confidence);

    // 2. Propagate through the causal chain
    let step1: Inference<states::PacketInspection> = initial_evidence.apply();
    println!("Step 1: Packet Inspection -> Confidence degraded to {:.2}", step1.confidence);

    let step2: Inference<states::SignatureBypass> = step1.apply();
    println!("Step 2: Signature Bypass -> Confidence degraded to {:.2}", step2.confidence);

    let step3: Inference<states::SandboxExecution> = step2.apply();
    println!("Step 3: Sandbox Execution -> Confidence degraded to {:.2}", step3.confidence);

    let step4: Inference<states::MemoryCorruption> = step3.apply();
    println!("Step 4: Memory Corruption -> Confidence degraded to {:.2}", step4.confidence);

    // Final Node
    let final_node: Inference<states::ZeroDayConfirmed> = step4.apply();
    println!("Final : Zero-Day Confirmed -> Final Bayesian Probability: {:.2}", final_node.confidence);

    // Extract Sanedrin DOT Graph
    let dot = states::CORTEX_SANEDRIN_DOT;
    
    let out_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string());
    let mut path = PathBuf::from(out_dir);
    path.push("target");
    let _ = fs::create_dir_all(&path);
    path.push("zero_day_poc.dot");
    
    fs::write(&path, dot).expect("Failed to write DOT");
    
    println!("\n[CORTEX] Sanedrin Audit DOT Graph emitted to: {}", path.display());
}
