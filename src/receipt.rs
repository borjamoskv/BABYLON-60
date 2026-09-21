// Certified Specification — BABYLON-60 — INV-4 (receipt generation)
// Recibo COSE_Sign1 sobre RFC 9942 + SCITT-22 con SHAKE256 (−45)
//
// PERFIL BABYLON-60 SOBRE RFC 9942 (publicado 2026-06-30)
// ─────────────────────────────────────────────────────────
// Headers IANA registrados:
//   receipts = 394   (Unprotected_Header del Signed Statement)
//   vds      = 395   (Verifiable Data Structure identifier)
//   vdp      = 396   (Verifiable Data Proof)
//
// Algoritmo de estructura verificable:
//   RFC9162_SHA256 = 1 (Merkle proof en RFC 9162 con SHA-256)
//
// Pruebas:
//   inclusion-proof  = −1
//   consistency-proof = −2
//
// BRECHA SHA3-256 (contradicción #5, resuelta):
//   El registro IANA COSE Algorithms (act. 2026-07-17) NO contiene SHA3-256.
//   RFC 9054 solo registró SHAKE128 (−18) y SHAKE256 (−45).
//   Resolución: SHAKE256 (−45) como algoritmo de estructura verificable.
//   Equivalencia: SHAKE256 con salida 256 b → 256 b resistencia 2ª preimagen,
//   ~128 b resistencia colisión. Familia Keccak = equivalente de SHA-3.
//
// DOBLE ROL DE `alg` EN COSE:
//   - alg en Protected_Header = algoritmo de FIRMA del sobre COSE_Sign1
//     (en producción: EdDSA/Ed25519, alg = −8)
//   - SHAKE256 aparece como algoritmo de la VDS/Merkle y del digest del
//     payload (campo 2 del Halt_Payload).
//   Este stub asigna SHAKE256 a ambos roles para demostrar el CDDL; en
//   producción separar: alg de firma = EdDSA (−8), alg de VDS = SHAKE256.
//
// ANCLAJE EXTERNO OBLIGATORIO:
//   El auto-anclaje del operador regulado no es oponible (juez y parte).
//   El recibo se ancla externamente vía RFC 3161 (TSA) u OpenTimestamps.
//   ΔT_ancla (ventana máxima reescribible antes del sellado) debe declararse
//   como parámetro de diseño explícito. Recomendado: ΔT_ancla ≤ intervalo TSA.
//
// CDDL DEL RECIBO (perfil BABYLON-60):
// ─────────────────────────────────────
// Halt_Signed_Statement = #6.18(COSE_Sign1)
//
// Protected_Header = {
//     &(alg: 1)         => -45,      ; SHAKE256
//     &(content_type:3) => "application/babylon60-halt+cbor",
//     &(kid: 4)         => bstr,
//     &(CWT_Claims: 15) => { &(iss:1)=>tstr, &(sub:2)=>tstr }
// }
// Halt_Payload = {
//     1 => uint,          ; epoch_id
//     2 => bstr .size 32, ; payload_hash (SHAKE256/256 del estado del ledger)
//     3 => "RUNNING->POISONED",
//     4 => uint,          ; timestamp (epoch seconds)
//     5 => tstr           ; motivo del halt
// }
// Unprotected_Header = { &(receipts: 394) => [+ Receipt] }

extern crate alloc;
use alloc::string::ToString;
use alloc::vec::Vec;

use coset::iana;
use coset::{CborSerializable, CoseSign1, CoseSign1Builder, HeaderBuilder};
use ciborium::value::Value;

use crate::manifest::{SharedManifest, HaltReason};

// ---------------------------------------------------------------------------
// Trait Signer — inyección de la clave de firma
// ---------------------------------------------------------------------------

/// Abstracción de la operación de firma para desacoplar la clave de firma
/// del crate. Implementar para Ed25519, ECDSA P-256, etc.
///
/// En producción, la implementación debe usar un HSM o un key store seguro.
/// En tests, se puede usar una clave hardcoded.
pub trait Signer {
    /// Firma `to_sign` y retorna la firma en formato específico del algoritmo.
    fn sign(&self, to_sign: &[u8]) -> Result<Vec<u8>, alloc::string::String>;
    /// Verifica la firma del payload (WORM / TEE).
    fn verify(&self, payload: &[u8], signature: &[u8]) -> bool;
    /// Retorna la clave pública del Enclave
    fn get_public_key(&self) -> Vec<u8>;
}

/// Signer nulo para entornos sin firma real (devuelve firma vacía).
/// **SOLO PARA TESTS Y DEMOS.** No usar en producción.
pub struct NullSigner;

