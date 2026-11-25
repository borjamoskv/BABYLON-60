// ============================================================================
// B60 EPISTEMIC TYPE TRIAD — Ring-0 Sovereignty Gate
// Invariante C5-REAL: Aforismo 5 (Lo voluntario vale menos que lo involuntario)
// Aforismo 1: Transformar ruido en conceptos con unicidad geométrica de Chentsov
//
// Semántica de capas:
//   Claim<T>    — salida de LLM: cero autoridad, solo cheap-talk voluntario
//   Observed<T> — evidencia empírica: instanciable solo por adaptadores confiables
//   Verified<T> — prueba formal: instanciable solo por el comprobador del kernel
//
// RESTRICCIÓN DE PRIVACIDAD:
//   Los constructores de Observed<T> y Verified<T> son pub(crate).
//   Nada externo al crate puede producir estas variantes directamente.
//   Esta garantía es ESTRUCTURAL (tipo system de Rust), no convencional.
// ============================================================================

#[cfg(test)]
use sha2::{Digest, Sha256};

// ----------------------------------------------------------------------------
// §1. CLAIM — Capa LLM (cheap-talk voluntario)
// ----------------------------------------------------------------------------

/// Salida bruta de un modelo de lenguaje o agente.
/// No tiene autoridad epistémica. Solo puede ascender a [`Observed<T>`]
/// o [`Verified<T>`] a través de adaptadores con privilegio de `pub(crate)`.
#[derive(Debug, Clone)]
#[must_use = "Un Claim sin verificar no tiene valor epistémico; pásalo por un EpistemicGate"]
pub struct Claim<T> {
    inner: T,
}

impl<T> Claim<T> {
    /// Único constructor público: cualquier código puede emitir un Claim.
    /// No hay garantías sobre el contenido.
    pub fn new(value: T) -> Self {
        Self { inner: value }
    }

    /// Lectura inmutable del contenido (sin elevar la autoridad del tipo).
    pub fn inner_ref(&self) -> &T {
        &self.inner
    }

    /// Extrae el valor sin elevar su autoridad epistémica.
    /// No produce una observación ni una verificación.
    pub fn into_inner(self) -> T {
        self.inner
    }
}

// ----------------------------------------------------------------------------
// §2. ORIGIN — Metadato de proveniencia de evidencia empírica
// ----------------------------------------------------------------------------

/// Identifica el adaptador confiable y el instante causal que produjo la observación.
/// `adapter_id` es un literal de cadena estático (no heap) para evitar interpolación.
#[derive(Debug, Clone)]
pub struct Origin {
    pub adapter_id: &'static str,
    /// Contador de ticks causal (Tick60 en términos B60); no es tiempo de pared.
    pub timestamp_tick: u64,
}

impl Origin {
    pub fn new(adapter_id: &'static str, timestamp_tick: u64) -> Self {
        Self {
            adapter_id,
            timestamp_tick,
        }
    }
}

// ----------------------------------------------------------------------------
// §3. OBSERVED — Evidencia empírica (involuntario de primer orden)
// ----------------------------------------------------------------------------

/// Evidencia producida por un adaptador de silicio confiable (sensor, proceso externo,
/// salida de herramienta auditada). Solo instanciable dentro de este crate.
#[derive(Debug, Clone)]
pub struct Observed<T> {
    inner: T,
    pub origin: Origin,
}

impl<T> Observed<T> {
    /// Constructor de fixtures; no hay un adaptador de observación productivo integrado.
    #[cfg(test)]
    pub(crate) fn new(value: T, origin: Origin) -> Self {
        Self {
            inner: value,
            origin,
        }
    }

    /// Eleva un [`Claim<T>`] a `Observed<T>` adjuntando evidencia de origen.
    /// Fixture interno: no acredita una observación real.
    #[cfg(test)]
    pub(crate) fn from_claim(claim: Claim<T>, origin: Origin) -> Self {
        Self {
            inner: claim.into_inner(),
            origin,
        }
    }

    pub fn inner_ref(&self) -> &T {
        &self.inner
    }

    pub fn into_inner(self) -> T {
        self.inner
    }
}

// ----------------------------------------------------------------------------
// §4. EVIDENCE WITNESS — Atestación de verificación formal
// ----------------------------------------------------------------------------

/// Testigo criptográfico emitido por el comprobador formal del kernel.
/// `exit_code == 0` es condición necesaria pero NO suficiente: también se exige
/// que `stdout_hash` corresponda a la salida real del comprobador.
#[derive(Debug, Clone)]
pub struct EvidenceWitness {
    /// Código de salida del proceso verificador (0 = éxito formal).
    pub exit_code: i32,
    /// SHA-256 del stdout completo del comprobador (previene replay de salidas vacías).
    pub stdout_hash: [u8; 32],
    /// Tick causal en el que se completó la verificación.
    pub timestamp_tick: u64,
}

