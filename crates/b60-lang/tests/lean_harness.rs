//! Isolated subprocess regressions; fake compilers do not provide Lean evidence.
#![cfg(all(unix, feature = "stress-bins"))]

#[allow(dead_code)]
#[path = "../src/bin/support/lean_harness.rs"]
mod lean_harness;

use lean_harness::{run_captured, verify_with_program, Action, Event, ScratchDir, Verdict};
use std::ffi::OsStr;
use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::process::ExitStatusExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{Duration, Instant};

const ACCEPTED: &str = "B60_TRACE_ACCEPTED";
const REJECTED: &str = "B60_TRACE_REJECTED";

fn nominal() -> Vec<Event> {
    vec![
        Event {
            thread_id: 1,
            seq: 1,
            action: Action::WriteBegin,
        },
        Event {
            thread_id: 1,
            seq: 2,
            action: Action::WriteEnd,
        },
        Event {
            thread_id: 2,
            seq: 2,
            action: Action::Read,
        },
    ]
}

fn corrupt() -> Vec<Event> {
    let valid = nominal();
    vec![
        valid[0].clone(),
        Event {
            thread_id: 2,
            seq: 1,
            action: Action::Read,
        },
        valid[1].clone(),
    ]
}

fn script(directory: &Path, name: &str, body: &str) -> PathBuf {
    let path = directory.join(name);
    fs::write(&path, format!("#!/bin/sh\nset -eu\n{body}\n")).unwrap();
    fs::set_permissions(&path, fs::Permissions::from_mode(0o700)).unwrap();
    path
}

fn quote(path: &Path) -> String {
    format!("'{}'", path.to_string_lossy().replace('\'', "'\"'\"'"))
}

fn verify_fake(body: &str, expected: Verdict) -> Result<lean_harness::CheckResult, String> {
    let directory = ScratchDir::new().unwrap();
    let program = script(directory.path(), "fake-lake", body);
    let events = if expected == Verdict::Accepted {
        nominal()
    } else {
        corrupt()
    };
    verify_with_program(
        &events,
        directory.path(),
        expected,
        program.as_os_str(),
        Duration::from_secs(5),
    )
}

fn rejected_fake(body: &str, expected: Verdict) -> String {
    verify_fake(body, expected)
        .err()
        .expect("compiler protocol error was accepted")
}

#[test]
fn accepts_only_the_single_expected_marker_for_each_verdict() {
    for (expected, marker) in [(Verdict::Accepted, ACCEPTED), (Verdict::Rejected, REJECTED)] {
        let result = verify_fake(&format!("printf '%s\\n' '{marker}'"), expected).unwrap();
        assert!(result.emit_seconds >= 0.0 && result.lean_seconds >= 0.0);
    }
}

#[test]
fn missing_duplicate_conflicting_and_extra_output_are_errors() {
    for body in [
        "exit 0",
        "printf 'B60_TRACE_ACCEPTED\\nB60_TRACE_ACCEPTED\\n'",
        "printf 'B60_TRACE_ACCEPTED\\nB60_TRACE_REJECTED\\n'",
        "printf 'unrelated output\\nB60_TRACE_ACCEPTED\\n'",
        "printf 'B60_TRACE_REJECTED\\n'",
    ] {
        assert!(
            rejected_fake(body, Verdict::Accepted).contains("did not certify"),
            "{body}"
        );
    }
    assert!(
        rejected_fake("printf 'B60_TRACE_ACCEPTED\\n'", Verdict::Rejected)
            .contains("did not certify")
    );
}

#[test]
fn nonzero_exit_is_an_error_even_after_the_expected_marker() {
    for code in [1, 2] {
        for (expected, marker) in [(Verdict::Accepted, ACCEPTED), (Verdict::Rejected, REJECTED)] {
            let error = rejected_fake(&format!("printf '%s\\n' '{marker}'\nexit {code}"), expected);
            assert!(error.contains("did not certify") && error.contains(marker));
        }
    }
}

#[test]
fn stderr_and_compiler_errors_cannot_count_as_a_semantic_rejection() {
    for body in [
        "printf 'B60_TRACE_REJECTED\\n'\nprintf 'unknown module BabylonTrace\\n' >&2\nexit 1",
        "printf 'B60_TRACE_REJECTED\\n'\nprintf 'unexpected token\\n' >&2\nexit 1",
        "printf 'B60_TRACE_REJECTED\\n'\nprintf 'warning or diagnostic\\n' >&2",
        "printf 'B60_TRACE_REJECTED\\n' >&2",
    ] {
        assert!(
            rejected_fake(body, Verdict::Rejected).contains("did not certify"),
            "{body}"
        );
    }
}

