// ============================================================================
// B60 PLAN CONSUMER GATE — STRUCTURAL VALIDATION
// Ring-0 Sovereignty Gate | Framework: C5-REAL
//
// Invariante C5-REAL: Aforismo 5 (Lo voluntario vale menos que lo involuntario)
// Directiva AX-0: Tripartición de autoridad. Ningún componente estocástico
// puede autorizar sus propios efectos. Solo este gate consumidor en Ring-0
// valida e instancia VerifiedPlan. Sin un ejecutor confiable integrado, el
// despacho se rechaza y no emite evidencia de efectos.
// ============================================================================

use std::collections::HashSet;

#[cfg(test)]
use crate::epistemic_types::{observe, verify, Claim, Observed, Origin, Verified};
use crate::epistemic_types::{EpistemicError, LinearCap};
use crate::mmr::MmrAccumulator;
use crate::verified_plan::{PlanBuilder, PlanError, VerifiedPlan};

/// Errores de despacho y ejecución en el PlanConsumerGate.
#[derive(Debug, PartialEq, Eq)]
pub enum PlanGateError {
    /// Error de validación interna del plan (fallo de builder/try_build).
    PlanBuildError(PlanError),
    /// El presupuesto solicitado por el plan excede el límite máximo del gate.
    BudgetLimitExceeded { requested: u32, limit: u32 },
    /// El límite de bytes de salida excede el límite máximo del gate.
    OutputLimitExceeded { requested: u32, limit: u32 },
    /// Intento de reutilizar un nonce de capacidad ya consumido (anti-replay).
    CapabilityAlreadySpent { nonce_prefix: [u8; 8] },
    /// Violación en la elevación o atestación de tipos epistémicos.
    EpistemicViolation(EpistemicError),
    /// Despacho detenido por fallo de ejecución en una operación.
    DispatchHalted { op_id: String, reason: String },
}

impl std::fmt::Display for PlanGateError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::PlanBuildError(e) => write!(f, "PlanGateError::PlanBuildError({e})"),
            Self::BudgetLimitExceeded { requested, limit } => write!(
                f,
                "PlanGateError::BudgetLimitExceeded(requested={requested}, limit={limit})"
            ),
            Self::OutputLimitExceeded { requested, limit } => write!(
                f,
                "PlanGateError::OutputLimitExceeded(requested={requested}, limit={limit})"
            ),
            Self::CapabilityAlreadySpent { nonce_prefix } => write!(
                f,
                "PlanGateError::CapabilityAlreadySpent(prefix={nonce_prefix:02x?})"
            ),
            Self::EpistemicViolation(e) => write!(f, "PlanGateError::EpistemicViolation({e})"),
            Self::DispatchHalted { op_id, reason } => write!(
                f,
                "PlanGateError::DispatchHalted(op={op_id}, reason={reason})"
            ),
        }
    }
}

impl std::error::Error for PlanGateError {}

impl From<PlanError> for PlanGateError {
    fn from(e: PlanError) -> Self {
        Self::PlanBuildError(e)
    }
}

impl From<EpistemicError> for PlanGateError {
    fn from(e: EpistemicError) -> Self {
        Self::EpistemicViolation(e)
    }
}

/// Estado resultante del despacho de un plan verificado.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PlanDispatchStatus {
    Success,
    Halted { failed_op_id: String },
}

/// Formato de recibo de ejecución. El gate actual no lo emite: falta integrar
/// un ejecutor confiable que observe los efectos antes de comprometerlos.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlanExecutionReceipt {
    /// SHA-256 inmutable del plan verificado.
    pub plan_digest: [u8; 32],
    /// Cantidad de operaciones despachadas exitosamente.
    pub executed_operations: usize,
    /// Coste presupuestario total efectivamente consumido.
    pub total_cost_spent: u32,
    /// Límite de bytes de salida acordado para el plan.
    pub output_bytes_limit: u32,
    /// Raíz del acumulador Merkle Mountain Range (MMR) tras comprometer la ejecución.
    pub mmr_root: String,
    /// Tick causal en el que se selló el recibo.
    pub timestamp_tick: u64,
    /// Estado final del despacho.
    pub status: PlanDispatchStatus,
}

