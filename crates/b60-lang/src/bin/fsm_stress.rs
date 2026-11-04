#[path = "support/lean_harness.rs"]
mod lean_harness;

use lean_harness::{Action, Event, Verdict};
use std::process::ExitCode;

fn generate_valid_trace(transactions: usize) -> Vec<Event> {
    let mut trace = Vec::with_capacity(transactions * 3);
    for i in 0..transactions {
        let thread_id = (i % 4) as u64 + 1;
        let seq = (i * 2 + 1) as u64;
        trace.push(Event {
            thread_id,
            seq,
            action: Action::WriteBegin,
        });
        trace.push(Event {
            thread_id,
            seq: seq + 1,
            action: Action::WriteEnd,
        });
        trace.push(Event {
            thread_id: ((i + 1) % 4) as u64 + 1,
            seq: seq + 1,
            action: Action::Read,
        });
    }
    trace
}

fn run() -> Result<(), String> {
    let quick = match std::env::args().skip(1).collect::<Vec<_>>().as_slice() {
        [] => false,
        [flag] if flag == "--quick" => true,
        _ => return Err("Usage: fsm_stress [--quick]".into()),
    };
    let workspace = lean_harness::workspace();
    let sizes: &[usize] = if quick {
        &[10]
    } else {
        &[10, 50, 100, 250, 500, 1000, 2000]
    };
    println!(
        "[LEAN_CHECK] Synthetic trace checks against BabylonTrace; timings are local observations."
    );
    for &transactions in sizes {
        let trace = generate_valid_trace(transactions);
        let result = lean_harness::verify(&trace, &workspace, Verdict::Accepted)?;
        println!(
            "[LEAN_CHECK] Proved true: {} events | emit {:.4}s | Lean {:.4}s",
            trace.len(),
            result.emit_seconds,
            result.lean_seconds
        );
    }
    let transactions = if quick { 10 } else { 500 };
    let mut corrupt = generate_valid_trace(transactions);
    corrupt.push(Event {
        thread_id: 99,
        seq: (transactions * 2 + 1) as u64,
        action: Action::Read,
    });
    let result = lean_harness::verify(&corrupt, &workspace, Verdict::Rejected)?;
    println!(
        "[LEAN_CHECK] Proved false: {} events | Lean {:.4}s",
        corrupt.len(),
        result.lean_seconds
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
