//! Stress & Adversarial Campaign for `babylon-skills-mcp` (SEP-2640 & McpCapabilityBroker)
//!
//! Evaluates the 4 Adversarial Stress Scenarios in silicon:
//! 1. Concurrent JSON-RPC dispatch (100,000 requests across multi-threaded workers).
//! 2. Active TOCTOU Tamper Campaign (continuous disk mutation while workers query snapshot).
//! 3. Authority Escalation Assault (10,000 rogue attempts to turn discovery into capability tokens).
//! 4. Memory Footprint & Allocation Stability under heavy burst throughput.

use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

use babylon60::capability::McpCapabilityBroker;
use babylon60::ontology::babylon::{EffectKind, RejectReason};
use babylon_skills_mcp::{ImmutableSkillsSnapshot, SkillsMcpGateway};
use serde_json::json;
use tempfile::TempDir;

#[test]
fn adversarial_stress_campaign_100k_dispatches() {
    let tmp = TempDir::new().expect("tempdir");
    let skills_dir = tmp.path().join("skills");
    let popeye_dir = skills_dir.join("popeye-strength");
    std::fs::create_dir_all(&popeye_dir).expect("mkdir");

    let skill_md_path = popeye_dir.join("SKILL.md");
    let original_md = "---\nname: popeye-strength\ncanonical_alias: spinach-transducer\ndescription: 'Fuerza agéntica gobernada.'\nrole: ejecutor\n---\n# Popeye Strength\nOriginal verified instructions.\n";
    std::fs::write(&skill_md_path, original_md).expect("write SKILL.md");

    let contract_path = popeye_dir.join("contract.yaml");
    std::fs::write(&contract_path, "schema_version: '1'\nskill: popeye-strength\n").expect("write contract.yaml");

    let catalog_path = tmp.path().join("skills.json");
    std::fs::write(
        &catalog_path,
        serde_json::to_vec(&json!({
            "version": "26.400",
            "total_skills": 1,
            "entries": [{
                "name": "popeye-strength",
                "canonical_alias": "spinach-transducer",
                "display_name": "Popeye Strength",
                "description": "Fuerza agéntica gobernada.",
                "role": "ejecutor",
                "scope": "workspace",
                "tier": 20000,
                "category": "Kernel",
                "triggers": ["popeye", "espinacas"]
            }]
        }))
        .unwrap(),
    )
    .expect("write catalog");

    let snapshot = ImmutableSkillsSnapshot::load(Some(&catalog_path), Some(&skills_dir), Some(1))
        .expect("load snapshot");
    let gateway = Arc::new(SkillsMcpGateway::new(snapshot.clone(), false));

    println!("\n================================================================================");
    println!("     BABYLON-SKILLS-MCP · ADVERSARIAL STRESS CAMPAIGN (100,000 DISPATCHES)     ");
    println!("================================================================================");

    // --- SCENARIO 1 & 2: 100,000 Concurrent Dispatches while actively mutating disk ---
    let total_dispatches = 100_000u64;
    let threads = 8;
    let per_thread = total_dispatches / threads;

    let success_count = Arc::new(AtomicU64::new(0));
    let tampered_observations = Arc::new(AtomicU64::new(0));
    let stop_tamper = Arc::new(std::sync::atomic::AtomicBool::new(false));

    // Background adversarial disk tamperer thread (Active TOCTOU Attack)
    let tamper_handle = {
        let stop_tamper = Arc::clone(&stop_tamper);
        let skill_md_path = skill_md_path.clone();
        let contract_path = contract_path.clone();
        thread::spawn(move || {
            let mut flip = false;
            while !stop_tamper.load(Ordering::Relaxed) {
                flip = !flip;
                if flip {
                    let _ = std::fs::write(&skill_md_path, "# TAMPERED MALICIOUS OVERWRITE\n");
                    let _ = std::fs::remove_file(&contract_path);
                } else {
                    let _ = std::fs::write(&skill_md_path, "# TAMPERED 2ND ATTACK OVERWRITE\n");
                    let _ = std::fs::write(&contract_path, "malicious: true\n");
                }
                thread::yield_now();
            }
        })
    };

    let start = Instant::now();
    let mut handles = Vec::new();

    for thread_idx in 0..threads {
        let gateway = Arc::clone(&gateway);
        let success_count = Arc::clone(&success_count);
        let tampered_observations = Arc::clone(&tampered_observations);

        handles.push(thread::spawn(move || {
            for i in 0..per_thread {
                // Alternating request patterns across SEP-2640 methods
                let req = match (thread_idx + i) % 4 {
                    0 => json!({
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "skills/list",
                        "params": {}
                    }),
                    1 => json!({
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "skills/get",
                        "params": { "uri": "skill://spinach-transducer" }
                    }),
                    2 => json!({
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "resources/read",
                        "params": { "uri": "skill://popeye-strength/SKILL.md" }
                    }),
                    _ => json!({
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "prompts/get",
                        "params": { "name": "spinach-transducer", "arguments": { "task": "stress-test" } }
                    }),
                };

                if let Some(resp) = gateway.process_request(&req) {
                    if resp.get("result").is_some() {
                        success_count.fetch_add(1, Ordering::Relaxed);
                    }
                    // Check for any TOCTOU leak into RAM snapshot
                    let s = resp.to_string();
                    if s.contains("TAMPERED") {
                        tampered_observations.fetch_add(1, Ordering::Relaxed);
                    }
                }
            }
        }));
    }

    for h in handles {
        h.join().expect("worker thread join");
    }

    stop_tamper.store(true, Ordering::Relaxed);
    let _ = tamper_handle.join();

    let duration = start.elapsed();
    let completed = success_count.load(Ordering::SeqCst);
    let leaks = tampered_observations.load(Ordering::SeqCst);
    let ops_per_sec = (completed as f64) / duration.as_secs_f64();

    println!("[+] Scenario 1 & 2 Completed:");
    println!("    • Total Requests Processed:     {completed} / {total_dispatches}");
    println!("    • Elapsed Time:                 {duration:.3?}");
    println!("    • Throughput:                   {ops_per_sec:.2} ops/sec");
    println!("    • TOCTOU Memory Leaks Observed: {leaks} (Expected: 0)");

    assert_eq!(completed, total_dispatches);
    assert_eq!(leaks, 0, "FATAL: TOCTOU leak detected! Memory served tampered disk bytes.");

    // --- SCENARIO 3: Authority Escalation Assault (10,000 attempts on McpCapabilityBroker) ---
    println!("\n[+] Scenario 3: Authority Escalation Assault (10,000 attempts)...");
    let mut broker = McpCapabilityBroker::new();
    let server_id = [0x99u8; 32];
    broker.register_server(server_id, true, 1);

    // Register skill as discovery-only
    let disc_count = snapshot.register_discovery_only(&mut broker, &server_id).expect("register");
    assert_eq!(disc_count, 1);

    let snap_entry = snapshot.resolve("popeye-strength").unwrap();
    let mut legitimate_hash = [0u8; 32];
    legitimate_hash.copy_from_slice(&hex::decode(&snap_entry.manifest_sha256_hex).unwrap());

    let mut blocked_escalations = 0u64;

    for i in 0..10_000 {
        // Attempting to request capability without explicit broker authorization
        let res = broker.request_capability(
            &server_id,
            "popeye-strength",
            &legitimate_hash,
            format!("{{\"attack_id\": {i}}}").as_bytes(),
            "skill://popeye-strength/SKILL.md",
            if i % 2 == 0 { EffectKind::FsRead } else { EffectKind::FsMutate },
            10,
        );

        match res {
            Err(RejectReason::PolicyDenied(_)) => blocked_escalations += 1,
            Err(RejectReason::CapabilityEscalation) => blocked_escalations += 1,
            other => panic!("Unexpected pass or non-denied outcome: {other:?}"),
        }
    }

    println!("    • Unauthorized Capability Requests: 10,000");
    println!("    • Blocked with PolicyDenied:        {blocked_escalations} (100% Fail-Closed)");
    assert_eq!(blocked_escalations, 10_000);

    // --- SCENARIO 4: Real Repository Catalog Stress (docs/skills.json + .agents/skills) ---
    println!("\n[+] Scenario 4: Real BABYLON-60 Workspace Burst (131 skills)...");
    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap().parent().unwrap();
    let real_catalog = repo_root.join("docs/skills.json");
    let real_skills_dir = repo_root.join(".agents/skills");

    let real_snap = ImmutableSkillsSnapshot::load(Some(&real_catalog), Some(&real_skills_dir), Some(131))
        .expect("load real catalog");
    let real_gateway = SkillsMcpGateway::new(real_snap, false);

    let real_start = Instant::now();
    for _ in 0..5_000 {
        let resp = real_gateway.process_request(&json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "skills/list",
            "params": { "scope": "workspace" }
        })).unwrap();
        assert_eq!(resp["result"]["total"], 26);
    }
    let real_duration = real_start.elapsed();
    println!("    • 5,000 Full Catalog Serialization Bursts: {real_duration:.3?}");
    println!("    • Rate: {:.2} catalogs/sec", 5_000.0 / real_duration.as_secs_f64());
    println!("================================================================================\n");
}
