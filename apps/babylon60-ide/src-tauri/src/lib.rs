// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
pub mod lexicon;
pub mod kernel;
pub mod ledger;
pub mod context;
pub mod inference;
pub mod ws_server;


use std::sync::{Arc, Mutex};
use tauri::State;
use serde_json::Value;
use ledger::{CortexLedger, CortexEvent};
use kernel::{VectorEntry, DispatchResult};
use lexicon::{Domain, Primitive, Modifier};
use inference::{InferenceResult, run_local_inference, check_local_status, run_openrouter_inference, check_openrouter_status};
use iceoryx2::prelude::*;
use iceoryx2::service::zero_copy::Service;
use iceoryx2::service::Service as ServiceTrait;
use once_cell::sync::OnceCell;

use iceoryx2::service::port_factory::publish_subscribe::PortFactory;

#[derive(Clone)]
pub struct IpcHandle(pub Arc<PortFactory<Service, Vec<u8>>>);

unsafe impl Send for IpcHandle {}
unsafe impl Sync for IpcHandle {}

struct AppState {
    ledger: Mutex<CortexLedger>,
    #[allow(dead_code)]
    ipc: IpcHandle,
}

static IPC_SERVICE: OnceCell<IpcHandle> = OnceCell::new();

fn init_ipc() -> IpcHandle {
    let service_name = ServiceName::new("babylon60_ipc").unwrap();
    let service_factory = Service::new(&service_name)
        .publish_subscribe()
        .open_or_create::<Vec<u8>>()
        .expect("Failed to create iceoryx2 IPC service");
    let handle = IpcHandle(Arc::new(service_factory));
    IPC_SERVICE.set(handle.clone()).ok();
    handle
}

// ═══════════════════════════════════════════════════════
//  LEDGER IPC
// ═══════════════════════════════════════════════════════

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

// ═══════════════════════════════════════════════════════
//  INFERENCE IPC (LOCAL SILICON / MLX / OLLAMA)
// ═══════════════════════════════════════════════════════

#[tauri::command]
fn local_infer_sync(prompt: String, model: Option<String>, base_url: Option<String>, temperature: Option<f32>) -> Result<InferenceResult, String> {
    run_local_inference(&prompt, model, base_url, temperature)
}

#[tauri::command]
fn get_local_inference_status() -> Result<Value, String> {
    check_local_status()
}

#[tauri::command]
fn openrouter_infer_sync(prompt: String, model: Option<String>, api_key: Option<String>, temperature: Option<f32>) -> Result<InferenceResult, String> {
    run_openrouter_inference(&prompt, model, api_key, temperature)
}

#[tauri::command]
fn get_openrouter_inference_status(api_key: Option<String>) -> Result<Value, String> {
    check_openrouter_status(api_key)
}


// ═══════════════════════════════════════════════════════
//  KINETIC BIND RAW — Ontology IPC Bridge
// ═══════════════════════════════════════════════════════


#[tauri::command]
fn list_ontology_vectors() -> Vec<VectorEntry> {
    kernel::list_vectors()
}

#[tauri::command]
fn dispatch_vector(domain: Domain, primitive: Primitive, modifier: Modifier) -> Result<DispatchResult, String> {
    kernel::dispatch_3d(domain, primitive, modifier)
}

// ═══════════════════════════════════════════════════════
//  BOOT SEQUENCE
// ═══════════════════════════════════════════════════════

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let db_path = "cortex.db";
    let ledger_instance = CortexLedger::new(db_path).expect("Failed to initialize CortexLedger");
    let ipc_handle = init_ipc();

    // kernel initialization moved to setup hook

    std::thread::spawn(|| {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            ws_server::start_server().await;
        });
    });

    let ctx_db = context::init_db().expect("Failed to initialize cognitive state db");
    let ctx_state = context::ContextState(std::sync::Mutex::new(context::ContextStateInner {
        current_state: context::CognitiveState::new(),
        db: ctx_db,
    }));

    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().build())
        .setup(|app| {
            let app_handle = app.handle().clone();
            kernel::init_kernel(app_handle);
            Ok(())
        })
        .manage(AppState {
            ledger: Mutex::new(ledger_instance),
            ipc: ipc_handle,
        })
        .manage(ctx_state)
        .invoke_handler(tauri::generate_handler![
            get_ledger_events,
            append_ledger_event,
            local_infer_sync,
            get_local_inference_status,
            openrouter_infer_sync,
            get_openrouter_inference_status,
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
