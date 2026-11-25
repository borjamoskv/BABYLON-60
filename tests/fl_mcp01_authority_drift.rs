//! FL-MCP-01: isolated broker experiments; no external MCP or protected effects.
use babylon60::capability::{sha256_digest, McpCapabilityBroker, McpToolDef};
use babylon60::ontology::babylon::EffectKind;

const SERVER: [u8; 32] = [0xC1; 32];

fn tool() -> McpToolDef {
    McpToolDef {
        name: "read".into(),
        code_hash: sha256_digest(b"fl-mcp01-read"),
        allowed_effects: vec![EffectKind::FsRead],
        target_resource_scope: "fixtures/safe".into(),
    }
}

#[test]
fn discovery_must_not_grant_authority() {
    let mut broker = McpCapabilityBroker::new();
    broker.register_server(SERVER, true, 1);
    broker.register_tool(&SERVER, tool()).unwrap();
    let mut implicit_expansions = 0;
    for _ in 0..10_000 {
        if broker
            .request_capability(
                &SERVER,
                "read",
                &tool().code_hash,
                b"args",
                "fixtures/safe/file",
                EffectKind::FsRead,
                10,
            )
            .is_ok()
        {
            implicit_expansions += 1;
        }
    }
    assert_eq!(
        implicit_expansions, 0,
        "external availability implicitly granted authority"
    );
}

use babylon60::capability::{McpCapabilityToken, McpPolicyState};
use std::sync::{Arc, Barrier, Mutex};
use std::time::Instant;

fn request(broker: &McpCapabilityBroker) -> Option<McpCapabilityToken> {
    broker
        .request_capability(
            &SERVER,
            "read",
            &tool().code_hash,
            b"args",
            "fixtures/safe/file",
            EffectKind::FsRead,
            10,
        )
        .ok()
}

fn commit(broker: &McpCapabilityBroker, token: &McpCapabilityToken) -> bool {
    broker
        .commit_execution(
            token,
            &SERVER,
            "read",
            &tool().code_hash,
            b"args",
            "fixtures/safe/file",
            EffectKind::FsRead,
            token.issued_epoch(),
        )
        .is_ok()
}

fn registered(authorized: bool) -> McpCapabilityBroker {
    let mut broker = McpCapabilityBroker::new();
    broker.register_server(SERVER, true, 1);
    broker.register_tool(&SERVER, tool()).unwrap();
    if authorized {
        broker.authorize_tool(&SERVER, tool()).unwrap();
    }
    broker
}

fn available(feature: McpPolicyState, global: McpPolicyState) -> bool {
    // Independent reference table for external resolution.
    use McpPolicyState::*;
    matches!((feature, global), (Enabled, _) | (Unconfigured, Enabled))
}

#[test]
fn policy_matrix_and_stress() {
    use McpPolicyState::*;
    let states = [Enabled, Disabled, Unconfigured];
    let mut implicit_expansions_c = 0;
    let mut unauthorized_effects_c = 0;
    let mut stale_bypasses_c = 0;
    let mut legitimate = 0;
    let mut false_rejections = 0;
    let mut drift_detected = 0;
    let mut expansions_a = 0;
    let mut expansions_b = 0;
    let mut latencies = Vec::new();

    // 100 warmup trials, followed by 10,044 measured trials (124 x 81).
    // A/B are intentionally unsafe reference models: B detects drift but retains
    // A's inheritance. C exercises the actual broker. Effects are local counters.
    for trial in 0..10_144 {
        let combination = trial % 81;
        let f0 = states[combination % 3];
        let g0 = states[(combination / 3) % 3];
        let f1 = states[(combination / 9) % 3];
        let g1 = states[(combination / 27) % 3];
        let measured = trial >= 100;
        let mut unauthorized = registered(false);
        unauthorized
            .update_external_policy(&SERVER, f0, g0)
            .unwrap();
        let start = Instant::now();
        unauthorized
            .update_external_policy(&SERVER, f1, g1)
            .unwrap();
        let issued = request(&unauthorized);
        if measured {
            latencies.push(start.elapsed().as_nanos());
            implicit_expansions_c += usize::from(issued.is_some());
            unauthorized_effects_c +=
                usize::from(issued.as_ref().is_some_and(|t| commit(&unauthorized, t)));
            // Count authority produced without any grant, even if previously available.
            expansions_a += usize::from(available(f1, g1));
            expansions_b += usize::from(available(f1, g1));
        }

        let mut authorized = registered(true);
        authorized.update_external_policy(&SERVER, f0, g0).unwrap();
        let old = request(&authorized);
        authorized.update_external_policy(&SERVER, f1, g1).unwrap();
        if measured {
            if let Some(old) = old {
                let changed = (f0, g0) != (f1, g1);
                let accepted = commit(&authorized, &old);
                stale_bypasses_c += usize::from(changed && accepted);
                drift_detected += usize::from(changed && !accepted);
            }
            if available(f1, g1) {
                let accepted = request(&authorized).is_some_and(|t| commit(&authorized, &t));
                legitimate += usize::from(accepted);
                false_rejections += usize::from(!accepted);
            } else {
                assert!(request(&authorized).is_none());
            }
        }
    }
    latencies.sort_unstable();
    println!("FL-MCP-01 synthetic: implicit_capability_expansions_C={implicit_expansions_c} \
        unauthorized_mcp_effects_C={unauthorized_effects_c} stale_policy_bypasses_C={stale_bypasses_c} \
        legitimate_tool_success={legitimate} false_rejections={false_rejections} \
        configuration_drift_detection={drift_detected} \
        policy_resolution_latency_p99_ns={} A_unauthorized={expansions_a} B_unauthorized={expansions_b}",
        latencies[(latencies.len() * 99).div_ceil(100) - 1]);
    assert_eq!(
        (
            implicit_expansions_c,
            unauthorized_effects_c,
            stale_bypasses_c
        ),
        (0, 0, 0)
    );
    assert_eq!(false_rejections, 0);
    assert!(legitimate > 0 && drift_detected > 0 && expansions_a > 0 && expansions_b > 0);
}