#[test]
fn a_missing_program_is_a_spawn_error() {
    let directory = ScratchDir::new().unwrap();
    let missing = directory.path().join("missing-compiler");
    let error = verify_with_program(
        &corrupt(),
        directory.path(),
        Verdict::Rejected,
        missing.as_os_str(),
        Duration::from_secs(1),
    )
    .err()
    .expect("missing compiler was accepted");
    assert!(error.contains("Process spawn"), "{error}");
}

#[test]
fn a_signal_is_an_execution_error_even_after_a_rejection_marker() {
    let error = rejected_fake(
        "printf 'B60_TRACE_REJECTED\\n'\nkill -TERM $$",
        Verdict::Rejected,
    );
    assert!(error.contains("did not certify"), "{error}");
    let mut command = Command::new("/bin/sh");
    command.args(["-c", "kill -TERM $$"]);
    let output = run_captured(command, Duration::from_secs(5)).unwrap();
    assert_eq!(output.status.code(), None);
    assert_eq!(output.status.signal(), Some(15));
}

#[test]
fn captures_both_streams_beyond_pipe_capacity() {
    let mut command = Command::new("/bin/sh");
    command.args(["-c", "i=0; while [ \"$i\" -lt 4096 ]; do printf 'stdout:0123456789abcdef0123456789abcdef\\n'; printf 'stderr:0123456789abcdef0123456789abcdef\\n' >&2; i=$((i + 1)); done"]);
    let output = run_captured(command, Duration::from_secs(10)).unwrap();
    assert!(output.status.success());
    assert_eq!(
        output.stdout,
        "stdout:0123456789abcdef0123456789abcdef\n"
            .repeat(4096)
            .as_bytes()
    );
    assert_eq!(
        output.stderr,
        "stderr:0123456789abcdef0123456789abcdef\n"
            .repeat(4096)
            .as_bytes()
    );
}

struct ReapIfNeeded(String);

impl Drop for ReapIfNeeded {
    fn drop(&mut self) {
        if process_is_running(&self.0) {
            let _ = Command::new("/bin/kill").args(["-KILL", &self.0]).output();
        }
    }
}

fn process_is_running(pid: &str) -> bool {
    let output = Command::new("/bin/ps")
        .args(["-o", "stat=", "-p", pid])
        .output()
        .unwrap();
    let state = String::from_utf8_lossy(&output.stdout);
    // Orphaned zombies can wait for PID 1 to reap them; they cannot keep executing.
    output.status.success() && !state.trim().is_empty() && !state.trim_start().starts_with('Z')
}

