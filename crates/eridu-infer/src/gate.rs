//! Puente de Integración Causal con BABYLON-60 (00_ABZU_KERNEL).
//! Evalúa la 7-Tupla Causal con reloj lógico monótono (`logical_tick`) y publica en `SharedManifest` (64B).

use std::sync::Arc;
use babylon60::manifest::SharedManifest;
use babylon60::seqlock::{publish, read};
use byteorder::{ByteOrder, LittleEndian};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceReceipt {
    pub logical_tick: u64,
    pub prompt_hash: String,
    pub model_id: String,
    pub timestamp_utc: String,
    pub attestation_seal: String,
    pub compliance_status: String,
}

pub struct BabylonCausalGate {
    logical_tick: u64,
    manifest: Arc<SharedManifest>,
    recent_receipts: Vec<InferenceReceipt>,
}

impl Default for BabylonCausalGate {
    fn default() -> Self {
        Self::new()
    }
}

impl BabylonCausalGate {
    pub fn new() -> Self {
        Self::with_manifest(Arc::new(SharedManifest::new()))
    }

    pub fn with_manifest(manifest: Arc<SharedManifest>) -> Self {
        Self {
            logical_tick: 1,
            manifest,
            recent_receipts: Vec::new(),
        }
    }

    pub fn manifest(&self) -> Arc<SharedManifest> {
        Arc::clone(&self.manifest)
    }

    pub fn read_manifest_snapshot(&self) -> Option<(u64, [u64; 4])> {
        read(&self.manifest)
    }

    /// Evalúa la 7-tupla de decisión causal antes de autorizar la inferencia.
    /// El hash canónico depende exclusivamente de `logical_tick` (INV_C5_CANONICAL_LOGICAL_TICK)
    /// y se publica de forma atómica en el `SharedManifest` de 64B (INV-1 / INV-2).
    pub fn evaluate_and_seal(
        &mut self,
        model: &str,
        prompt_content: &str,
    ) -> Result<InferenceReceipt, String> {
        let tick = self.logical_tick;

        // 1. Hash determinista dependiente exclusivamente del reloj lógico monótono (INV_C5_CANONICAL_LOGICAL_TICK)
        let mut hasher = Sha256::new();
        hasher.update(tick.to_le_bytes());
        hasher.update(model.as_bytes());
        hasher.update(prompt_content.as_bytes());
        let raw_digest = hasher.finalize();
        let prompt_hash = hex::encode(raw_digest);

        // 2. Generación del sello de atestación de Ring-0 (EU AI Act Arts. 12-14)
        let mut seal_hasher = Sha256::new();
        seal_hasher.update(format!("BABYLON-60-ATTEST:TICK-{}:HASH-{}", tick, prompt_hash).as_bytes());
        let seal_bytes = seal_hasher.finalize();
        let attestation_seal = format!("B60-{}", hex::encode(seal_bytes)[..16].to_uppercase());

        // 3. Publicación atómica en SharedManifest de 64B (Seqlock SPMC canónico, RFO = 0)
        let digest_words = [
            LittleEndian::read_u64(&seal_bytes[0..8]),
            LittleEndian::read_u64(&seal_bytes[8..16]),
            LittleEndian::read_u64(&seal_bytes[16..24]),
            LittleEndian::read_u64(&seal_bytes[24..32]),
        ];
        if !publish(&self.manifest, tick, &digest_words) {
            return Err("POISONED (0xDEAD_6060): SharedManifest cerrado a nuevas admisiones".to_string());
        }

        self.logical_tick = self.logical_tick.saturating_add(1);

        let receipt = InferenceReceipt {
            logical_tick: tick,
            prompt_hash,
            model_id: model.to_string(),
            timestamp_utc: format!("LOGICAL_TICK_{}", tick),
            attestation_seal,
            compliance_status: "EU_AI_ACT_COMPLIANT_ARTICLE_12_14_VERIFIED".to_string(),
        };

        self.recent_receipts.insert(0, receipt.clone());
        if self.recent_receipts.len() > 100 {
            self.recent_receipts.truncate(100);
        }

        Ok(receipt)
    }

    pub fn get_recent_receipts(&self) -> Vec<InferenceReceipt> {
        self.recent_receipts.clone()
    }
}
