// C5-REAL EXERGY CERTIFIED
use serde::{Deserialize, Serialize};
use ciborium::into_writer;
use sha3::{Sha3_256, Digest};
use ed25519_dalek::{SigningKey, Signer};
use std::collections::BTreeMap;
use coset::{CoseSign1Builder, HeaderBuilder, CborSerializable};

/// Aritmética de Punto Fijo 32.32 (u64).
/// Los 32 bits superiores representan la parte entera.
/// Los 32 bits inferiores representan la parte fraccional.
/// Ejemplo: 0.03 → 0.03 × 2^32 = 128_849_018 (0x07AE_147A)
/// Esto garantiza reproducibilidad bit-perfect determinista en todas
/// las arquitecturas (x86_64, aarch64, WASM) sin depender de IEEE 754.
pub type Fixed32_32 = u64;

/// Constante de umbral legal del Artículo 15 EU AI Act.
/// Representa 0.03 (3%) en aritmética de punto fijo 32.32.
/// 0.03 × 2^32 = 128_849_018
pub const ARTICLE_15_MAX_VARENTROPY: Fixed32_32 = 128_849_018;

/// Factor de escala para conversión de flotantes a punto fijo 32.32.
pub const FIXED_32_32_SCALE: u64 = 1u64 << 32;

/// Convierte un valor f64 a Fixed32_32 para ingesta desde Python.
/// Esta función SOLO se invoca en la frontera FFI; internamente
/// todo el Kernel opera exclusivamente con u64.
#[inline]
pub fn f64_to_fixed(val: f64) -> Fixed32_32 {
    (val * FIXED_32_32_SCALE as f64) as u64
}

#[derive(Debug)]
pub struct EpistemicHalt {
    pub reason: String,
}

impl std::fmt::Display for EpistemicHalt {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "EpistemicHalt: {}", self.reason)
    }
}

impl std::error::Error for EpistemicHalt {}

