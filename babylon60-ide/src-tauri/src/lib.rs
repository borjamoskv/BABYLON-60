pub mod lexicon;
pub mod kernel;
pub mod ledger;
pub mod context;
pub mod inference;

use std::sync::Mutex;
use tauri::State;
use serde_json::Value;
use ledger::{CortexLedger, CortexEvent};
use kernel::{VectorEntry, DispatchResult};
use lexicon::{Domain, Primitive, Modifier};
use inference::{InferenceResult, run_local_inference, check_local_status};

struct AppState {
    ledger: Mutex<CortexLedger>,
}


fn get_ledger_events(state: State<AppState>, limit: u32) -> Result<Vec<CortexEvent>, String> {
    let ledger = state.ledger.lock().unwrap();
    ledger.get_events(limit).map_err(|e| e.to_string())
}

fn append_ledger_event(state: State<AppState>, event_type: String, payload: Value) -> Result<CortexEvent, String> {
    let ledger = state.ledger.lock().unwrap();
    ledger.append_event(&event_type, &payload).map_err(|e| e.to_string())
}


fn local_infer_sync(prompt: String, model: Option<String>, base_url: Option<String>, temperature: Option<f32>) -> Result<InferenceResult, String> {
    run_local_inference(&prompt, model, base_url, temperature)
}

fn get_local_inference_status() -> Result<Value, String> {
    check_local_status()
}


fn list_ontology_vectors() -> Vec<VectorEntry> {
    kernel::list_vectors()
}

fn dispatch_vector(domain: Domain, primitive: Primitive, modifier: Modifier) -> Result<DispatchResult, String> {
    kernel::dispatch_3d(domain, primitive, modifier)
}


pub fn run() {
    let db_path = "cortex.db";
    let ledger_instance = CortexLedger::new(db_path).expect("Failed to initialize CortexLedger");

    kernel::init_kernel();

    let ctx_db = context::init_db().expect("Failed to initialize cognitive state db");
    let ctx_state = context::ContextState(std::sync::Mutex::new(context::ContextStateInner {
        current_state: context::CognitiveState::new(),
        db: ctx_db,
    }));

    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().build())
        .manage(AppState {
            ledger: Mutex::new(ledger_instance),
        })
        .manage(ctx_state)
        .invoke_handler(tauri::generate_handler![
            get_ledger_events,
            append_ledger_event,
            local_infer_sync,
            get_local_inference_status,
            list_ontology_vectors,
            dispatch_vector,
            kernel::dispatch,
            kernel::list_vectors,
            context::get_cognitive_state,
            context::checkpoint,
            context::restore_checkpoint,
            context::get_continuity_metrics,
            context::get_cognitive_weather,
            context::record_context_switch,
            context::get_attention_budget
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

