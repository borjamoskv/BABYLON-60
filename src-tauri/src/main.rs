#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod ledger;
mod antigravity;
mod dsp_clock;
mod precognition;
mod llm_bridge;

use std::sync::Arc;
use tokio::sync::Mutex; // Usar Mutex asíncrono para prevenir bloqueos del hilo de render

struct AppState {
    db: Arc<Mutex<ledger::CortexLedger>>,
    antigravity: Arc<antigravity::AntigravityEngine>,
}

#[tokio::main]
async fn main() {
    let db = ledger::CortexLedger::init().expect("Error al inicializar la base de datos.");
    let db_arc = Arc::new(Mutex::new(db));
    let antigravity_engine = Arc::new(antigravity::AntigravityEngine::new());

    // Iniciar el Demonio de Precognición
    let db_for_precognition = db_arc.clone();
    tokio::spawn(async move {
        precognition::ignite_precognition_daemon(db_for_precognition).await;
    });
    // Iniciar el Puente LLM (CORTEX Bridge)
    let db_for_bridge = db_arc.clone();
    tokio::spawn(async move {
        llm_bridge::ignite_cortex_bridge(db_for_bridge).await;
    });

    tauri::Builder::default()
        .manage(AppState { 
            db: db_arc, 
            antigravity: antigravity_engine,
        })
        .run(tauri::generate_context!())
        .expect("FATAL: Tauri colapsó");
}
