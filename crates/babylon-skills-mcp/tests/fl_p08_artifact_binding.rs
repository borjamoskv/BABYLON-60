//! FL-P08 v3.2 — artifact binding adversarial suite.
//!
//! Before v3.2, catalog skills without a workspace folder were sealed with a digest of synthetic
//! catalog text: tampering with the real global `SKILL.md` could never surface as a mismatch.
//! These tests pin the replacement contract:
//! - provenance is explicit and part of `tool_identity_hash` (I1);
//! - one physical artifact per skill name across roots (I2);
//! - global roots are walked with the same `O_NOFOLLOW` discipline (I3);
//! - the repository lock is independent of global roots (I4);
//! - effectful skills without a sealed physical artifact are denied (I5).

use babylon60::capability::sha256_digest;
use babylon_skills_mcp::{
    compute_tool_identity_hash, ArtifactProvenance, EffectClass, ImmutableSkillsSnapshot,
    LockScope, SkillsLockfile, SkillsMcpGateway, GATEWAY_EXPECTED_AUDIENCE, LOCK_SCHEMA_VERSION,
};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use tempfile::TempDir;

const DESTRUCTIVE: &str = "lab-purge-protocol"; // "purge" => DESTRUCTIVE
const PURE: &str = "lab-notes"; // arquitecto, no effect keywords => PURE

struct Lab {
    _tmp: TempDir,
    root: PathBuf,
    catalog: PathBuf,
    workspace: PathBuf,
    global: PathBuf,
}

fn entry(name: &str, role: &str) -> Value {
    json!({
        "name": name, "canonical_alias": name, "display_name": name,
        "description": format!("{name} fixture"), "role": role, "scope": "global",
        "tier": 20000, "category": "Kernel", "triggers": [name]
    })
}

fn write_skill(root: &Path, name: &str, body: &str) {
    let dir = root.join(name);
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(dir.join("SKILL.md"), format!("---\nname: {name}\n---\n{body}\n")).unwrap();
}

/// Catalog with one DESTRUCTIVE and one PURE global skill; empty workspace; global root with both.
fn lab() -> Lab {
    let tmp = TempDir::new().unwrap();
    let root = tmp.path().to_path_buf();
    let catalog = root.join("skills.json");
    std::fs::write(
        &catalog,
        serde_json::to_vec(&json!({
            "version": "26.400",
            "entries": [entry(DESTRUCTIVE, "ejecutor"), entry(PURE, "arquitecto")]
        }))
        .unwrap(),
    )
    .unwrap();
    let workspace = root.join("workspace-skills");
    std::fs::create_dir_all(&workspace).unwrap();
    let global = root.join("global-skills");
    write_skill(&global, DESTRUCTIVE, "# purge\nreal body");
    write_skill(&global, PURE, "# notes\nreal body");
    Lab { _tmp: tmp, root, catalog, workspace, global }
}

fn load(lab: &Lab, globals: &[&Path]) -> Result<ImmutableSkillsSnapshot, String> {
    ImmutableSkillsSnapshot::load_with_globals(
        Some(&lab.catalog),
        Some(&lab.workspace),
        globals,
        Some(2),
    )
}

fn propose(gateway: &SkillsMcpGateway, skill: &str, target: &Path, nonce: &str) -> Value {
    let snap = gateway.snapshot().resolve(skill).unwrap();
    let pre_hash = hex::encode(sha256_digest(b"before"));
    let args = json!({
        "skill_id": snap.name, "version": snap.version, "tool_identity_hash": snap.tool_identity_hash,
        "arguments": {"target_path": target, "expected_pre_hash": pre_hash},
        "precondition_snapshot": {"allowed_roots": [target.parent().unwrap()], "observed_pre_hash": pre_hash},
        "credential": {"audience": GATEWAY_EXPECTED_AUDIENCE, "project_id": "lab", "nonce": nonce}
    });
    gateway.handle_skills_propose_effect(args.as_object().unwrap())
}

fn target(lab: &Lab) -> PathBuf {
    let t = lab.root.join("state");
    std::fs::write(&t, b"before").unwrap();
    t
}

#[test]
fn synthetic_destructive_denied_artifact_unbound() {
    let lab = lab();
    let snapshot = load(&lab, &[]).unwrap();
    let snap = snapshot.resolve(DESTRUCTIVE).unwrap();
    assert_eq!(snap.effect_profile.class, EffectClass::Destructive);
    assert_eq!(snap.artifact_provenance, ArtifactProvenance::CatalogSynthetic);
    assert!(!snap.is_artifact_bound());

    let gateway = SkillsMcpGateway::with_lockfile(snapshot.clone(), snapshot.to_lockfile(), false)
        .unwrap();
    let t = target(&lab);
    let result = propose(&gateway, DESTRUCTIVE, &t, "n1");
    assert_eq!(result["status"], "DENIED");
    assert_eq!(result["failure_class"], "ARTIFACT_UNBOUND");
    assert_eq!(std::fs::read(&t).unwrap(), b"before");
}

