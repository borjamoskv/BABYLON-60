// Emisor Lean 4 fail-closed hacia BabylonTrace.lean (B60-05).

/// Registro de traza serializable a `BabylonEvent`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TraceRecord {
    /// Identificador de paso.
    pub step_id: u64,
    /// Agente.
    pub agent_id: u8,
    /// Secuencia FL-011 al inicio.
    pub seq_start: u64,
    /// Secuencia FL-011 al final.
    pub seq_end: u64,
    /// Época del kernel.
    pub kernel_epoch: u64,
    /// Época de expiración del lease.
    pub lease_epoch: u64,
    /// Testigo formal presente.
    pub formal_witness_ok: bool,
    /// Veto formal presente.
    pub formal_veto: bool,
    /// Peso heurístico acumulado.
    pub heuristic_weight: u32,
    /// Umbral del quórum.
    pub quorum_threshold: u32,
}

impl TraceRecord {
    /// Emite una definición computable en Lean 4 (campos exhaustivos, sin comodines).
    #[must_use]
    pub fn emit_lean4_def(&self) -> String {
        format!(
            "set_option warningAsError true\n\ndef trace_step_{id} : B60.Ledger.BabylonEvent := {{\n  \
             agentId := {agent},\n  \
             seqStart := {ss},\n  \
             seqEnd := {se},\n  \
             kernelEpoch := {ke},\n  \
             leaseEpoch := {le},\n  \
             formalWitnessOk := {fw},\n  \
             formalVeto := {fv},\n  \
             heuristicWeight := {hw},\n  \
             quorumThreshold := {qt}\n\
             }}\n\
             theorem trace_step_{id}_valid : B60.Ledger.ValidBabylonTransition trace_step_{id} := by decide\n\
             /-- info: 'trace_step_{id}_valid' does not depend on any axioms -/\n\
             #guard_msgs in\n#print axioms trace_step_{id}_valid\n",
            id = self.step_id,
            agent = self.agent_id,
            ss = self.seq_start,
            se = self.seq_end,
            ke = self.kernel_epoch,
            le = self.lease_epoch,
            fw = self.formal_witness_ok,
            fv = self.formal_veto,
            hw = self.heuristic_weight,
            qt = self.quorum_threshold,
        )
    }
}
