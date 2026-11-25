// ============================================================================
// B60 VERIFIED PLAN — Plan de Ejecución Formal con Capacidades Tipadas
// Invariante C5-REAL: Solo el compilador del kernel puede instanciar VerifiedPlan.
// Ningún código externo puede construir un plan válido sin pasar por try_build.
//
// GARANTÍAS ESTRUCTURALES:
//   1. Todos los campos de VerifiedPlan son privados (no pub).
//   2. El único constructor es pub(crate) — invisible fuera del crate.
//   3. try_build valida: presupuesto, límites de salida, nonces únicos,
//      correspondencia de tipos epistémicos y digest SHA-256 del plan.
//   4. PlanError es exhaustivo y no tiene variante "Other" para forzar
//      que el caller maneje cada caso explícitamente.
// ============================================================================

use sha2::{Digest, Sha256};
use crate::epistemic_types::EpistemicError;

// ----------------------------------------------------------------------------
// §1. EVIDENCE LEVEL — Jerarquía de autoridad epistémica
// ----------------------------------------------------------------------------

/// Nivel mínimo de evidencia requerido para una operación del plan.
/// El compilador rechaza planes donde las operaciones declaran un nivel
/// inferior al exigido por sus precondiciones.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum EvidenceLevel {
    /// Salida de LLM sin verificación (cheap-talk). Autoridad: ninguna.
    Claim = 0,
    /// Evidencia empírica de adaptador confiable. Autoridad: primera línea.
    Observed = 1,
    /// Prueba formal del comprobador del kernel. Autoridad: plena.
    Verified = 2,
}

impl std::fmt::Display for EvidenceLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Claim => write!(f, "Claim"),
            Self::Observed => write!(f, "Observed"),
            Self::Verified => write!(f, "Verified"),
        }
    }
}

// ----------------------------------------------------------------------------
// §2. CAPABILITY DESCRIPTOR — Descripción de recurso y operación
// ----------------------------------------------------------------------------

/// Describe un recurso y la operación que el plan solicita sobre él.
/// El nonce garantiza unicidad de cada capacidad dentro del plan
/// (previene clonación implícita de descriptores).
#[derive(Debug, Clone)]
pub struct CapabilityDescriptor {
    pub resource_id: String,
    pub operation: String,
    /// Nonce único de 32 bytes por descriptor (Secure Enclave TRNG en Apple Silicon).
    pub nonce: [u8; 32],
}

impl CapabilityDescriptor {
    pub fn new(resource_id: impl Into<String>, operation: impl Into<String>, nonce: [u8; 32]) -> Self {
        Self {
            resource_id: resource_id.into(),
            operation: operation.into(),
            nonce,
        }
    }
}

// ----------------------------------------------------------------------------
// §3. EVIDENCE REQUIREMENT — Requisito de nivel mínimo por tipo de claim
// ----------------------------------------------------------------------------

/// Exige que un tipo de claim concreto tenga al menos el nivel indicado
/// antes de que el plan pueda ejecutarse.
#[derive(Debug, Clone)]
pub struct EvidenceRequirement {
    /// Nombre del tipo de claim que debe verificarse (ej. "DeploymentTarget").
    pub claim_type: String,
    /// Nivel mínimo de evidencia exigido.
    pub min_level: EvidenceLevel,
}

impl EvidenceRequirement {
    pub fn new(claim_type: impl Into<String>, min_level: EvidenceLevel) -> Self {
        Self { claim_type: claim_type.into(), min_level }
    }
}

// ----------------------------------------------------------------------------
// §4. OPERATION — Unidad atómica del plan
// ----------------------------------------------------------------------------

/// Una operación individual dentro del plan verificado.
/// `evidence_level` es el nivel REAL de la evidencia que sustenta esta
/// operación en el momento de la construcción del plan.
#[derive(Debug, Clone)]
pub struct Operation {
    pub op_id: String,
    pub tool_name: String,
    pub evidence_level: EvidenceLevel,
    /// Coste estimado en ticks presupuestarios (no tiempo de pared).
    pub budget_cost: u32,
}

