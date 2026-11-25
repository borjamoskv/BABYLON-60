//! # `babylon-skills-mcp` stdio JSON-RPC 2.0 Server Entrypoint (Architecture v3.2)
//!
//! Loads the immutable `ImmutableSkillsSnapshot` into RAM at startup, verifies or emits
//! `skills-lock.json` (repository layer) and, when `--global-skills-dir` is supplied, the
//! operator-local global lock, then serves the 3 stateless orchestration primitives
//! (`skills.discover`, `skills.inspect`, `skills.propose_effect`) alongside SEP-2640 over
//! `stdio` without reading the filesystem during request processing.

use std::collections::BTreeMap;
use std::io::{self, BufRead, Write};
use std::path::{Path, PathBuf};
use std::process;

use babylon_skills_mcp::{
    read_bytes_nofollow, ImmutableSkillsSnapshot, SkillsLockfile, SkillsMcpGateway,
};
use serde_json::Value;

const USAGE: &str = "Usage: babylon-skills-mcp [--catalog <skills.json>] [--skills-dir <.agents/skills>] \
[--global-skills-dir <dir>]... [--lockfile <skills-lock.json>] [--global-lockfile <skills-lock.global.json>] \
[--emit-lockfile <skills-lock.json>] [--emit-global-lockfile <skills-lock.global.json>] \
[--expect-count <N>] [--use-canonical-names] [--authoritative-epoch <N>] [--bind-project <project_id>] \
[--allowed-root <project_id|*>=<root>]... [--allow-skills <project_id|*>=<skill>[,<skill>...]]...";

/// Parses `<project_id>=<value>` for the server-side policy flags; exits on malformed input.
fn split_project_flag(flag: &str, raw: Option<String>) -> (String, String) {
    let parsed = raw
        .as_deref()
        .and_then(|v| v.split_once('='))
        .and_then(|(p, v)| {
            let (p, v) = (p.trim(), v.trim());
            (!p.is_empty() && !v.is_empty()).then(|| (p.to_string(), v.to_string()))
        });
    parsed.unwrap_or_else(|| {
        eprintln!("{flag} requires <project_id|*>=<value>");
        process::exit(2);
    })
}

fn write_lock(lock: &SkillsLockfile, out_path: &Path) {
    let pretty = serde_json::to_string_pretty(lock).unwrap_or_else(|e| {
        eprintln!("Failed to serialize lockfile: {e}");
        process::exit(1);
    });
    if let Err(e) = std::fs::write(out_path, format!("{pretty}\n")) {
        eprintln!("Failed to write {}: {e}", out_path.display());
        process::exit(1);
    }
}

fn read_lock(path: &Path) -> SkillsLockfile {
    let raw = read_bytes_nofollow(path).unwrap_or_else(|e| {
        eprintln!("Failed to read lockfile {}: {e}", path.display());
        process::exit(1);
    });
    serde_json::from_slice(&raw).unwrap_or_else(|e| {
        eprintln!("Invalid JSON in lockfile {}: {e}", path.display());
        process::exit(1);
    })
}

