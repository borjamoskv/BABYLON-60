//! Preimágenes canónicas del recibo, idénticas byte a byte a las de `src/crypto/canonical.ts`.
//!
//! ```text
//! NODO       = ["BABYLON60_EXEC_NODE_V1", node_id, [padres ordenados por bytes], state_status,
//!               smt_verified (0|1), reduction_steps, [] | [violation_reason]]
//! state_hash = merkle_b3::leaf_hash(NODO)
//! raíz       = merkle_b3::build_root(NODOS ordenados por los bytes de node_id)
//!
//! MANIFIESTO = ["BABYLON60_EXEC_MANIFEST_V1", execution_id, manifest_version, policy_epoch,
//!               logical_tick, seq_id, agent_id, policy_profile, payload_raw]
//!
//! SOBRE      = ["BABYLON60_EXEC_RECEIPT_V1", execution_id, policy_epoch, logical_tick, seq_id,
//!               h'manifest_hash', raíz, h'trace_hash', heuristic_weight, lean.status,
//!               lean.theorem_ident, lean.sorry_count, memory_bytes, h'prev_receipt_hash',
//!               h'worm_txid']
//!
//! A_FIRMAR   = ["Signature1", h'a10127', h'', SOBRE]   (Sig_structure de COSE_Sign1)
//! ```

use crate::cbor::{array, bytes, text, uint};
use crate::merkle_b3;

/// Etiqueta de dominio de la preimagen de nodo.
pub const NODE_DOMAIN: &str = "BABYLON60_EXEC_NODE_V1";
/// Etiqueta de dominio de la preimagen del manifiesto de entrada.
pub const MANIFEST_DOMAIN: &str = "BABYLON60_EXEC_MANIFEST_V1";
/// Etiqueta de dominio del sobre firmado.
pub const RECEIPT_DOMAIN: &str = "BABYLON60_EXEC_RECEIPT_V1";
/// Cabecera protegida COSE del perfil ACS para Ed25519: el mapa {1 (alg): -8 (EdDSA)}.
pub const COSE_PROTECTED_ED25519: [u8; 3] = [0xa1, 0x01, 0x27];

/// Campos de un nodo del DAG (todo salvo `state_hash`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NodeFields {
    /// Identificador canónico `EV_{tick:08}_{seq:06}`.
    pub node_id: String,
    /// Padres causales (el orden de llegada no afecta al hash).
    pub parent_ids: Vec<String>,
    /// Estado declarado del paso.
    pub state_status: String,
    /// Si el paso pasó la comprobación SMT.
    pub smt_verified: bool,
    /// Pasos de reducción (gas lógico).
    pub reduction_steps: u64,
    /// Motivo de la violación, si el paso se detuvo.
    pub violation_reason: Option<String>,
}

/// Reloj lógico causal.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CausalClock {
    /// Época de política.
    pub policy_epoch: u64,
    /// Tick lógico.
    pub logical_tick: u64,
    /// Número de secuencia.
    pub seq_id: u64,
}

/// Manifiesto de entrada.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ingress {
    /// Agente que origina la ejecución.
    pub agent_id: String,
    /// Perfil de política.
    pub policy_profile: String,
    /// Carga útil tal como llegó.
    pub payload_raw: String,
}

/// Commit LARSA declarado por el emisor.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LarsaCommit {
    /// Hash de la traza asociada al testigo formal.
    pub trace_hash: [u8; 32],
    /// Peso heurístico acumulado (u32 en el kernel).
    pub heuristic_weight: u32,
}

/// Constancia Lean 4 declarada por el emisor.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Lean4Proof {
    /// Estado declarado.
    pub status: String,
    /// Identificador del teorema.
    pub theorem_ident: String,
    /// Número de `sorry` declarado.
    pub sorry_count: u64,
}

/// Métricas de auditoría declaradas por el emisor.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AuditMetrics {
    /// Memoria usada, en bytes.
    pub memory_bytes: u64,
    /// `receipt_hash` del recibo anterior.
    pub prev_receipt_hash: [u8; 32],
    /// Identificador de la transacción WORM.
    pub worm_txid: [u8; 32],
}

/// Campos que cubre el sobre firmado (los hashes, tal como los declara el recibo).
#[derive(Debug, Clone, Copy)]
pub struct EnvelopeFields<'a> {
    /// Identificador de la ejecución.
    pub execution_id: &'a str,
    /// Reloj lógico.
    pub clock: CausalClock,
    /// Compromiso de fase 1.
    pub phase_one_manifest_hash: [u8; 32],
    /// Raíz Merkle v1 (`b3:…`).
    pub phase_two_merkle_root: &'a str,
    /// Commit LARSA declarado.
    pub larsa: LarsaCommit,
    /// Constancia Lean 4 declarada.
    pub lean: &'a Lean4Proof,
    /// Métricas de auditoría.
    pub audit: AuditMetrics,
}

