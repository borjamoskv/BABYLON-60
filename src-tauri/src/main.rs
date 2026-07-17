#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod ledger;
use std::sync::Mutex;

struct AppState {
    db: Mutex<ledger::CortexLedger>,
}

fn main() {
    let db = ledger::CortexLedger::init().unwrap();

    tauri::Builder::default()
        .manage(AppState { db: Mutex::new(db) })
        .run(tauri::generate_context!())
        .expect("FATAL: Tauri colapsó");
}
