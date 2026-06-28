use epistemic_engine::{epistemic, Inference, Transition};
use std::fs;
use std::path::PathBuf;

epistemic! {
    graph scientific_method {
        Hypothesis -> SandboxDeployment [0.95];
        SandboxDeployment -> EmpiricalExecution [0.90];
        EmpiricalExecution -> DataIngestion [0.98];
        DataIngestion -> CausalAssertion [0.85];
    }
}

fn main() {
    println!("[SCIENCE] Automated Causal Falsification Protocol...");
    let evidence = Inference::<states::Hypothesis>::new("LLM Token Degradation leads to hallucination".to_string(), 1.0);
    
    let step1: Inference<states::SandboxDeployment> = evidence.apply();
    let step2: Inference<states::EmpiricalExecution> = step1.apply();
    let step3: Inference<states::DataIngestion> = step2.apply();
    let final_node: Inference<states::CausalAssertion> = step3.apply();
    
    println!("Final Epistemic Falsification Confidence: {:.2}", final_node.confidence);

    let dot = states::CORTEX_SANEDRIN_DOT;
    let mut path = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
    path.push("target");
    let _ = fs::create_dir_all(&path);
    path.push("poc_science.dot");
    fs::write(&path, dot).unwrap();
    println!("[SCIENCE] Emitido: {}", path.display());
}
