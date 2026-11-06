use std::fs;
use std::process::Command;
use std::time::Instant;

/// PoC: Emisor Chunked y Orquestación de Lean 4
/// Superando el "AST Explosion Limit" dividiendo el log en lotes (Chunking)
const CHUNK_SIZE: usize = 5000;
const LEAN_OUTPUT_DIR: &str = "scripts/c5_demos/lean_chunks";

pub struct Lean4Emitter;

impl Lean4Emitter {
    pub fn prove_end_to_end(total_events: usize) -> Result<(), String> {
        println!("🚀 Iniciando Proof-Carrying Execution (Rust -> Lean 4)");
        println!("📊 Total de eventos a verificar: {}", total_events);

        Self::validate_chunk(total_events, 0)?;

        fs::create_dir_all(LEAN_OUTPUT_DIR).map_err(|e| e.to_string())?;

        let num_chunks = total_events.div_ceil(CHUNK_SIZE);

        for chunk_idx in 0..num_chunks {
            let start = chunk_idx * CHUNK_SIZE;
            let end = std::cmp::min(start.saturating_add(CHUNK_SIZE), total_events);
            let size = end - start;

            // 1. Emitir archivo Lean
            let file_path = format!("{}/chunk_{}.lean", LEAN_OUTPUT_DIR, chunk_idx);
            Self::emit_lean_chunk(&file_path, size, start)?;

            // 2. Invocar Oráculo (Lean 4)
            println!(
                "⚖️  Evaluando Chunk {} (Eventos {} a {}) en Lean 4...",
                chunk_idx,
                start,
                end - 1
            );
            let t0 = Instant::now();
            let status = Command::new("elan")
                .args([
                    "run",
                    include_str!("../proof/lean/lean-toolchain").trim(),
                    "lean",
                ])
                .arg(&file_path)
                .status()
                .map_err(|e| format!("Fallo al invocar Lean: {}", e))?;

            let elapsed = t0.elapsed();

            if status.success() {
                println!(
                    "✅ EXIT 0: Chunk {} validado en {:.2?}.",
                    chunk_idx, elapsed
                );
            } else {
                println!("❌ EXIT != 0: Paradoja en Chunk {}.", chunk_idx);
                return Err("Traza corrompida detectada por Lean 4.".into());
            }
        }

        println!("🏆 Verificación End-to-End completada con éxito. Causalidad preservada.");
        Ok(())
    }

    fn validate_chunk(size: usize, offset: usize) -> Result<(), String> {
        if size == 0 || !size.is_multiple_of(2) || !offset.is_multiple_of(2) {
            return Err(
                "Chunks must start and end outside a write, with a positive even size.".into(),
            );
        }
        let end = offset.checked_add(size).ok_or("Sequence overflow")?;
        u64::try_from(end).map_err(|_| "Sequence exceeds BitVec 64")?;
        Ok(())
    }

    fn render_lean_chunk(size: usize, offset: usize) -> Result<String, String> {
        Self::validate_chunk(size, offset)?;
        let mut events = Vec::with_capacity(size);
        for i in 0..size {
            let action = if i % 2 == 0 { "WriteBegin" } else { "WriteEnd" };
            events.push(format!(
                "  {{ thread := 1, seq := {}, action := Action.{} }}",
                offset + i + 1,
                action
            ));
        }
        Ok(format!(
            r#"
{}
set_option maxRecDepth 1000000
set_option maxHeartbeats 10000000
open B60.ExampleSeqlockTrace

def chunk_trace : List SeqlockEvent := [
{}
]

theorem chunk_is_valid : isValidTrace chunk_trace {} = true := by decide
"#,
            include_str!("../proof/lean/ExampleSeqlockTrace.lean"),
            events.join(",\n"),
            offset
        ))
    }

    fn emit_lean_chunk(path: &str, size: usize, offset: usize) -> Result<(), String> {
        let code = Self::render_lean_chunk(size, offset)?;
        fs::write(path, code).map_err(|e| e.to_string())
    }
}

fn main() {
    let total_events = 15000; // Por encima del límite de asfixia (10k)
    match Lean4Emitter::prove_end_to_end(total_events) {
        Ok(_) => std::process::exit(0),
        Err(e) => {
            eprintln!("Fallo Crítico: {}", e);
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_open_or_overflowing_chunk_boundaries() {
        for (size, offset) in [(0, 0), (1, 0), (2, 1), (3, 5000), (2, usize::MAX - 1)] {
            assert!(Lean4Emitter::render_lean_chunk(size, offset).is_err());
        }
    }

    #[test]
    fn chunk_offsets_are_event_counts() {
        let code = Lean4Emitter::render_lean_chunk(2, 5000).unwrap();
        assert!(code.contains("seq := 5001, action := Action.WriteBegin"));
        assert!(code.contains("seq := 5002, action := Action.WriteEnd"));
        assert!(code.contains("isValidTrace chunk_trace 5000 = true"));
    }

    #[test]
    #[ignore = "requires pinned Lean; executed by verify_lean.yml"]
    fn generated_chunks_are_checked_by_lean() {
        let dir = std::env::temp_dir().join(format!(
            "babylon-example-lean-{}-{}",
            std::process::id(),
            rand::random::<u64>()
        ));
        std::fs::create_dir(&dir).unwrap();
        struct TestDir(std::path::PathBuf);
        impl Drop for TestDir {
            fn drop(&mut self) {
                let _ = std::fs::remove_dir_all(&self.0);
            }
        }
        let dir = TestDir(dir);
        let path = dir.0.join("chunk.lean");
        let check = |source: &str| {
            std::fs::write(&path, source).unwrap();
            Command::new("elan")
                .args([
                    "run",
                    include_str!("../proof/lean/lean-toolchain").trim(),
                    "lean",
                ])
                .arg(&path)
                .output()
                .expect("pinned Lean must be installed")
        };
        for offset in [0, 5000, 10000] {
            let source = Lean4Emitter::render_lean_chunk(CHUNK_SIZE, offset).unwrap();
            let out = check(&source);
            assert!(
                out.status.success(),
                "{}",
                String::from_utf8_lossy(&out.stdout)
            );
        }
        let valid = Lean4Emitter::render_lean_chunk(2, 0).unwrap();
        for corrupted in [
            valid.replace(
                "seq := 1, action := Action.WriteBegin",
                "seq := 101, action := Action.WriteBegin",
            ),
            valid.replace(
                "seq := 2, action := Action.WriteEnd",
                "seq := 0, action := Action.WriteEnd",
            ),
            valid.replace(
                "thread := 1, seq := 2, action := Action.WriteEnd",
                "thread := 2, seq := 2, action := Action.WriteEnd",
            ),
            valid.replace(
                ",\n  { thread := 1, seq := 2, action := Action.WriteEnd }",
                "",
            ),
        ] {
            assert!(
                !check(&corrupted).status.success(),
                "Lean accepted a corrupt generated trace"
            );
        }
    }
}
