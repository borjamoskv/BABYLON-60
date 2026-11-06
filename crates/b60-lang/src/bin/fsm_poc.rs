#[path = "support/lean_harness.rs"]
mod lean_harness;

use lean_harness::{Action, Event, ScratchDir, Verdict};
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;
use std::process::{Command, ExitCode};
use std::time::Duration;

fn verify_csv(events: &[Event], oracle: &Path, trace: &Path) -> Result<Verdict, String> {
    let mut writer = BufWriter::new(File::create(trace).map_err(|e| e.to_string())?);
    for event in events {
        let action = match event.action {
            Action::WriteBegin => 0,
            Action::WriteEnd => 1,
            Action::Read => 2,
        };
        writeln!(writer, "{},{},{}", event.thread_id, event.seq, action)
            .map_err(|e| e.to_string())?;
    }
    writer.flush().map_err(|e| e.to_string())?;
    let mut command = Command::new(oracle);
    command.arg(trace);
    let output = lean_harness::run_captured(command, Duration::from_secs(120))?;
    // CSV oracle contract: 0 = accepted, 2 = rejected step, 1 = format/I/O error.
    match output.status.code() {
        Some(0) => Ok(Verdict::Accepted),
        Some(2) => Ok(Verdict::Rejected),
        _ => Err(format!(
            "CSV oracle execution error ({}):\nstdout: {}\nstderr: {}",
            output.status,
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        )),
    }
}

fn run() -> Result<(), String> {
    let lean_only = match std::env::args().skip(1).collect::<Vec<_>>().as_slice() {
        [] => false,
        [flag] if matches!(flag.as_str(), "--lean-only" | "--jit-only") => true,
        _ => return Err("Usage: fsm_poc [--lean-only] (legacy alias: --jit-only)".into()),
    };
    let workspace = lean_harness::workspace();
    let nominal = vec![
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
    ];
    lean_harness::verify(&nominal, &workspace, Verdict::Accepted)?;
    println!("[LEAN_CHECK] Nominal trace: Lean proved validateTrace = true (3 events).");
    let corrupt = vec![
        nominal[0].clone(),
        Event {
            thread_id: 2,
            seq: 1,
            action: Action::Read,
        },
        nominal[1].clone(),
    ];
    lean_harness::verify(&corrupt, &workspace, Verdict::Rejected)?;
    println!("[LEAN_CHECK] Negative trace: Lean proved validateTrace = false (3 events).");
    if lean_only {
        return Ok(());
    }

    let oracle = std::env::var_os("BABYLON_ORACLE_BIN")
        .map(Into::into)
        .unwrap_or_else(|| workspace.join(".lake/build/bin/oracle"));
    // Synthetic sequential input; this does not observe concurrent Rust execution.
    let mut trace = Vec::with_capacity(1_000_002);
    for transaction in 0..333_334 {
        let seq = transaction * 2 + 1;
        trace.push(Event {
            thread_id: 1,
            seq,
            action: Action::WriteBegin,
        });
        trace.push(Event {
            thread_id: 1,
            seq: seq + 1,
            action: Action::WriteEnd,
        });
        trace.push(Event {
            thread_id: 2,
            seq: seq + 1,
            action: Action::Read,
        });
    }
    let scratch = ScratchDir::new()?;
    if verify_csv(&trace, &oracle, &scratch.path().join("nominal.csv"))? != Verdict::Accepted {
        return Err("CSV oracle rejected the nominal control".into());
    }
    println!(
        "[CSV] Nominal synthetic trace accepted ({} events).",
        trace.len()
    );
    trace[500_000] = Event {
        thread_id: 99,
        seq: trace[500_000].seq - 1,
        action: Action::Read,
    };
    if verify_csv(&trace, &oracle, &scratch.path().join("corrupt.csv"))? != Verdict::Rejected {
        return Err("CSV oracle accepted the negative control".into());
    }
    println!(
        "[CSV] Negative synthetic trace rejected ({} events).",
        trace.len()
    );
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("[HARNESS ERROR] {error}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(all(test, unix))]
mod tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn csv_oracle_distinguishes_model_verdicts_from_execution_errors() {
        let scratch = ScratchDir::new().unwrap();
        let oracle = scratch.path().join("oracle");
        for (body, expected) in [
            ("exit 0", Some(Verdict::Accepted)),
            ("exit 2", Some(Verdict::Rejected)),
            ("echo format-error >&2; exit 1", None),
            ("exit 3", None),
            ("kill -TERM $$", None),
        ] {
            std::fs::write(&oracle, format!("#!/bin/sh\n{body}\n")).unwrap();
            std::fs::set_permissions(&oracle, std::fs::Permissions::from_mode(0o700)).unwrap();
            let result = verify_csv(&[], &oracle, &scratch.path().join("trace.csv"));
            match expected {
                Some(verdict) => assert_eq!(result.unwrap(), verdict),
                None => assert!(result.is_err()),
            }
        }
        assert!(verify_csv(
            &[],
            &scratch.path().join("missing-oracle"),
            &scratch.path().join("trace.csv")
        )
        .is_err());
        assert!(verify_csv(
            &[],
            &oracle,
            &scratch.path().join("missing-parent/trace.csv")
        )
        .is_err());
    }
}
