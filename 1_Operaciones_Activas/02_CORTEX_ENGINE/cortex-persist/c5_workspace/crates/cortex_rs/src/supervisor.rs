use crate::babylon_kernel::{AgentClient, CorrectionProposal, DiagnosticTicket};
use cortex_ledger::memory_store::EpistemicFailure;
use dialoguer::{theme::ColorfulTheme, Input, Select};

/// Proxy estructural que fuerza la validación humana (HITL) antes de la mutación POSIX.
pub struct HumanSupervisorProxy<A: AgentClient> {
    inner_agent: A,
}

impl<A: AgentClient> HumanSupervisorProxy<A> {
    pub fn new(inner_agent: A) -> Self {
        Self { inner_agent }
    }
}

impl<A: AgentClient> AgentClient for HumanSupervisorProxy<A> {
    fn request_correction(
        &self,
        ticket: &DiagnosticTicket,
        history: &[EpistemicFailure],
    ) -> Result<CorrectionProposal, String> {
        // 1. Inferencia Autónoma (Delegar al LLM o mock interno)
        println!(
            "\n[SUPERVISOR] Delegando inferencia al Kernel Autónomo para {}...",
            ticket.ticket_id
        );
        let proposal = self.inner_agent.request_correction(ticket, history)?;

        // 2. TUI Diff Validation (Estrangulamiento termodinámico)
        println!("\n==================================================");
        println!(
            "[{}] {}: {}",
            ticket.ticket_id, ticket.error_code, ticket.message
        );
        println!("Ruta: {}", ticket.file_path.display());
        println!("--- ORIGINAL ---");
        println!("{}", proposal.original_content_snippet);
        println!("+++ REEMPLAZO PROPUESTO +++");
        println!("{}", proposal.replacement_content);
        println!("==================================================\n");

        let selections = &[
            "[A]probar Mutación Atómica",
            "[R]echazar (Inyectar Restricción Negativa al RAG)",
            "[A]bortar Kernel (Kill)",
        ];

        let selection = Select::with_theme(&ColorfulTheme::default())
            .with_prompt("Evaluación Termodinámica (HITL)")
            .default(0)
            .items(&selections[..])
            .interact()
            .map_err(|e| format!("Fallo en UI interactiva: {}", e))?;

        match selection {
            0 => {
                println!("[SUPERVISOR] Mutación Aprobada. Liberando hacia el Applier...");
                Ok(proposal)
            }
            1 => {
                let reason: String = Input::with_theme(&ColorfulTheme::default())
                    .with_prompt("Motivo del rechazo (se inyectará en MemoryStore)")
                    .interact_text()
                    .map_err(|e| format!("Fallo en entrada de texto: {}", e))?;

                println!("[SUPERVISOR] Rechazo inyectado. Abortando ciclo actual para forzar recálculo.");
                Err(reason) // Este error será capturado por el Orchestrator y logueado en MemoryStore
            }
            _ => {
                println!("[SUPERVISOR] Abortando núcleo termodinámico.");
                std::process::exit(1);
            }
        }
    }
}
