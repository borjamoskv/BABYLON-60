//! # `babylon-skills-mcp` stdio JSON-RPC 2.0 Server Entrypoint (Architecture v3.1)
//!
//! Loads the immutable `ImmutableSkillsSnapshot` into RAM at startup, verifies or emits
//! `skills-lock.json`, and serves the 3 stateless orchestration primitives (`skills.discover`,
//! `skills.inspect`, `skills.propose_effect`) alongside SEP-2640 over `stdio` without reading
//! the filesystem during request processing.

use std::io::{self, BufRead, Write};
use std::path::PathBuf;
use std::process;

use babylon_skills_mcp::{
    read_bytes_nofollow, ImmutableSkillsSnapshot, SkillsLockfile, SkillsMcpGateway,
};
use serde_json::Value;

fn main() {
    let mut catalog_path: Option<PathBuf> = None;
    let mut skills_dir: Option<PathBuf> = None;
    let mut lockfile_path: Option<PathBuf> = None;
    let mut emit_lockfile_path: Option<PathBuf> = None;
    let mut expected_count: Option<usize> = None;
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
            "--lockfile" => {
                lockfile_path = args.next().map(PathBuf::from);
            }
            "--emit-lockfile" => {
                emit_lockfile_path = args.next().map(PathBuf::from);
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
            "--help" | "-h" => {
                println!(
                    "Usage: babylon-skills-mcp [--catalog <skills.json>] [--skills-dir <.agents/skills>] [--lockfile <skills-lock.json>] [--emit-lockfile <skills-lock.json>] [--expect-count <N>] [--use-canonical-names]"
                );
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

    let snapshot = match ImmutableSkillsSnapshot::load(
        resolved_catalog.as_deref(),
        resolved_skills_dir.as_deref(),
        expected_count,
    ) {
        Ok(s) => s,
        Err(err) => {
            eprintln!("babylon-skills-mcp failed to load snapshot: {err}");
            process::exit(1);
        }
    };

    if let Some(out_path) = emit_lockfile_path {
        let lock = snapshot.to_lockfile();
        let pretty = serde_json::to_string_pretty(&lock).unwrap_or_else(|e| {
            eprintln!("Failed to serialize skills-lock.json: {e}");
            process::exit(1);
        });
        if let Err(e) = std::fs::write(&out_path, format!("{pretty}\n")) {
            eprintln!("Failed to write {}: {e}", out_path.display());
            process::exit(1);
        }
        return;
    }

    // The entrypoint pins the supplied catalog; deriving a fresh lock is only an
    // explicit maintenance operation (--emit-lockfile), never startup approval.
    let resolved_lockfile = lockfile_path.or_else(|| {
        resolved_catalog
            .as_ref()
            .map(|catalog| catalog.with_file_name("skills-lock.json"))
    });
    let gateway = if let Some(lf_path) = resolved_lockfile {
        let raw = read_bytes_nofollow(&lf_path).unwrap_or_else(|e| {
            eprintln!("Failed to read lockfile {}: {e}", lf_path.display());
            process::exit(1);
        });
        let parsed: SkillsLockfile = serde_json::from_slice(&raw).unwrap_or_else(|e| {
            eprintln!("Invalid JSON in lockfile {}: {e}", lf_path.display());
            process::exit(1);
        });
        SkillsMcpGateway::with_lockfile(snapshot, parsed, use_canonical).unwrap_or_else(|r| {
            eprintln!("Lockfile verification failed (FL-P08): {r:?}");
            process::exit(1);
        })
    } else {
        SkillsMcpGateway::new(snapshot, use_canonical)
    };

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
