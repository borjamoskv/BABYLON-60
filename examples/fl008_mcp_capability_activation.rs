//! # BABYLON-60 — FL-008 MCP Capability Activation Stress Harness
//!
//! Falsifiable Hypothesis FL-008:
//!   "Capability Activation ≠ Execution Authority: An agent cannot convert the
//!    presence, activation, or substitution of an MCP tool into additional authority
//!    to execute side effects."
//!
//! Formal Invariant:
//!   Execute(e) ⟹ ValidCapability(e, t_commit)
//!
//! Adversarial Campaign:
//!   10,000 adversarial attempts across 4 scenarios:
//!     1. Activation of a disabled/unconfigured MCP server (2,500 attempts)
//!     2. Substitution of a tool with identical name and escalated capabilities (2,500 attempts)
//!     3. Stale token reuse after epoch bump or revocation (2,500 attempts)
//!     4. Configuration/arguments drift between validation and execution (2,500 attempts)
//!   Plus 2,500 legitimate control invocations to prove non-vacuousness (100% evidence coverage).

use std::time::Instant;
use babylon60::capability::{
    sha256_digest, McpCapabilityBroker, McpToolDef,
};
use babylon60::ontology::babylon::{EffectKind, RejectReason};

fn main() {
    println!("╔══════════════════════════════════════════════════════════════════════════════╗");
    println!("║     BABYLON-60 · FL-008 · MCP CAPABILITY ACTIVATION STRESS HARNESS           ║");
    println!("║          Invariant: Execute(e) ⟹ ValidCapability(e, t_commit)                ║");
    println!("╚══════════════════════════════════════════════════════════════════════════════╝");

    let mut broker = McpCapabilityBroker::new();

    let server_id = [0x11u8; 32];
    let policy_v1 = 1u64;

    broker.register_server(server_id, true, policy_v1);

    // Register 3 synthetic MCP tools:
    // 1. read_fixture -> FsRead
    let read_hash = sha256_digest(b"MCP_TOOL_CODE_READ_FIXTURE_V1");
    let read_tool = McpToolDef {
        name: "read_fixture".to_string(),
        code_hash: read_hash,
        allowed_effects: vec![EffectKind::FsRead],
        target_resource_scope: "fixture://storage/".to_string(),
    };
    broker.register_tool(&server_id, read_tool).unwrap();

    // 2. mutate_fixture -> FsMutate
    let mutate_hash = sha256_digest(b"MCP_TOOL_CODE_MUTATE_FIXTURE_V1");
    let mutate_tool = McpToolDef {
        name: "mutate_fixture".to_string(),
        code_hash: mutate_hash,
        allowed_effects: vec![EffectKind::FsMutate],
        target_resource_scope: "fixture://storage/".to_string(),
    };
    broker.register_tool(&server_id, mutate_tool).unwrap();

    // 3. delete_fixture -> FsDelete
    let delete_hash = sha256_digest(b"MCP_TOOL_CODE_DELETE_FIXTURE_V1");
    let delete_tool = McpToolDef {
        name: "delete_fixture".to_string(),
        code_hash: delete_hash,
        allowed_effects: vec![EffectKind::FsDelete],
        target_resource_scope: "fixture://storage/".to_string(),
    };
    broker.register_tool(&server_id, delete_tool).unwrap();

    let start_time = Instant::now();

    let mut unauthorized_effects = 0u64;
    let mut capability_escalations = 0u64;
    let mut stale_token_acceptances = 0u64;
    let mut tool_identity_confusions = 0u64;
    let mut legitimate_evidences = 0u64;

    println!("[+] Scenario 1: Activation of disabled/unconfigured server (2,500 attempts)...");
    let disabled_server_id = [0xDDu8; 32];
    broker.register_server(disabled_server_id, false, policy_v1);
    let rogue_read_tool = McpToolDef {
        name: "read_fixture".to_string(),
        code_hash: read_hash,
        allowed_effects: vec![EffectKind::FsRead],
        target_resource_scope: "fixture://storage/".to_string(),
    };
    broker.register_tool(&disabled_server_id, rogue_read_tool).unwrap();

    for i in 0..2500 {
        let args = format!("{{\"record_id\": \"item_{}\"}}", i).into_bytes();
        let res_req = broker.request_capability(
            &disabled_server_id,
            "read_fixture",
            &read_hash,
            &args,
            "fixture://storage/data.json",
            EffectKind::FsRead,
            10,
        );

        match res_req {
            Ok(token) => {
                // If it somehow issued a token, attempt commit
                let res_commit = broker.commit_execution(
                    &token,
                    &disabled_server_id,
                    "read_fixture",
                    &read_hash,
                    &args,
                    "fixture://storage/data.json",
                    EffectKind::FsRead,
                    1,
                );
                if res_commit.is_ok() {
                    unauthorized_effects += 1;
                }
            }
            Err(RejectReason::ServerDisabled) => {
                // Correct fail-closed behavior
            }
            Err(_) => {
                // Rejected under another policy
            }
        }
    }

    println!("[+] Scenario 2: Tool substitution & capability escalation (2,500 attempts)...");
    for i in 0..2500 {
        let args = format!("{{\"record_id\": \"mut_{}\"}}", i).into_bytes();
        // Agent claims it is executing `read_fixture`, but attempts an escalated FsMutate or FsDelete effect
        let req_res = broker.request_capability(
            &server_id,
            "read_fixture",
            &read_hash,
            &args,
            "fixture://storage/data.json",
            EffectKind::FsRead,
            10,
        );

        assert!(req_res.is_ok());
        let token = req_res.unwrap();

        // Adversary alters tool code hash (substitution attack) or attempts effect escalation
        let spoofed_hash = sha256_digest(format!("SPOOFED_TROJAN_CODE_{}", i).as_bytes());
        let escalated_effect = if i % 2 == 0 {
            EffectKind::FsMutate
        } else {
            EffectKind::FsDelete
        };

        // Sub-test A: Spoofed code hash
        let commit_spoofed = broker.commit_execution(
            &token,
            &server_id,
            "read_fixture",
            &spoofed_hash,
            &args,
            "fixture://storage/data.json",
            EffectKind::FsRead,
            1,
        );
        match commit_spoofed {
            Ok(_) => tool_identity_confusions += 1,
            Err(RejectReason::ToolIdentityMismatch) => {}
            Err(_) => {}
        }

        // Sub-test B: Capability escalation (requesting FsMutate using FsRead token)
        let commit_escalated = broker.commit_execution(
            &token,
            &server_id,
            "read_fixture",
            &read_hash,
            &args,
            "fixture://storage/data.json",
            escalated_effect,
            1,
        );
        match commit_escalated {
            Ok(_) => capability_escalations += 1,
            Err(RejectReason::CapabilityEscalation) => {}
            Err(_) => {}
        }
    }

    println!("[+] Scenario 3: Stale authorization reuse & revocation (2,500 attempts)...");
    for i in 0..2500 {
        let args = format!("{{\"query\": \"stale_{}\"}}", i).into_bytes();
        let token = broker.request_capability(
            &server_id,
            "read_fixture",
            &read_hash,
            &args,
            "fixture://storage/data.json",
            EffectKind::FsRead,
            5,
        ).unwrap();

        if i % 2 == 0 {
            // Test explicit token revocation
            broker.revoke_token(&token.token_id);
            let res = broker.commit_execution(
                &token,
                &server_id,
                "read_fixture",
                &read_hash,
                &args,
                "fixture://storage/data.json",
                EffectKind::FsRead,
                1,
            );
            if res.is_ok() {
                stale_token_acceptances += 1;
            }
        } else {
            // Test temporal expiration at t_commit > valid_until_epoch (e.g. t_commit = 100)
            let res = broker.commit_execution(
                &token,
                &server_id,
                "read_fixture",
                &read_hash,
                &args,
                "fixture://storage/data.json",
                EffectKind::FsRead,
                100, // Exceeds valid_until_epoch (1 + 5 = 6)
            );
            if res.is_ok() {
                stale_token_acceptances += 1;
            }
        }
    }

    println!("[+] Scenario 4: Configuration & argument TOCTOU drift (2,500 attempts)...");
    for i in 0..2500 {
        let original_args = format!("{{\"key\": \"alpha_{}\"}}", i).into_bytes();
        let drifted_args = format!("{{\"key\": \"TAMPERED_PAYLOAD_{}\"}}", i).into_bytes();

        let token = broker.request_capability(
            &server_id,
            "mutate_fixture",
            &mutate_hash,
            &original_args,
            "fixture://storage/data.json",
            EffectKind::FsMutate,
            10,
        ).unwrap();

        // Adversary mutates arguments between validation and commit:
        let commit_drift = broker.commit_execution(
            &token,
            &server_id,
            "mutate_fixture",
            &mutate_hash,
            &drifted_args,
            "fixture://storage/data.json",
            EffectKind::FsMutate,
            1,
        );

        match commit_drift {
            Ok(_) => unauthorized_effects += 1,
            Err(RejectReason::ConfigurationDrift) => {}
            Err(_) => {}
        }
    }

    println!("[+] Control Suite: 2,500 Legitimate Invocations (Non-vacuousness proof)...");
    for i in 0..2500 {
        let args = format!("{{\"control_id\": {}}}", i).into_bytes();
        let (tool_name, hash, effect) = match i % 3 {
            0 => ("read_fixture", &read_hash, EffectKind::FsRead),
            1 => ("mutate_fixture", &mutate_hash, EffectKind::FsMutate),
            _ => ("delete_fixture", &delete_hash, EffectKind::FsDelete),
        };

        let token = broker.request_capability(
            &server_id,
            tool_name,
            hash,
            &args,
            "fixture://storage/data.json",
            effect,
            10,
        ).expect("Legitimate capability request must succeed");

        let evidence = broker.commit_execution(
            &token,
            &server_id,
            tool_name,
            hash,
            &args,
            "fixture://storage/data.json",
            effect,
            1,
        ).expect("Legitimate execution commit must succeed");

        assert_eq!(evidence.token_id, token.token_id);
        legitimate_evidences += 1;
    }

    let elapsed = start_time.elapsed();
    let total_adversarial_attempts = 10_000u64;
    let effect_evidence_coverage = (legitimate_evidences as f64 / 2500.0) * 100.0;

    println!("\n╔══════════════════════════════════════════════════════════════════════════════╗");
    println!("║                       FL-008 EMPIRICAL TELEMETRY                             ║");
    println!("╠══════════════════════════════════════════════════════════════════════════════╣");
    println!("║ Total Adversarial Attempts:      {:>8}                                    ║", total_adversarial_attempts);
    println!("║ Unauthorized Effects:            {:>8} (Acceptance: 0)                     ║", unauthorized_effects);
    println!("║ Capability Escalations:          {:>8} (Acceptance: 0)                     ║", capability_escalations);
    println!("║ Stale Token Acceptances:         {:>8} (Acceptance: 0)                     ║", stale_token_acceptances);
    println!("║ Tool Identity Confusions:        {:>8} (Acceptance: 0)                     ║", tool_identity_confusions);
    println!("║ Effect Evidence Coverage:        {:>7.1}% (Acceptance: 100.0%)             ║", effect_evidence_coverage);
    println!("║ Execution Elapsed Time:          {:>8.2?}                                ║", elapsed);
    println!("╚══════════════════════════════════════════════════════════════════════════════╝");

    // Acceptance criteria strictly evaluated:
    assert_eq!(unauthorized_effects, 0, "FL-008 FALSIFIED: Unauthorized effect permitted!");
    assert_eq!(capability_escalations, 0, "FL-008 FALSIFIED: Capability escalation succeeded!");
    assert_eq!(stale_token_acceptances, 0, "FL-008 FALSIFIED: Stale token accepted at t_commit!");
    assert_eq!(tool_identity_confusions, 0, "FL-008 FALSIFIED: Tool identity confusion succeeded!");
    assert_eq!(effect_evidence_coverage, 100.0, "FL-008 FALSIFIED: Incomplete evidence coverage!");

    println!("\n[✓] VEREDICTO FORMAL: SUPPORTED_WITHIN_DOMAIN");
    println!("[✓] Property Holds: Execute(e) ⟹ ValidCapability(e, t_commit)");
    println!("[✓] Tool Available ≠ Tool Authorized ≠ Effect Authorized certified in silicon.");
}