#[test]
fn timeout_terminates_the_process_group_including_a_descendant() {
    let directory = ScratchDir::new().unwrap();
    let pidfile = directory.path().join("descendant.pid");
    let program = script(
        directory.path(),
        "sleeping-compiler",
        &format!(
            "/bin/sleep 60 &\nchild=$!\nprintf '%s\\n' \"$child\" > {}\nwait \"$child\"",
            quote(&pidfile)
        ),
    );
    let start = Instant::now();
    // Allow interpreter startup while other subprocess tests run in parallel.
    // This checks termination and descendants, not a one-second latency target.
    let result = run_captured(Command::new(&program), Duration::from_secs(5));
    let elapsed = start.elapsed();
    let pid = fs::read_to_string(&pidfile)
        .unwrap_or_else(|error| {
            panic!("compiler did not start its descendant: {error}; runner: {result:?}")
        })
        .trim()
        .to_owned();
    let _reap = ReapIfNeeded(pid.clone());
    let error = result.err().expect("timed out process was accepted");
    assert!(error.contains("Process timeout"), "{error}");
    assert!(
        elapsed < Duration::from_secs(10),
        "timeout took {elapsed:?}"
    );
    for _ in 0..50 {
        if !process_is_running(&pid) {
            return;
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    panic!("descendant {pid} remained alive after timeout");
}

#[test]
fn emits_the_expected_theorem_in_a_temporary_source_and_removes_it() {
    for (expected, literal, marker) in [
        (Verdict::Accepted, "true", ACCEPTED),
        (Verdict::Rejected, "false", REJECTED),
    ] {
        let directory = ScratchDir::new().unwrap();
        let snapshot = directory.path().join("snapshot.txt");
        let source_path = directory.path().join("source-path.txt");
        let fixture = directory.path().join("BabylonAutoTrace.lean");
        fs::write(&fixture, "existing tracked-style fixture").unwrap();
        let program = script(directory.path(), "source-recorder", &format!(
            "[ \"$#\" -eq 3 ] && [ \"$1\" = env ] && [ \"$2\" = lean ]\n/bin/cat \"$3\" > {}\nprintf '%s' \"$3\" > {}\nprintf '%s\\n' '{marker}'",
            quote(&snapshot), quote(&source_path)
        ));
        let events = if expected == Verdict::Accepted {
            nominal()
        } else {
            corrupt()
        };
        verify_with_program(
            &events,
            directory.path(),
            expected,
            program.as_os_str(),
            Duration::from_secs(5),
        )
        .unwrap();
        let source = fs::read_to_string(snapshot).unwrap();
        let theorem = format!("theorem trace_expected_verdict : validateTrace auto_execution_trace = {literal} := by\n  decide");
        assert!(source.starts_with("import BabylonTrace\nset_option warningAsError true\n"));
        assert!(source.contains(&theorem));
        assert!(source.contains("#guard_msgs in\n#print axioms trace_expected_verdict"));
        assert!(
            source.find(&theorem).unwrap()
                < source
                    .find(&format!("#eval IO.println \"{marker}\""))
                    .unwrap()
        );
        assert!(source.contains("threadId := 1, seq := 1, action := Action.writeBegin"));
        let generated = PathBuf::from(fs::read_to_string(source_path).unwrap());
        assert!(generated.is_absolute() && !generated.starts_with(directory.path()));
        assert!(!generated.exists(), "temporary Lean source was not removed");
        assert!(
            !generated.parent().unwrap().exists(),
            "temporary directory was not removed"
        );
        assert_eq!(
            fs::read_to_string(fixture).unwrap(),
            "existing tracked-style fixture"
        );
    }
}

const FAKE_LAKE: &str = r#"
[ "$#" -eq 3 ] && [ "$1" = env ] && [ "$2" = lean ]
source=$(/bin/cat "$3")
case "$source" in
  *"validateTrace auto_execution_trace = true := by"*) verdict=true; marker=B60_TRACE_ACCEPTED ;;
  *"validateTrace auto_execution_trace = false := by"*) verdict=false; marker=B60_TRACE_REJECTED ;;
  *) exit 90 ;;
esac
printf '%s\n' "$verdict" >> "$B60_TEST_CALLS"
printf '%s\n' "$3" >> "$B60_TEST_SOURCES"
case "$B60_TEST_MODE:$verdict" in
  nominal_fail:true|negative_fail:false) printf '%s\n' "$marker"; printf 'simulated compiler error\n' >&2; exit 1 ;;
  accepted_negative:false) printf 'B60_TRACE_ACCEPTED\n' ;;
  *) printf '%s\n' "$marker" ;;
esac
"#;

struct CliResult {
    output: Output,
    calls: Vec<String>,
}

fn run_cli(binary: &str, argument: &str, mode: &str) -> CliResult {
    let directory = ScratchDir::new().unwrap();
    script(directory.path(), "lake", FAKE_LAKE);
    let calls = directory.path().join("calls.txt");
    let sources = directory.path().join("sources.txt");
    let fixture = directory.path().join("BabylonStressCorrupt.lean");
    fs::write(&fixture, "fixture must survive CLI checks").unwrap();
    let mut command = Command::new(binary);
    command
        .arg(argument)
        .env("PATH", directory.path())
        .env("BABYLON_LEAN_WORKSPACE", directory.path())
        .env("B60_TEST_MODE", mode)
        .env("B60_TEST_CALLS", &calls)
        .env("B60_TEST_SOURCES", &sources);
    let output = run_captured(command, Duration::from_secs(10)).unwrap();
    let calls = fs::read_to_string(calls)
        .unwrap_or_default()
        .lines()
        .map(str::to_owned)
        .collect();
    for source in fs::read_to_string(sources).unwrap_or_default().lines() {
        assert!(
            !Path::new(source).exists(),
            "CLI left temporary Lean source behind"
        );
    }
    assert_eq!(
        fs::read_to_string(fixture).unwrap(),
        "fixture must survive CLI checks"
    );
    CliResult { output, calls }
}

