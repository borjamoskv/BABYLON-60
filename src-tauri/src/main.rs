#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

pub mod void;
pub mod ear;
pub mod silence;

use std::sync::Arc;

pub struct Apex {
    pub void_state: Arc<void::CortexLedger>,
    pub ear_state: Arc<ear::EarListener>,
    pub silence_state: Arc<silence::SilenceController>,
}

impl Apex {
    pub fn init() -> Self {
        let db = void::CortexLedger::init().expect("Error al inicializar la base de datos.");
        Self {
            void_state: Arc::new(db),
            ear_state: Arc::new(ear::EarListener::new()),
            silence_state: Arc::new(silence::SilenceController::new()),
        }
    }
}

// Execution: Initialization of the Trinity
#[tokio::main]
async fn main() {
    let state = Apex::init(); // Memory + Audio + Swarm
    
    // Antigravity execution
    tauri::Builder::default()
        .manage(state)
        .run(tauri::generate_context!())
        .expect("FATAL: System desync");
}