#[test]
fn synthetic_pure_not_gated() {
    let lab = lab();
    let snapshot = load(&lab, &[]).unwrap();
    assert_eq!(snapshot.resolve(PURE).unwrap().effect_profile.class, EffectClass::Pure);
    let gateway = SkillsMcpGateway::with_lockfile(snapshot.clone(), snapshot.to_lockfile(), false)
        .unwrap();
    let result = propose(&gateway, PURE, &target(&lab), "n2");
    assert_ne!(result["failure_class"], "ARTIFACT_UNBOUND", "{result}");
}

#[test]
fn global_bound_destructive_passes_artifact_gate() {
    let lab = lab();
    let snapshot = load(&lab, &[&lab.global]).unwrap();
    assert_eq!(snapshot.global_bound_count(), 2);
    let gateway = SkillsMcpGateway::with_lockfiles(
        snapshot.clone(),
        snapshot.to_lockfile(),
        Some(snapshot.to_global_lockfile()),
        false,
    )
    .unwrap();
    let result = propose(&gateway, DESTRUCTIVE, &target(&lab), "n3");
    assert_ne!(result["failure_class"], "ARTIFACT_UNBOUND", "{result}");
    // Served resource is the physical global file, not synthetic catalog text.
    let res = gateway
        .snapshot()
        .read_resource(&format!("skill://{DESTRUCTIVE}/SKILL.md"))
        .unwrap();
    assert!(res.text.contains("real body"));
}

#[test]
fn global_tamper_one_byte_detected() {
    let lab = lab();
    let sealed = load(&lab, &[&lab.global]).unwrap().to_global_lockfile();
    let md = lab.global.join(DESTRUCTIVE).join("SKILL.md");
    let mut bytes = std::fs::read(&md).unwrap();
    bytes.push(b'x');
    std::fs::write(&md, bytes).unwrap();

    let tampered = load(&lab, &[&lab.global]).unwrap();
    assert!(tampered.verify_against_global_lockfile(&sealed).is_err());
    assert!(SkillsMcpGateway::with_lockfiles(
        tampered.clone(),
        tampered.to_lockfile(),
        Some(sealed),
        false
    )
    .is_err());
}

#[test]
fn global_resource_added_detected() {
    let lab = lab();
    let sealed = load(&lab, &[&lab.global]).unwrap().to_global_lockfile();
    let scripts = lab.global.join(DESTRUCTIVE).join("scripts");
    std::fs::create_dir_all(&scripts).unwrap();
    std::fs::write(scripts.join("x.sh"), b"rm -rf /tmp/never\n").unwrap();
    let mutated = load(&lab, &[&lab.global]).unwrap();
    assert!(mutated.verify_against_global_lockfile(&sealed).is_err());
}

#[test]
fn global_symlinked_skill_md_not_followed() {
    let lab = lab();
    let outside = lab.root.join("outside.md");
    std::fs::write(&outside, format!("---\nname: {DESTRUCTIVE}\n---\nexfil\n")).unwrap();
    let md = lab.global.join(DESTRUCTIVE).join("SKILL.md");
    std::fs::remove_file(&md).unwrap();
    std::os::unix::fs::symlink(&outside, &md).unwrap();

    // Either the symlinked skill is skipped (unbound) or the load fails closed (Err is accepted).
    if let Ok(snapshot) = load(&lab, &[&lab.global]) {
        let snap = snapshot.resolve(DESTRUCTIVE).unwrap();
        assert!(snap.global_artifact.is_none(), "symlink must not bind a global artifact");
        assert!(!snap.is_artifact_bound());
    }
}

#[test]
fn duplicate_workspace_and_global_rejected() {
    let lab = lab();
    write_skill(&lab.workspace, DESTRUCTIVE, "# shadow copy");
    let err = load(&lab, &[&lab.global]).unwrap_err();
    assert!(err.contains("DUPLICATE_SKILL_ARTIFACT"), "{err}");
}

#[test]
fn duplicate_across_global_roots_rejected() {
    let lab = lab();
    let second = lab.root.join("global-2");
    write_skill(&second, PURE, "# other copy");
    let err = load(&lab, &[&lab.global, &second]).unwrap_err();
    assert!(err.contains("DUPLICATE_SKILL_ARTIFACT"), "{err}");
}

#[test]
fn v31_lock_rejected_at_parse() {
    let lab = lab();
    let mut lock = serde_json::to_value(load(&lab, &[]).unwrap().to_lockfile()).unwrap();
    lock["schema_version"] = json!("3.1.0");
    lock.as_object_mut().unwrap().remove("lock_scope");
    for entry in lock["skills"].as_object_mut().unwrap().values_mut() {
        entry.as_object_mut().unwrap().remove("artifact_provenance");
    }
    assert!(serde_json::from_value::<SkillsLockfile>(lock).is_err());
}

