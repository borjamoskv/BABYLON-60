pub mod lexicon;
pub mod kernel;
pub mod ledger;

use std::sync::Mutex;
use tauri::State;
use serde_json::Value;
use ledger::{CortexLedger, CortexEvent};

struct AppState {
    ledger: Mutex<CortexLedger>,
}

#[tauri::command]
fn get_ledger_events(state: State<AppState>, limit: u32) -> Result<Vec<CortexEvent>, String> {
    let ledger = state.ledger.lock().unwrap();
    ledger.get_events(limit).map_err(|e| e.to_string())
}

#[tauri::command]
fn append_ledger_event(state: State<AppState>, event_type: String, payload: Value) -> Result<CortexEvent, String> {
    let ledger = state.ledger.lock().unwrap();
    ledger.append_event(&event_type, &payload).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let db_path = "cortex.db"; // Will be created in current directory
    let ledger_instance = CortexLedger::new(db_path).expect("Failed to initialize CortexLedger");

    // [ AXIOMA: NOMENCLATURE_IS_STRUCTURE ]
    kernel::build_ontology();

    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().build())
        .manage(AppState {
            ledger: Mutex::new(ledger_instance),
        })
        .invoke_handler(tauri::generate_handler![get_ledger_events, append_ledger_event])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