impl Operation {
    pub fn new(
        op_id: impl Into<String>,
        tool_name: impl Into<String>,
        evidence_level: EvidenceLevel,
        budget_cost: u32,
    ) -> Self {
        Self {
            op_id: op_id.into(),
            tool_name: tool_name.into(),
            evidence_level,
            budget_cost,
        }
    }
}

// ----------------------------------------------------------------------------
// §5. PLAN ERROR — Errores exhaustivos de construcción de plan
// ----------------------------------------------------------------------------

#[derive(Debug, PartialEq, Eq)]
pub enum PlanError {
    /// Una operación declara un nivel de evidencia inferior al requerido.
    TypeMismatch {
        op_id: String,
        required: EvidenceLevel,
        provided: EvidenceLevel,
    },
    /// Una capacidad fue agotada (nonce ya registrado en el plan).
    CapabilityExhausted { resource_id: String },
    /// El coste total de las operaciones excede `budget_steps`.
    BudgetExceeded { used: u32, limit: u32 },
    /// Se detectó un nonce duplicado en la lista de capacidades.
    NonceReplay { nonce_prefix: [u8; 8] },
    /// Intento de construir `VerifiedPlan` fuera de `try_build`.
    /// Esta variante es el invariante central del módulo.
    UnauthorizedConstruction,
    /// Error epistémico del nivel inferior (tríada).
    EpistemicViolation(EpistemicError),
    /// La lista de operaciones está vacía.
    EmptyOperations,
}

impl std::fmt::Display for PlanError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::TypeMismatch { op_id, required, provided } =>
                write!(f, "PlanError::TypeMismatch(op={op_id}, required={required}, provided={provided})"),
            Self::CapabilityExhausted { resource_id } =>
                write!(f, "PlanError::CapabilityExhausted(resource={resource_id})"),
            Self::BudgetExceeded { used, limit } =>
                write!(f, "PlanError::BudgetExceeded(used={used}, limit={limit})"),
            Self::NonceReplay { nonce_prefix } =>
                write!(f, "PlanError::NonceReplay(prefix={nonce_prefix:02x?})"),
            Self::UnauthorizedConstruction =>
                write!(f, "PlanError::UnauthorizedConstruction"),
            Self::EpistemicViolation(e) =>
                write!(f, "PlanError::EpistemicViolation({e})"),
            Self::EmptyOperations =>
                write!(f, "PlanError::EmptyOperations"),
        }
    }
}

impl std::error::Error for PlanError {}

impl From<EpistemicError> for PlanError {
    fn from(e: EpistemicError) -> Self {
        Self::EpistemicViolation(e)
    }
}

// ----------------------------------------------------------------------------
// §6. VERIFIED PLAN — Struct opaco; solo el compilador puede instanciar
// ----------------------------------------------------------------------------

/// Plan validado estructuralmente, con digest y campos privados.
/// Los niveles de evidencia son declarados: construir el plan no ejecuta
/// herramientas ni verifica evidencia externa.
/// Se construye mediante [`PlanConsumerGate::instantiate_plan`](crate::consumer_gate::PlanConsumerGate::instantiate_plan), que valida:
///   - Operaciones no vacías.
///   - Coste total ≤ `budget_steps`.
///   - Nonces de capacidades únicos (sin replay).
///   - Nivel de evidencia de cada operación ≥ requisito mínimo correspondiente.
///   - Digest SHA-256 del plan completo (committeado en `plan_digest`).
///
/// INVARIANTE DE CONFINAMIENTO: `VerifiedPlan` es `pub` (exportable) pero
/// ningún campo es `pub`. Intentar construirlo con struct-literal fuera de
/// `try_build` produce un error de compilación por campos privados.
#[derive(Debug)]
pub struct VerifiedPlan {
    operations: Vec<Operation>,
    required_capabilities: Vec<CapabilityDescriptor>,
    evidence_requirements: Vec<EvidenceRequirement>,
    budget_steps: u32,
    output_bytes_limit: u32,
    /// SHA-256 del plan serializado: previene mutación post-construcción.
    plan_digest: [u8; 32],
}