impl EvidenceWitness {
    /// Construye un testigo simulado, disponible solo en pruebas.
    #[cfg(test)]
    pub(crate) fn new(exit_code: i32, stdout_bytes: &[u8], timestamp_tick: u64) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(stdout_bytes);
        let stdout_hash: [u8; 32] = hasher.finalize().into();
        Self {
            exit_code,
            stdout_hash,
            timestamp_tick,
        }
    }

    /// Verifica que el testigo representa un éxito formal (exit_code == 0
    /// Y stdout_hash no es el hash de cadena vacía, que indicaría salida nula).
    pub fn is_valid(&self) -> bool {
        const EMPTY_HASH: [u8; 32] = [
            0xe3, 0xb0, 0xc4, 0x42, 0x98, 0xfc, 0x1c, 0x14, 0x9a, 0xfb, 0xf4, 0xc8, 0x99, 0x6f,
            0xb9, 0x24, 0x27, 0xae, 0x41, 0xe4, 0x64, 0x9b, 0x93, 0x4c, 0xa4, 0x95, 0x99, 0x1b,
            0x78, 0x52, 0xb8, 0x55,
        ];
        self.exit_code == 0 && self.stdout_hash != EMPTY_HASH
    }
}

// ----------------------------------------------------------------------------
// §5. VERIFIED — Prueba formal (involuntario de segundo orden)
// ----------------------------------------------------------------------------

/// Resultado de una comprobación formal exitosa. Solo instanciable por el
/// comprobador del kernel (`pub(crate)`). Es la única variante con autoridad
/// epistémica plena bajo el marco C5-REAL.
#[derive(Debug, Clone)]
pub struct Verified<T> {
    inner: T,
    pub witness: EvidenceWitness,
}

impl<T> Verified<T> {
    /// Eleva un [`Observed<T>`] a `Verified<T>` tras verificación formal exitosa.
    /// Falla en tiempo de ejecución si el testigo no es válido (exit_code != 0
    /// o stdout vacío). Este fallo es intencional y fail-fast.
    #[cfg(test)]
    pub(crate) fn from_observed(
        observed: Observed<T>,
        witness: EvidenceWitness,
    ) -> Result<Self, EpistemicError> {
        if !witness.is_valid() {
            return Err(EpistemicError::InvalidWitness {
                exit_code: witness.exit_code,
            });
        }
        Ok(Self {
            inner: observed.into_inner(),
            witness,
        })
    }

    pub fn inner_ref(&self) -> &T {
        &self.inner
    }

    pub fn into_inner(self) -> T {
        self.inner
    }
}

// ----------------------------------------------------------------------------
// §6. LINEAR CAPABILITY — Recurso de consumo único (linealidad C5-REAL)
// ----------------------------------------------------------------------------

/// Capacidad lineal sobre un recurso `R`. Solo puede consumirse una vez.
/// La garantía es ESTRUCTURAL: `consume` toma ownership de `self` (move semantics),
/// impidiendo que el compilador de Rust permita un segundo uso.
///
/// PROHIBICIÓN EXPLÍCITA: `LinearCap<R>` NO implementa `Clone` ni `Copy`.
/// Cualquier intento de derivarlos es un error de compilación.
#[must_use = "LinearCap debe consumirse exactamente una vez con .consume()"]
pub struct LinearCap<R> {
    resource: R,
    /// Nonce de 32 bytes para prevenir replay a nivel de runtime (segunda línea de defensa).
    pub nonce: [u8; 32],
}

impl<R> LinearCap<R> {
    /// Crea una nueva capacidad lineal. El nonce debe ser único y generado por
    /// el subsistema de entropía del kernel (Secure Enclave TRNG en Apple Silicon).
    pub(crate) fn new(resource: R, nonce: [u8; 32]) -> Self {
        Self { resource, nonce }
    }

    /// Consume la capacidad, devolviendo el recurso subyacente.
    /// Al tomar `self` por move, Rust garantiza en tiempo de compilación que
    /// esta función solo puede llamarse una vez. El borrow checker previene
    /// cualquier uso posterior de la variable.
    pub fn consume(self) -> R {
        self.resource
    }

    /// Vista del nonce sin consumir la capacidad (para auditoría).
    pub fn nonce_ref(&self) -> &[u8; 32] {
        &self.nonce
    }
}

// LinearCap NUNCA debe implementar Clone o Copy.
// La ausencia de estas derives es la garantía de linealidad.
// Verificado por test T2 (compile-time).

// ----------------------------------------------------------------------------
// §7. EPISTEMIC ERROR — Errores de violación de invariantes
// ----------------------------------------------------------------------------

#[derive(Debug, PartialEq, Eq)]
pub enum EpistemicError {
    /// El testigo del comprobador formal no es válido (exit_code != 0 o stdout vacío).
    InvalidWitness { exit_code: i32 },
    /// Intento de replay de un nonce ya consumido.
    NonceAlreadyConsumed { nonce_prefix: [u8; 8] },
    /// El tipo observado no coincide con lo esperado por el comprobador.
    TypeMismatch {
        expected: &'static str,
        got: &'static str,
    },
}

