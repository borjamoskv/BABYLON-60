use std::process::Command;
use std::fs;
use std::time::Instant;

/// PoC: AOT Emitter y Orquestación Hacia Silicio O(1)
/// Generación de un millón de eventos y evaluación O(1) nativa en C (Lean).
const TRACE_FILE: &str = "scripts/c5_demos/trace_1M.bin";
const TOTAL_EVENTS: usize = 1_000_000; // Un millón de transacciones

pub struct Lean4AOTEmitter;

impl Lean4AOTEmitter {
    pub fn prove_end_to_end() -> Result<(), String> {
        println!("🚀 [RUST] Iniciando Emisión Masiva para Oráculo AOT (N={}) [ZERO-COPY BINARY]", TOTAL_EVENTS);
        
        fs::create_dir_all("scripts/c5_demos").map_err(|e| e.to_string())?;

        let t0 = Instant::now();
        Self::emit_binary_trace(TRACE_FILE, TOTAL_EVENTS)?;
        let elapsed_emit = t0.elapsed();
        println!("✅ [RUST] Volcado binario completado en {:.2?}.", elapsed_emit);

        println!("⚖️  [RUST] Invocando Oráculo AOT (Lean 4 Nativo) en segundo plano...");
        let t1 = Instant::now();
        
        // Invocar el binario nativo de Lean 4
        let status = Command::new("proof/lean/.lake/build/bin/babylon_aot_oracle")
            .arg(TRACE_FILE)
            .status()
            .map_err(|e| format!("Fallo al invocar Oráculo AOT: {}", e))?;
            
        let elapsed_oracle = t1.elapsed();
        
        if status.success() {
            println!("🏆 [RUST] EXIT 0: Traza validada a velocidad O(1) Zero-Copy en {:.2?}.", elapsed_oracle);
        } else {
            println!("❌ [RUST] EXIT != 0: El Oráculo detectó una paradoja. Traza corrupta.");
            return Err("Colapso termodinámico. Leyes violadas.".into());
        }
        
        Ok(())
    }
    
    fn emit_binary_trace(path: &str, size: usize) -> Result<(), String> {
        use std::io::{BufWriter, Write};
        let file = fs::File::create(path).map_err(|e| e.to_string())?;
        let mut writer = BufWriter::new(file);
        
        let mut seq: u32 = 1;
        let thread_id: u32 = 1;
        
        for i in 0..size {
            let action: u8 = if i % 2 == 0 { 0 } else { 1 };
            let current_seq = if action == 0 { seq } else { seq + 1 };
            
            // Empaquetado: [ seq (32) | thread_id (24) | action (8) ]
            let packed: u64 = (action as u64) | ((thread_id as u64) << 8) | ((current_seq as u64) << 32);
            
            writer.write_all(&packed.to_le_bytes()).map_err(|e| e.to_string())?;
            
            if action == 1 {
                seq += 2;
            }
        }
        
        Ok(())
    }
}

fn main() {
    match Lean4AOTEmitter::prove_end_to_end() {
        Ok(_) => std::process::exit(0),
        Err(e) => {
            eprintln!("Fallo Crítico: {}", e);
            std::process::exit(1);
        }
    }
}