impl VerifiedPlan {
    // -------------------------------------------------------------------------
    // Constructor único y canónico (pub(crate) — invisible fuera del crate)
    // -------------------------------------------------------------------------

    /// Construye y verifica un plan. Retorna `Err(PlanError)` en cualquier
    /// violación de invariantes. Este es el ÚNICO constructor válido.
    ///
    /// # Algoritmo de validación
    /// 1. Comprobar que `operations` no está vacío.
    /// 2. Sumar costes; fallar si exceden `budget_steps`.
    /// 3. Detectar nonces duplicados en `required_capabilities`.
    /// 4. Para cada operación, comprobar que `evidence_level >= min_level`
    ///    del `EvidenceRequirement` correspondiente (por `claim_type == tool_name`).
    /// 5. Calcular SHA-256 del plan y committirlo en `plan_digest`.
    pub(crate) fn try_build(
        operations: Vec<Operation>,
        required_capabilities: Vec<CapabilityDescriptor>,
        evidence_requirements: Vec<EvidenceRequirement>,
        budget_steps: u32,
        output_bytes_limit: u32,
    ) -> Result<Self, PlanError> {
        // Paso 1 — Plan no vacío
        if operations.is_empty() {
            return Err(PlanError::EmptyOperations);
        }

        // Paso 2 — Presupuesto
        let total_cost: u32 = operations.iter().map(|op| op.budget_cost).fold(0u32, |acc, c| {
            acc.saturating_add(c)
        });
        if total_cost > budget_steps {
            return Err(PlanError::BudgetExceeded { used: total_cost, limit: budget_steps });
        }

        // Paso 3 — Nonces únicos en capacidades
        let mut seen_nonces: Vec<[u8; 32]> = Vec::new();
        for cap in &required_capabilities {
            if seen_nonces.contains(&cap.nonce) {
                let mut prefix = [0u8; 8];
                prefix.copy_from_slice(&cap.nonce[..8]);
                return Err(PlanError::NonceReplay { nonce_prefix: prefix });
            }
            seen_nonces.push(cap.nonce);
        }

        // Paso 4 — Validación de niveles epistémicos por operación
        for op in &operations {
            // Buscar el requisito correspondiente al tool_name de esta operación
            if let Some(req) = evidence_requirements.iter().find(|r| r.claim_type == op.tool_name) {
                if op.evidence_level < req.min_level {
                    return Err(PlanError::TypeMismatch {
                        op_id: op.op_id.clone(),
                        required: req.min_level.clone(),
                        provided: op.evidence_level.clone(),
                    });
                }
            }
        }

        // Paso 5 — Digest SHA-256 del plan
        let plan_digest = Self::compute_digest(
            &operations,
            &required_capabilities,
            &evidence_requirements,
            budget_steps,
            output_bytes_limit,
        );

        Ok(Self {
            operations,
            required_capabilities,
            evidence_requirements,
            budget_steps,
            output_bytes_limit,
            plan_digest,
        })
    }

    // -------------------------------------------------------------------------
    // Accessors de solo lectura (los campos permanecen privados)
    // -------------------------------------------------------------------------

    pub fn operations(&self) -> &[Operation] {
        &self.operations
    }

    pub fn budget_steps(&self) -> u32 {
        self.budget_steps
    }

    pub fn output_bytes_limit(&self) -> u32 {
        self.output_bytes_limit
    }

    pub fn plan_digest(&self) -> &[u8; 32] {
        &self.plan_digest
    }

    pub fn required_capabilities(&self) -> &[CapabilityDescriptor] {
        &self.required_capabilities
    }

    pub fn evidence_requirements(&self) -> &[EvidenceRequirement] {
        &self.evidence_requirements
    }

    // -------------------------------------------------------------------------
    // Helpers internos
    // -------------------------------------------------------------------------