/// Preimagen CBOR de un nodo.
pub fn node_preimage(n: &NodeFields) -> Vec<u8> {
    let mut parents: Vec<&str> = n.parent_ids.iter().map(String::as_str).collect();
    parents.sort_unstable(); // orden de `str` = orden por bytes UTF-8
    let reason = match &n.violation_reason {
        None => array(vec![]),
        Some(r) => array(vec![text(r)]),
    };
    array(vec![
        text(NODE_DOMAIN),
        text(&n.node_id),
        array(parents.into_iter().map(text).collect()),
        text(&n.state_status),
        uint(u64::from(n.smt_verified)),
        uint(n.reduction_steps),
        reason,
    ])
}

/// Hash de hoja Merkle v1 del nodo (`state_hash`).
pub fn node_leaf_hash(n: &NodeFields) -> [u8; 32] {
    merkle_b3::leaf_hash(&node_preimage(n))
}

/// Raíz Merkle v1 del DAG con las hojas ordenadas por los bytes de `node_id`.
/// Error `EMPTY_TREE` si no hay nodos, igual que el kernel.
pub fn dag_merkle_root(nodes: &[&NodeFields]) -> Result<String, String> {
    let mut ordered: Vec<&NodeFields> = nodes.to_vec();
    ordered.sort_by(|a, b| a.node_id.as_bytes().cmp(b.node_id.as_bytes()));
    let leaves: Vec<Vec<u8>> = ordered.into_iter().map(node_preimage).collect();
    merkle_b3::build_root(&leaves)
}

/// Preimagen CBOR del manifiesto de entrada.
pub fn manifest_preimage(
    execution_id: &str,
    manifest_version: &str,
    clock: &CausalClock,
    ingress: &Ingress,
) -> Vec<u8> {
    array(vec![
        text(MANIFEST_DOMAIN),
        text(execution_id),
        text(manifest_version),
        uint(clock.policy_epoch),
        uint(clock.logical_tick),
        uint(clock.seq_id),
        text(&ingress.agent_id),
        text(&ingress.policy_profile),
        text(&ingress.payload_raw),
    ])
}

/// `phase_one_manifest_hash`: BLAKE3 de la preimagen del manifiesto.
pub fn manifest_hash(
    execution_id: &str,
    manifest_version: &str,
    clock: &CausalClock,
    ingress: &Ingress,
) -> [u8; 32] {
    *blake3::hash(&manifest_preimage(
        execution_id,
        manifest_version,
        clock,
        ingress,
    ))
    .as_bytes()
}

/// Sobre canónico: los bytes que resume `receipt_hash` y que cubre la firma.
pub fn receipt_envelope(f: &EnvelopeFields<'_>) -> Vec<u8> {
    array(vec![
        text(RECEIPT_DOMAIN),
        text(f.execution_id),
        uint(f.clock.policy_epoch),
        uint(f.clock.logical_tick),
        uint(f.clock.seq_id),
        bytes(&f.phase_one_manifest_hash),
        text(f.phase_two_merkle_root),
        bytes(&f.larsa.trace_hash),
        uint(u64::from(f.larsa.heuristic_weight)),
        text(&f.lean.status),
        text(&f.lean.theorem_ident),
        uint(f.lean.sorry_count),
        uint(f.audit.memory_bytes),
        bytes(&f.audit.prev_receipt_hash),
        bytes(&f.audit.worm_txid),
    ])
}

/// `receipt_hash`: BLAKE3 del sobre.
pub fn receipt_hash(envelope: &[u8]) -> [u8; 32] {
    *blake3::hash(envelope).as_bytes()
}

/// Bytes que firma la autoridad: Sig_structure de COSE_Sign1 (igual que `signing_bytes` del kernel).
pub fn signature_input(payload: &[u8]) -> Vec<u8> {
    array(vec![
        text("Signature1"),
        bytes(&COSE_PROTECTED_ED25519),
        bytes(&[]),
        bytes(payload),
    ])
}

/// Hex en minúsculas, sin prefijo.
pub fn to_hex(data: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(data.len() * 2);
    for b in data {
        out.push(char::from(HEX[usize::from(b >> 4)]));
        out.push(char::from(HEX[usize::from(b & 0x0f)]));
    }
    out
}

/// Decodifica hex estricto en minúsculas de exactamente `N` bytes.
pub fn from_hex_strict<const N: usize>(hex: &str) -> Option<[u8; N]> {
    let raw = hex.as_bytes();
    if raw.len() != N * 2 {
        return None;
    }
    let nibble = |c: u8| match c {
        b'0'..=b'9' => Some(c - b'0'),
        b'a'..=b'f' => Some(c - b'a' + 10),
        _ => None,
    };
    let mut out = [0u8; N];
    for (i, byte) in out.iter_mut().enumerate() {
        *byte = (nibble(raw[2 * i])? << 4) | nibble(raw[2 * i + 1])?;
    }
    Some(out)
}
