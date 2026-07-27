use cortex_ledger::memory_store::{EpistemicFailure, MemoryStore};
use std::path::PathBuf;
use fs2::FileExt;
use tempfile::NamedTempFile;
use std::fs::File;
use std::io::{Read, Write};
use std::collections::HashMap;

#[derive(Eq, PartialEq, Hash, Clone, Debug, serde::Serialize, serde::Deserialize)]
pub enum Phase {
    Compile,
    Filter,
    AgentCall,
    Apply,
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct AuditEntry {
    pub ticket_id: String,
    pub total_ms: u128,
    pub phase_timings: HashMap<Phase, u128>,
    pub status: String,
}

/// Representa un ticket de error del compilador (LSP), acotando la visión del agente.
#[derive(serde::Serialize, serde::Deserialize, Debug)]
pub struct DiagnosticTicket {
    pub ticket_id: String,
    pub error_code: String,
    pub file_path: PathBuf,
    pub target_span_start: usize,
    pub target_span_end: usize,
    pub message: String,
}

/// La propuesta atómica devuelta por el LLM.
#[derive(serde::Serialize, serde::Deserialize, Debug)]
pub struct CorrectionProposal {
    pub ticket_id: String,
    pub file_path: PathBuf,
    pub original_content_snippet: String,
    pub replacement_content: String,
}

/// Cliente genérico para aislar al LLM (FABLE, Claude, etc).
pub trait AgentClient {
    fn request_correction(
        &self,
        ticket: &DiagnosticTicket,
        history: &[EpistemicFailure],
    ) -> Result<CorrectionProposal, String>;
}

/// El Ledger inmutable (Auditor).
pub trait AuditLogger {
    fn log_cycle(&self, entry: AuditEntry);
}

/// El Applier atómico (reemplazo de AST).
pub struct SourceApplier;

impl SourceApplier {
    pub fn apply(proposal: &CorrectionProposal) -> Result<(), String> {
        let file_path = &proposal.file_path;

        if proposal.original_content_snippet.is_empty() {
            return Err("Fidelidad de contexto fallida: El código original no coincide.".to_string());
        }

        // 1. Adquirir Bloqueo Exclusivo (OS-Level Lock)
        let mut target_file = File::options()
            .read(true)
            .write(true)
            .open(file_path)
            .map_err(|e| format!("Error abriendo archivo destino: {}", e))?;

        // Fail-fast termodinámico (Regla K1)
        target_file.try_lock_exclusive().map_err(|e| {
            format!("Data Race prevenido: El archivo está bloqueado por otro proceso. {}", e)
        })?;

        // 2. Verificar Topología Actual
        let mut current_content = String::new();
        target_file.read_to_string(&mut current_content)
            .map_err(|e| format!("Error leyendo archivo destino: {}", e))?;

        if !current_content.contains(&proposal.original_content_snippet) {
            return Err("Fidelidad de contexto fallida: El archivo ha mutado fuera del control del agente.".to_string());
        }

        let new_content = current_content.replace(
            &proposal.original_content_snippet,
            &proposal.replacement_content
        );

        // 3. Mutación Atómica con NamedTempFile
        let dir = file_path.parent().unwrap_or(std::path::Path::new(""));
        let mut temp_file = NamedTempFile::new_in(dir)
            .map_err(|e| format!("Error creando archivo temporal: {}", e))?;

        temp_file.write_all(new_content.as_bytes())
            .map_err(|e| format!("Error escribiendo en archivo temporal: {}", e))?;

        // 4. Renombrado atómico POSIX
        temp_file.persist(file_path)
            .map_err(|e| format!("Error ejecutando persistencia atómica POSIX: {}", e))?;

        // El bloqueo de fs2 se libera automáticamente al caer el File Handle (target_file drop).
        Ok(())
    }
}

/// El orquestador que cierra el bucle empírico.
pub struct RefactorOrchestrator;

impl RefactorOrchestrator {
    pub fn run_cycle<A: AgentClient, L: AuditLogger>(
        agent: &A,
        logger: &L,
        memory: &MemoryStore,
        ticket: DiagnosticTicket,
    ) -> Result<(), String> {
        let cycle_start = std::time::Instant::now();

        // 1. Recuperar contexto histórico (RAG determinista O(1))
        let history = memory
            .retrieve_failures(&ticket.error_code, &ticket.file_path, "ast_scope_mock", 2)
            .unwrap_or_default();

        // 2. Pedir mutación al agente acotada por memoria epistémica
        let proposal = agent.request_correction(&ticket, &history)?;

        // 3. Aplicar mutación (Pre-flight content match + Atomic write)
        match SourceApplier::apply(&proposal) {
            Ok(_) => {
                let elapsed_ms = cycle_start.elapsed().as_millis();
                let mut phase_timings = HashMap::new();
                phase_timings.insert(Phase::Apply, elapsed_ms);
                logger.log_cycle(AuditEntry {
                    ticket_id: ticket.ticket_id.clone(),
                    total_ms: elapsed_ms,
                    phase_timings,
                    status: "Success".to_string(),
                });
                Ok(())
            }
            Err(e) => {
                let elapsed_ms = cycle_start.elapsed().as_millis();
                let mut phase_timings = HashMap::new();
                phase_timings.insert(Phase::Apply, elapsed_ms);
                logger.log_cycle(AuditEntry {
                    ticket_id: ticket.ticket_id.clone(),
                    total_ms: elapsed_ms,
                    phase_timings,
                    status: format!("Failure: {}", e),
                });
                let _ = memory.log_failure(
                    &ticket.error_code,
                    &ticket.file_path,
                    "ast_scope_mock",
                    &proposal.replacement_content,
                    &e,
                );
                Err(e)
            }
        }
    }
}

/// THE ENGINE ROOM
/// Kernel de integración que instancía los módulos y ejecuta el ciclo de vida real.
pub struct BabylonKernel<A: AgentClient, L: AuditLogger> {
    pub agent: A,
    pub logger: L,
    pub memory: MemoryStore,
}

impl<A: AgentClient, L: AuditLogger> BabylonKernel<A, L> {
    pub fn new(agent: A, logger: L, memory: MemoryStore) -> Self {
        Self { agent, logger, memory }
    }

