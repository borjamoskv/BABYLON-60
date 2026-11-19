//! Prover regressions. Positive certification uses the pinned real Lean checker.
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

struct Workspace(PathBuf);
impl Workspace {
    fn new() -> Self {
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let root = std::env::temp_dir().join(format!(
            "b60-prove-regression-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).unwrap();
        Self(root)
    }

    fn source(&self, text: &str) -> PathBuf {
        let path = self.0.join("program.b60");
        fs::write(&path, text).unwrap();
        path
    }

    fn command(&self) -> Command {
        let mut cmd = Command::new(env!("CARGO_BIN_EXE_b60"));
        cmd.current_dir(&self.0)
            .arg("prove")
            .arg(self.0.join("program.b60"));
        cmd
    }

    fn assert_no_scratch(&self) {
        for entry in fs::read_dir(&self.0).unwrap() {
            let name = entry.unwrap().file_name();
            let name = name.to_string_lossy();
            assert!(!name.starts_with(".b60-check-"), "{name}");
            assert!(!name.starts_with(".b60-proof-"), "{name}");
        }
    }
}
impl Drop for Workspace {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
fn invalid_source_is_rejected_before_emission() {
    let w = Workspace::new();
    w.source("THIS IS NOT A VALID B60 PROGRAM @@@\n");
    let result = w.command().output().unwrap();
    assert!(!result.status.success());
    assert!(!w.0.join("program.lean").exists());
    assert!(!String::from_utf8_lossy(&result.stdout).contains("VERIFIED: compiled"));
    w.assert_no_scratch();
}

#[test]
fn unsupported_effectful_isa_is_rejected_without_execution() {
    let w = Workspace::new();
    w.source("TOUCHID_SIGN\nHALT\n");
    let result = w.command().output().unwrap();
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr).contains("outside the verified"));
    assert!(!w.0.join("program.lean").exists());
}

#[test]
fn a_missing_checker_never_certifies_the_emitted_file() {
    let w = Workspace::new();
    w.source("NOOP\nHALT\n");
    let result = w.command().env("PATH", &w.0).output().unwrap();
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr).contains("cannot execute pinned Lean verifier"));
    assert!(!String::from_utf8_lossy(&result.stdout).contains("VERIFIED: compiled"));
    w.assert_no_scratch();
}

#[cfg(unix)]
#[test]
fn a_checker_failure_never_certifies_the_emitted_file() {
    use std::os::unix::fs::PermissionsExt;
    let w = Workspace::new();
    w.source("HALT\n");
    fs::write(w.0.join("program.lean"), "prior artifact\n").unwrap();
    // Negative process-protocol fixture only: it does not supply Lean evidence.
    let checker = w.0.join("elan");
    fs::write(&checker, "#!/bin/sh\nexit 7\n").unwrap();
    fs::set_permissions(&checker, fs::Permissions::from_mode(0o700)).unwrap();
    let result = w.command().env("PATH", &w.0).output().unwrap();
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr).contains("Lean rejected"));
    assert!(!String::from_utf8_lossy(&result.stdout).contains("VERIFIED: compiled"));
    assert_eq!(
        fs::read_to_string(w.0.join("program.lean")).unwrap(),
        "prior artifact\n"
    );
    w.assert_no_scratch();
}

#[cfg(unix)]
#[test]
fn a_proof_path_symlink_cannot_overwrite_another_file() {
    use std::os::unix::fs::symlink;
    let w = Workspace::new();
    w.source("HALT\n");
    let canary = w.0.join("canary");
    fs::write(&canary, "unchanged").unwrap();
    symlink(&canary, w.0.join("program.lean")).unwrap();
    assert!(!w.command().output().unwrap().status.success());
    assert_eq!(fs::read_to_string(canary).unwrap(), "unchanged");
}

#[test]
#[ignore = "requires installed pinned Lean toolchain; run explicitly for formal validation"]
fn a_real_program_is_checked_by_pinned_lean() {
    let w = Workspace::new();
    let source = "NOOP\nHALT\n";
    w.source(source);
    let result = w.command().output().unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let output = String::from_utf8(result.stdout).unwrap();
    assert!(output.contains("VERIFIED: compiled HALT/NOOP"));
    assert!(output.contains(blake3::hash(source.as_bytes()).to_hex().as_str()));
    assert!(output.contains(blake3::hash(&[2u8, 0]).to_hex().as_str()));
    assert!(output.contains(include_str!("../../../proof/lean/lean-toolchain").trim()));
    let checked = fs::read(w.0.join("program.lean")).unwrap();
    assert!(output.contains(&format!("proof_blake3={}", blake3::hash(&checked))));
    w.assert_no_scratch();
}

