use epistemic_engine::epistemic;
use std::fs;
use std::path::PathBuf;

epistemic! {
    graph security_audit {
        UserRequest -> TokenValidation [0.99];
        TokenValidation -> PolicyEngine [0.95];
        PolicyEngine -> DatabaseCommit [1.0];
    }
}

fn main() {
    // The macro should have generated CORTEX_SANEDRIN_DOT inside the `states` module
    let dot = states::CORTEX_SANEDRIN_DOT;
    
    // Assert it contains the specific shapes, colors and edges
    assert!(dot.contains("digraph security_audit"));
    assert!(dot.contains("UserRequest -> TokenValidation [label=\"0.99\"]"));
    assert!(dot.contains("TokenValidation -> PolicyEngine [label=\"0.95\"]"));
    assert!(dot.contains("PolicyEngine -> DatabaseCommit [label=\"1\"]"));
    assert!(dot.contains("fillcolor=\"#0A0A0A\""));
    assert!(dot.contains("fontcolor=\"#2B3BE5\""));

    // Write it to disk for external auditory (Sanedrin)
    let out_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string());
    let mut path = PathBuf::from(out_dir);
    path.push("target");
    let _ = fs::create_dir_all(&path);
    path.push("cortex_sanedrin_audit.dot");
    
    fs::write(&path, dot).expect("Failed to write the DOT artifact for external audit");
    
    println!("Sanedrin Audit Target generated at: {}", path.display());
}
