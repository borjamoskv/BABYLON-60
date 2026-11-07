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

/// Registro de traza de `CompositeSafetyGate` (`FL-018` / `FL-026`) proyectado sobre `BitVec 64` en Lean 4.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CompositeTraceRecord {
    /// Identificador único de paso de traza.
    pub step_id: u64,
    /// Máscara de controles críticos requeridos (`BitVec 64`).
    pub required_critical_mask: u64,
    /// Máscara de controles críticos verificados (`BitVec 64`).
    pub verified_critical_mask: u64,
    /// Prefijo de 64 bits del hash del artefacto aceptado (`Hash(a_accepted)`).
    pub accepted_artifact_hash_u64: u64,
    /// Prefijo de 64 bits del hash del artefacto verificado (`Hash(a_verified)`).
    pub verified_artifact_hash_u64: u64,
    /// Época mínima de política activa.
    pub min_policy_epoch: u64,
    /// Época registrada en la evidencia.
    pub evidence_epoch: u64,
    /// Peso heurístico comprometido.
    pub heuristic_weight: u32,
    /// Umbral del quórum heurístico.
    pub quorum_threshold: u32,
}

impl CompositeTraceRecord {
    /// Emite una definición `CompositeGateState` sobre `BitVec 64` y su teorema `ValidCompositeAcceptance` en Lean 4.
    #[must_use]
    pub fn emit_lean4_composite_def(&self) -> String {
        format!(
            "set_option warningAsError true\n\ndef composite_step_{id} : B60.Ledger.CompositeGateState := {{\n  \
             requiredCriticalMask := {rcm}#64,\n  \
             verifiedCriticalMask := {vcm}#64,\n  \
             acceptedArtifactHash := {aah}#64,\n  \
             verifiedArtifactHash := {vah}#64,\n  \
             minPolicyEpoch := {mpe}#64,\n  \
             evidenceEpoch := {ee}#64,\n  \
             heuristicWeight := {hw}#64,\n  \
             quorumThreshold := {qt}#64\n\
             }}\n\
             theorem composite_step_{id}_valid : B60.Ledger.ValidCompositeAcceptance composite_step_{id} := by decide\n\
             /-- info: 'composite_step_{id}_valid' depends on axioms: [propext, Quot.sound] -/\n\
             #guard_msgs in\n#print axioms composite_step_{id}_valid\n",
            id = self.step_id,
            rcm = self.required_critical_mask,
            vcm = self.verified_critical_mask,
            aah = self.accepted_artifact_hash_u64,
            vah = self.verified_artifact_hash_u64,
            mpe = self.min_policy_epoch,
            ee = self.evidence_epoch,
            hw = self.heuristic_weight,
            qt = self.quorum_threshold,
        )
    }
}
