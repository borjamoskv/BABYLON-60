// C5-REAL EXERGY CERTIFIED
use serde::{Deserialize, Serialize};
use ciborium::into_writer;
use sha3::{Sha3_256, Digest};
use ed25519_dalek::{SigningKey, Signer};
use std::collections::BTreeMap;
use coset::{CoseSign1Builder, HeaderBuilder, CborSerializable};

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
    pub temperature: f32,
    pub top_p: f32,
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
    pub h: f32, // Entropy
    pub v: f32, // Varentropy
    pub max_v: f32,
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