#[test]
fn schema_version_downgrade_rejected() {
    let lab = lab();
    let snapshot = load(&lab, &[]).unwrap();
    let mut lock = snapshot.to_lockfile();
    assert_eq!(lock.schema_version, LOCK_SCHEMA_VERSION);
    lock.schema_version = "3.1.0".into();
    assert!(snapshot.verify_against_lockfile(&lock).is_err());
}

#[test]
fn lock_scope_substitution_rejected() {
    let lab = lab();
    let snapshot = load(&lab, &[&lab.global]).unwrap();
    let global = snapshot.to_global_lockfile();
    assert_eq!(global.lock_scope, LockScope::Global);
    // Global lock presented as repo lock, and vice versa.
    assert!(snapshot.verify_against_lockfile(&global).is_err());
    assert!(snapshot.verify_against_global_lockfile(&snapshot.to_lockfile()).is_err());
}

#[test]
fn provenance_flip_changes_identity() {
    let digest = "ab".repeat(32);
    let ids: Vec<String> = [
        ArtifactProvenance::WorkspaceDisk,
        ArtifactProvenance::GlobalDisk,
        ArtifactProvenance::CatalogSynthetic,
    ]
    .into_iter()
    .map(|p| compute_tool_identity_hash("s", "1.0.0", &digest, p, EffectClass::Destructive))
    .collect();
    assert_ne!(ids[0], ids[1]);
    assert_ne!(ids[1], ids[2]);
    assert_ne!(ids[0], ids[2]);
}

#[test]
fn provenance_tamper_in_repo_lock_rejected() {
    let lab = lab();
    let snapshot = load(&lab, &[]).unwrap();
    let mut lock = snapshot.to_lockfile();
    lock.skills.get_mut(DESTRUCTIVE).unwrap().artifact_provenance =
        ArtifactProvenance::WorkspaceDisk;
    assert!(snapshot.verify_against_lockfile(&lock).is_err());
}

#[test]
fn repo_lock_independent_of_global_roots() {
    let lab = lab();
    let without = serde_json::to_vec(&load(&lab, &[]).unwrap().to_lockfile()).unwrap();
    let with = serde_json::to_vec(&load(&lab, &[&lab.global]).unwrap().to_lockfile()).unwrap();
    assert_eq!(without, with);
}

#[test]
fn global_bindings_require_pinned_global_lock() {
    let lab = lab();
    let snapshot = load(&lab, &[&lab.global]).unwrap();
    assert!(SkillsMcpGateway::with_lockfile(snapshot.clone(), snapshot.to_lockfile(), false).is_err());
}

#[test]
fn bin_global_dir_without_global_lock_exits_1() {
    let lab = lab();
    let lock = lab.root.join("skills-lock.json");
    let emit = std::process::Command::new(env!("CARGO_BIN_EXE_babylon-skills-mcp"))
        .args(["--catalog"]).arg(&lab.catalog)
        .args(["--skills-dir"]).arg(&lab.workspace)
        .args(["--emit-lockfile"]).arg(&lock)
        .output()
        .unwrap();
    assert!(emit.status.success(), "{}", String::from_utf8_lossy(&emit.stderr));

    let out = std::process::Command::new(env!("CARGO_BIN_EXE_babylon-skills-mcp"))
        .args(["--catalog"]).arg(&lab.catalog)
        .args(["--skills-dir"]).arg(&lab.workspace)
        .args(["--lockfile"]).arg(&lock)
        .args(["--global-skills-dir"]).arg(&lab.global)
        .stdin(std::process::Stdio::null())
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&out.stderr).contains("GLOBAL_LOCK_REQUIRED"));
}

#[test]
fn bin_global_roundtrip_and_tamper() {
    let lab = lab();
    let lock = lab.root.join("skills-lock.json");
    let glock = lab.root.join("skills-lock.global.json");
    let bin = env!("CARGO_BIN_EXE_babylon-skills-mcp");
    let base = |cmd: &mut std::process::Command| {
        cmd.args(["--catalog"]).arg(&lab.catalog)
            .args(["--skills-dir"]).arg(&lab.workspace)
            .args(["--global-skills-dir"]).arg(&lab.global)
            .stdin(std::process::Stdio::null());
    };
    let mut emit = std::process::Command::new(bin);
    base(&mut emit);
    let emit = emit
        .args(["--emit-lockfile"]).arg(&lock)
        .args(["--emit-global-lockfile"]).arg(&glock)
        .output()
        .unwrap();
    assert!(emit.status.success(), "{}", String::from_utf8_lossy(&emit.stderr));

    let run = |expect: i32| {
        let mut cmd = std::process::Command::new(bin);
        base(&mut cmd);
        let out = cmd
            .args(["--lockfile"]).arg(&lock)
            .args(["--global-lockfile"]).arg(&glock)
            .output()
            .unwrap();
        assert_eq!(out.status.code(), Some(expect), "{}", String::from_utf8_lossy(&out.stderr));
    };
    run(0);
    std::fs::write(lab.global.join(PURE).join("SKILL.md"), b"---\nname: lab-notes\n---\nswapped\n")
        .unwrap();
    run(1);
}
