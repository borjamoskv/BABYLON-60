//! Isolated checks of a closed trace in BabylonTrace, not a Rust concurrency proof.
use std::ffi::OsStr;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy)]
pub enum Action {
    WriteBegin,
    WriteEnd,
    Read,
}

#[derive(Debug, Clone)]
pub struct Event {
    pub thread_id: u64,
    pub seq: u64,
    pub action: Action,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verdict {
    Accepted,
    Rejected,
}

impl Verdict {
    fn literal(self) -> &'static str {
        match self {
            Self::Accepted => "true",
            Self::Rejected => "false",
        }
    }

    fn marker(self) -> &'static str {
        match self {
            Self::Accepted => "B60_TRACE_ACCEPTED",
            Self::Rejected => "B60_TRACE_REJECTED",
        }
    }
}

// Timing fields are used by fsm_stress; fsm_poc only requires successful verification.
#[allow(dead_code)]
pub struct CheckResult {
    pub emit_seconds: f64,
    pub lean_seconds: f64,
}

pub fn workspace() -> PathBuf {
    std::env::var_os("BABYLON_LEAN_WORKSPACE")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            if Path::new("proof/lean").is_dir() {
                PathBuf::from("proof/lean")
            } else {
                PathBuf::from(std::env::var_os("BABYLON_HOME").unwrap_or_else(|| ".".into()))
                    .join("proof/lean")
            }
        })
}

pub struct ScratchDir {
    path: PathBuf,
}

impl ScratchDir {
    pub fn new() -> Result<Self, String> {
        static NEXT: AtomicU64 = AtomicU64::new(0);
        for _ in 0..100 {
            let path = std::env::temp_dir().join(format!(
                "b60-lean-{}-{}",
                std::process::id(),
                NEXT.fetch_add(1, Ordering::Relaxed)
            ));
            let mut builder = fs::DirBuilder::new();
            #[cfg(unix)]
            {
                use std::os::unix::fs::DirBuilderExt;
                builder.mode(0o700);
            }
            match builder.create(&path) {
                Ok(()) => return Ok(Self { path }),
                Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(error) => return Err(format!("Temporary directory: {error}")),
            }
        }
        Err("Unable to allocate temporary directory".into())
    }

    pub fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for ScratchDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

pub fn verify(
    events: &[Event],
    workspace: &Path,
    expected: Verdict,
) -> Result<CheckResult, String> {
    verify_with_program(
        events,
        workspace,
        expected,
        OsStr::new("lake"),
        Duration::from_secs(120),
    )
}

pub fn verify_with_program(
    events: &[Event],
    workspace: &Path,
    expected: Verdict,
    program: &OsStr,
    timeout: Duration,
) -> Result<CheckResult, String> {
    let scratch = ScratchDir::new()?;
    let source = scratch.path().join("TraceCheck.lean");
    let emit_start = Instant::now();
    emit(events, expected, &source).map_err(|error| format!("Lean source I/O: {error}"))?;
    let emit_seconds = emit_start.elapsed().as_secs_f64();
    let mut command = Command::new(program);
    command
        .args(["env", "lean"])
        .arg(&source)
        .current_dir(workspace);
    let lean_start = Instant::now();
    let output = run_captured(command, timeout)?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    // Lean may continue to #eval after a failed theorem: a marker alone is insufficient.
    if !output.status.success() || stdout.trim() != expected.marker() || !stderr.trim().is_empty() {
        return Err(format!(
            "Lean did not certify the expected {} verdict ({}):\nstdout: {}\nstderr: {}",
            expected.literal(),
            output.status,
            stdout,
            stderr
        ));
    }
    Ok(CheckResult {
        emit_seconds,
        lean_seconds: lean_start.elapsed().as_secs_f64(),
    })
}

fn emit(events: &[Event], expected: Verdict, path: &Path) -> std::io::Result<()> {
    let mut writer = BufWriter::new(File::options().write(true).create_new(true).open(path)?);
    writeln!(
        writer,
        "import BabylonTrace\nset_option warningAsError true\nnamespace B60.Ledger"
    )?;
    writeln!(
        writer,
        "set_option maxRecDepth 2000000\nset_option maxHeartbeats 5000000"
    )?;
    writeln!(writer, "def auto_execution_trace : List Event := [")?;
    for (i, event) in events.iter().enumerate() {
        let action = match event.action {
            Action::WriteBegin => "Action.writeBegin",
            Action::WriteEnd => "Action.writeEnd",
            Action::Read => "Action.read",
        };
        writeln!(
            writer,
            "  {{ threadId := {}, seq := {}, action := {} }}{}",
            event.thread_id,
            event.seq,
            action,
            if i + 1 == events.len() { "" } else { "," }
        )?;
    }
    writeln!(writer, "]\ntheorem trace_expected_verdict : validateTrace auto_execution_trace = {} := by\n  decide", expected.literal())?;
    writeln!(
        writer,
        "/-- info: 'B60.Ledger.trace_expected_verdict' does not depend on any axioms -/"
    )?;
    writeln!(
        writer,
        "#guard_msgs in\n#print axioms trace_expected_verdict"
    )?;
    writeln!(
        writer,
        "#eval IO.println \"{}\"\nend B60.Ledger",
        expected.marker()
    )?;
    writer.flush()
}

/// Capture both streams without pipe deadlocks. Timeout kills the process group on Unix.
/// On other platforms it terminates only the direct child.
pub fn run_captured(mut command: Command, timeout: Duration) -> Result<Output, String> {
    let scratch = ScratchDir::new()?;
    let stdout_path = scratch.path().join("stdout");
    let stderr_path = scratch.path().join("stderr");
    command
        .stdin(Stdio::null())
        .stdout(
            File::options()
                .write(true)
                .create_new(true)
                .open(&stdout_path)
                .map_err(|e| e.to_string())?,
        )
        .stderr(
            File::options()
                .write(true)
                .create_new(true)
                .open(&stderr_path)
                .map_err(|e| e.to_string())?,
        );
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    let mut child = command
        .spawn()
        .map_err(|error| format!("Process spawn: {error}"))?;
    let start = Instant::now();
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) if start.elapsed() < timeout => std::thread::sleep(Duration::from_millis(10)),
            result => {
                #[cfg(unix)]
                let group_kill = Command::new("/bin/kill")
                    .args(["-KILL", "--", &format!("-{}", child.id())])
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status();
                let _ = child.kill();
                let _ = child.wait();
                #[cfg(unix)]
                if !matches!(group_kill, Ok(status) if status.success()) {
                    return Err("Process cleanup failed for Unix process group".into());
                }
                return Err(match result {
                    Err(error) => format!("Process wait: {error}"),
                    _ => format!("Process timeout after {:.3}s", timeout.as_secs_f64()),
                });
            }
        }
    };
    Ok(Output {
        status,
        stdout: fs::read(stdout_path).map_err(|e| e.to_string())?,
        stderr: fs::read(stderr_path).map_err(|e| e.to_string())?,
    })
}
