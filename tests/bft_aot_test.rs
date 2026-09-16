use std::fs;
use babylon60::larsa_bft::{LarsaTriadConsensus, LarsaVertex, VertexState};
use babylon60::manifest::{POISONED, RUNNING};

fn pack_event(thread_id: u32, seq: u32, action: u8) -> u64 {
    (action as u64) | ((thread_id as u64) << 8) | ((seq as u64) << 32)
}

#[test]
fn test_bft_aot_oracle_integration() {
    // 1. Instanciar la Tríada en estado perfecto (Quórum 3/3)
    let triad = LarsaTriadConsensus::new();
    assert_eq!(triad.active_count(), 3);
    assert_eq!(triad.evaluate_quorum(), RUNNING);

    // 2. Crear una traza válida (pequeña traza binaria Zero-Copy).
    let trace_path = "target/valid_trace.bin";
    let valid_events = vec![
        pack_event(1, 1, 0),
        pack_event(1, 2, 1),
        pack_event(1, 3, 0),
        pack_event(1, 4, 1),
    ];
    let valid_bytes: Vec<u8> = valid_events.iter().flat_map(|e| e.to_le_bytes()).collect();
    fs::write(trace_path, valid_bytes).unwrap();

    // 3. Evaluar traza válida en el Lóbulo Inhibidor
    let status = triad.evaluate_trace(trace_path);
    assert_eq!(status, RUNNING);
    assert_eq!(triad.get_state(LarsaVertex::Beta), VertexState::Active);

    // 4. Crear una traza PARADÓJICA de Estado (doble WriteBegin). 
    // Z3 la dejará pasar (seq es monótono), pero Lean 4 la aniquilará.
    let bad_state_trace_path = "target/corrupt_state.bin";
    let bad_state_events = vec![
        pack_event(1, 1, 0),
        pack_event(1, 2, 0), // Paradoja de estado
    ];
    let bad_state_bytes: Vec<u8> = bad_state_events.iter().flat_map(|e| e.to_le_bytes()).collect();
    fs::write(bad_state_trace_path, bad_state_bytes).unwrap();

    // 5. Evaluar traza. El Oráculo (Lean 4) debe colapsar el Vértice Beta.
    let status = triad.evaluate_trace(bad_state_trace_path);
    assert_eq!(triad.get_state(LarsaVertex::Beta), VertexState::Fallen);
    assert_eq!(triad.get_state(LarsaVertex::Gamma), VertexState::Active);
    assert_eq!(triad.active_count(), 2);
    assert_eq!(status, RUNNING);
    triad.restore_vertex(LarsaVertex::Beta);

    // 6. Crear una traza PARADÓJICA Temporal (Inversión Lamport).
    // MUSHUSHU-0 (Z3) debe aniquilarla al instante.
    let bad_time_trace_path = "target/corrupt_time.bin";
    let bad_time_events = vec![
        pack_event(1, 5, 0),
        pack_event(1, 2, 1), // Paradoja temporal (5 > 2)
    ];
    let bad_time_bytes: Vec<u8> = bad_time_events.iter().flat_map(|e| e.to_le_bytes()).collect();
    fs::write(bad_time_trace_path, bad_time_bytes).unwrap();

    // 7. Evaluar traza. Z3 colapsa Gamma y aborta el pipe (Lean 4 ni se entera).
    let status = triad.evaluate_trace(bad_time_trace_path);
    assert_eq!(triad.get_state(LarsaVertex::Gamma), VertexState::Fallen);
    assert_eq!(triad.active_count(), 2);
    assert_eq!(status, RUNNING);

    // 8. Falla un segundo nodo (Alpha). Apoptosis total.
    triad.report_failure(LarsaVertex::Alpha);
    assert_eq!(triad.evaluate_quorum(), POISONED);
}