/// Gate para validación estructural de planes y consumo de capacidades lineales.
/// El despacho se rechaza mientras no exista un ejecutor confiable integrado.
/// Las rutas que aceptan observaciones y stdout simulados son solo fixtures internos.
/// Un consumidor externo no puede elevar sus propios datos:
///
/// ```compile_fail,E0599
/// use b60_lang::PlanConsumerGate;
/// let mut gate = PlanConsumerGate::new(100, 1024);
/// let _ = gate.observe_raw(42, "caller_supplied_sensor");
/// ```
///
/// ```compile_fail,E0599
/// use b60_lang::{Claim, PlanConsumerGate};
/// let mut gate = PlanConsumerGate::new(100, 1024);
/// let _ = gate.authorize_claim(Claim::new(42), "caller_supplied_sensor");
/// ```
///
/// ```compile_fail,E0599
/// use b60_lang::PlanConsumerGate;
/// let _ = PlanConsumerGate::verify_observation::<u32>;
/// ```
pub struct PlanConsumerGate {
    pub mmr_accumulator: MmrAccumulator,
    spent_nonces: HashSet<[u8; 32]>,
    max_budget_limit: u32,
    max_output_limit: u32,
    current_tick: u64,
}

impl PlanConsumerGate {
    /// Construye un nuevo gate consumidor con los límites de seguridad de Ring-0.
    pub fn new(max_budget_limit: u32, max_output_limit: u32) -> Self {
        Self {
            mmr_accumulator: MmrAccumulator::new(),
            spent_nonces: HashSet::new(),
            max_budget_limit,
            max_output_limit,
            current_tick: 1,
        }
    }

    /// Retorna el tick causal actual del gate.
    pub fn current_tick(&self) -> u64 {
        self.current_tick
    }

    /// Avanza el contador causal de ticks.
    pub fn advance_tick(&mut self, delta: u64) {
        self.current_tick = self.current_tick.saturating_add(delta);
    }

    /// Comprueba si un nonce de capacidad ya ha sido consumido.
    pub fn is_nonce_spent(&self, nonce: &[u8; 32]) -> bool {
        self.spent_nonces.contains(nonce)
    }

    /// Retorna la cantidad de nonces actualmente registrados en el ledger de gasto.
    pub fn spent_nonces_count(&self) -> usize {
        self.spent_nonces.len()
    }

    // -------------------------------------------------------------------------
    // § Elevación de Autoridad Epistémica (Ring-0)
    // -------------------------------------------------------------------------

    /// Fixture interno: adjunta un origen simulado a un claim.
    #[cfg(test)]
    fn authorize_claim<T>(&mut self, claim: Claim<T>, adapter_id: &'static str) -> Observed<T> {
        let tick = self.current_tick;
        self.advance_tick(1);
        let origin = Origin::new(adapter_id, tick);
        Observed::from_claim(claim, origin)
    }

    /// Fixture interno: genera una observación sin invocar un sensor real.
    #[cfg(test)]
    fn observe_raw<T>(&mut self, value: T, adapter_id: &'static str) -> Observed<T> {
        let tick = self.current_tick;
        self.advance_tick(1);
        observe(value, adapter_id, tick)
    }

    /// Fixture interno: verifica stdout simulado, sin ejecutar un comprobador.
    #[cfg(test)]
    fn verify_observation<T>(
        &mut self,
        observed: Observed<T>,
        witness_stdout: &[u8],
        exit_code: i32,
    ) -> Result<Verified<T>, EpistemicError> {
        let tick = self.current_tick;
        self.advance_tick(1);
        verify(observed, witness_stdout, exit_code, tick)
    }