fn binaries() -> [(&'static str, &'static str); 3] {
    [
        (env!("CARGO_BIN_EXE_fsm_poc"), "--lean-only"),
        (env!("CARGO_BIN_EXE_fsm_poc"), "--jit-only"),
        (env!("CARGO_BIN_EXE_fsm_stress"), "--quick"),
    ]
}

#[test]
fn both_clis_require_the_nominal_control_before_the_negative_control() {
    for (binary, argument) in binaries() {
        let result = run_cli(binary, argument, "success");
        assert!(
            result.output.status.success(),
            "{}",
            String::from_utf8_lossy(&result.output.stderr)
        );
        assert_eq!(result.calls, ["true", "false"], "{binary}");
    }
}

#[test]
fn both_clis_fail_globally_on_nominal_negative_or_wrong_verdict_errors() {
    for (binary, argument) in binaries() {
        for mode in ["nominal_fail", "negative_fail", "accepted_negative"] {
            let result = run_cli(binary, argument, mode);
            assert!(!result.output.status.success(), "{binary} accepted {mode}");
            assert!(String::from_utf8_lossy(&result.output.stderr).contains("HARNESS ERROR"));
            let expected = if mode == "nominal_fail" {
                vec!["true"]
            } else {
                vec!["true", "false"]
            };
            assert_eq!(result.calls, expected, "{binary}: {mode}");
        }
    }
}

#[test]
fn both_clis_reject_invalid_arguments_before_invoking_lean() {
    for (binary, _) in binaries() {
        let result = run_cli(binary, "--unknown", "success");
        assert!(!result.output.status.success());
        assert!(String::from_utf8_lossy(&result.output.stderr).contains("Usage:"));
        assert!(result.calls.is_empty());
    }
}

#[test]
#[ignore = "requires the project-pinned Lake toolchain and built BabylonTrace import"]
fn real_lean_proves_both_verdicts_and_rejects_a_wrong_expectation() {
    let workspace = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../proof/lean");
    let snapshots: Vec<_> = ["BabylonAutoTrace.lean", "BabylonStressCorrupt.lean"]
        .into_iter()
        .map(|name| {
            let path = workspace.join(name);
            let content = fs::read(&path).unwrap();
            (path, content)
        })
        .collect();
    for (events, expected) in [
        (nominal(), Verdict::Accepted),
        (corrupt(), Verdict::Rejected),
    ] {
        verify_with_program(
            &events,
            &workspace,
            expected,
            OsStr::new("lake"),
            Duration::from_secs(120),
        )
        .unwrap();
    }
    let wrong = verify_with_program(
        &nominal(),
        &workspace,
        Verdict::Rejected,
        OsStr::new("lake"),
        Duration::from_secs(120),
    );
    assert!(wrong.is_err(), "Lean certified the wrong model expectation");
    let lookup = Command::new("/bin/sh")
        .args(["-c", "command -v lake"])
        .output()
        .unwrap();
    assert!(
        lookup.status.success(),
        "Lake is required for this explicit test"
    );
    let real_lake = PathBuf::from(String::from_utf8(lookup.stdout).unwrap().trim());
    assert!(
        real_lake.is_absolute(),
        "Lake lookup must resolve an absolute executable"
    );
    let directory = ScratchDir::new().unwrap();
    for (name, broken_source) in [
        (
            "missing-import",
            "import B60HarnessDeliberatelyMissingImport",
        ),
        (
            "invalid-syntax",
            "import BabylonTrace\ntheorem broken : := by",
        ),
    ] {
        // Only replace the disposable generated source; all project sources remain intact.
        let wrapper = script(
            directory.path(),
            name,
            &format!(
                "printf '%s\\n' '{broken_source}' > \"$3\"\nexec {} \"$@\"",
                quote(&real_lake)
            ),
        );
        let error = verify_with_program(
            &corrupt(),
            &workspace,
            Verdict::Rejected,
            wrapper.as_os_str(),
            Duration::from_secs(120),
        )
        .err()
        .expect("broken Lean source counted as a semantic rejection");
        assert!(
            error.contains("did not certify") && error.contains("error:"),
            "{name}: {error}"
        );
    }
    for (path, original) in snapshots {
        assert_eq!(fs::read(path).unwrap(), original);
    }
}
