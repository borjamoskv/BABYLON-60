//! Lease, roots and project policy are decided by the server; the JSON-RPC client can only
//! shorten a lease or narrow the roots, never declare them.
use babylon60::capability::sha256_digest;
use babylon_skills_mcp::{
    ImmutableSkillsSnapshot, SkillsMcpGateway, DEFAULT_SERVER_EPOCH, GATEWAY_EXPECTED_AUDIENCE,
    MAX_CAPABILITY_LEASE_EPOCHS,
};
use serde_json::{json, Value};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

const SKILL: &str = "thermo-audit";
const MUTATING_SKILL: &str = "apple-bypass";
const NETWORK_SKILL: &str = "c5-gemini-api-2026-standards";

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf()
}

/// Real catalog plus a global root binding the network skill to a physical artifact; the
/// snapshot is frozen in RAM, so the temporary root may be dropped after loading.
fn snapshot() -> ImmutableSkillsSnapshot {
    let root = repo_root();
    let global = tempfile::tempdir().unwrap();
    let dir = global.path().join(NETWORK_SKILL);
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("SKILL.md"),
        format!("---\nname: {NETWORK_SKILL}\n---\nfixture\n"),
    )
    .unwrap();
    ImmutableSkillsSnapshot::load_with_globals(
        Some(&root.join("docs/skills.json")),
        Some(&root.join(".agents/skills")),
        &[global.path()],
        None,
    )
    .unwrap()
}

fn request(gw: &SkillsMcpGateway, project: &str, nonce: &str, target: &str) -> Value {
    request_for(gw, SKILL, project, nonce, target)
}

fn request_for(
    gw: &SkillsMcpGateway,
    skill_id: &str,
    project: &str,
    nonce: &str,
    target: &str,
) -> Value {
    let skill = gw.snapshot().resolve(skill_id).unwrap();
    json!({
        "skill_id": skill_id, "version": skill.version, "tool_identity_hash": skill.tool_identity_hash,
        "arguments": {"target_path": target},
        "precondition_snapshot": {},
        "credential": {"audience": GATEWAY_EXPECTED_AUDIENCE, "project_id": project, "nonce": nonce}
    })
}

fn propose(gw: &SkillsMcpGateway, args: &Value) -> Value {
    gw.handle_skills_propose_effect(args.as_object().unwrap())
}

#[test]
fn client_cannot_extend_the_lease_or_set_the_clock() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let mut args = request(&gw, "p", "lease", "workspace://src/lib.rs");
    args["credential"]["current_epoch"] = json!(1_000_000);
    args["credential"]["expires_at_epoch"] = json!(u64::MAX);
    let r = propose(&gw, &args);
    assert_eq!(r["status"], "AUTHORIZED", "{r}");
    assert_eq!(
        r["action_capability"]["issued_epoch"],
        json!(DEFAULT_SERVER_EPOCH)
    );
    assert_eq!(
        r["action_capability"]["expires_at_epoch"],
        json!(DEFAULT_SERVER_EPOCH + MAX_CAPABILITY_LEASE_EPOCHS)
    );
}

#[test]
fn client_can_shorten_the_lease() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let mut args = request(&gw, "p", "short", "workspace://src/lib.rs");
    args["credential"]["expires_at_epoch"] = json!(DEFAULT_SERVER_EPOCH + 3);
    let r = propose(&gw, &args);
    assert_eq!(r["status"], "AUTHORIZED", "{r}");
    assert_eq!(
        r["action_capability"]["expires_at_epoch"],
        json!(DEFAULT_SERVER_EPOCH + 3)
    );
}

#[test]
fn credential_expired_on_the_server_clock_is_not_revived_by_the_client() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_authoritative_epoch(1000);
    let mut args = request(&gw, "p", "revive", "workspace://src/lib.rs");
    args["credential"]["current_epoch"] = json!(1);
    args["credential"]["expires_at_epoch"] = json!(500);
    let r = propose(&gw, &args);
    assert_eq!(r["failure_class"], "CREDENTIAL_EXPIRED", "{r}");
}

#[test]
fn client_roots_cannot_widen_the_server_default_roots() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    for roots in [
        json!(["/etc"]),
        json!(["."]),
        json!(["/Users", "workspace://"]),
    ] {
        let mut args = request(&gw, "p", "widen", "/etc/passwd");
        args["precondition_snapshot"]["allowed_roots"] = roots.clone();
        let r = propose(&gw, &args);
        assert_eq!(r["status"], "DENIED", "roots {roots}: {r}");
    }
}

