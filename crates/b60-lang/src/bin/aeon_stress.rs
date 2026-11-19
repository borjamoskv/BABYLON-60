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

fn emit_single_aeon(aeon: &AeonBlock, file_path: &Path) -> IoResult<()> {
    let file = File::create(file_path)?;
    let mut writer = BufWriter::new(file);

    writeln!(writer, "import BabylonTrace\n")?;
    writeln!(writer, "namespace B60.Ledger\n")?;
    writeln!(writer, "set_option maxRecDepth 2000000")?;
    writeln!(writer, "set_option maxHeartbeats 8000000\n")?;

    writeln!(writer, "def aeon_events : List Event := [")?;
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
        "theorem aeon_valid : runAeon (some {}) aeon_events = some {} := by",
        aeon.initial_state.to_lean_syntax(),
        aeon.final_state.to_lean_syntax()
    )?;
    writeln!(writer, "  decide\n")?;
    writeln!(writer, "end B60.Ledger")?;
    writer.flush()?;
    Ok(())
}

fn generate_aeon(aeon_index: usize, start_seq: u64, n_transactions: usize) -> AeonBlock {
    let mut events = Vec::with_capacity(n_transactions * 3);
    let mut current_seq = start_seq;
    let initial_state = LockState { seq: start_seq, writer: None };

    for i in 0..n_transactions {
        let thread = (i % 4) as u64 + 1;
        current_seq += 1;
        events.push(Event { thread_id: thread, seq: current_seq, action: Action::WriteBegin });
        current_seq += 1;
        events.push(Event { thread_id: thread, seq: current_seq, action: Action::WriteEnd });
        events.push(Event { thread_id: ((i + 1) % 4) as u64 + 1, seq: current_seq, action: Action::Read });
    }

    let final_state = LockState { seq: current_seq, writer: None };
    AeonBlock { aeon_index, initial_state, final_state, events }
}

fn verify_single(aeon: &AeonBlock, lean_dir: &str) -> Result<(bool, f64, f64), String> {
    let fname = "BabylonAeonStress.lean";
    let target = Path::new(lean_dir).join(fname);

    let t0 = Instant::now();
    emit_single_aeon(aeon, &target).map_err(|e| format!("{}", e))?;
    let t_emit = t0.elapsed().as_secs_f64();

    let t1 = Instant::now();
    let out = Command::new("lake")
        .arg("env").arg("lean").arg(fname)
        .current_dir(lean_dir)
        .output()
        .map_err(|e| format!("{}", e))?;
    let t_lean = t1.elapsed().as_secs_f64();

    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr);
        return Err(format!("Lean Exit != 0: {}", stderr));
    }
    Ok((true, t_emit, t_lean))
}

fn main() {
    let default_lean = if std::path::Path::new("proof/lean").exists() {
        "proof/lean".to_string()
    } else {
        format!("{}/proof/lean", std::env::var("BABYLON_HOME").unwrap_or_else(|_| ".".to_string()))
    };
    let lean_dir = std::env::var("BABYLON_LEAN_WORKSPACE").unwrap_or(default_lean);
    let lean_dir = lean_dir.as_str();
    println!("================================================================================");
    println!("🔥 [AEON STRESS] ESCALA DE AEONES INDIVIDUALES - BUSCANDO LA PARED TERMODINÁMICA");
    println!("================================================================================\n");

    // Tamaños crecientes de transacciones POR AEÓN individual
    let test_sizes: Vec<usize> = vec![100, 500, 1000, 2000, 3000, 5000, 7500, 10000];

    for &n_tx in &test_sizes {
        let total_events = n_tx * 3;
        let aeon = generate_aeon(0, 0, n_tx);
        print!("  Aeón individual: {} txs ({} eventos)... ", n_tx, total_events);

        match verify_single(&aeon, lean_dir) {
            Ok((_ok, t_emit, t_lean)) => {
                let rate = total_events as f64 / t_lean;
                println!(
                    "✅ | Emit: {:.4}s | Lean: {:.2}s | Rate: {:.0} evts/s",
                    t_emit, t_lean, rate
                );
            }
            Err(e) => {
                println!("❌ PARED ALCANZADA");
                println!("    Detalle: {}", &e[..e.len().min(300)]);
                break;
            }
        }
    }

    println!("\n--- ESCALA HORIZONTAL: ENCADENAMIENTO DE MÚLTIPLES AEONES (500 txs/aeon) ---\n");

    let tx_per_aeon = 500;
    let aeon_counts: Vec<usize> = vec![5, 10, 20, 50];

    for &n_aeons in &aeon_counts {
        let total_events = n_aeons * tx_per_aeon * 3;
        let mut aeons = Vec::new();
        let mut seq = 0u64;
        for i in 0..n_aeons {
            let a = generate_aeon(i, seq, tx_per_aeon);
            seq = a.final_state.seq;
            aeons.push(a);
        }

        print!("  {} Aeones x {} txs = {} eventos totales... ", n_aeons, tx_per_aeon, total_events);

        // Verificar cada Aeón individualmente (escala horizontal real)
        let t_total = Instant::now();
        let mut all_ok = true;
        for aeon in &aeons {
            match verify_single(aeon, lean_dir) {
                Ok(_) => {}
                Err(e) => {
                    println!("❌ Aeón {} falló: {}", aeon.aeon_index, &e[..e.len().min(200)]);
                    all_ok = false;
                    break;
                }
            }
        }
        let t_wall = t_total.elapsed().as_secs_f64();

        if all_ok {
            let rate = total_events as f64 / t_wall;
            println!("✅ | Wall: {:.2}s | Rate: {:.0} evts/s", t_wall, rate);
        }
    }
}
