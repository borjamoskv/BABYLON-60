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

#[derive(Debug, Clone)]
pub struct LockState {
    pub seq: u64,
    pub writer: Option<u64>,
}

impl LockState {
    fn to_lean_syntax(&self) -> String {
        let writer_str = match self.writer {
            Some(w) => format!("some {}", w),
            None => "none".to_string(),
        };
        format!("{{ seq := {}, writer := {} }}", self.seq, writer_str)
    }
}

pub struct AeonBlock {
    pub aeon_index: usize,
    pub initial_state: LockState,
    pub final_state: LockState,
    pub events: Vec<Event>,
}

pub struct AeonChainingPipeline;

impl AeonChainingPipeline {
    pub fn verify_aeons(
        aeons: &[AeonBlock],
        lean_workspace_dir: &str,
        output_file_name: &str,
    ) -> Result<(bool, f64, f64, String), String> {
        let target_path = Path::new(lean_workspace_dir).join(output_file_name);

        let t_emit = Instant::now();
        Self::emit_chained_file(aeons, &target_path)
            .map_err(|e| format!("I/O Error: {}", e))?;
        let emit_sec = t_emit.elapsed().as_secs_f64();

        let t_lean = Instant::now();
        let output = Command::new("lake")
            .arg("env")
            .arg("lean")
            .arg(output_file_name)
            .current_dir(lean_workspace_dir)
            .output()
            .map_err(|e| format!("Lean execution failed: {}", e))?;
        let lean_sec = t_lean.elapsed().as_secs_f64();

        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Ok((output.status.success(), emit_sec, lean_sec, stderr))
    }

    fn emit_chained_file(aeons: &[AeonBlock], file_path: &Path) -> IoResult<()> {
        let file = File::create(file_path)?;
        let mut writer = BufWriter::new(file);

        writeln!(writer, "-- ========================================================")?;
        writeln!(writer, "-- 🌀 BABYLON-60: ENCADENAMIENTO CONFORME DE AEONES (INV_C5_AEON)")?;
        writeln!(writer, "-- Particionado O(1) de AST para Escala a 1M de Transacciones")?;
        writeln!(writer, "-- ========================================================\n")?;
        writeln!(writer, "import BabylonTrace\n")?;
        writeln!(writer, "namespace B60.Ledger\n")?;
        writeln!(writer, "set_option maxRecDepth 2000000\n")?;
        writeln!(writer, "set_option maxHeartbeats 5000000\n")?;

        for aeon in aeons {
            let idx = aeon.aeon_index;
            writeln!(writer, "-- --- AEÓN {} ---", idx)?;
            writeln!(writer, "def aeon_{}_events : List Event := [", idx)?;
            for (i, ev) in aeon.events.iter().enumerate() {
                let comma = if i == aeon.events.len() - 1 { "" } else { "," };
                writeln!(
                    writer,
                    "  {{ threadId := {}, seq := {}, action := {} }}{}",
                    ev.thread_id, ev.seq, ev.action.to_lean_syntax(), comma
                )?;
            }
            writeln!(writer, "]\n")?;

            writeln!(
                writer,
                "theorem aeon_{}_step : runAeon (some {}) aeon_{}_events = some {} := by",
                idx, aeon.initial_state.to_lean_syntax(), idx, aeon.final_state.to_lean_syntax()
            )?;
            writeln!(writer, "  decide\n")?;
        }

        writeln!(writer, "end B60.Ledger")?;
        writer.flush()?;
        Ok(())
    }
}

fn generate_aeon(aeon_index: usize, start_seq: u64, n_transactions: usize) -> AeonBlock {
    let mut events = Vec::with_capacity(n_transactions * 3);
    let mut current_seq = start_seq;
    let initial_state = LockState { seq: start_seq, writer: None };

    for i in 0..n_transactions {
        let thread = (i % 4) as u64 + 1;
        // WriteBegin
        current_seq += 1;
        events.push(Event { thread_id: thread, seq: current_seq, action: Action::WriteBegin });
        // WriteEnd
        current_seq += 1;
        events.push(Event { thread_id: thread, seq: current_seq, action: Action::WriteEnd });
        // Read
        events.push(Event { thread_id: ((i + 1) % 4) as u64 + 1, seq: current_seq, action: Action::Read });
    }

    let final_state = LockState { seq: current_seq, writer: None };
    AeonBlock {
        aeon_index,
        initial_state,
        final_state,
        events,
    }
}

fn main() {
    let default_lean = if std::path::Path::new("proof/lean").exists() {
        "proof/lean".to_string()
    } else {
        format!("{}/proof/lean", std::env::var("BABYLON_HOME").unwrap_or_else(|_| ".".to_string()))
    };
    let lean_workspace = std::env::var("BABYLON_LEAN_WORKSPACE").unwrap_or(default_lean);
    let lean_workspace = lean_workspace.as_str();
    println!("================================================================================");
    println!("🌀 [AEON CHAINING] PROOF BY REFLECTION CONFORME (INV_C5_AEON)");
    println!("================================================================================");

    // Simulamos 5 Aeones continuos de 500 txs cada uno (1.500 eventos por aeon = 7.500 eventos)
    let n_aeons = 5;
    let tx_per_aeon = 500;
    let mut aeons = Vec::new();
    let mut seq = 0u64;

    for i in 0..n_aeons {
        let aeon = generate_aeon(i, seq, tx_per_aeon);
        seq = aeon.final_state.seq;
        aeons.push(aeon);
    }

    println!("Demostrando la historia de {} Aeones encadenados ({} eventos en total)...",
        n_aeons, n_aeons * tx_per_aeon * 3);

    match AeonChainingPipeline::verify_aeons(&aeons, &lean_workspace, "BabylonAeonChain.lean") {
        Ok((success, emit_sec, lean_sec, stderr)) => {
            if success {
                println!("✅ ÉXITO TOTAL: {} Aeones verificados formalmente en cadena.", n_aeons);
                println!("⏱️ Telemetría: Emisión AST: {:.4}s | Verificación Lean 4: {:.4}s", emit_sec, lean_sec);
                println!("🚀 Causalidad Conforme Preservada: S_0 -> S_1 -> S_2 -> S_3 -> S_4 -> S_5");
            } else {
                println!("❌ FALLO: {}", stderr);
            }
        }
        Err(e) => println!("💥 ERROR FATAL: {}", e),
    }
}
