//! Proposals must not accept client-authored execution evidence.

use babylon60::capability::sha256_digest;
use babylon60::ontology::babylon::{EffectState, FailureReason};
use babylon_skills_mcp::{
    ActionCapability, ImmutableSkillsSnapshot, SkillsMcpGateway, GATEWAY_EXPECTED_AUDIENCE,
};
use serde_json::{json, Value};
use std::path::Path;

fn snapshot() -> ImmutableSkillsSnapshot {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap();
    ImmutableSkillsSnapshot::load(
        Some(&root.join("docs/skills.json")),
        Some(&root.join(".agents/skills")),
        None,
    )
    .unwrap()
}

fn proposal(snapshot: &ImmutableSkillsSnapshot, target: &Path) -> Value {
    let skill = snapshot.resolve("c5-neural-face-swap-cuadrilla").unwrap();
    let pre_hash = hex::encode(sha256_digest(b"before"));
    json!({
        "skill_id": skill.name, "version": skill.version, "tool_identity_hash": skill.tool_identity_hash,
        "arguments": {"target_path": target, "expected_pre_hash": pre_hash},
        "precondition_snapshot": {"allowed_roots": [target.parent().unwrap()], "observed_pre_hash": pre_hash},
        "credential": {"audience": GATEWAY_EXPECTED_AUDIENCE, "project_id": "fixture", "nonce": "once"}
    })
}

#[test]
fn proposal_does_not_certify_execution() {
    let lab = tempfile::tempdir().unwrap();
    let target = lab.path().join("state");
    std::fs::write(&target, b"before").unwrap();
    let snapshot = snapshot();
    let args = proposal(&snapshot, &target);
    let gateway = SkillsMcpGateway::new(snapshot, false);
    let result = gateway.handle_skills_propose_effect(args.as_object().unwrap());
    assert_eq!(result["status"], "AUTHORIZED");
    assert_eq!(result["effects_executed"], 0);
    assert_eq!(result["evidence"]["postconditions_checked"], json!([]));
    assert!(result["evidence"].get("verified_by").is_none());
    assert_eq!(std::fs::read(target).unwrap(), b"before");
}

#[test]
fn client_cannot_forge_postconditions() {
    let lab = tempfile::tempdir().unwrap();
    let target = lab.path().join("state");
    std::fs::write(&target, b"before").unwrap();
    for evidence in [
        Value::Null,
        json!({}),
        json!({"observed_post_hash": "bb".repeat(32)}),
        json!({"observed_post_hash": "bb".repeat(32), "actual_file_sha256": "bb".repeat(32), "http_status": 200}),
    ] {
        let snapshot = snapshot();
        let mut args = proposal(&snapshot, &target);
        let gateway = SkillsMcpGateway::new(snapshot, false);
        args["simulated_execution_result"] = evidence;
        for _ in 0..110 {
            // 10 warmups, 100 repeated adversarial requests.
            let result = gateway.handle_skills_propose_effect(args.as_object().unwrap());
            assert_eq!(result["status"], "DENIED");
            assert_eq!(result["failure_class"], "UNTRUSTED_EXECUTION_EVIDENCE");
            assert!(result.get("action_capability").is_none());
        }
        args.as_object_mut()
            .unwrap()
            .remove("simulated_execution_result");
        assert_eq!(
            gateway.handle_skills_propose_effect(args.as_object().unwrap())["status"],
            "AUTHORIZED"
        );
        assert_eq!(std::fs::read(&target).unwrap(), b"before");
    }
}

#[test]
fn proposal_requires_exact_identity() {
    for field in ["version", "tool_identity_hash"] {
        let snapshot = snapshot();
        let mut args = proposal(&snapshot, Path::new("/workspace/state"));
        args.as_object_mut().unwrap().remove(field);
        let gateway = SkillsMcpGateway::new(snapshot, false);
        let result = gateway.handle_skills_propose_effect(args.as_object().unwrap());
        assert_eq!(result["status"], "DENIED");
        assert_eq!(result["failure_class"], "TOOL_IDENTITY_MISMATCH");
    }
}

#[test]
fn lock_pins_policy_as_well_as_artifact() {
    for field in ["effect_profile", "guard_invariants", "skill_id"] {
        let snapshot = snapshot();
        let mut lock = snapshot.to_lockfile();
        let entry = lock
            .skills
            .get_mut("c5-neural-face-swap-cuadrilla")
            .unwrap();
        match field {
            "effect_profile" => entry.effect_profile.requires_action_lease = false,
            "guard_invariants" => entry.guard_invariants.postconditions.clear(),
            _ => entry.skill_id = "shadow".into(),
        }
        assert!(snapshot.verify_against_lockfile(&lock).is_err(), "{field}");
    }
}

#[test]
fn stdio_requires_a_pin_for_the_catalog() {
    let lab = tempfile::tempdir().unwrap();
    let catalog = lab.path().join("skills.json");
    std::fs::write(&catalog, b"{}").unwrap();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_babylon-skills-mcp"))
        .current_dir(lab.path())
        .arg("--catalog")
        .arg(&catalog)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(output.stdout.is_empty());
    assert!(String::from_utf8_lossy(&output.stderr).contains("Failed to read lockfile"));
}

#[test]
fn only_independent_file_observation_can_verify_execution() {
    let lab = tempfile::tempdir().unwrap();
    for mutate in [false, true] {
        let target = lab.path().join("state");
        std::fs::write(&target, b"before").unwrap();
        let snapshot = snapshot();
        let args = proposal(&snapshot, &target);
        let gateway = SkillsMcpGateway::new(snapshot, false);
        let result = gateway.handle_skills_propose_effect(args.as_object().unwrap());
        let capability: ActionCapability =
            serde_json::from_value(result["action_capability"].clone()).unwrap();
        let state = gateway
            .execute_with_capability(
                &capability,
                GATEWAY_EXPECTED_AUDIENCE,
                1,
                || {
                    if mutate {
                        std::fs::write(&target, b"after").unwrap();
                    }
                    Ok(sha256_digest(b"after"))
                },
                || Ok(sha256_digest(&std::fs::read(&target).unwrap())),
            )
            .unwrap();
        if mutate {
            assert_eq!(state, EffectState::Verified);
        } else {
            assert!(matches!(
                state,
                EffectState::Failed(FailureReason::DivergenceDetected { .. })
            ));
        }
        assert_eq!(
            std::fs::read(&target).unwrap(),
            if mutate {
                &b"after"[..]
            } else {
                &b"before"[..]
            }
        );
        assert!(gateway
            .execute_with_capability(
                &capability,
                GATEWAY_EXPECTED_AUDIENCE,
                1,
                || panic!("replay executed"),
                || panic!("replay verified")
            )
            .is_err());
    }
}