#[test]
fn tool_expansion_is_bounded_by_original_grant() {
    let mut broker = registered(true);
    let old = request(&broker).unwrap();
    let mut expanded = tool();
    expanded.allowed_effects.push(EffectKind::FsDelete);
    expanded.target_resource_scope = "fixtures".into();
    broker.register_tool(&SERVER, expanded.clone()).unwrap();
    assert!(!commit(&broker, &old));
    assert!(request(&broker).is_some()); // original scope/effect remains usable
    for (resource, effect) in [
        ("fixtures/safe/file", EffectKind::FsDelete),
        ("fixtures/secret", EffectKind::FsRead),
    ] {
        assert!(broker
            .request_capability(
                &SERVER,
                "read",
                &tool().code_hash,
                b"args",
                resource,
                effect,
                10,
            )
            .is_err());
    }
    broker.authorize_tool(&SERVER, expanded).unwrap();
    let token = broker
        .request_capability(
            &SERVER,
            "read",
            &tool().code_hash,
            b"args",
            "fixtures/secret",
            EffectKind::FsDelete,
            10,
        )
        .unwrap();
    assert!(broker
        .commit_execution(
            &token,
            &SERVER,
            "read",
            &tool().code_hash,
            b"args",
            "fixtures/secret",
            EffectKind::FsDelete,
            token.issued_epoch(),
        )
        .is_ok());
}

#[test]
fn new_servers_tools_and_re_registration_require_grants() {
    let mut broker = registered(true);
    let token = request(&broker).unwrap();
    let other = [0xC2; 32];
    broker.register_server(other, true, 1);
    broker.register_tool(&other, tool()).unwrap();
    assert!(broker
        .request_capability(
            &other,
            "read",
            &tool().code_hash,
            b"args",
            "fixtures/safe/file",
            EffectKind::FsRead,
            10,
        )
        .is_err());
    let mut new_tool = tool();
    new_tool.name = "new-ga-tool".into();
    broker.register_tool(&SERVER, new_tool).unwrap();
    assert!(broker
        .request_capability(
            &SERVER,
            "new-ga-tool",
            &tool().code_hash,
            b"args",
            "fixtures/safe/file",
            EffectKind::FsRead,
            10,
        )
        .is_err());
    broker.register_server(SERVER, true, 1);
    broker.register_tool(&SERVER, tool()).unwrap();
    assert!(request(&broker).is_none());
    broker.authorize_tool(&SERVER, tool()).unwrap();
    assert!(!commit(&broker, &token));
    assert!(commit(&broker, &request(&broker).unwrap()));
}

#[test]
fn aba_revocation_and_identity_changes_invalidate_tokens() {
    for scenario in 0..4 {
        let mut broker = registered(true);
        let old = request(&broker).unwrap();
        match scenario {
            0 => {
                broker.set_server_enabled(&SERVER, false).unwrap();
                broker.set_server_enabled(&SERVER, true).unwrap();
            }
            1 => {
                broker.update_policy_version(&SERVER, 2).unwrap();
                broker.update_policy_version(&SERVER, 1).unwrap();
            }
            2 => {
                broker.revoke_tool(&SERVER, "read").unwrap();
                assert!(request(&broker).is_none());
                assert!(!commit(&broker, &old));
                broker.authorize_tool(&SERVER, tool()).unwrap();
            }
            _ => {
                let mut replacement = tool();
                replacement.code_hash = [0xEF; 32];
                broker.register_tool(&SERVER, replacement).unwrap();
                assert!(broker
                    .request_capability(
                        &SERVER,
                        "read",
                        &[0xEF; 32],
                        b"args",
                        "fixtures/safe/file",
                        EffectKind::FsRead,
                        10,
                    )
                    .is_err());
                broker.register_tool(&SERVER, tool()).unwrap();
            }
        }
        assert!(!commit(&broker, &old));
        assert!(commit(&broker, &request(&broker).unwrap()));
    }
}

#[test]
fn policy_change_between_resolution_and_commit_on_another_thread() {
    let broker = Arc::new(Mutex::new(registered(true)));
    let token = request(&broker.lock().unwrap()).unwrap();
    let barrier = Arc::new(Barrier::new(2));
    let worker_broker = broker.clone();
    let worker_barrier = barrier.clone();
    let writer = std::thread::spawn(move || {
        worker_barrier.wait();
        let mut broker = worker_broker.lock().unwrap();
        broker.set_server_enabled(&SERVER, false).unwrap();
        broker.set_server_enabled(&SERVER, true).unwrap();
    });
    barrier.wait();
    writer.join().unwrap();
    assert!(!commit(&broker.lock().unwrap(), &token));
}

#[test]
fn identical_refresh_preserves_authorized_tokens_and_overflow_is_rejected() {
    let mut broker = registered(true);
    let token = request(&broker).unwrap();
    broker.register_tool(&SERVER, tool()).unwrap();
    broker.authorize_tool(&SERVER, tool()).unwrap();
    broker.set_server_enabled(&SERVER, true).unwrap();
    broker.update_policy_version(&SERVER, 1).unwrap();
    assert!(commit(&broker, &token));
    assert!(broker
        .request_capability(
            &SERVER,
            "read",
            &tool().code_hash,
            b"args",
            "fixtures/safe/file",
            EffectKind::FsRead,
            u64::MAX,
        )
        .is_err());
}
