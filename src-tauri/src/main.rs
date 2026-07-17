#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod ledger;
mod atomic_swarm;
mod audio_dsp; // Importamos el sintetizador

use std::sync::{Arc, Mutex};
use audio_dsp::AstAcoustics;

// Estado global de la aplicación (El sistema nervioso central)
pub struct ApexState {
    pub memory: Arc<Mutex<ledger::CortexLedger>>,
    pub acoustics: Arc<AstAcoustics>, // El puente hacia el audio (Lock-free Atomic)
}

#[tauri::command]
fn system_ready(state: tauri::State<ApexState>) -> String {
    let memory_lock = state.memory.lock().unwrap();
    
    let payload = "{\"action\": \"ignition\", \"status\": \"online\"}";
    let semantic_context = "Ignición del sistema operativo cognitivo MOSKV-1-apex. Inicialización del canvas WebGPU y el bus latente de memoria CORTEX.";

    // Sello con indexación vectorial instantánea
    match memory_lock.seal_event_vectorized("SYSTEM_BOOT", payload, semantic_context) {
        Ok(_) => println!("📊 Hipocampo: Nodo de arranque indexado semánticamente."),
        Err(e) => eprintln!("❌ Fallo al inyectar vector: {:?}", e),
    }
    
    let msg = "⚡ CORTEX: Puente IPC establecido. Memoria inmutable montada.";
    println!("{}", msg);
    msg.to_string()
}

#[tauri::command]
async fn command_swarm_assault(
    state: tauri::State<'_, ApexState>, 
    target_url: String
) -> Result<String, String> {
    
    // 1. El Alcove (Notch) empieza a parpadear en azul cobalto (Modo Sonar)
    println!("📡 Desplegando enjambre atómico a {}...", target_url);

    // 2. Ejecutar asalto asíncrono
    let harvest = atomic_swarm::deploy_swarm(&target_url).await
        .map_err(|e| format!("Fallo en el enjambre: {}", e))?;

    let memory_lock = state.memory.lock().unwrap();

    // 3. Digerir e indexar vectorialmente cada fragmento cosechado
    for fragment in harvest {
        let payload = format!("{{\"agent\": \"{}\", \"data\": \"{}\"}}", fragment.agent_id, fragment.extracted_data);
        
        let _ = memory_lock.seal_event_vectorized(
            "OSINT_SWARM_HARVEST", 
            &payload, 
            &fragment.extracted_data
        ).map_err(|e| format!("Error en memoria vectorial: {:?}", e))?;
    }

    Ok("Asimilación completa. Conocimiento inyectado en CORTEX.".to_string())
}

#[tauri::command]
fn update_ast_topology(state: tauri::State<ApexState>, nesting_level: f32, has_locks: bool) {
    // Isomorfismo puro (Sin Mutex.lock(), atómico directo C5-REAL): 
    let comp_idx = if nesting_level > 3.0 { (nesting_level - 3.0) * 0.5 } else { 0.0 };
    state.acoustics.set_complexity(comp_idx);
    
    let press_idx = if has_locks { 1.0 } else { 0.0 };
    state.acoustics.set_pressure(press_idx);
}

fn main() {
    // 1. Despertar la base de datos vectorial BGE-Small
    let db = ledger::CortexLedger::ignite().expect("Error crítico: Imposible forjar la memoria.");

    // Estado inicial del código: Paz absoluta (Dron limpio, Atomics C5-REAL)
    let acoustics = Arc::new(AstAcoustics::new());

    // Iniciar el Sintetizador en paralelo
    audio_dsp::ignite_dsp_engine(acoustics.clone());

    tauri::Builder::default()
        // 2. Inyectar el Ledger y el Sintetizador en el estado de Tauri
        .manage(ApexState {
            memory: Arc::new(Mutex::new(db)),
            acoustics,
        })
        .setup(|_app| {
            println!("⬛ El Vacío ha sido instanciado.");
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            system_ready, 
            command_swarm_assault,
            update_ast_topology
        ])
        .run(tauri::generate_context!())
        .expect("Colapso del motor Tauri.");
}