    // -------------------------------------------------------------------------
    // § Gestión de Capacidades Lineales (LinearCap)
    // -------------------------------------------------------------------------

    /// Emite una capacidad lineal sobre un recurso `R`.
    /// Falla si el nonce ya ha sido registrado como gastado.
    pub fn mint_linear_capability<R>(
        &mut self,
        resource: R,
        nonce: [u8; 32],
    ) -> Result<LinearCap<R>, PlanGateError> {
        if self.spent_nonces.contains(&nonce) {
            let mut prefix = [0u8; 8];
            prefix.copy_from_slice(&nonce[..8]);
            return Err(PlanGateError::CapabilityAlreadySpent {
                nonce_prefix: prefix,
            });
        }
        Ok(LinearCap::new(resource, nonce))
    }

    /// Consume una capacidad lineal `LinearCap<R>` garantizando no-replay.
    /// Registra el nonce en el ledger de gasto del gate.
    pub fn consume_linear_capability<R>(&mut self, cap: LinearCap<R>) -> Result<R, PlanGateError> {
        let nonce = *cap.nonce_ref();
        if self.spent_nonces.contains(&nonce) {
            let mut prefix = [0u8; 8];
            prefix.copy_from_slice(&nonce[..8]);
            return Err(PlanGateError::CapabilityAlreadySpent {
                nonce_prefix: prefix,
            });
        }
        self.spent_nonces.insert(nonce);
        self.advance_tick(1);
        Ok(cap.consume())
    }

    // -------------------------------------------------------------------------
    // § Instanciación de VerifiedPlan
    // -------------------------------------------------------------------------

    /// Instancia formalmente un `VerifiedPlan` validando límites termodinámicos
    /// y anti-replay contra el estado del kernel.
    /// Este método es el ÚNICO puente que invoca `PlanBuilder::build` en producción.
    pub fn instantiate_plan(
        &mut self,
        builder: PlanBuilder,
    ) -> Result<VerifiedPlan, PlanGateError> {
        // 1. Validar e instanciar el plan invocando el constructor controlado (pub(crate))
        let plan = builder.build()?;

        // 2. Validar que el presupuesto del plan no excede el límite soberano del gate
        if plan.budget_steps() > self.max_budget_limit {
            return Err(PlanGateError::BudgetLimitExceeded {
                requested: plan.budget_steps(),
                limit: self.max_budget_limit,
            });
        }

        // 3. Validar límite de bytes de salida
        if plan.output_bytes_limit() > self.max_output_limit {
            return Err(PlanGateError::OutputLimitExceeded {
                requested: plan.output_bytes_limit(),
                limit: self.max_output_limit,
            });
        }

        // 4. Validar que ninguna de las capacidades requeridas ha sido gastada previamente
        for cap in plan.required_capabilities() {
            if self.spent_nonces.contains(&cap.nonce) {
                let mut prefix = [0u8; 8];
                prefix.copy_from_slice(&cap.nonce[..8]);
                return Err(PlanGateError::CapabilityAlreadySpent {
                    nonce_prefix: prefix,
                });
            }
        }

        Ok(plan)
    }

    // -------------------------------------------------------------------------
    // § Despacho y Ejecución Causal de VerifiedPlan
    // -------------------------------------------------------------------------

    /// Rechaza el despacho hasta que exista un ejecutor confiable integrado.
    /// `instantiate_plan` solo valida la estructura; no demuestra efectos.
    /// Sin ejecutor no se consumen capacidades, avanzan ticks ni emiten recibos.
    pub fn dispatch(&mut self, plan: &VerifiedPlan) -> Result<PlanExecutionReceipt, PlanGateError> {
        // Conservar el rechazo de capacidades gastadas incluso sin ejecutor.
        for cap in plan.required_capabilities() {
            if self.spent_nonces.contains(&cap.nonce) {
                let mut prefix = [0u8; 8];
                prefix.copy_from_slice(&cap.nonce[..8]);
                return Err(PlanGateError::CapabilityAlreadySpent {
                    nonce_prefix: prefix,
                });
            }
        }
        Err(PlanGateError::DispatchHalted {
            op_id: plan.operations()[0].op_id.clone(),
            reason: "No trusted operation executor is configured; plan validation does not execute effects".into(),
        })
    }