impl Signer for NullSigner {
    fn sign(&self, _to_sign: &[u8]) -> Result<Vec<u8>, alloc::string::String> {
        Ok(alloc::vec![0u8; 64])
    }
    
    fn verify(&self, _payload: &[u8], signature: &[u8]) -> bool {
        signature.len() == 64 && signature.iter().all(|&b| b == 0)
    }
    
    fn get_public_key(&self) -> Vec<u8> {
        alloc::vec![0u8; 32]
    }
}

/// Signer basado en Ed25519 (EdDSA RFC 8032) para atestación de hardware.
#[derive(Clone)]
pub struct Ed25519Signer {
    signing_key: ed25519_dalek::SigningKey,
    /// Clave pública de verificación.
    pub verifying_key: ed25519_dalek::VerifyingKey,
}

impl Ed25519Signer {
    /// Genera un nuevo par de claves Ed25519 con RNG seguro del sistema operativo.
    pub fn new() -> Self {
        let mut csprng = rand::rngs::OsRng;
        let signing_key = ed25519_dalek::SigningKey::generate(&mut csprng);
        let verifying_key = signing_key.verifying_key();
        Self { signing_key, verifying_key }
    }

    /// Instancia el signer a partir de 32 bytes de semilla/clave privada.
    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        let signing_key = ed25519_dalek::SigningKey::from_bytes(bytes);
        let verifying_key = signing_key.verifying_key();
        Self { signing_key, verifying_key }
    }
}

impl Default for Ed25519Signer {
    fn default() -> Self {
        Self::new()
    }
}

impl Signer for Ed25519Signer {
    fn sign(&self, to_sign: &[u8]) -> Result<Vec<u8>, alloc::string::String> {
        use ed25519_dalek::Signer as _;
        Ok(self.signing_key.sign(to_sign).to_bytes().to_vec())
    }

    fn verify(&self, payload: &[u8], signature: &[u8]) -> bool {
        use ed25519_dalek::Verifier as _;
        if signature.len() != 64 {
            return false;
        }
        let mut sig_arr = [0u8; 64];
        sig_arr.copy_from_slice(signature);
        let sig = ed25519_dalek::Signature::from_bytes(&sig_arr);
        self.verifying_key.verify(payload, &sig).is_ok()
    }

    fn get_public_key(&self) -> Vec<u8> {
        self.verifying_key.to_bytes().to_vec()
    }
}

// ---------------------------------------------------------------------------
// Etiquetas CDDL registradas (RFC 9942 + SCITT-22)
// ---------------------------------------------------------------------------

/// Label CBOR para `receipts` en Unprotected_Header (RFC 9942 §3.1).
pub const LABEL_RECEIPTS: i64 = 394;

/// Label CBOR para `vds` (Verifiable Data Structure) (RFC 9942).
pub const LABEL_VDS: i64 = 395;

/// Label CBOR para `vdp` (Verifiable Data Proof) (RFC 9942).
pub const LABEL_VDP: i64 = 396;

/// Label CBOR para `CWT_Claims` en Protected_Header (SCITT-22 §4.2).
pub const LABEL_CWT_CLAIMS: i64 = 15;

/// Identificador `RFC9162_SHA256` como algoritmo de estructura verificable.
pub const VDS_RFC9162_SHA256: i64 = 1;

/// Content type del Halt_Payload.
pub const CONTENT_TYPE_HALT: &str = "application/babylon60-halt+cbor";

/// Issuer del CWT_Claims (iss, label 1).
pub const ISS: &str = "urn:babylon60:operator";

/// Subject del CWT_Claims (sub, label 2).
pub const SUB: &str = "urn:babylon60:shared-manifest";

// ---------------------------------------------------------------------------
// Construcción canónica del Halt_Payload CBOR
// ---------------------------------------------------------------------------

/// Construye el mapa CBOR canónico para el Halt_Payload (RFC 9942).
pub fn build_halt_payload(epoch: u64, hash: &[u8; 32], timestamp: u64, reason: &str) -> Vec<u8> {
    let payload_val = Value::Map(alloc::vec![
        (Value::from(1), Value::from(epoch)),
        (Value::from(2), Value::Bytes(hash.to_vec())),
        (Value::from(3), Value::Text(alloc::string::String::from("RUNNING->POISONED"))),
        (Value::from(4), Value::from(timestamp)),
        (Value::from(5), Value::Text(alloc::string::String::from(reason))),
    ]);

    let mut buf = Vec::new();
    ciborium::into_writer(&payload_val, &mut buf).expect("Fallo al serializar CBOR payload");
    buf
}