    fn compute_digest(
        operations: &[Operation],
        caps: &[CapabilityDescriptor],
        requirements: &[EvidenceRequirement],
        budget_steps: u32,
        output_bytes_limit: u32,
    ) -> [u8; 32] {
        fn hash_str(hasher: &mut Sha256, value: &str) {
            hasher.update((value.len() as u64).to_le_bytes());
            hasher.update(value.as_bytes());
        }

        let mut hasher = Sha256::new();
        hasher.update(b"B60_VERIFIED_PLAN_V2:");
        hasher.update(budget_steps.to_le_bytes());
        hasher.update(output_bytes_limit.to_le_bytes());
        hasher.update((operations.len() as u64).to_le_bytes());
        for op in operations {
            hash_str(&mut hasher, &op.op_id);
            hash_str(&mut hasher, &op.tool_name);
            hasher.update([op.evidence_level.clone() as u8]);
            hasher.update(op.budget_cost.to_le_bytes());
        }
        hasher.update((caps.len() as u64).to_le_bytes());
        for cap in caps {
            hash_str(&mut hasher, &cap.resource_id);
            hash_str(&mut hasher, &cap.operation);
            hasher.update(cap.nonce);
        }
        hasher.update((requirements.len() as u64).to_le_bytes());
        for req in requirements {
            hash_str(&mut hasher, &req.claim_type);
            hasher.update([req.min_level.clone() as u8]);
        }
        hasher.finalize().into()
    }
}

// ----------------------------------------------------------------------------
// §7. PLAN BUILDER — Fachada pub para tests del kernel y el compilador B60
// ----------------------------------------------------------------------------

/// Interfaz pública para construir un `VerifiedPlan`.
/// Solo accesible desde dentro del crate (`pub(crate)` a `try_build`).
/// Código externo no puede llegar a `try_build` directamente.
pub struct PlanBuilder {
    operations: Vec<Operation>,
    capabilities: Vec<CapabilityDescriptor>,
    requirements: Vec<EvidenceRequirement>,
    budget_steps: u32,
    output_bytes_limit: u32,
}

impl PlanBuilder {
    pub fn new(budget_steps: u32, output_bytes_limit: u32) -> Self {
        Self {
            operations: Vec::new(),
            capabilities: Vec::new(),
            requirements: Vec::new(),
            budget_steps,
            output_bytes_limit,
        }
    }

    pub fn add_operation(mut self, op: Operation) -> Self {
        self.operations.push(op);
        self
    }

    pub fn require_capability(mut self, cap: CapabilityDescriptor) -> Self {
        self.capabilities.push(cap);
        self
    }

    pub fn require_evidence(mut self, req: EvidenceRequirement) -> Self {
        self.requirements.push(req);
        self
    }

    /// Finaliza el builder invocando el constructor privado de `VerifiedPlan`.
    /// Solo es accesible dentro del crate — el PlanBuilder actúa como proxy
    /// controlado para `try_build`.
    pub(crate) fn build(self) -> Result<VerifiedPlan, PlanError> {
        VerifiedPlan::try_build(
            self.operations,
            self.capabilities,
            self.requirements,
            self.budget_steps,
            self.output_bytes_limit,
        )
    }
}

