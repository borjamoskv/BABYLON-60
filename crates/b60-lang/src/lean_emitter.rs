// ============================================================================
// B60 LEAN 4 EMITTER: SEQLOCK FSM + CAUSAL DAG PROOF GENERATION
// Framework: C5-REAL | Proof by Reflection (by decide) over Bool FSMs
// ============================================================================

use std::fs::File;
use std::io::{BufWriter, Write, Result as IoResult};
use std::path::Path;
use std::process::Command;

use crate::dag::CompiledCausalPlan;

// ============================================================================
// 1. ISOMORFISMO ESTRUCTURAL (Seqlock FSM)
// Mapeo 1:1 con las estructuras de BabylonTrace.lean
// ============================================================================

/// Acción atómica del Seqlock: WriteBegin/WriteEnd/Read
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SeqlockAction {
    WriteBegin,
    WriteEnd,
    Read,
}

impl SeqlockAction {
    /// Traducción mecánica a la ontología de Lean 4. Cero deducción.
    pub fn to_lean_syntax(&self) -> &'static str {
        match self {
            SeqlockAction::WriteBegin => "Action.writeBegin",
            SeqlockAction::WriteEnd => "Action.writeEnd",
            SeqlockAction::Read => "Action.read",
        }
    }
}

/// Evento atómico de la traza Seqlock
#[derive(Debug, Clone)]
pub struct SeqlockEvent {
    pub thread_id: u64,
    pub seq: u64,
    pub action: SeqlockAction,
}

/// Estado del candado tras evaluar un bloque de eventos (Aeón)
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeqlockState {
    pub seq: u64,
    pub writer: Option<u64>,
}

impl SeqlockState {
    pub fn initial() -> Self {
        Self { seq: 0, writer: None }
    }

    pub fn to_lean_syntax(&self) -> String {
        let writer_str = match self.writer {
            Some(w) => format!("some {}", w),
            None => "none".to_string(),
        };
        format!("{{ seq := {}, writer := {} }}", self.seq, writer_str)
    }
}

/// Bloque conforme de eventos (INV_C5_AEON): partición acotada de la traza
#[derive(Debug, Clone)]
pub struct AeonBlock {
    pub aeon_index: usize,
    pub initial_state: SeqlockState,
    pub final_state: SeqlockState,
    pub events: Vec<SeqlockEvent>,
}

// ============================================================================
// 2. LEAN 4 EMITTER (Unificado: Seqlock FSM + CausalDAG)
// ============================================================================

// Write in the destination directory and rename; never truncate a symlink target.
struct AtomicProofFile {
    writer: BufWriter<File>,
    temporary: std::path::PathBuf,
    destination: std::path::PathBuf,
}
impl AtomicProofFile {
    fn new(destination: &Path) -> IoResult<Self> {
        use std::sync::atomic::{AtomicU64, Ordering};
        static NEXT: AtomicU64 = AtomicU64::new(0);
        if std::fs::symlink_metadata(destination).is_ok_and(|m| m.file_type().is_symlink()) {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidInput, "proof output is a symlink"));
        }
        let parent = destination.parent().unwrap_or(Path::new("."));
        let temporary = parent.join(format!(".b60-proof-{}-{}.tmp", std::process::id(), NEXT.fetch_add(1, Ordering::Relaxed)));
        let mut options = std::fs::OpenOptions::new();
        options.write(true).create_new(true);
        #[cfg(unix)] {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        let writer = BufWriter::new(options.open(&temporary)?);
        Ok(Self { writer, temporary, destination: destination.to_path_buf() })
    }
    fn commit(mut self) -> IoResult<()> {
        self.writer.flush()?;
        self.writer.get_ref().sync_all()?;
        std::fs::rename(&self.temporary, &self.destination)
    }
}
impl Drop for AtomicProofFile {
    fn drop(&mut self) { let _ = std::fs::remove_file(&self.temporary); }
}