#[test]
fn client_roots_can_narrow_the_server_default_roots() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let mut inside = request(&gw, "p", "narrow-in", "workspace://src/lib.rs");
    inside["precondition_snapshot"]["allowed_roots"] = json!(["workspace://src"]);
    assert_eq!(propose(&gw, &inside)["status"], "AUTHORIZED");

    let mut outside = request(&gw, "p", "narrow-out", "workspace://docs/a.md");
    outside["precondition_snapshot"]["allowed_roots"] = json!(["workspace://src"]);
    assert_eq!(propose(&gw, &outside)["status"], "DENIED");
}

#[test]
fn unconfigured_project_does_not_escape_per_project_policy() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots("tenant-a", ["workspace://tenant-a"]);

    let own = request(&gw, "tenant-a", "own", "workspace://tenant-a/x");
    assert_eq!(propose(&gw, &own)["status"], "AUTHORIZED");

    let shadow = request(&gw, "tenant-a-shadow", "shadow", "workspace://tenant-a/x");
    let r = propose(&gw, &shadow);
    assert_eq!(r["failure_class"], "PROJECT_POLICY_DENIED", "{r}");
}

#[test]
fn wildcard_policy_applies_to_projects_without_their_own() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots("*", ["workspace://shared"]);
    gw.set_project_allowed_roots("tenant-a", ["workspace://tenant-a"]);

    let other = request(&gw, "tenant-b", "w1", "workspace://shared/x");
    assert_eq!(propose(&gw, &other)["status"], "AUTHORIZED");
    let escape = request(&gw, "tenant-b", "w2", "workspace://tenant-a/x");
    assert_eq!(propose(&gw, &escape)["status"], "DENIED");
}

#[test]
fn slash_only_server_roots_do_not_grant_the_whole_filesystem() {
    for root in ["/", "//", "///", ""] {
        let gw = SkillsMcpGateway::new(snapshot(), false);
        gw.set_project_allowed_roots("p", [root]);
        let r = propose(&gw, &request(&gw, "p", "slashes", "/etc/passwd"));
        assert_eq!(r["status"], "DENIED", "root {root:?}: {r}");
    }
}

/// A mutation request whose client-declared pre-hash matches `declared`.
fn mutation(gw: &SkillsMcpGateway, nonce: &str, target: &str, declared: &[u8]) -> Value {
    let hash = hex::encode(sha256_digest(declared));
    let mut args = request_for(gw, MUTATING_SKILL, "lab", nonce, target);
    args["arguments"]["expected_pre_hash"] = json!(hash);
    args["precondition_snapshot"]["observed_pre_hash"] = json!(hash);
    args
}

#[test]
fn local_mutation_is_checked_against_the_digest_the_server_observes() {
    let lab = tempfile::tempdir().unwrap();
    let target = lab.path().join("state");
    std::fs::write(&target, b"actual").unwrap();
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots("lab", [lab.path().to_str().unwrap().to_string()]);
    let target = target.to_str().unwrap();

    let genuine = propose(&gw, &mutation(&gw, "m-ok", target, b"actual"));
    assert_eq!(genuine["status"], "AUTHORIZED", "{genuine}");
    let forged = propose(&gw, &mutation(&gw, "m-forged", target, b"forged"));
    assert_eq!(forged["failure_class"], "PRECONDITION_MISMATCH", "{forged}");
}

#[test]
fn local_mutation_the_server_cannot_observe_is_denied() {
    let lab = tempfile::tempdir().unwrap();
    let real = lab.path().join("real");
    std::fs::write(&real, b"actual").unwrap();
    let link = lab.path().join("link");
    std::os::unix::fs::symlink(&real, &link).unwrap();
    let missing = lab.path().join("missing");
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots(
        "lab",
        [
            lab.path().to_str().unwrap().to_string(),
            "tests".to_string(),
        ],
    );

    for (nonce, target) in [
        ("u-link", link.to_str().unwrap()),
        ("u-missing", missing.to_str().unwrap()),
        ("u-dir", lab.path().to_str().unwrap()),
        // Exists relative to the crate directory, but a relative path is cwd-dependent.
        ("u-relative", "tests/proposal_boundary.rs"),
    ] {
        let r = propose(&gw, &mutation(&gw, nonce, target, b"forged"));
        assert_eq!(
            r["failure_class"], "PRECONDITION_UNOBSERVABLE",
            "{target}: {r}"
        );
    }
}

