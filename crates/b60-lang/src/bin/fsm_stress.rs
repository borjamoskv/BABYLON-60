use std::fs::File;
use std::io::{BufWriter, Write, Result as IoResult};
use std::process::Command;
use std::path::Path;
use std::time::Instant;

#[derive(Debug, Clone)]
pub enum Action {
    WriteBegin,
    WriteEnd,
    Read,
}

impl Action {
    fn to_lean_syntax(&self) -> &'static str {
        match self {
            Action::WriteBegin => "Action.writeBegin",
            Action::WriteEnd => "Action.writeEnd",
            Action::Read => "Action.read",
        }
    }
}

#[derive(Debug, Clone)]
pub struct Event {
    pub thread_id: u64,
    pub seq: u64,
    pub action: Action,
}

pub struct ProofPipeline;

impl ProofPipeline {
    pub fn verify(
        events: &[Event],
        lean_workspace_dir: &str,
        output_file_name: &str,
    ) -> Result<(bool, f64, f64, String), String> {
        let target_path = Path::new(lean_workspace_dir).join(output_file_name);

        let t_emit_start = Instant::now();
        Self::emit_lean_file(events, &target_path)
            .map_err(|e| format!("I/O Error: {}", e))?;
        let emit_duration = t_emit_start.elapsed().as_secs_f64();

        let t_lean_start = Instant::now();
        let output = Command::new("lake")
            .arg("env")
            .arg("lean")
            .arg(output_file_name)
            .current_dir(lean_workspace_dir)
            .output()
            .map_err(|e| format!("Lean execution failed: {}", e))?;
        let lean_duration = t_lean_start.elapsed().as_secs_f64();

        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        Ok((output.status.success(), emit_duration, lean_duration, stderr))
    }

    fn emit_lean_file(events: &[Event], file_path: &Path) -> IoResult<()> {
        let file = File::create(file_path)?;
        let mut writer = BufWriter::new(file);

        writeln!(writer, "import BabylonTrace\n")?;
        writeln!(writer, "namespace B60.Ledger\n")?;
        writeln!(writer, "set_option maxRecDepth 2000000\n")?;
        writeln!(writer, "set_option maxHeartbeats 5000000\n")?;

        writeln!(writer, "def auto_execution_trace : List Event := [")?;
        for (i, event) in events.iter().enumerate() {
            let comma = if i == events.len() - 1 { "" } else { "," };
            writeln!(
                writer,
                "  {{ threadId := {}, seq := {}, action := {} }}{}",
                event.thread_id, event.seq, event.action.to_lean_syntax(), comma
            )?;
        }
        writeln!(writer, "]\n")?;

        writeln!(writer, "theorem trace_is_paradox_free_auto : validateTrace auto_execution_trace = true := by")?;
        writeln!(writer, "  decide\n")?;
        writeln!(writer, "end B60.Ledger")?;

        writer.flush()?;
        Ok(())
    }
}

fn generate_valid_trace(n_transactions: usize) -> Vec<Event> {
    let mut trace = Vec::with_capacity(n_transactions * 3);
    let mut seq = 0u64;
    for i in 0..n_transactions {
        let thread = (i % 4) as u64 + 1;
        // WriteBegin
        seq += 1;
        trace.push(Event { thread_id: thread, seq, action: Action::WriteBegin });
        // WriteEnd
        seq += 1;
        trace.push(Event { thread_id: thread, seq, action: Action::WriteEnd });
        // Read
        trace.push(Event { thread_id: ((i + 1) % 4) as u64 + 1, seq, action: Action::Read });
    }
    trace
}

fn main() {
    let lean_workspace = "/Users/borjafernandezangulo/BABYLON-60/proof/lean";
    println!("================================================================================");
    println!("🔥 [STRESS TEST] FSM PROOF-BY-REFLECTION EMPIRICAL AUDIT");
    println!("================================================================================");

    let test_sizes = vec![10, 50, 100, 250, 500, 1000, 2000];

    for &n_tx in &test_sizes {
        let total_events = n_tx * 3;
        let trace = generate_valid_trace(n_tx);
        print!("Probando N = {} txs ({} eventos)... ", n_tx, total_events);

        match ProofPipeline::verify(&trace, lean_workspace, "BabylonStressTrace.lean") {
            Ok((success, emit_sec, lean_sec, stderr)) => {
                if success {
                    println!("✅ ÉXITO | Emit: {:.4}s | Lean: {:.4}s | Total: {:.4}s",
                        emit_sec, lean_sec, emit_sec + lean_sec);
                } else {
                    println!("❌ FALLO DE COMPROBACIÓN | Emit: {:.4}s | Lean: {:.4}s", emit_sec, lean_sec);
                    println!("Stderr: {}", stderr);
                    break;
                }
            }
            Err(e) => {
                println!("💥 ERROR FATAL: {}", e);
                break;
            }
        }
    }

    println!("\n--- TEST DE RECHAZO BAJO ESTRÉS (INYECCIÓN DE ANOMALÍA EN TAIL) ---");
    let n_tx = 500;
    let mut corrupted_trace = generate_valid_trace(n_tx);
    corrupted_trace.push(Event {
        thread_id: 99,
        seq: (n_tx * 2 + 1) as u64, // Odd seq (Torn Read)
        action: Action::Read,
    });

    match ProofPipeline::verify(&corrupted_trace, lean_workspace, "BabylonStressCorrupt.lean") {
        Ok((success, _emit_sec, lean_sec, _)) => {
            if !success {
                println!(
                    "🛡️ RECHAZO EXITOSO DE ANOMALÍA (N = {} eventos). Lean abortó en {:.4}s",
                    corrupted_trace.len(),
                    lean_sec
                );
            } else {
                println!("🔥 ERROR CRÍTICO: Anomalía no fue rechazada.");
            }
        }
        Err(e) => println!("💥 ERROR FATAL: {}", e),
    }
}
