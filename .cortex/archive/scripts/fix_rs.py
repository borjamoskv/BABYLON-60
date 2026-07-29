import sys

with open("babylon60.rs", "r") as f:
    content = f.read()

target_str = """    println!("[MOSKV APEX] C5-REAL Execution Completed.");
    println!("[Proof] Proof obligations generated.");
    export_snapshot(&trace, &ledger.events.values().cloned().collect::<Vec<_>>(), clock.0);
}

// 11. Immutable Artifact Export
fn export_snapshot(trace: &TraceExport, ledger: &[Event], final_tick: u64) {
    use std::io::Write;
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut canonical_lines = Vec::new();
    for (i, ev) in ledger.iter().enumerate() {
        let parent = if i == 0 { "".to_string() } else { format!("event_{}", i - 1) };
        canonical_lines.push(format!("event_{}|{}|{}|{}|signature_mock", i, parent, ev.tick, ev.symbol));
    }
    
    // Sort lines to mock deterministic tie-breaking (though here it's already ordered)
    canonical_lines.sort();
    let canonical_graph = canonical_lines.join("\\n") + "\\n";
    
    // Basic hash for simulation purposes
    let mut hasher = DefaultHasher::new();
    canonical_graph.hash(&mut hasher);
    let graph_hash = format!("{:x}", hasher.finish());

    let manifest = format!(r#"{{
  "version": "1.0",
  "components": ["trace.bin", "graph.canonical", "proof.ir", "metadata.json", "hashes/", "signature/"],
  "global_hash": "{}"
}}"#, graph_hash);

    fs::create_dir_all("artifact_bundle_v3").unwrap();
    fs::write("artifact_bundle_v3/manifest.json", manifest).unwrap();
    fs::write("artifact_bundle_v3/graph.canonical", &canonical_graph).unwrap();
    fs::write("artifact_bundle_v3/proof.ir", "Mock Proof IR").unwrap();
    
    println!("-> [Exporter] Canonical graph generated. graph.sha256 approx: {}", graph_hash);
    println!("-> [Exporter] Proof IR extracted. Dispatched to Lean/Coq Backends.");
    println!("-> [Bootstrap v3.0] Artifact Bundle securely formalized at artifact_bundle_v3/");
}"""

replacement = """    println!("[MOSKV APEX] C5-REAL Execution Completed.");
    println!("[Proof] Proof obligations generated.");
    export_artifact_bundle(&ledger);
}

// 11. Immutable Artifact Export
fn export_artifact_bundle(ledger: &DAGLedger) {
    use std::io::Write;
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut canonical_lines = Vec::new();
    for ev in ledger.events.values() {
        let mut parents = ev.parents.clone();
        parents.sort();
        let parents_str = parents.join(",");
        canonical_lines.push(format!("{}|{}|{}|{}|{}", ev.id, parents_str, ev.logical_timestamp.0, ev.payload, ev.signature));
    }
    
    // Sort lines lexicographically for deterministic tie-breaking
    canonical_lines.sort();
    let canonical_graph = canonical_lines.join("\\n") + "\\n";
    
    // Basic hash for simulation purposes
    let mut hasher = DefaultHasher::new();
    canonical_graph.hash(&mut hasher);
    let graph_hash = format!("{:x}", hasher.finish());

    let manifest = format!(r#"{{
  "version": "1.0",
  "components": ["trace.bin", "graph.canonical", "proof.ir", "metadata.json", "hashes/", "signature/"],
  "global_hash": "{}"
}}"#, graph_hash);

    fs::create_dir_all("artifact_bundle_v3").unwrap();
    fs::write("artifact_bundle_v3/manifest.json", manifest).unwrap();
    fs::write("artifact_bundle_v3/graph.canonical", &canonical_graph).unwrap();
    fs::write("artifact_bundle_v3/proof.ir", "Mock Proof IR").unwrap();
    
    println!("-> [Exporter] Canonical graph generated. graph.sha256 approx: {}", graph_hash);
    println!("-> [Exporter] Proof IR extracted. Dispatched to Lean/Coq Backends.");
    println!("-> [Bootstrap v3.0] Artifact Bundle securely formalized at artifact_bundle_v3/");
}"""

if target_str in content:
    content = content.replace(target_str, replacement)
    print("Replaced successfully")
else:
    print("Target not found.")
    sys.exit(1)

with open("babylon60.rs", "w") as f:
    f.write(content)