#[test]
fn relabelling_the_trace_or_project_does_not_split_read_from_network_egress() {
    for (nonce, project, trace) in [
        ("f-trace", "babylon60", Some("fresh-trace")),
        ("f-project", "other-project", None),
        ("f-same", "babylon60", Some("read-trace")),
    ] {
        let gw = SkillsMcpGateway::new(snapshot(), false);
        let mut read = request(&gw, "babylon60", "f-read", "workspace://src/lib.rs");
        read["trace_id"] = json!("read-trace");
        assert_eq!(propose(&gw, &read)["status"], "AUTHORIZED");

        let mut egress = request_for(&gw, NETWORK_SKILL, project, nonce, "workspace://out");
        egress["arguments"]["network_destination"] = json!("https://example.invalid/collect");
        if let Some(trace) = trace {
            egress["trace_id"] = json!(trace);
        }
        let r = propose(&gw, &egress);
        assert_eq!(r["status"], "PENDING_APPROVAL", "{project}/{trace:?}: {r}");
    }
}

#[test]
fn network_egress_without_a_prior_local_read_is_not_escalated() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let mut egress = request_for(&gw, NETWORK_SKILL, "babylon60", "f-only", "workspace://out");
    egress["arguments"]["network_destination"] = json!("https://example.invalid/collect");
    let r = propose(&gw, &egress);
    assert_ne!(r["status"], "PENDING_APPROVAL", "{r}");
}

fn call_binary(flags: &[&str], arguments: Value) -> Value {
    let mut child = Command::new(env!("CARGO_BIN_EXE_babylon-skills-mcp"))
        .args(flags)
        .current_dir(repo_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let req = json!({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "skills.propose_effect", "arguments": arguments}
    });
    writeln!(child.stdin.as_mut().unwrap(), "{req}").unwrap();
    drop(child.stdin.take());
    let out = child.wait_with_output().unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout);
    let line = stdout
        .lines()
        .next()
        .unwrap_or_else(|| panic!("no response: {}", String::from_utf8_lossy(&out.stderr)));
    serde_json::from_str(line).unwrap()
}

#[test]
fn stdio_binary_denies_client_chosen_roots_and_lease() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let mut args = request(&gw, "any", "bin-default", "/etc/passwd");
    args["precondition_snapshot"]["allowed_roots"] = json!(["/etc"]);
    args["credential"]["expires_at_epoch"] = json!(u64::MAX);
    let resp = call_binary(&[], args);
    assert_eq!(resp["result"]["status"], "DENIED", "{resp}");
}

#[test]
fn stdio_binary_applies_operator_provisioned_policy() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let flags = [
        "--authoritative-epoch",
        "700",
        "--allowed-root",
        "tenant-a=workspace://tenant-a",
    ];

    let mut ok = request(&gw, "tenant-a", "bin-ok", "workspace://tenant-a/x");
    ok["credential"]["expires_at_epoch"] = json!(u64::MAX);
    let resp = call_binary(&flags, ok);
    assert_eq!(resp["result"]["status"], "AUTHORIZED", "{resp}");
    assert_eq!(
        resp["result"]["action_capability"]["issued_epoch"],
        json!(700)
    );
    assert_eq!(
        resp["result"]["action_capability"]["expires_at_epoch"],
        json!(700 + MAX_CAPABILITY_LEASE_EPOCHS)
    );

    let mut other = request(&gw, "tenant-b", "bin-other", "workspace://tenant-a/x");
    other["credential"]["expires_at_epoch"] = json!(760);
    let resp = call_binary(&flags, other);
    assert_eq!(resp["result"]["status"], "DENIED", "{resp}");
}

#[test]
fn stdio_binary_rejects_malformed_policy_flags() {
    for flags in [
        &["--allowed-root", "no-separator"][..],
        &["--allowed-root", "p=/"][..],
        &["--allowed-root", "p=//"][..],
        &["--allowed-root", "p=///"][..],
        &["--allowed-root", "p=/a/../b"][..],
        &["--authoritative-epoch", "soon"][..],
        &["--allow-skills", "=x"][..],
    ] {
        let out = Command::new(env!("CARGO_BIN_EXE_babylon-skills-mcp"))
            .args(flags)
            .current_dir(repo_root())
            .stdin(Stdio::null())
            .output()
            .unwrap();
        assert_eq!(out.status.code(), Some(2), "{flags:?}");
    }
}