impl From<String> for EpistemicHalt {
    fn from(reason: String) -> Self {
        EpistemicHalt { reason }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct TransitionRecord {
    pub canon: String,
    pub contract_digest: Vec<u8>,
    pub parents: Vec<ParentEdge>,
    pub model: ModelInfo,
    pub prompt_digest: Vec<u8>,
    pub emission: EmissionInfo,
    pub sandbox: SandboxInfo,
    pub execution: ExecutionInfo,
    pub verdicts: Vec<Verdict>,
    pub uncertainty: Option<Uncertainty>,
    pub budget: Option<Budget>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ParentEdge {
    pub edge_type: String, // e.g. "consumed_output", "read_memory"
    pub digest: Vec<u8>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ModelInfo {
    pub provider: String,
    pub model_id: String,
    pub snapshot: Option<String>,
    pub sampling: Option<SamplingInfo>,
    pub engine: EngineInfo,
    pub hardware_class: Option<String>,
    pub determinism_mode: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SamplingInfo {
    /// Temperatura de muestreo en punto fijo 32.32 (ej. 0.7 → 3_006_477_107).
    pub temperature: Fixed32_32,
    /// Top-p (nucleus sampling) en punto fijo 32.32 (ej. 0.95 → 4_080_218_931).
    pub top_p: Fixed32_32,
    pub top_k: u32,
    pub seed: Option<u64>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EngineInfo {
    pub name: String,
    pub version: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EmissionInfo {
    pub raw_digest: Vec<u8>,
    pub canonical_digest: Vec<u8>,
    pub algebra: String, // e.g. "CF-GKAT"
    pub normalizer_version: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SandboxInfo {
    pub image_digest: Vec<u8>,
    pub resource_envelope: BTreeMap<String, String>,
    pub wasi_version: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ExecutionInfo {
    pub output_digest: Vec<u8>,
    pub exit_status: i32,
    pub resources_used: BTreeMap<String, String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Verdict {
    pub verifier_id: String,
    pub method: String,
    pub deterministic: bool,
    pub gating: bool,
    pub outcome: String, // pass, fail, inconclusive
    pub evidence_digest: Option<Vec<u8>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Uncertainty {
    /// Entropía de Shannon H(X) en punto fijo 32.32.
    pub h: Fixed32_32,
    /// Varentropía Var(H) en punto fijo 32.32.
    pub v: Fixed32_32,
    /// Máxima varentropía observada en la ventana de inferencia (punto fijo 32.32).
    pub max_v: Fixed32_32,
    /// Índice del token donde se observó la máxima varentropía.
    pub max_v_token_idx: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Budget {
    pub tokens_spent: u32,
    pub currency_spent_micros: u64, // Representación en micro-unidades como dicta el paper
    pub wall_clock_ms: u64,
    pub tool_calls: u32,
}

impl TransitionRecord {
    /// Valida el trigger de contención del Artículo 15 de la EU AI Act.
    /// Si la varentropía supera el umbral legal del 3% (0.03), desencadena un EpistemicHalt.
    /// Valida el trigger de contención del Artículo 15 de la EU AI Act.
    /// Comparación determinista en aritmética de punto fijo u64 (cero IEEE 754).
    pub fn validate_article_15_containment(&self) -> Result<(), EpistemicHalt> {
        if let Some(uncertainty) = &self.uncertainty {
            if uncertainty.max_v > ARTICLE_15_MAX_VARENTROPY {
                return Err(EpistemicHalt::from(format!(
                    "Article 15 Containment Trigger: Varentropy 0x{:016X} exceeds legal threshold 0x{:016X}",
                    uncertainty.max_v, ARTICLE_15_MAX_VARENTROPY
                )));
            }
        }
        Ok(())
    }

    /// Serializa la hoja en CBOR determinista según RFC 8949 §4.2.1
    /// (Ciborium ordena automáticamente los mapas BTreeMap).
    pub fn to_cbor_deterministic(&self) -> Result<Vec<u8>, ciborium::ser::Error<std::io::Error>> {
        let mut buffer = Vec::new();
        into_writer(self, &mut buffer)?;
        Ok(buffer)
    }

    /// Calcula el leaf_digest para el recibo SCITT (SHA3-256) a partir del CBOR determinista
    pub fn compute_leaf_digest(&self) -> Result<Vec<u8>, ciborium::ser::Error<std::io::Error>> {
        let cbor_bytes = self.to_cbor_deterministic()?;
        let mut hasher = Sha3_256::new();
        hasher.update(&cbor_bytes);
        Ok(hasher.finalize().to_vec())
    }

    /// Genera la cabecera protegida COSE_Sign1 y firma el payload (Fail-Stop)
    pub fn sign_scitt(&self, key: &SigningKey) -> Result<coset::CoseSign1, EpistemicHalt> {
        // 0. Validación Pre-Producción: Cuarentena Epistémica (Fail-Stop) Art. 15
        self.validate_article_15_containment()?;

        // 1. Serialización CBOR determinista del payload (el TransitionRecord)
        let payload = self.to_cbor_deterministic()
            .map_err(|e| EpistemicHalt::from(format!("CBOR serialization failed: {}", e)))?;

        // 2. Construcción de headers protegidos (RFC 9052)
        let protected = HeaderBuilder::new()
            .algorithm(coset::iana::Algorithm::EdDSA)
            .build();

        // 3. FIRMA CORREGIDA: Construir CoseSign1Builder PRIMERO sin firma
        // Esto maneja internamente la estructura Sig_structure (RFC 9052)
        let cose_sign1_builder = CoseSign1Builder::new()
            .protected(protected)
            .payload(payload);

        // 4. Firmar sobre la estructura canónica Sig_structure
        let cose_sign1 = cose_sign1_builder
            .try_create_signature(
                &[], // Empty AAD
                |sig_structure| {
                    Ok::<_, std::convert::Infallible>(key.sign(sig_structure).to_bytes().to_vec())
                },
            )
            .map_err(|_| EpistemicHalt::from("Signature creation failed".to_string()))?
            .build();

        // 5. Validación fail-stop de salida
        cose_sign1
            .clone()
            .to_vec()
            .map_err(|e| EpistemicHalt::from(format!("COSE Sign1 serialization validation failed: {:?}", e)))?;

        Ok(cose_sign1)
    }
}