fn main() {
    let mut catalog_path: Option<PathBuf> = None;
    let mut skills_dir: Option<PathBuf> = None;
    let mut global_skills_dirs: Vec<PathBuf> = Vec::new();
    let mut lockfile_path: Option<PathBuf> = None;
    let mut global_lockfile_path: Option<PathBuf> = None;
    let mut emit_lockfile_path: Option<PathBuf> = None;
    let mut emit_global_lockfile_path: Option<PathBuf> = None;
    let mut expected_count: Option<usize> = None;
    // Server-side policy: provisioned by the operator, never by the JSON-RPC client.
    let mut authoritative_epoch: Option<u64> = None;
    let mut bound_project: Option<String> = None;
    let mut project_roots: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut project_skills: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut use_canonical = std::env::var("BABYLON60_MCP_CANONICAL_NAMES")
        .map(|v| matches!(v.trim().to_ascii_lowercase().as_str(), "1" | "true" | "yes"))
        .unwrap_or(false);

    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--catalog" => {
                catalog_path = args.next().map(PathBuf::from);
            }
            "--skills-dir" => {
                skills_dir = args.next().map(PathBuf::from);
            }
            "--global-skills-dir" => match args.next() {
                Some(dir) => global_skills_dirs.push(PathBuf::from(dir)),
                None => {
                    eprintln!("--global-skills-dir requires a value");
                    process::exit(2);
                }
            },
            "--lockfile" => {
                lockfile_path = args.next().map(PathBuf::from);
            }
            "--global-lockfile" => {
                global_lockfile_path = args.next().map(PathBuf::from);
            }
            "--emit-lockfile" => {
                emit_lockfile_path = args.next().map(PathBuf::from);
            }
            "--emit-global-lockfile" => {
                emit_global_lockfile_path = args.next().map(PathBuf::from);
            }
            "--expect-count" => {
                if let Some(val) = args.next() {
                    expected_count = Some(val.parse().unwrap_or_else(|_| {
                        eprintln!("Invalid --expect-count value: {val}");
                        process::exit(2);
                    }));
                }
            }
            "--use-canonical-names" => {
                use_canonical = true;
            }
            "--authoritative-epoch" => {
                let val = args.next().unwrap_or_default();
                authoritative_epoch = Some(val.parse().unwrap_or_else(|_| {
                    eprintln!("Invalid --authoritative-epoch value: {val:?}");
                    process::exit(2);
                }));
            }
            "--allowed-root" => {
                let (project, root) = split_project_flag("--allowed-root", args.next());
                if root.trim_end_matches('/').is_empty()
                    || root.split(['/', '\\']).any(|seg| seg == "..")
                {
                    eprintln!(
                        "--allowed-root rejects the filesystem root and traversal segments: {root}"
                    );
                    process::exit(2);
                }
                project_roots.entry(project).or_default().push(root);
            }
            "--allow-skills" => {
                let (project, skills) = split_project_flag("--allow-skills", args.next());
                project_skills.entry(project).or_default().extend(
                    skills
                        .split(',')
                        .map(str::trim)
                        .filter(|s| !s.is_empty())
                        .map(String::from),
                );
            }
            "--bind-project" => {
                let val = args.next().unwrap_or_default();
                let project = val.trim();
                if project.is_empty() || project == "*" {
                    eprintln!("--bind-project requires a concrete project_id: {val:?}");
                    process::exit(2);
                }
                bound_project = Some(project.to_string());
            }
            "--help" | "-h" => {
                println!("{USAGE}");
                return;
            }
            other => {
                eprintln!("Unknown argument: {other}");
                process::exit(2);
            }
        }
    }

    let default_catalog = PathBuf::from("docs/skills.json");
    let default_skills_dir = PathBuf::from(".agents/skills");

    let resolved_catalog = catalog_path.or_else(|| {
        if default_catalog.is_file() {
            Some(default_catalog)
        } else {
            None
        }
    });
    let resolved_skills_dir = skills_dir.or_else(|| {
        if default_skills_dir.is_dir() {
            Some(default_skills_dir)
        } else {
            None
        }
    });

    let global_refs: Vec<&Path> = global_skills_dirs.iter().map(PathBuf::as_path).collect();
    let snapshot = match ImmutableSkillsSnapshot::load_with_globals(
        resolved_catalog.as_deref(),
        resolved_skills_dir.as_deref(),
        &global_refs,
        expected_count,
    ) {
        Ok(s) => s,
        Err(err) => {
            eprintln!("babylon-skills-mcp failed to load snapshot: {err}");
            process::exit(1);
        }
    };

    // Explicit maintenance operations: derive locks from the loaded snapshot and exit.
    if emit_lockfile_path.is_some() || emit_global_lockfile_path.is_some() {
        if let Some(out_path) = emit_lockfile_path {
            write_lock(&snapshot.to_lockfile(), &out_path);
        }
        if let Some(out_path) = emit_global_lockfile_path {
            if global_refs.is_empty() {
                eprintln!("--emit-global-lockfile requires at least one --global-skills-dir");
                process::exit(2);
            }
            write_lock(&snapshot.to_global_lockfile(), &out_path);
            eprintln!(
                "global lock: {} catalog skills bound to global artifacts",
                snapshot.global_bound_count()
            );
        }
        return;
    }

    // Global roots without a pinned global lock would be trust-on-load: refuse (I5).
    if !global_refs.is_empty() && global_lockfile_path.is_none() {
        eprintln!("GLOBAL_LOCK_REQUIRED: --global-skills-dir requires --global-lockfile");
        process::exit(1);
    }
    if global_refs.is_empty() && global_lockfile_path.is_some() {
        eprintln!("--global-lockfile requires at least one --global-skills-dir");
        process::exit(2);
    }

    // The entrypoint pins the supplied catalog; deriving a fresh lock is only an
    // explicit maintenance operation (--emit-lockfile), never startup approval.
    let resolved_lockfile = lockfile_path.or_else(|| {
        resolved_catalog
            .as_ref()
            .map(|catalog| catalog.with_file_name("skills-lock.json"))
    });
    let gateway = if let Some(lf_path) = resolved_lockfile {
        let parsed = read_lock(&lf_path);
        let global = global_lockfile_path.as_deref().map(read_lock);
        SkillsMcpGateway::with_lockfiles(snapshot, parsed, global, use_canonical).unwrap_or_else(
            |r| {
                eprintln!("Lockfile verification failed (FL-P08): {r:?}");
                process::exit(1);
            },
        )
    } else {
        SkillsMcpGateway::new(snapshot, use_canonical)
    };

    if let Some(epoch) = authoritative_epoch {
        gateway.set_authoritative_epoch(epoch);
    }
    if let Some(project) = bound_project {
        gateway.bind_session_project(&project);
    }
    for (project, roots) in project_roots {
        gateway.set_project_allowed_roots(&project, roots);
    }
    for (project, skills) in project_skills {
        gateway.set_project_allowlist(&project, skills);
    }

    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line_res in stdin.lock().lines() {
        let Ok(line) = line_res else {
            break;
        };
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let Ok(req) = serde_json::from_str::<Value>(trimmed) else {
            continue;
        };
        if let Some(resp) = gateway.process_request(&req) {
            if let Ok(serialized) = serde_json::to_string(&resp) {
                let _ = writeln!(stdout, "{serialized}");
                let _ = stdout.flush();
            }
        }
    }
}
