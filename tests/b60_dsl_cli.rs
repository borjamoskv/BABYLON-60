use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

struct Workspace(PathBuf);

impl Workspace {
    fn new() -> Self {
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let path = std::env::temp_dir().join(format!(
            "babylon60-dsl-cli-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}

impl Drop for Workspace {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

struct Run {
    output: Output,
    graph: String,
    manifest: String,
}

fn run_cli(source: &str) -> Run {
    let workspace = Workspace::new();
    fs::write(workspace.0.join("input.b60"), source).unwrap();
    let mut child = Command::new(env!("CARGO_BIN_EXE_babylon60-dsl"))
        .current_dir(&workspace.0)
        .arg("input.b60")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let deadline = Instant::now() + Duration::from_secs(5);
    while child.try_wait().unwrap().is_none() {
        if Instant::now() >= deadline {
            let _ = child.kill();
            let output = child.wait_with_output().unwrap();
            panic!("CLI no terminó dentro del límite: {:?}", output);
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    let output = child.wait_with_output().unwrap();
    let root = workspace.0.join("artifact_bundle_v3");
    let bundle = if root.join("quarantine").exists() {
        root.join("quarantine")
    } else {
        root
    };
    Run {
        output,
        graph: fs::read_to_string(bundle.join("graph.canonical")).unwrap(),
        manifest: fs::read_to_string(bundle.join("manifest.json")).unwrap(),
    }
}

#[test]
fn cli_reports_the_executed_counter_and_repeats_the_same_artifacts() {
    let source = include_str!("../tools/examples/counter_sync.b60");
    let first = run_cli(source);
    assert!(first.output.status.success(), "{:?}", first.output);
    assert!(String::from_utf8_lossy(&first.output.stdout).contains("R10 peak: 59"));
    assert!(first.graph.starts_with("B60-events-v2\n"));
    let hash = blake3::hash(first.graph.as_bytes());
    assert!(first
        .manifest
        .contains(&format!("\"global_hash\": \"{}\"", hash)));
    assert!(first.manifest.contains("\"signed\": false"));
    assert!(!first.graph.contains("TEOREMA_CAUSAL_VALIDADO"));
    let repeated = run_cli(source);
    assert_eq!(first.graph, repeated.graph);
    assert_eq!(first.manifest, repeated.manifest);
}

#[test]
fn cli_hash_changes_when_opcode_changes_with_the_same_payload() {
    let assign = run_cli("NIG R0 [ - ]\nHALT");
    let observe = run_cli("SAR R0\nHALT");
    assert!(assign.output.status.success());
    assert!(observe.output.status.success());
    assert_ne!(assign.graph, observe.graph);
    assert_ne!(assign.manifest, observe.manifest);
}

#[test]
fn cli_returns_failure_for_an_unfulfilled_wait() {
    let run = run_cli("AWAIT \"NEVER\" DONE\nMUB DONE\nHALT");
    assert!(!run.output.status.success());
    assert!(String::from_utf8_lossy(&run.output.stderr).contains("StepLimitExceeded"));
}