    pub fn execute_ticket(&self, ticket: DiagnosticTicket) -> Result<(), String> {
        RefactorOrchestrator::run_cycle(&self.agent, &self.logger, &self.memory, ticket)
    }
}

use reqwest::blocking::Client;
use serde_json::json;
use std::time::Duration;

pub struct FableAgent {
    pub api_key: String,
    pub client: Client,
}

impl FableAgent {
    pub fn new(api_key: String) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to build HTTP client");
        Self { api_key, client }
    }
}

impl AgentClient for FableAgent {
    fn request_correction(
        &self,
        ticket: &DiagnosticTicket,
        _history: &[EpistemicFailure],
    ) -> Result<CorrectionProposal, String> {
        let response = self.client.post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&json!({
                "model": "claude-3-5-sonnet-20240620",
                "system": "Eres un ejecutor de parches AST. Retorna ÚNICAMENTE JSON válido bajo el esquema CorrectionProposal. Sin explicaciones.",
                "messages": [{"role": "user", "content": format!("Corregir error {}: {:?}", ticket.error_code, ticket)}],
                "max_tokens": 1024
            }))
            .send()
            .map_err(|e| format!("HTTP Request failed: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("API Error: {}", response.status()));
        }

        let body: serde_json::Value = response.json().map_err(|e| e.to_string())?;
        let raw_content = body["content"][0]["text"].as_str().ok_or("No content in response")?;
        
        let clean_json = raw_content
            .replace("```json", "")
            .replace("```", "")
            .trim()
            .to_string();

        serde_json::from_str::<CorrectionProposal>(&clean_json)
            .map_err(|e| format!("Parsing Failure: {}. Buffer: {}", e, clean_json))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use std::fs;
    use std::thread;
    use std::sync::{Arc, atomic::{AtomicUsize, Ordering}};
    use std::time::Duration;

    #[test]
    fn test_source_applier_concurrency() {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("target.rs");
        let original_content = "fn main() { println!(\"Hello\"); }";
        fs::write(&file_path, original_content).unwrap();

        let thread_count = 10;
        let success_count = Arc::new(AtomicUsize::new(0));
        let error_count = Arc::new(AtomicUsize::new(0));
        let mut handles = vec![];

        for i in 0..thread_count {
            let path_clone = file_path.clone();
            let success_clone = Arc::clone(&success_count);
            let error_clone = Arc::clone(&error_count);
            
            handles.push(thread::spawn(move || {
                let proposal = CorrectionProposal {
                    ticket_id: format!("TICKET-{}", i),
                    file_path: path_clone,
                    original_content_snippet: "fn main() { println!(\"Hello\"); }".to_string(),
                    replacement_content: format!("fn main() {{ println!(\"Thread {}\"); }}", i),
                };
                
                match SourceApplier::apply(&proposal) {
                    Ok(_) => { success_clone.fetch_add(1, Ordering::SeqCst); },
                    Err(e) => { 
                        if e.contains("bloqueado por otro proceso") || e.contains("mutado fuera del control") {
                            error_clone.fetch_add(1, Ordering::SeqCst);
                        } else {
                            panic!("Error inesperado: {}", e);
                        }
                    }
                }
            }));
        }

        for h in handles {
            let _ = h.join();
        }

        let final_success = success_count.load(Ordering::SeqCst);
        let final_errors = error_count.load(Ordering::SeqCst);
        
        // El fail-fast debería garantizar que las carreras de datos se resuelvan con error
        // para los hilos que colisionan, permitiendo que 1 o más logren escribir.
        assert!(final_success > 0, "Al menos una mutación debe triunfar");
        assert!(final_success + final_errors == thread_count, "Todos los hilos deben resolverse atómicamente");
    }
}