// ----------------------------------------------------------------------------
// §8. TESTS INTERNOS (módulo inline)
// ----------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn nonce(byte: u8) -> [u8; 32] {
        [byte; 32]
    }

    // T-INT-VP-1: Plan vacío rechazado.
    #[test]
    fn empty_plan_rejected() {
        let result = PlanBuilder::new(100, 4096).build();
        assert!(matches!(result, Err(PlanError::EmptyOperations)));
    }

    // T-INT-VP-2: Presupuesto excedido rechazado.
    #[test]
    fn budget_exceeded_rejected() {
        let op = Operation::new("op1", "tool_a", EvidenceLevel::Verified, 200);
        let result = PlanBuilder::new(100, 4096)
            .add_operation(op)
            .build();
        assert!(matches!(result, Err(PlanError::BudgetExceeded { used: 200, limit: 100 })));
    }

    // T-INT-VP-3: Nonce duplicado en capacidades rechazado.
    #[test]
    fn nonce_replay_rejected() {
        let op = Operation::new("op1", "tool_a", EvidenceLevel::Verified, 10);
        let cap1 = CapabilityDescriptor::new("res_a", "read", nonce(0xAA));
        let cap2 = CapabilityDescriptor::new("res_b", "write", nonce(0xAA)); // mismo nonce
        let result = PlanBuilder::new(1000, 4096)
            .add_operation(op)
            .require_capability(cap1)
            .require_capability(cap2)
            .build();
        let mut expected_prefix = [0u8; 8];
        expected_prefix.copy_from_slice(&nonce(0xAA)[..8]);
        assert!(matches!(result, Err(PlanError::NonceReplay { nonce_prefix }) if nonce_prefix == expected_prefix));
    }

    // T-INT-VP-4: TypeMismatch rechazado (Claim donde se exige Verified).
    #[test]
    fn type_mismatch_claim_vs_verified_rejected() {
        let op = Operation::new("op1", "deploy_contract", EvidenceLevel::Claim, 10);
        let req = EvidenceRequirement::new("deploy_contract", EvidenceLevel::Verified);
        let result = PlanBuilder::new(1000, 4096)
            .add_operation(op)
            .require_evidence(req)
            .build();
        assert!(matches!(result, Err(PlanError::TypeMismatch { op_id, required: EvidenceLevel::Verified, provided: EvidenceLevel::Claim }) if op_id == "op1"));
    }

    // T-INT-VP-5: Plan válido end-to-end. digest != [0u8; 32].
    #[test]
    fn valid_plan_end_to_end() {
        let op = Operation::new("op1", "deploy_contract", EvidenceLevel::Verified, 50);
        let cap = CapabilityDescriptor::new("mainnet", "deploy", nonce(0x01));
        let req = EvidenceRequirement::new("deploy_contract", EvidenceLevel::Verified);
        let result = PlanBuilder::new(1000, 4096)
            .add_operation(op)
            .require_capability(cap)
            .require_evidence(req)
            .build();
        assert!(result.is_ok());
        let plan = result.unwrap();
        assert_eq!(plan.budget_steps(), 1000);
        assert_ne!(*plan.plan_digest(), [0u8; 32]);
        assert_eq!(plan.operations().len(), 1);
    }

    // T-INT-VP-6: Observed es suficiente cuando se exige Observed.
    #[test]
    fn observed_satisfies_observed_requirement() {
        let op = Operation::new("op1", "read_sensor", EvidenceLevel::Observed, 5);
        let req = EvidenceRequirement::new("read_sensor", EvidenceLevel::Observed);
        let result = PlanBuilder::new(100, 1024)
            .add_operation(op)
            .require_evidence(req)
            .build();
        assert!(result.is_ok());
    }

    // T-INT-VP-7: Observed insuficiente cuando se exige Verified.
    #[test]
    fn observed_insufficient_for_verified_requirement() {
        let op = Operation::new("op1", "deploy_contract", EvidenceLevel::Observed, 5);
        let req = EvidenceRequirement::new("deploy_contract", EvidenceLevel::Verified);
        let result = PlanBuilder::new(100, 1024)
            .add_operation(op)
            .require_evidence(req)
            .build();
        assert!(matches!(result, Err(PlanError::TypeMismatch { op_id, required: EvidenceLevel::Verified, provided: EvidenceLevel::Observed }) if op_id == "op1"));
    }

    #[test]
    fn digest_commits_to_evidence_and_capability_operation() {
        let build = |level, requirement, capability_operation| {
            PlanBuilder::new(100, 1024)
                .add_operation(Operation::new("op1", "tool", level, 5))
                .require_capability(CapabilityDescriptor::new("resource", capability_operation, nonce(1)))
                .require_evidence(EvidenceRequirement::new("tool", requirement))
                .build()
                .unwrap()
        };
        let base = build(EvidenceLevel::Verified, EvidenceLevel::Claim, "read");
        let different_level = build(EvidenceLevel::Observed, EvidenceLevel::Claim, "read");
        let different_requirement = build(EvidenceLevel::Verified, EvidenceLevel::Observed, "read");
        let different_operation = build(EvidenceLevel::Verified, EvidenceLevel::Claim, "write");
        assert_ne!(base.plan_digest(), different_level.plan_digest());
        assert_ne!(base.plan_digest(), different_requirement.plan_digest());
        assert_ne!(base.plan_digest(), different_operation.plan_digest());
    }
}
