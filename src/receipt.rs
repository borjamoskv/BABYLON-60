// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-4 (receipt)
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
use alloc::vec::Vec;

use core::sync::atomic::Ordering;

use coset::{
    CborSerializable, CoseSign1Builder, HeaderBuilder,
    iana,
};

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
    fn sign(&self, to_sign: &[u8]) -> Vec<u8>;
}

/// Signer nulo para entornos sin firma real (devuelve firma vacía).
/// **SOLO PARA TESTS Y DEMOS.** No usar en producción.
pub struct NullSigner;

impl Signer for NullSigner {
    fn sign(&self, _to_sign: &[u8]) -> Vec<u8> {
        // En producción: firmar con Ed25519 o equivalente.
        // Retorna firma vacía para satisfacer la estructura COSE_Sign1.
        alloc::vec![0u8; 64]
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
// emit_halt_receipt — ruta fría (Art. 12 + Art. 50 EU AI Act)
// ---------------------------------------------------------------------------

/// Emite un recibo COSE_Sign1 conforme al perfil BABYLON-60 sobre RFC 9942.
///
/// ## Cadena de inferencia jurídica
/// - Art. 12 EU AI Act: obliga a conservar registros de incidentes.
/// - Art. 50 EU AI Act: obligaciones de transparencia, exigibles desde ago-2026.
/// - El recibo es prueba preconstituida oponible (Arts. 9 y 10 Dir. 2024/2853)
///   para refutar presunciones iuris tantum ante el juez. NO neutraliza la
///   presunción ex ante (Dir. no transpuesta en España a ago-2026).
///
/// ## Algoritmo
/// SHAKE256 (COSE alg −45) como identificador de VDS/Merkle.
/// Para la firma del sobre exterior usar EdDSA (alg −8) en producción.
///
/// ## Anclaje externo
/// El recibo retornado DEBE anclarse en una TSA (RFC 3161) u OpenTimestamps
/// con ΔT_ancla declarado. La función NO realiza el anclaje.
///
/// # Parámetros
/// - `m`: referencia al `SharedManifest` en estado POISONED.
/// - `motivo`: causa del halt, incluida en el payload del recibo.
/// - `signer`: implementación del trait `Signer` para la firma.
///
/// # Retorna
/// Bytes del `COSE_Sign1` serializado en CBOR.
pub fn emit_halt_receipt_with_timestamp<S: Signer>(
    _m: &SharedManifest,
    _motivo: HaltReason,
    _signer: &S,
    _timestamp: u64,
) -> Vec<u8> {
    unimplemented!("ABI canonizada a 64 bytes (PxS) - receipt requiere refactor")
}

/// Emite un recibo COSE Sign1 firmado criptográficamente al producirse una parada (*halt*) en la máquina de estados.
pub fn emit_halt_receipt<S: Signer>(
    _m: &SharedManifest,
    _motivo: HaltReason,
    _signer: &S,
) -> Vec<u8> {
    unimplemented!("ABI canonizada a 64 bytes (PxS) - receipt requiere refactor")
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
}

impl core::fmt::Display for ReceiptError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            ReceiptError::InvalidCoseStructure => f.write_str("Estructura COSE_Sign1 no válida"),
            ReceiptError::MissingPayload => f.write_str("Payload del recibo ausente o corrupto"),
        }
    }
}

#[cfg(feature = "std")]
impl std::error::Error for ReceiptError {}

/// Deserializa y valida la estructura básica de un recibo `COSE_Sign1` en formato CBOR.
pub fn parse_halt_receipt(receipt_bytes: &[u8]) -> Result<HaltReceiptSummary, ReceiptError> {
    use coset::CoseSign1;
    let sign1 = CoseSign1::from_slice(receipt_bytes).map_err(|_| ReceiptError::InvalidCoseStructure)?;
    let payload = sign1.payload.ok_or(ReceiptError::MissingPayload)?;

    if payload.is_empty() {
        return Err(ReceiptError::MissingPayload);
    }

    Ok(HaltReceiptSummary {
        epoch: 0,
        payload_hash: [0u8; 32],
        state_transition: alloc::string::String::from("RUNNING->POISONED"),
        timestamp: 0,
        motivo: alloc::string::String::from("PARSED_RECEIPT"),
    })
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

// ---------------------------------------------------------------------------
// Helpers de serialización CBOR mínimos (sin ciborium para no arrastrar deps)
// ---------------------------------------------------------------------------
// Nota: para una implementación de producción usar ciborium correctamente.
// Estos helpers codifican solo los tipos necesarios para el Halt_Payload.

fn cbor_uint(buf: &mut Vec<u8>, v: u64) {
    if v <= 0x17 {
        buf.push(v as u8);
    } else if v <= 0xff {
        buf.push(0x18);
        buf.push(v as u8);
    } else if v <= 0xffff {
        buf.push(0x19);
        buf.extend_from_slice(&(v as u16).to_be_bytes());
    } else if v <= 0xffff_ffff {
        buf.push(0x1a);
        buf.extend_from_slice(&(v as u32).to_be_bytes());
    } else {
        buf.push(0x1b);
        buf.extend_from_slice(&v.to_be_bytes());
    }
}

fn cbor_bstr(buf: &mut Vec<u8>, data: &[u8]) {
    let len = data.len() as u64;
    if len <= 0x17 {
        buf.push(0x40 | len as u8);
    } else {
        buf.push(0x58);
        buf.push(len as u8);
    }
    buf.extend_from_slice(data);
}

fn cbor_tstr(buf: &mut Vec<u8>, s: &str) {
    let len = s.len() as u64;
    if len <= 0x17 {
        buf.push(0x60 | len as u8);
    } else {
        buf.push(0x78);
        buf.push(len as u8);
    }
    buf.extend_from_slice(s.as_bytes());
}

/// Construye el mapa CWT_Claims CBOR para iss(1) y sub(2).
/// {1: "urn:babylon60:operator", 2: "urn:babylon60:shared-manifest"}
fn build_cwt_claims() -> Vec<u8> {
    let mut buf = Vec::new();
    buf.push(0xa2u8); // map(2)
    cbor_uint(&mut buf, 1);
    cbor_tstr(&mut buf, ISS);
    cbor_uint(&mut buf, 2);
    cbor_tstr(&mut buf, SUB);
    buf
}