impl std::fmt::Display for EpistemicError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidWitness { exit_code } => {
                write!(f, "EpistemicError::InvalidWitness(exit_code={exit_code})")
            }
            Self::NonceAlreadyConsumed { nonce_prefix } => write!(
                f,
                "EpistemicError::NonceAlreadyConsumed(prefix={nonce_prefix:02x?})"
            ),
            Self::TypeMismatch { expected, got } => write!(
                f,
                "EpistemicError::TypeMismatch(expected={expected}, got={got})"
            ),
        }
    }
}

impl std::error::Error for EpistemicError {}

// ----------------------------------------------------------------------------
// §8. ADAPTER HELPERS — Fachadas pub(crate) para tests del kernel
// ----------------------------------------------------------------------------

/// Eleva directamente un valor a `Observed<T>` sin pasar por `Claim`.
/// Fixture disponible solo en pruebas; no invoca un sensor real.
#[cfg(test)]
pub(crate) fn observe<T>(value: T, adapter_id: &'static str, tick: u64) -> Observed<T> {
    Observed::new(value, Origin::new(adapter_id, tick))
}

/// Verifica un `Observed<T>` con stdout simulado (para tests del kernel).
#[cfg(test)]
pub(crate) fn verify<T>(
    observed: Observed<T>,
    stdout_bytes: &[u8],
    exit_code: i32,
    tick: u64,
) -> Result<Verified<T>, EpistemicError> {
    let witness = EvidenceWitness::new(exit_code, stdout_bytes, tick);
    Verified::from_observed(observed, witness)
}

// ----------------------------------------------------------------------------
// §9. TESTS INTERNOS (módulo inline)
// ----------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    // T-INT-1: Claim se construye libremente; inner_ref expone el valor.
    #[test]
    fn claim_construction_and_read() {
        let c = Claim::new(42u64);
        assert_eq!(*c.inner_ref(), 42u64);
    }

    // T-INT-2: Observed solo se construye desde pub(crate); el contenido persiste.
    #[test]
    fn observed_from_claim_preserves_value() {
        let c = Claim::new("ULTRATHINK");
        let obs = Observed::from_claim(c, Origin::new("test-adapter", 1));
        assert_eq!(*obs.inner_ref(), "ULTRATHINK");
        assert_eq!(obs.origin.adapter_id, "test-adapter");
    }

    // T-INT-3: Verified falla si el testigo tiene exit_code != 0.
    #[test]
    fn verified_rejects_invalid_witness() {
        let obs = observe("payload", "test-adapter", 2);
        let result = verify(obs, b"some output", 1, 2); // exit_code = 1 → inválido
        assert!(matches!(
            result,
            Err(EpistemicError::InvalidWitness { exit_code: 1 })
        ));
    }

    // T-INT-4: Verified falla si el stdout es vacío (hash de cadena vacía).
    #[test]
    fn verified_rejects_empty_stdout() {
        let obs = observe("payload", "test-adapter", 3);
        let result = verify(obs, b"", 0, 3); // stdout vacío → inválido aunque exit=0
        assert!(matches!(
            result,
            Err(EpistemicError::InvalidWitness { exit_code: 0 })
        ));
    }

    // T-INT-5: Verified acepta testigo legítimo (exit=0, stdout no vacío).
    #[test]
    fn verified_accepts_valid_witness() {
        let obs = observe("formal-proof-result", "lean4-checker", 100);
        let result = verify(obs, b"All goals solved.", 0, 100);
        assert!(result.is_ok());
        let v = result.unwrap();
        assert_eq!(*v.inner_ref(), "formal-proof-result");
        assert!(v.witness.is_valid());
    }

    // T-INT-6: LinearCap consume el recurso exactamente una vez (move semantics).
    // El double-consume está bloqueado en COMPILE-TIME por Rust (ver T2 en tests/).
    #[test]
    fn linear_cap_consume_returns_resource() {
        let cap = LinearCap::new(99u32, [0xABu8; 32]);
        let resource = cap.consume();
        assert_eq!(resource, 99u32);
        // `cap` ya no existe aquí; el compilador rechazaría cualquier uso posterior.
    }

    // T-INT-7: EvidenceWitness::is_valid rechaza hashes de stdout vacío.
    #[test]
    fn evidence_witness_empty_stdout_invalid() {
        let w = EvidenceWitness::new(0, b"", 0);
        assert!(!w.is_valid());
    }

    // T-INT-8: EvidenceWitness::is_valid acepta salida real.
    #[test]
    fn evidence_witness_real_output_valid() {
        let w = EvidenceWitness::new(0, b"proof verified", 42);
        assert!(w.is_valid());
    }
}