    /// Valida el plan e intenta despacharlo. Sin ejecutor devuelve un rechazo.
    pub fn authorize_and_dispatch(
        &mut self,
        builder: PlanBuilder,
    ) -> Result<PlanExecutionReceipt, PlanGateError> {
        let plan = self.instantiate_plan(builder)?;
        self.dispatch(&plan)
    }
}

// ----------------------------------------------------------------------------
// § Tests del Gate Consumidor
// ----------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::verified_plan::{
        CapabilityDescriptor, EvidenceLevel, EvidenceRequirement, Operation,
    };

    fn test_nonce(byte: u8) -> [u8; 32] {
        [byte; 32]
    }

    #[test]
    fn test_gate_claim_elevation_and_verification() {
        let mut gate = PlanConsumerGate::new(5000, 65536);
        let claim = Claim::new("target_hash_0x1234".to_string());
        let observed = gate.authorize_claim(claim, "sensor_hardware_0");
        assert_eq!(observed.inner_ref(), "target_hash_0x1234");
        assert_eq!(observed.origin.adapter_id, "sensor_hardware_0");

        let witness_stdout = b"LEAN4_THEOREM_PROVEN: OK";
        let verified = gate
            .verify_observation(observed, witness_stdout, 0)
            .expect("Verificación exitosa");
        assert_eq!(verified.inner_ref(), "target_hash_0x1234");
        assert!(verified.witness.is_valid());
    }

    #[test]
    fn test_gate_simulated_verification_rejects_failed_or_empty_witnesses() {
        let mut gate = PlanConsumerGate::new(100, 1024);
        for (stdout, exit_code) in [(b"".as_slice(), 0), (b"failure".as_slice(), 1)] {
            let observed = gate.observe_raw(42, "test_sensor");
            assert!(gate
                .verify_observation(observed, stdout, exit_code)
                .is_err());
        }
    }

    #[test]
    fn test_gate_linear_capability_lifecycle() {
        let mut gate = PlanConsumerGate::new(5000, 65536);
        let n = test_nonce(0x77);

        let cap = gate
            .mint_linear_capability("exclusive_hardware_bus", n)
            .expect("Mint OK");
        assert!(!gate.is_nonce_spent(&n));

        let res = gate.consume_linear_capability(cap).expect("Consume OK");
        assert_eq!(res, "exclusive_hardware_bus");
        assert!(gate.is_nonce_spent(&n));

        // Replay attempt must fail
        let replay_attempt = gate.mint_linear_capability("exclusive_hardware_bus_2", n);
        assert!(matches!(
            replay_attempt,
            Err(PlanGateError::CapabilityAlreadySpent { .. })
        ));
    }

    #[test]
    fn test_gate_instantiate_rejects_budget_overflow() {
        let mut gate = PlanConsumerGate::new(100, 4096);
        let builder = PlanBuilder::new(500, 2048).add_operation(Operation::new(
            "op1",
            "tool_a",
            EvidenceLevel::Verified,
            10,
        ));

        let err = gate.instantiate_plan(builder);
        assert!(matches!(
            err,
            Err(PlanGateError::BudgetLimitExceeded {
                requested: 500,
                limit: 100
            })
        ));
    }

    #[test]
    fn test_gate_instantiate_rejects_output_limit_overflow() {
        let mut gate = PlanConsumerGate::new(1000, 1024);
        let builder = PlanBuilder::new(100, 4096).add_operation(Operation::new(
            "op1",
            "tool_a",
            EvidenceLevel::Verified,
            10,
        ));

        let err = gate.instantiate_plan(builder);
        assert!(matches!(
            err,
            Err(PlanGateError::OutputLimitExceeded {
                requested: 4096,
                limit: 1024
            })
        ));
    }

    #[test]
    fn test_gate_dispatch_without_executor_rejects_without_side_effects() {
        let mut gate = PlanConsumerGate::new(2000, 8192);
        let cap = CapabilityDescriptor::new("storage_sector_9", "write", test_nonce(0x33));
        let req = EvidenceRequirement::new("write_tool", EvidenceLevel::Observed);
        let op1 = Operation::new("op1", "write_tool", EvidenceLevel::Observed, 40);
        let op2 = Operation::new("op2", "write_tool", EvidenceLevel::Verified, 60);

        let builder = PlanBuilder::new(500, 4096)
            .require_capability(cap)
            .require_evidence(req)
            .add_operation(op1)
            .add_operation(op2);

        let plan = gate
            .instantiate_plan(builder)
            .expect("Plan estructuralmente válido");
        let root_before = gate.mmr_accumulator.get_root();
        let tick_before = gate.current_tick();

        for _ in 0..2 {
            let error = gate.dispatch(&plan).expect_err("No hay ejecutor conectado");
            assert!(matches!(error, PlanGateError::DispatchHalted { op_id, .. } if op_id == "op1"));
            assert!(!gate.is_nonce_spent(&test_nonce(0x33)));
            assert_eq!(gate.spent_nonces_count(), 0);
            assert_eq!(gate.mmr_accumulator.get_root(), root_before);
            assert_eq!(gate.current_tick(), tick_before);
        }

        // Rechazar un despacho no invalida la capacidad de un plan posterior.
        let duplicate_cap =
            CapabilityDescriptor::new("storage_sector_9", "write", test_nonce(0x33));
        let builder2 = PlanBuilder::new(500, 4096)
            .require_capability(duplicate_cap)
            .add_operation(Operation::new(
                "op3",
                "write_tool",
                EvidenceLevel::Claim,
                10,
            ));

        let err = gate.authorize_and_dispatch(builder2);
        assert!(matches!(err, Err(PlanGateError::DispatchHalted { op_id, .. }) if op_id == "op3"));
        assert!(!gate.is_nonce_spent(&test_nonce(0x33)));
    }

    #[test]
    fn test_gate_dispatch_unknown_tool_never_reports_success() {
        let mut gate = PlanConsumerGate::new(100, 1024);
        let builder = PlanBuilder::new(10, 128).add_operation(Operation::new(
            "unknown",
            "nonexistent_tool",
            EvidenceLevel::Claim,
            1,
        ));
        let result = gate.authorize_and_dispatch(builder);
        assert!(
            matches!(result, Err(PlanGateError::DispatchHalted { op_id, .. }) if op_id == "unknown")
        );
    }

    #[test]
    fn test_gate_dispatch_still_rejects_spent_capabilities() {
        let mut gate = PlanConsumerGate::new(100, 1024);
        let nonce = test_nonce(0x99);
        let builder = PlanBuilder::new(10, 128)
            .require_capability(CapabilityDescriptor::new("resource", "write", nonce))
            .add_operation(Operation::new("op", "tool", EvidenceLevel::Claim, 1));
        let plan = gate
            .instantiate_plan(builder)
            .expect("Plan estructuralmente válido");
        let cap = gate
            .mint_linear_capability("resource", nonce)
            .expect("Mint de capacidad lineal válido");
        gate.consume_linear_capability(cap)
            .expect("Consumo de capacidad lineal válido");
        let result = gate.dispatch(&plan);
        assert!(matches!(
            result,
            Err(PlanGateError::CapabilityAlreadySpent { .. })
        ));
    }
}
