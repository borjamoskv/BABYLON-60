//! Prover regressions. Positive certification uses the pinned real Lean checker.
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

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
}

#[cfg(unix)]
#[test]
fn a_checker_failure_never_certifies_the_emitted_file() {
    use std::os::unix::fs::PermissionsExt;
    let w = Workspace::new();
    w.source("HALT\n");
    // Negative process-protocol fixture only: it does not supply Lean evidence.
    let checker = w.0.join("elan");
    fs::write(&checker, "#!/bin/sh\nexit 7\n").unwrap();
    fs::set_permissions(&checker, fs::Permissions::from_mode(0o700)).unwrap();
    let result = w.command().env("PATH", &w.0).output().unwrap();
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr).contains("Lean rejected"));
    assert!(!String::from_utf8_lossy(&result.stdout).contains("VERIFIED: compiled"));
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
            ])
            .arg(&proof)
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