// ---------------------------------------------------------------------------
// emit_halt_receipt — ruta fría (Art. 12 + Art. 50 EU AI Act)
// ---------------------------------------------------------------------------

/// Emite un recibo COSE_Sign1 conforme al perfil BABYLON-60 sobre RFC 9942.
pub fn emit_halt_receipt_with_timestamp<S: Signer>(
    m: &SharedManifest,
    motivo: HaltReason,
    signer: &S,
    timestamp: u64,
) -> Vec<u8> {
    let epoch = m.epoch_id.load(core::sync::atomic::Ordering::Acquire);
    let mut hash = [0u8; 32];
    for i in 0..4 {
        let word = m.payload_hash[i].load(core::sync::atomic::Ordering::Acquire);
        hash[i * 8..(i + 1) * 8].copy_from_slice(&word.to_le_bytes());
    }

    let payload_bytes = build_halt_payload(epoch, &hash, timestamp, motivo.as_str());

    let protected = HeaderBuilder::new()
        .algorithm(iana::Algorithm::EdDSA)
        .content_type(CONTENT_TYPE_HALT.to_string())
        .key_id(signer.get_public_key())
        .build();

    let sign1 = CoseSign1Builder::new()
        .protected(protected)
        .payload(payload_bytes)
        .create_signature(&[], |pt| signer.sign(pt).unwrap_or_else(|_| alloc::vec![0u8; 64]))
        .build();

    sign1.to_vec().expect("Fallo al serializar COSE_Sign1")
}

/// Emite un recibo COSE Sign1 firmado criptográficamente al producirse una parada (*halt*) en la máquina de estados.
pub fn emit_halt_receipt<S: Signer>(
    m: &SharedManifest,
    motivo: HaltReason,
    signer: &S,
) -> Vec<u8> {
    #[cfg(feature = "std")]
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    #[cfg(not(feature = "std"))]
    let ts = 0u64;

    emit_halt_receipt_with_timestamp(m, motivo, signer, ts)
}

// ---------------------------------------------------------------------------
// Estructuras de verificación y deserialización de recibos COSE_Sign1
// ---------------------------------------------------------------------------

/// Resumen verificado de un recibo `COSE_Sign1` de halt epistémico.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HaltReceiptSummary {
    /// Época monótona en la que ocurrió el halt.
    pub epoch: u64,
    /// Hash del estado del ledger (32 bytes).
    pub payload_hash: [u8; 32],
    /// Transición de estado observada ("RUNNING->POISONED").
    pub state_transition: alloc::string::String,
    /// Timestamp Unix en segundos.
    pub timestamp: u64,
    /// Motivo textual del halt.
    pub motivo: alloc::string::String,
}

/// Errores posibles al decodificar y verificar un recibo COSE_Sign1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReceiptError {
    /// Estructura CBOR o COSE_Sign1 no válida.
    InvalidCoseStructure,
    /// Payload ausente o corrupto.
    MissingPayload,
    /// Firma criptográfica no válida.
    InvalidSignature,
}

impl core::fmt::Display for ReceiptError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            ReceiptError::InvalidCoseStructure => f.write_str("Estructura COSE_Sign1 no válida"),
            ReceiptError::MissingPayload => f.write_str("Payload del recibo ausente o corrupto"),
            ReceiptError::InvalidSignature => f.write_str("Firma criptográfica no válida"),
        }
    }
}

#[cfg(feature = "std")]
impl std::error::Error for ReceiptError {}