fn output_basename(name: &str) -> Result<(), String> {
    if Path::new(name).file_name() != Some(std::ffi::OsStr::new(name)) {
        return Err("proof output must be an exact file name".into());
    }
    let mut components = Path::new(name).components();
    match (components.next(), components.next()) {
        (Some(std::path::Component::Normal(_)), None) => Ok(()),
        _ => Err("proof output must be a single file name".into()),
    }
}

pub struct Lean4Emitter;

impl Lean4Emitter {
    // -----------------------------------------------------------------------
    // A) SEQLOCK FSM: Proof-Carrying Execution via Aeon Chaining
    // -----------------------------------------------------------------------

    /// Emite un archivo Lean 4 con los teoremas de transición para cada Aeón.
    /// Cada Aeón demuestra: `runAeon (some S_i) events_i = some S_{i+1} := by decide`
    pub fn emit_aeon_chain(aeons: &[AeonBlock], file_path: &Path) -> IoResult<()> {
        let genesis_ok = aeons.first().is_none_or(|a| a.initial_state == SeqlockState::initial());
        let connected = aeons.windows(2).all(|pair|
            pair[0].final_state == pair[1].initial_state && pair[0].aeon_index < pair[1].aeon_index);
        if !genesis_ok || !connected {
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidInput, "disconnected aeon chain"));
        }
        let mut output = AtomicProofFile::new(file_path)?;
        let writer = &mut output.writer;

        writeln!(writer, "-- ========================================================")?;
        writeln!(writer, "-- 🌀 BABYLON-60: AEON CHAIN (INV_C5_AEON)")?;
        writeln!(writer, "-- AUTOGENERATED — DO NOT MODIFY")?;
        writeln!(writer, "-- ========================================================\n")?;
        writeln!(writer, "import BabylonTrace\n")?;
        writeln!(writer, "set_option warningAsError true\nnamespace B60.Ledger\n")?;
        writeln!(writer, "set_option maxRecDepth 2000000")?;
        writeln!(writer, "set_option maxHeartbeats 8000000\n")?;

        for aeon in aeons {
            Self::emit_aeon_block(writer, aeon)?;
        }

        writeln!(writer, "end B60.Ledger")?;
        output.commit()
    }

    /// Emite un archivo Lean 4 para un Aeón individual (verificación atómica).
    pub fn emit_single_aeon(aeon: &AeonBlock, file_path: &Path) -> IoResult<()> {
        let mut output = AtomicProofFile::new(file_path)?;
        let writer = &mut output.writer;

        writeln!(writer, "import BabylonTrace\n")?;
        writeln!(writer, "set_option warningAsError true\nnamespace B60.Ledger\n")?;
        writeln!(writer, "set_option maxRecDepth 2000000")?;
        writeln!(writer, "set_option maxHeartbeats 8000000\n")?;

        Self::emit_aeon_block(writer, aeon)?;

        writeln!(writer, "end B60.Ledger")?;
        output.commit()
    }

    fn emit_aeon_block(writer: &mut BufWriter<File>, aeon: &AeonBlock) -> IoResult<()> {
        let idx = aeon.aeon_index;

        writeln!(writer, "-- --- AEÓN {} ({} eventos) ---", idx, aeon.events.len())?;
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
            "theorem aeon_{}_valid : runAeon (some {}) aeon_{}_events = some {} := by",
            idx, aeon.initial_state.to_lean_syntax(), idx, aeon.final_state.to_lean_syntax()
        )?;
        writeln!(writer, "  decide\n/-- info: 'B60.Ledger.aeon_{idx}_valid' does not depend on any axioms -/\n#guard_msgs in\n#print axioms aeon_{idx}_valid\n")
    }

    // -----------------------------------------------------------------------
    // B) ORQUESTACIÓN E2E: Emite + Invoca Lean 4 + Retorna veredicto
    // -----------------------------------------------------------------------

    /// Pipeline E2E para verificar una cadena de Aeones contra el Oráculo.
    pub fn verify_aeon_chain(
        aeons: &[AeonBlock],
        lean_workspace_dir: &str,
        output_file_name: &str,
    ) -> Result<bool, String> {
        output_basename(output_file_name)?;
        let target_path = Path::new(lean_workspace_dir).join(output_file_name);

        Self::emit_aeon_chain(aeons, &target_path)
            .map_err(|e| format!("I/O Error emitting Lean AST: {}", e))?;

        // Pass an absolute path so names such as `--version` cannot become Lean options.
        let verification_path = target_path
            .canonicalize()
            .map_err(|e| format!("I/O Error resolving emitted Lean AST: {}", e))?;
        let status = Command::new("lake")
            .arg("env")
            .arg("lean")
            .arg(&verification_path)
            .current_dir(lean_workspace_dir)
            .status()
            .map_err(|e| format!("Lean invocation failed: {}", e))?;

        Ok(status.success())
    }

    /// Pipeline E2E para verificar un Aeón individual.
    pub fn verify_single_aeon(
        aeon: &AeonBlock,
        lean_workspace_dir: &str,
        output_file_name: &str,
    ) -> Result<bool, String> {
        output_basename(output_file_name)?;
        let target_path = Path::new(lean_workspace_dir).join(output_file_name);

        Self::emit_single_aeon(aeon, &target_path)
            .map_err(|e| format!("I/O Error emitting Lean AST: {}", e))?;

        // Pass an absolute path so names such as `--version` cannot become Lean options.
        let verification_path = target_path
            .canonicalize()
            .map_err(|e| format!("I/O Error resolving emitted Lean AST: {}", e))?;
        let status = Command::new("lake")
            .arg("env")
            .arg("lean")
            .arg(&verification_path)
            .current_dir(lean_workspace_dir)
            .status()
            .map_err(|e| format!("Lean invocation failed: {}", e))?;

        Ok(status.success())
    }

    // -----------------------------------------------------------------------
    // C) CAUSAL DAG: Obligaciones de prueba por conservación de exergía
    // -----------------------------------------------------------------------

    /// Genera las obligaciones de prueba formales para un plan causal (Isomorfismo Curry-Howard)
    pub fn emit_causal_plan_proof(plan: &CompiledCausalPlan, module_name: &str) -> String {
        let mut lean = String::new();

        lean.push_str("import Init\n\n");
        lean.push_str("set_option warningAsError true\n\n");
        lean.push_str("-- ============================================================================\n");
        lean.push_str(&format!("-- AUTO-GENERATED PROOF IR FOR: {}\n", module_name));
        lean.push_str("-- ============================================================================\n\n");

        lean.push_str("namespace CausalDAGProof\n\n");

        lean.push_str("-- 1. Topological Stage Definitions\n");
        for stage in &plan.execution_stages {
            lean.push_str(&format!(
                "def Stage_{}_budget : Nat := {}\n",
                stage.stage_index, stage.stage_exergy_budget
            ));
        }
        lean.push('\n');

        lean.push_str("-- 2. Total Exergy Invariant\n");
        lean.push_str(&format!("def total_exergy : Nat := {}\n", plan.total_exergy_cost));
        lean.push_str("theorem exergy_conservation : total_exergy = ");
        let budget_terms: Vec<String> = plan
            .execution_stages
            .iter()
            .map(|s| format!("Stage_{}_budget", s.stage_index))
            .collect();
        if budget_terms.is_empty() {
            lean.push_str("0 := by rfl\n\n");
        } else {
            lean.push_str(&format!("{} := by rfl\n\n", budget_terms.join(" + ")));
        }

        lean.push_str("-- 3. Causal Lineage Admissibility (Monotonic Wave Ordering)\n");
        let stage_indices_str: Vec<String> = plan
            .execution_stages
            .iter()
            .map(|s| s.stage_index.to_string())
            .collect();
        lean.push_str(&format!(
            "def stage_indices : List Nat := [{}]\n\n",
            stage_indices_str.join(", ")
        ));
        lean.push_str("def isStrictlyIncreasing : List Nat → Bool\n");
        lean.push_str("  | [] => true\n");
        lean.push_str("  | [_] => true\n");
        lean.push_str("  | a :: b :: rest => (a < b) && isStrictlyIncreasing (b :: rest)\n\n");
        lean.push_str("theorem causal_order_admissible : isStrictlyIncreasing stage_indices = true := by\n");
        lean.push_str("  decide\n\n");
        lean.push_str("/-- info: 'CausalDAGProof.causal_order_admissible' does not depend on any axioms -/\n");
        lean.push_str("#guard_msgs in\n");
        lean.push_str("#print axioms causal_order_admissible\n\n");

        lean.push_str("end CausalDAGProof\n");

        lean
    }

    /// Genera las obligaciones para una traza de bytecode B60 (F60VM Constructive Halting Bound)
    pub fn emit_bytecode_trace_proof(bytecode: &[u8], module_name: &str) -> String {
        let mut lean = String::new();

        lean.push_str("import Init\n\n");
        lean.push_str("set_option warningAsError true\n\n");
        lean.push_str("-- ============================================================================\n");
        lean.push_str(&format!(
            "-- AUTO-GENERATED BYTECODE TRACE PROOF FOR: {}\n",
            module_name
        ));
        lean.push_str("-- ============================================================================\n\n");

        lean.push_str("namespace BytecodeTrace\n\n");

        let opcodes_list: Vec<String> = bytecode
            .iter()
            .map(|&b| b.to_string())
            .collect();
        let mnemonics_comment: Vec<String> = bytecode
            .iter()
            .map(|&b| {
                crate::isa::SexaOpCode::from_u8(b)
                    .map(|op| op.mnemonic().to_string())
                    .unwrap_or_else(|| format!("RAW_0x{b:02X}"))
            })
            .collect();
        lean.push_str(&format!(
            "-- Decoded ISA stream: [{}]\n",
            mnemonics_comment.join(", ")
        ));
        lean.push_str(&format!(
            "def trace_opcodes : List Nat := [{}]\n",
            opcodes_list.join(", ")
        ));
        lean.push_str(&format!("def trace_length : Nat := {}\n\n", bytecode.len()));
        lean.push_str("theorem trace_opcodes_length_eq : trace_opcodes.length = trace_length := by\n");
        lean.push_str("  rfl\n\n");

        lean.push_str("structure F60VMState where\n");
        lean.push_str("  pc     : Nat\n");
        lean.push_str("  fuel   : Nat\n");
        lean.push_str("  halted : Bool\n");
        lean.push_str("  deriving Repr, BEq, DecidableEq\n\n");

        lean.push_str("def stepVM (s : F60VMState) : F60VMState :=\n");
        lean.push_str("  if s.halted || s.fuel == 0 || s.pc >= trace_length then\n");
        lean.push_str("    { s with halted := true, fuel := 0 }\n");
        lean.push_str("  else\n");
        lean.push_str("    { pc := s.pc + 1, fuel := s.fuel - 1, halted := false }\n\n");

        lean.push_str("-- Constructive proof: zero fuel deterministically transitions F60VM to halted state\n");
        lean.push_str("theorem valid_halting_path (s : F60VMState) (h_zero : s.fuel = 0) :\n");
        lean.push_str("    (stepVM s).halted = true := by\n");
        lean.push_str("  unfold stepVM\n");
        lean.push_str("  simp [h_zero]\n\n");

        lean.push_str("theorem finite_fuel_horizon (total_fuel step_cost : Nat) :\n");
        lean.push_str("    (total_fuel / step_cost) * step_cost ≤ total_fuel := by\n");
        lean.push_str("  exact Nat.div_mul_le_self total_fuel step_cost\n\n");

        lean.push_str("end BytecodeTrace\n");

        lean
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dag::{ExecutionStage, CompiledCausalPlan};

    #[test]
    fn test_lean_emitter_causal_plan_and_bytecode_proof() {
        let plan = CompiledCausalPlan {
            topological_order: vec![1, 2],
            execution_stages: vec![
                ExecutionStage { stage_index: 0, parallel_node_ids: vec![1], stage_exergy_budget: 100 },
                ExecutionStage { stage_index: 1, parallel_node_ids: vec![2], stage_exergy_budget: 200 },
            ],
            total_exergy_cost: 300,
            cumulative_fisher_action: 0.5,
        };

        let lean_code = Lean4Emitter::emit_causal_plan_proof(&plan, "TestCausalPlan");
        assert!(lean_code.contains("def Stage_0_budget : Nat := 100"));
        assert!(lean_code.contains("def Stage_1_budget : Nat := 200"));
        assert!(lean_code.contains("def total_exergy : Nat := 300"));
        assert!(lean_code.contains("Stage_0_budget + Stage_1_budget"));
        assert!(lean_code.contains("isStrictlyIncreasing stage_indices = true"));

        let bytecode_lean = Lean4Emitter::emit_bytecode_trace_proof(&[0x01, 0x02, 0x60], "TestBytecode");
        assert!(bytecode_lean.contains("def trace_length : Nat := 3"));
        assert!(bytecode_lean.contains("theorem valid_halting_path"));
        assert!(!bytecode_lean.contains("exact em"));

        if Command::new("lean").arg("--version").output().is_ok() {
            let plan_file = std::env::temp_dir().join(format!("b60_causal_plan_{}.lean", std::process::id()));
            std::fs::write(&plan_file, &lean_code).unwrap();
            let status_plan = Command::new("lean").arg(&plan_file).status().unwrap();
            let _ = std::fs::remove_file(&plan_file);
            assert!(status_plan.success(), "Emitted CausalDAGProof Lean 4 code must compile cleanly");

            let bc_file = std::env::temp_dir().join(format!("b60_bytecode_trace_{}.lean", std::process::id()));
            std::fs::write(&bc_file, &bytecode_lean).unwrap();
            let status_bc = Command::new("lean").arg(&bc_file).status().unwrap();
            let _ = std::fs::remove_file(&bc_file);
            assert!(status_bc.success(), "Emitted BytecodeTrace Lean 4 code must compile cleanly");
        }
    }

    #[test]
    fn test_seqlock_event_lean_syntax() {
        assert_eq!(SeqlockAction::WriteBegin.to_lean_syntax(), "Action.writeBegin");
        assert_eq!(SeqlockAction::WriteEnd.to_lean_syntax(), "Action.writeEnd");
        assert_eq!(SeqlockAction::Read.to_lean_syntax(), "Action.read");
    }

    #[test]
    fn test_seqlock_state_lean_syntax() {
        let s = SeqlockState { seq: 42, writer: Some(7) };
        assert_eq!(s.to_lean_syntax(), "{ seq := 42, writer := some 7 }");

        let s0 = SeqlockState::initial();
        assert_eq!(s0.to_lean_syntax(), "{ seq := 0, writer := none }");
    }

    #[test]
    fn test_emit_single_aeon_creates_file() {
        let aeon = AeonBlock {
            aeon_index: 0,
            initial_state: SeqlockState::initial(),
            final_state: SeqlockState { seq: 2, writer: None },
            events: vec![
                SeqlockEvent { thread_id: 1, seq: 1, action: SeqlockAction::WriteBegin },
                SeqlockEvent { thread_id: 1, seq: 2, action: SeqlockAction::WriteEnd },
            ],
        };
        let tmp = std::env::temp_dir().join("test_aeon_emit.lean");
        Lean4Emitter::emit_single_aeon(&aeon, &tmp).unwrap();
        let content = std::fs::read_to_string(&tmp).unwrap();
        assert!(content.contains("aeon_0_events"));
        assert!(content.contains("aeon_0_valid"));
        assert!(content.contains("by"));
        assert!(content.contains("decide"));
        std::fs::remove_file(&tmp).ok();
    }

    #[test]
    #[ignore = "requires lake and an isolated BABYLON_LEAN_TEST_WORKSPACE with BabylonTrace built"]
    fn test_verification_checks_option_like_output_names() {
        let workspace = std::env::var("BABYLON_LEAN_TEST_WORKSPACE")
            .expect("set BABYLON_LEAN_TEST_WORKSPACE to an isolated Lean workspace");
        let valid = AeonBlock {
            aeon_index: 0,
            initial_state: SeqlockState::initial(),
            final_state: SeqlockState::initial(),
            events: Vec::new(),
        };
        let invalid = AeonBlock {
            final_state: SeqlockState { seq: 1, writer: None },
            ..valid.clone()
        };

        for output in ["--version", "--help", "B60 invocation regression.lean"] {
            assert!(
                !Lean4Emitter::verify_single_aeon(&invalid, &workspace, output).unwrap(),
                "an invalid single aeon was accepted for {output}"
            );
            assert!(
                !Lean4Emitter::verify_aeon_chain(std::slice::from_ref(&invalid), &workspace, output)
                    .unwrap(),
                "an invalid aeon chain was accepted for {output}"
            );
            assert!(Lean4Emitter::verify_single_aeon(&valid, &workspace, output).unwrap());
            assert!(
                Lean4Emitter::verify_aeon_chain(std::slice::from_ref(&valid), &workspace, output)
                    .unwrap()
            );
            std::fs::remove_file(Path::new(&workspace).join(output)).unwrap();
        }
    }

    #[test]
    fn security_verifier_output_cannot_escape_workspace() {
        let root = std::env::temp_dir().join(format!("b60_emit_boundary_{}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        let workspace = root.join("workspace");
        std::fs::create_dir(&workspace).unwrap();
        let victim = root.join("outside.lean");
        std::fs::write(&victim, "SENTINEL").unwrap();
        let block = AeonBlock { aeon_index: 0, initial_state: SeqlockState::initial(),
            final_state: SeqlockState::initial(), events: vec![] };
        let result = Lean4Emitter::verify_single_aeon(&block, workspace.to_str().unwrap(), "../outside.lean");
        let contents = std::fs::read_to_string(&victim).unwrap();
        std::fs::remove_dir_all(&root).unwrap();
        assert_eq!(contents, "SENTINEL", "verification overwrote a file outside its workspace");
        assert!(result.is_err());
    }

    #[test]
    #[cfg(unix)]
    fn security_verifier_output_does_not_follow_symlink() {
        let root = std::env::temp_dir().join(format!("b60_emit_symlink_{}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        let workspace = root.join("workspace");
        std::fs::create_dir(&workspace).unwrap();
        let victim = root.join("outside.lean");
        std::fs::write(&victim, "SENTINEL").unwrap();
        std::os::unix::fs::symlink(&victim, workspace.join("proof.lean")).unwrap();
        let block = AeonBlock { aeon_index: 0, initial_state: SeqlockState::initial(),
            final_state: SeqlockState::initial(), events: vec![] };
        let result = Lean4Emitter::verify_single_aeon(&block, workspace.to_str().unwrap(), "proof.lean");
        let contents = std::fs::read_to_string(&victim).unwrap();
        std::fs::remove_dir_all(&root).unwrap();
        assert_eq!(contents, "SENTINEL", "verification followed a pre-existing symlink");
        assert!(result.is_err());
    }

    #[test]
    #[ignore = "requires a prepared BABYLON_LEAN_TEST_WORKSPACE"]
    fn security_disconnected_aeons_cannot_verify_as_a_chain() {
        let workspace = std::env::var("BABYLON_LEAN_TEST_WORKSPACE").unwrap();
        let first = AeonBlock { aeon_index: 0, initial_state: SeqlockState::initial(),
            final_state: SeqlockState::initial(), events: vec![] };
        let second = AeonBlock { aeon_index: 1, initial_state: SeqlockState { seq: 2, writer: None },
            final_state: SeqlockState { seq: 2, writer: None }, events: vec![] };
        let output = "security_disconnected_aeons.lean";
        let connected = AeonBlock { aeon_index: 1, initial_state: SeqlockState::initial(),
            final_state: SeqlockState::initial(), events: vec![] };
        assert!(Lean4Emitter::verify_aeon_chain(&[first.clone(), connected], &workspace, output).unwrap());
        let result = Lean4Emitter::verify_aeon_chain(&[first, second], &workspace, output);
        let _ = std::fs::remove_file(Path::new(&workspace).join(output));
        assert!(!result.unwrap_or(false), "independent proofs were accepted as one contiguous history");
    }
}
