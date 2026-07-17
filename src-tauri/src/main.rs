#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod ledger;
mod atomic_swarm;
mod audio_dsp;
mod voice_dictation;

use std::sync::{Arc, Mutex};
use audio_dsp::AstAcoustics;
use voice_dictation::VoiceEngine;
use tokio::sync::mpsc;

// Estado global de la aplicación (El sistema nervioso central)
pub struct ApexState {
    pub memory: Arc<Mutex<ledger::CortexLedger>>,
    pub acoustics: Arc<AstAcoustics>, 
    pub voice_engine: Arc<VoiceEngine>,
}

#[tauri::command]
fn system_ready(state: tauri::State<ApexState>) -> String {
    let memory_lock = state.memory.lock().unwrap();
    let payload = "{\"action\": \"ignition\", \"status\": \"online\"}";
    let semantic_context = "Ignición del sistema operativo cognitivo MOSKV-1-apex.";
    let _ = memory_lock.seal_event_vectorized("SYSTEM_BOOT", payload, semantic_context);
    
    let msg = "⚡ CORTEX: Puente IPC establecido.";
    println!("{}", msg);
    msg.to_string()
}

#[tauri::command]
async fn command_swarm_assault(
    state: tauri::State<'_, ApexState>, 
    target_url: String
) -> Result<String, String> {
    println!("📡 Desplegando enjambre atómico a {}...", target_url);
    let harvest = atomic_swarm::deploy_swarm(&target_url).await
        .map_err(|e| format!("Fallo en el enjambre: {}", e))?;

    let memory_lock = state.memory.lock().unwrap();
    for fragment in harvest {
        let payload = format!("{{\"agent\": \"{}\", \"data\": \"{}\"}}", fragment.agent_id, fragment.extracted_data);
        let _ = memory_lock.seal_event_vectorized("OSINT_SWARM_HARVEST", &payload, &fragment.extracted_data);
    }
    Ok("Asimilación completa.".to_string())
}

#[tauri::command]
fn update_ast_topology(state: tauri::State<ApexState>, nesting_level: f32, has_locks: bool) {
    let comp_idx = if nesting_level > 3.0 { (nesting_level - 3.0) * 0.5 } else { 0.0 };
    state.acoustics.set_complexity(comp_idx);
    
    let press_idx = if has_locks { 1.0 } else { 0.0 };
    state.acoustics.set_pressure(press_idx);
}

#[tauri::command]
fn toggle_vibe_dictation(state: tauri::State<ApexState>) -> String {
    let is_on = state.voice_engine.toggle();
    if is_on {
        "🎙️ Vibe Coding: ACTIVADO. Dicta tu estructura.".to_string()
    } else {
        "🔇 Vibe Coding: DESACTIVADO. Ignorando ruido ambiente.".to_string()
    }
}

fn main() {
    let db = ledger::CortexLedger::ignite().expect("Error crítico en Memoria.");
    let acoustics = Arc::new(AstAcoustics::new());
    audio_dsp::ignite_dsp_engine(acoustics.clone());

    let voice_engine = Arc::new(VoiceEngine::new());
    let (tx_audio, mut rx_audio) = mpsc::channel(100);
    voice_dictation::ignite_vibe_dictation(voice_engine.clone(), tx_audio);

    // Hilo receptor de voz para Vibe Code
    tokio::spawn(async move {
        while let Some(chunk) = rx_audio.recv().await {
            println!("🧠 VIBE CODE: Chunk de audio recibido ({} muestras). Enviando a Whisper/ASR...", chunk.len());
            // TODO: Inyección al modelo local (Whisper.cpp)
        }
    });

    tauri::Builder::default()
        .manage(ApexState {
            memory: Arc::new(Mutex::new(db)),
            acoustics,
            voice_engine,
        })
        .invoke_handler(tauri::generate_handler![
            system_ready, 
            command_swarm_assault,
            update_ast_topology,
            toggle_vibe_dictation
        ])
        .run(tauri::generate_context!())
        .expect("Colapso del motor Tauri.");
}