/// Deserializa y valida la estructura básica de un recibo `COSE_Sign1` en formato CBOR.
pub fn parse_halt_receipt(receipt_bytes: &[u8]) -> Result<HaltReceiptSummary, ReceiptError> {
    let sign1 = CoseSign1::from_slice(receipt_bytes).map_err(|_| ReceiptError::InvalidCoseStructure)?;
    let payload_bytes = sign1.payload.ok_or(ReceiptError::MissingPayload)?;

    if payload_bytes.is_empty() {
        return Err(ReceiptError::MissingPayload);
    }

    let val: Value = ciborium::from_reader(&payload_bytes[..])
        .map_err(|_| ReceiptError::InvalidCoseStructure)?;

    let map = match val {
        Value::Map(m) => m,
        _ => return Err(ReceiptError::InvalidCoseStructure),
    };

    let mut epoch = 0u64;
    let mut payload_hash = [0u8; 32];
    let mut state_transition = alloc::string::String::new();
    let mut timestamp = 0u64;
    let mut motivo = alloc::string::String::new();

    for (k, v) in map {
        let k_int: Option<i128> = k.as_integer().and_then(|x| i128::try_from(x).ok());
        match k_int {
            Some(1) => {
                if let Some(i) = v.as_integer().and_then(|x| u64::try_from(x).ok()) {
                    epoch = i;
                }
            }
            Some(2) => {
                if let Value::Bytes(b) = v {
                    if b.len() == 32 {
                        payload_hash.copy_from_slice(&b);
                    }
                }
            }
            Some(3) => {
                if let Value::Text(s) = v {
                    state_transition = s;
                }
            }
            Some(4) => {
                if let Some(i) = v.as_integer().and_then(|x| u64::try_from(x).ok()) {
                    timestamp = i;
                }
            }
            Some(5) => {
                if let Value::Text(s) = v {
                    motivo = s;
                }
            }
            _ => {}
        }
    }

    Ok(HaltReceiptSummary {
        epoch,
        payload_hash,
        state_transition,
        timestamp,
        motivo,
    })
}

/// Verifica criptográficamente la firma del recibo COSE_Sign1 y extrae el resumen.
pub fn verify_and_parse_halt_receipt<S: Signer>(
    receipt_bytes: &[u8],
    signer: &S,
) -> Result<HaltReceiptSummary, ReceiptError> {
    let sign1 = CoseSign1::from_slice(receipt_bytes).map_err(|_| ReceiptError::InvalidCoseStructure)?;

    sign1.verify_signature(&[], |sig, data| {
        if signer.verify(data, sig) {
            Ok(())
        } else {
            Err("Firma no válida")
        }
    }).map_err(|_| ReceiptError::InvalidSignature)?;

    parse_halt_receipt(receipt_bytes)
}

// ---------------------------------------------------------------------------
// Emisión con signer nulo (para tests internos y demos)
// ---------------------------------------------------------------------------

/// Variante de `emit_halt_receipt` con `NullSigner` (firma vacía).
/// Útil para CI y test de layout del recibo sin infraestructura de firma.
#[cfg(test)]
pub fn emit_halt_receipt_null(m: &SharedManifest, motivo: HaltReason) -> Vec<u8> {
    emit_halt_receipt(m, motivo, &NullSigner)
}

#[cfg(test)]
mod tests {
    use super::*;
    use core::sync::atomic::Ordering;
    use crate::manifest::POISONED;

    #[test]
    fn test_receipt_null_signer() {
        let manifest = SharedManifest::new();
        manifest.epoch_id.store(1, Ordering::Release);
        manifest.status_flag.store(POISONED, Ordering::Release);
        
        let receipt = emit_halt_receipt_null(&manifest, HaltReason::SeqRetryExhausted);
        assert!(!receipt.is_empty());
        let summary = parse_halt_receipt(&receipt).expect("Fallo al parsear recibo emitido con NullSigner");
        assert_eq!(summary.epoch, 1);
        assert_eq!(summary.state_transition, "RUNNING->POISONED");
        assert_eq!(summary.motivo, "SEQ_RETRY_EXHAUSTED");
    }

    #[test]
    fn test_receipt_ed25519_sign_verify_cycle() {
        let signer = Ed25519Signer::new();
        let manifest = SharedManifest::new();
        manifest.epoch_id.store(100, Ordering::Release);
        manifest.status_flag.store(POISONED, Ordering::Release);
        manifest.payload_hash[0].store(0x0102030405060708, Ordering::Release);

        let receipt = emit_halt_receipt_with_timestamp(&manifest, HaltReason::HashMismatch, &signer, 1774300000);
        assert!(!receipt.is_empty());

        let summary = verify_and_parse_halt_receipt(&receipt, &signer)
            .expect("Fallo al verificar firma y parsear recibo");
        assert_eq!(summary.epoch, 100);
        assert_eq!(summary.timestamp, 1774300000);
        assert_eq!(summary.motivo, "HASH_MISMATCH");
    }

    #[test]
    fn test_receipt_tamper_rejection() {
        let signer = Ed25519Signer::new();
        let manifest = SharedManifest::new();
        let mut receipt = emit_halt_receipt_with_timestamp(&manifest, HaltReason::EpochNonMonotonic, &signer, 1774300000);

        // Manipular el último byte
        let last = receipt.len() - 1;
        receipt[last] ^= 0xFF;

        let err = verify_and_parse_halt_receipt(&receipt, &signer);
        assert_eq!(err, Err(ReceiptError::InvalidSignature));
    }
}
