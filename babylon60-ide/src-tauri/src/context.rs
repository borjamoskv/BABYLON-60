use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::{State, command};
use rusqlite::{Connection, Result as SqlResult, params};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CognitiveState {
    pub session_start: DateTime<Utc>,
    pub route_history: Vec<(String, DateTime<Utc>, u64)>,
    pub context_switches: u32,
    pub current_intent: String,
    pub open_questions: Vec<String>,
    pub discarded_options: Vec<(String, String)>,
    pub confidence: f64,
    pub cognitive_temperature: f64,

    pub i_intent: String,
    pub b_belief_state: String,
    pub g_goal_graph: String,
    pub m_memory_compression: String,
    pub e_entropy: f64,
    pub h_history_operator: String,
    pub p_prediction: String,

    pub next_optimal_transformation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CognitiveWeather {
    Clear,
    Fog,
    Storm,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContinuityMetrics {
    pub focus_pct: f64,
    pub context_pct: f64,
    pub drift_pct: f64,
    pub reentry_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AttentionBudget {
    pub total: u64,
    pub spent: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriftDetector {
    pub current_drift_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextCache {
    pub l1_15s: String,
    pub l2_10m: String,
    pub l3_weeks: String,
    pub disk: String,
}

pub struct ContextStateInner {
    pub current_state: CognitiveState,
    pub db: Connection,
}

pub struct ContextState(pub Mutex<ContextStateInner>);

impl CognitiveState {
    pub fn new() -> Self {
        Self {
            session_start: Utc::now(),
            route_history: Vec::new(),
            context_switches: 0,
            current_intent: "".to_string(),
            open_questions: Vec::new(),
            discarded_options: Vec::new(),
            confidence: 1.0,
            cognitive_temperature: 0.0,
            i_intent: "".to_string(),
            b_belief_state: "".to_string(),
            g_goal_graph: "".to_string(),
            m_memory_compression: "".to_string(),
            e_entropy: 0.0,
            h_history_operator: "".to_string(),
            p_prediction: "".to_string(),
            next_optimal_transformation: "".to_string(),
        }
    }
}

pub fn init_db() -> SqlResult<Connection> {
    let conn = Connection::open("cognitive_state.db")?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cognitive_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            state_json TEXT NOT NULL
        )",
        [],
    )?;
    Ok(conn)
}

#[command]
pub fn get_cognitive_state(state: State<'_, ContextState>) -> Result<CognitiveState, String> {
    let inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    Ok(inner.current_state.clone())
}

#[command]
pub fn checkpoint(state: State<'_, ContextState>) -> Result<(), String> {
    let inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    let state_json = serde_json::to_string(&inner.current_state).map_err(|e| e.to_string())?;
    inner.db.execute(
        "INSERT INTO cognitive_checkpoints (timestamp, state_json) VALUES (?1, ?2)",
        params![Utc::now().to_rfc3339(), state_json],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[command]
pub fn restore_checkpoint(state: State<'_, ContextState>, id: i64) -> Result<(), String> {
    let mut inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    let state_json: String = {
        let mut stmt = inner.db.prepare("SELECT state_json FROM cognitive_checkpoints WHERE id = ?1").map_err(|e| e.to_string())?;
        stmt.query_row(params![id], |row| row.get(0)).map_err(|e| e.to_string())?
    };
    
    let restored_state: CognitiveState = serde_json::from_str(&state_json).map_err(|e| e.to_string())?;
    inner.current_state = restored_state;
    Ok(())
}

#[command]
pub fn get_continuity_metrics(state: State<'_, ContextState>) -> Result<ContinuityMetrics, String> {
    let inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    let switches = inner.current_state.context_switches;
    let entropy = inner.current_state.e_entropy;
    
    Ok(ContinuityMetrics {
        focus_pct: 100.0 - (switches as f64 * 5.0).min(100.0),
        context_pct: 100.0 - (entropy * 10.0).min(100.0),
        drift_pct: (switches as f64 * 2.0).min(100.0),
        reentry_time_ms: 500,
    })
}

#[command]
pub fn get_cognitive_weather(state: State<'_, ContextState>) -> Result<CognitiveWeather, String> {
    let inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    let e = inner.current_state.e_entropy;
    let switches = inner.current_state.context_switches;
    
    if e < 2.0 && switches < 5 {
        Ok(CognitiveWeather::Clear)
    } else if e < 5.0 && switches < 10 {
        Ok(CognitiveWeather::Fog)
    } else {
        Ok(CognitiveWeather::Storm)
    }
}

#[command]
pub fn record_context_switch(state: State<'_, ContextState>, reason: String) -> Result<(), String> {
    let mut inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    inner.current_state.context_switches += 1;
    inner.current_state.h_history_operator = format!("{} -> {}", inner.current_state.h_history_operator, reason);
    Ok(())
}

#[command]
pub fn get_attention_budget(state: State<'_, ContextState>) -> Result<AttentionBudget, String> {
    let inner = state.0.lock().map_err(|_| "Failed to lock state".to_string())?;
    let spent = (inner.current_state.context_switches as u64) * 10;
    Ok(AttentionBudget {
        total: 1000,
        spent,
    })
}