#[test]
#[ignore = "requires installed pinned Lean toolchain; run explicitly for formal validation"]
fn encoded_bytes_are_a_checked_obligation() {
    use b60_lang::Lean4Emitter;
    let w = Workspace::new();
    let correct = Lean4Emitter::emit_bytecode_trace_proof(&[3, 4, 0, 2, 0], "Jump").unwrap();
    let mutated = correct.replace(
        "def traceBytes : List (BitVec 8) := [3, 4, 0, 2, 0]",
        "def traceBytes : List (BitVec 8) := [255]",
    );
    assert_ne!(correct, mutated);
    let proof = w.0.join("jump.lean");
    for (code, expected_success) in [(correct, true), (mutated, false)] {
        fs::write(&proof, code).unwrap();
        let output = Command::new("elan")
            .args([
                "run",
                include_str!("../../../proof/lean/lean-toolchain").trim(),
                "lean",
                "--stdin",
            ])
            .stdin(fs::File::open(&proof).unwrap())
            .output()
            .unwrap();
        assert_eq!(
            output.status.success(),
            expected_success,
            "{}{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

#[test]
fn input_and_output_cannot_be_the_same_path() {
    let w = Workspace::new();
    let path = w.0.join("program.lean");
    fs::write(&path, "HALT\n").unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_b60"))
        .arg("prove")
        .arg(&path)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert_eq!(fs::read_to_string(path).unwrap(), "HALT\n");
    w.assert_no_scratch();
}

#[cfg(unix)]
#[test]
fn a_source_symlink_cannot_alias_the_output() {
    use std::os::unix::fs::symlink;
    let w = Workspace::new();
    let target = w.0.join("program.lean");
    fs::write(&target, "HALT\n").unwrap();
    symlink(&target, w.0.join("program.b60")).unwrap();
    let output = w.command().output().unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("same file"));
    assert_eq!(fs::read_to_string(target).unwrap(), "HALT\n");
    w.assert_no_scratch();
}

#[cfg(unix)]
#[test]
fn an_existing_hardlink_is_conservatively_rejected() {
    let w = Workspace::new();
    let source = w.source("HALT\n");
    fs::hard_link(source, w.0.join("program.lean")).unwrap();
    let output = w.command().output().unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("same file"));
    assert_eq!(
        fs::read_to_string(w.0.join("program.b60")).unwrap(),
        "HALT\n"
    );
    assert_eq!(
        fs::read_to_string(w.0.join("program.lean")).unwrap(),
        "HALT\n"
    );
    w.assert_no_scratch();
}

#[test]
#[ignore = "uses pinned real Lean on a case-sensitive filesystem"]
fn case_variant_extension_never_overwrites_the_source() {
    let w = Workspace::new();
    let source = w.0.join("program.LEAN");
    fs::write(&source, "HALT\n").unwrap();
    let aliased = w.0.join("program.lean").exists();
    let output = Command::new(env!("CARGO_BIN_EXE_b60"))
        .arg("prove")
        .arg(&source)
        .output()
        .unwrap();
    assert_eq!(
        output.status.success(),
        !aliased,
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(fs::read_to_string(source).unwrap(), "HALT\n");
    w.assert_no_scratch();
}

#[test]
#[ignore = "requires installed pinned Lean toolchain; run explicitly for formal validation"]
fn option_like_source_names_are_really_checked() {
    let w = Workspace::new();
    for name in ["-v.b60", "-h.b60", "-qv.b60"] {
        fs::write(w.0.join(name), "NOOP\nHALT\n").unwrap();
        let result = Command::new(env!("CARGO_BIN_EXE_b60"))
            .current_dir(&w.0)
            .args(["prove", "--", name])
            .output()
            .unwrap();
        assert!(
            result.status.success(),
            "{}",
            String::from_utf8_lossy(&result.stderr)
        );
        let stdout = String::from_utf8(result.stdout).unwrap();
        assert!(!stdout.contains("Lean (version"), "{stdout}");
        assert!(!stdout.contains("Usage:"), "{stdout}");
        let proof = fs::read(w.0.join(name).with_extension("lean")).unwrap();
        assert!(stdout.contains(&format!("proof_blake3={}", blake3::hash(&proof))));
        assert!(proof
            .windows(b"B60_PROOF_CHECKED_".len())
            .any(|s| s == b"B60_PROOF_CHECKED_"));
    }
    w.assert_no_scratch();
}

#[cfg(unix)]
fn real_checker_wrapper(w: &Workspace, body: &str) -> (String, String) {
    use std::os::unix::fs::PermissionsExt;
    let python = Command::new("python3")
        .args(["-c", "import sys; print(sys.executable)"])
        .output()
        .unwrap();
    assert!(python.status.success());
    let python = String::from_utf8(python.stdout).unwrap();
    let real = Command::new("python3")
        .args(["-c", "import shutil; print(shutil.which('elan') or '')"])
        .output()
        .unwrap();
    let real = String::from_utf8(real.stdout).unwrap().trim().to_string();
    assert!(!real.is_empty());
    let wrapper = w.0.join("elan");
    fs::write(&wrapper, format!("#!{}\n{body}", python.trim())).unwrap();
    fs::set_permissions(&wrapper, fs::Permissions::from_mode(0o700)).unwrap();
    (
        format!(
            "{}:{}",
            w.0.display(),
            std::env::var("PATH").unwrap_or_default()
        ),
        real,
    )
}

#[cfg(unix)]
#[test]
#[ignore = "requires pinned real Lean and Python scheduling wrapper"]
fn concurrent_provers_check_their_own_captured_bytes_before_publication() {
    let w = Workspace::new();
    let control = w.0.join("control");
    fs::create_dir(&control).unwrap();
    // This wrapper controls scheduling and then execs the real pinned checker.
    // It never fabricates a successful checking result.
    let (path, real) = real_checker_wrapper(
        &w,
        r#"
import os, pathlib, sys, time
control = pathlib.Path(os.environ['B60_TEST_CONTROL'])
role = os.environ['B60_TEST_ROLE']
payload = sys.stdin.buffer.read()
(control / (role + '.stdin')).write_bytes(payload)
(control / (role + '.cwd')).write_text(os.getcwd())
if role == 'first':
    (control / 'ready').touch()
    while not (control / 'release').exists():
        time.sleep(0.01)
with (control / (role + '.stdin')).open('rb') as captured:
    os.dup2(captured.fileno(), 0)
os.execv(os.environ['B60_TEST_REAL_ELAN'], [os.environ['B60_TEST_REAL_ELAN']] + sys.argv[1:])
"#,
    );
    w.source("NOOP\nHALT\n");
    let first = w
        .command()
        .env("PATH", &path)
        .env("B60_TEST_REAL_ELAN", &real)
        .env("B60_TEST_CONTROL", &control)
        .env("B60_TEST_ROLE", "first")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let started = Instant::now();
    while !control.join("ready").exists() && started.elapsed() < Duration::from_secs(10) {
        std::thread::sleep(Duration::from_millis(10));
    }
    assert!(control.join("ready").exists());
    assert!(
        !w.0.join("program.lean").exists(),
        "publication happened before checking"
    );
    w.source("HALT\n");
    let second = w
        .command()
        .env("PATH", &path)
        .env("B60_TEST_REAL_ELAN", &real)
        .env("B60_TEST_CONTROL", &control)
        .env("B60_TEST_ROLE", "second")
        .output()
        .unwrap();
    assert!(
        second.status.success(),
        "{}",
        String::from_utf8_lossy(&second.stderr)
    );
    let first_bytes = fs::read(control.join("first.stdin")).unwrap();
    let second_bytes = fs::read(control.join("second.stdin")).unwrap();
    assert_ne!(first_bytes, second_bytes);
    assert_eq!(fs::read(w.0.join("program.lean")).unwrap(), second_bytes);
    fs::write(control.join("release"), "continue").unwrap();
    let first = first.wait_with_output().unwrap();
    assert!(
        first.status.success(),
        "{}",
        String::from_utf8_lossy(&first.stderr)
    );
    for (output, checked) in [
        (&first.stdout, &first_bytes),
        (&second.stdout, &second_bytes),
    ] {
        assert!(String::from_utf8_lossy(output)
            .contains(&format!("proof_blake3={}", blake3::hash(checked))));
    }
    assert_eq!(fs::read(w.0.join("program.lean")).unwrap(), first_bytes);
    assert_ne!(
        fs::read(control.join("first.cwd")).unwrap(),
        fs::read(control.join("second.cwd")).unwrap()
    );
    w.assert_no_scratch();
}

#[cfg(unix)]
#[test]
#[ignore = "requires pinned real Lean and Python process witness"]
fn timeout_cleans_the_real_checker_group_without_publishing() {
    let w = Workspace::new();
    let witness = w.0.join("checker.pid");
    let (path, real) = real_checker_wrapper(
        &w,
        r#"
import os, pathlib, sys
pathlib.Path(os.environ['B60_TEST_PID']).write_text(str(os.getpid()))
os.execv(os.environ['B60_TEST_REAL_ELAN'], [os.environ['B60_TEST_REAL_ELAN']] + sys.argv[1:])
"#,
    );
    w.source(&("NOOP\n".repeat(1000) + "HALT\n"));
    let started = Instant::now();
    let output = w
        .command()
        .args(["--checker-timeout-ms", "1000"])
        .env("PATH", path)
        .env("B60_TEST_REAL_ELAN", real)
        .env("B60_TEST_PID", &witness)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("Lean timeout"));
    assert!(started.elapsed() < Duration::from_secs(10));
    assert!(!w.0.join("program.lean").exists());
    let group = fs::read_to_string(witness).unwrap();
    let groups = Command::new("/bin/ps")
        .args(["-eo", "pgid="])
        .output()
        .unwrap();
    assert!(!String::from_utf8_lossy(&groups.stdout)
        .lines()
        .any(|s| s.trim() == group.trim()));
    w.assert_no_scratch();
}
