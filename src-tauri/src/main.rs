#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

pub mod void;
pub mod ear;
pub mod silence;
pub mod llm_bridge;
pub mod antigravity;
pub mod dsp_clock;
pub mod precognition;
pub mod inference;

use std::sync::Arc;

pub struct Apex {
    pub void_state: Arc<void::VoidLedger>,
    pub ear_state: Arc<ear::EarListener>,
    pub silence_state: Arc<silence::SilenceController>,
}

impl Apex {
    pub fn init() -> Self {
        let db = void::VoidLedger::init().expect("Error al inicializar la base de datos.");
        Self {
            void_state: Arc::new(db),
            ear_state: Arc::new(ear::EarListener::new()),
            silence_state: Arc::new(silence::SilenceController::new()),
        }
    }
}

async fn main() {
    let state = Apex::init(); // Memory + Audio + Swarm + Antigravity
    
    let bridge_state = state.void_state.clone();
    tokio::spawn(async move {
        llm_bridge::ignite_cortex_bridge(bridge_state).await;
    });

    let precog_state = state.void_state.clone();
    tokio::spawn(async move {
        precognition::ignite_precognition_daemon(precog_state).await;
    });

    tauri::Builder::default()
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            inference::infer_local_command,
            inference::check_inference_health_command
        ])
        .run(tauri::generate_context!())
        .expect("FATAL: System desync");
}
