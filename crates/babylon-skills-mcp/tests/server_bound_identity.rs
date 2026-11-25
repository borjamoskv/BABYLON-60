//! Proyecto, traza y forma de `workspace://` los fija el servidor: el cliente JSON-RPC no
//! elige el proyecto de una instancia atada, no etiqueta la traza de la capacidad ni cuela
//! rutas absolutas por el espacio de nombres opaco.
use babylon60::capability::sha256_digest;
use babylon_skills_mcp::{
    ImmutableSkillsSnapshot, SkillsMcpGateway, GATEWAY_EXPECTED_AUDIENCE, GATEWAY_FLOW_TRACE,
};
use serde_json::{json, Value};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

const SKILL: &str = "thermo-audit";
const MUTATING_SKILL: &str = "apple-bypass";

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf()
}

fn snapshot() -> ImmutableSkillsSnapshot {
    let root = repo_root();
    ImmutableSkillsSnapshot::load_with_globals(
        Some(&root.join("docs/skills.json")),
        Some(&root.join(".agents/skills")),
        &[],
        None,
    )
    .unwrap()
}

fn request(skill_id: &str, project: &str, nonce: &str, target: &str) -> Value {
    let gw = SkillsMcpGateway::new(snapshot(), false);
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

/// Dos proyectos provisionados en el mismo proceso; la instancia queda atada a `tenant-a`.
fn bound_gateway() -> SkillsMcpGateway {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots("tenant-a", ["workspace://tenant-a"]);
    gw.set_project_allowed_roots("tenant-b", ["workspace://tenant-b"]);
    gw.bind_session_project("tenant-a");
    gw
}

#[test]
fn bound_gateway_denies_a_credential_for_another_provisioned_project() {
    let gw = bound_gateway();
    let r = propose(
        &gw,
        &request(SKILL, "tenant-b", "b1", "workspace://tenant-b/x"),
    );
    assert_eq!(r["failure_class"], "PROJECT_BINDING_MISMATCH", "{r}");
}

#[test]
fn bound_gateway_serves_its_own_project_within_its_roots() {
    let gw = bound_gateway();
    let own = propose(
        &gw,
        &request(SKILL, "tenant-a", "a1", "workspace://tenant-a/x"),
    );
    assert_eq!(own["status"], "AUTHORIZED", "{own}");
    let other_roots = propose(
        &gw,
        &request(SKILL, "tenant-a", "a2", "workspace://tenant-b/x"),
    );
    assert_eq!(other_roots["status"], "DENIED", "{other_roots}");
}

#[test]
fn unbound_gateway_keeps_per_project_policy() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots("tenant-b", ["workspace://tenant-b"]);
    let r = propose(
        &gw,
        &request(SKILL, "tenant-b", "u1", "workspace://tenant-b/x"),
    );
    assert_eq!(r["status"], "AUTHORIZED", "{r}");
}

#[test]
fn capability_carries_the_trace_the_server_bound_not_the_client_label() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let mut args = request(SKILL, "p", "t1", "workspace://src/lib.rs");
    args["trace_id"] = json!("client-label");
    let r = propose(&gw, &args);
    assert_eq!(r["status"], "AUTHORIZED", "{r}");
    assert_eq!(
        r["action_capability"]["trace_id"],
        json!(GATEWAY_FLOW_TRACE),
        "{r}"
    );
}

#[test]
fn malformed_workspace_targets_are_denied() {
    for (nonce, target) in [
        ("w-single", "workspace:/etc/passwd"),
        ("w-bare", "workspace:etc/passwd"),
        ("w-absolute", "workspace:///etc/passwd"),
    ] {
        let gw = SkillsMcpGateway::new(snapshot(), false);
        let r = propose(&gw, &request(SKILL, "p", nonce, target));
        assert_eq!(r["status"], "DENIED", "{target}: {r}");
    }
}

#[test]
fn absolute_path_behind_workspace_scheme_does_not_take_the_client_hash() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let forged = hex::encode(sha256_digest(b"forged"));
    let mut args = request(MUTATING_SKILL, "p", "w-mut", "workspace:///etc/passwd");
    args["arguments"]["expected_pre_hash"] = json!(forged);
    args["precondition_snapshot"]["observed_pre_hash"] = json!(forged);
    let r = propose(&gw, &args);
    assert_eq!(r["status"], "DENIED", "{r}");
}

#[test]
fn malformed_workspace_client_root_does_not_count_as_narrowing() {
    for root in ["workspace:/etc", "workspace:///etc"] {
        let gw = SkillsMcpGateway::new(snapshot(), false);
        let mut args = request(SKILL, "p", "w-root", "workspace://src/lib.rs");
        args["precondition_snapshot"]["allowed_roots"] = json!([root]);
        let r = propose(&gw, &args);
        assert_eq!(r["status"], "DENIED", "{root}: {r}");
    }
}

#[test]
fn well_formed_workspace_target_is_still_authorized() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let r = propose(&gw, &request(SKILL, "p", "w-ok", "workspace://src/lib.rs"));
    assert_eq!(r["status"], "AUTHORIZED", "{r}");
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
fn stdio_binary_binds_the_session_project() {
    let flags = [
        "--bind-project",
        "tenant-a",
        "--allowed-root",
        "tenant-a=workspace://tenant-a",
        "--allowed-root",
        "tenant-b=workspace://tenant-b",
    ];
    let own = call_binary(
        &flags,
        request(SKILL, "tenant-a", "bin-a", "workspace://tenant-a/x"),
    );
    assert_eq!(own["result"]["status"], "AUTHORIZED", "{own}");
    let other = call_binary(
        &flags,
        request(SKILL, "tenant-b", "bin-b", "workspace://tenant-b/x"),
    );
    assert_eq!(
        other["result"]["failure_class"], "PROJECT_BINDING_MISMATCH",
        "{other}"
    );
}

#[test]
fn stdio_binary_rejects_a_bind_project_without_a_concrete_project() {
    for flags in [
        &["--bind-project"][..],
        &["--bind-project", ""][..],
        &["--bind-project", "  "][..],
        &["--bind-project", "*"][..],
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
