//! Emisor de referencia: sella un recibo como `src/crypto/receiptSealer.ts` (mismos bytes para la
//! misma entrada y la misma clave; Ed25519 es determinista).
//!
//! Firma con una clave en memoria. Existe para generar vectores de prueba y contrastar las dos
//! implementaciones: un emisor de producción firmaría con una clave custodiada en hardware.
//!
//! Valida la estructura de la entrada (tipos, formatos, cotas) pero no su semántica: puede sellar
//! un DAG con ciclos o un nodo `COMMITTED` sin SMT, porque las pruebas necesitan modelar un emisor
//! defectuoso. Las reglas semánticas son tarea del verificador.

use ed25519_dalek::{Signer, SigningKey};
use serde_json::{json, Value};

use crate::canonical::{
    dag_merkle_root, manifest_hash, node_leaf_hash, receipt_envelope, signature_input, to_hex,
    AuditMetrics, CausalClock, EnvelopeFields, Ingress, LarsaCommit, Lean4Proof, NodeFields,
};
use crate::schema::{
    exact_object, is_execution_id, is_manifest_version, read_audit, read_clock, read_ingress,
    read_larsa, read_lean, read_nodes, read_string, Failure, FailureCollector,
    MAX_EXECUTION_ID_LENGTH,
};

/// Lo que aporta un emisor antes de sellar: todo salvo hashes y firma.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Unsealed {
    /// Identificador de la ejecución.
    pub execution_id: String,
    /// Reloj lógico.
    pub clock: CausalClock,
    /// Versión del manifiesto.
    pub manifest_version: String,
    /// Manifiesto de entrada.
    pub ingress: Ingress,
    /// Nodos del DAG.
    pub nodes: Vec<NodeFields>,
    /// Commit LARSA declarado.
    pub larsa: LarsaCommit,
    /// Constancia Lean 4 declarada.
    pub lean: Lean4Proof,
    /// Métricas de auditoría.
    pub audit: AuditMetrics,
}

const UNSEALED_KEYS: [&str; 8] = [
    "execution_id",
    "causal_clock",
    "manifest_version",
    "ingress",
    "nodes",
    "larsa_commit",
    "lean4_proof",
    "audit_metrics",
];

/// Interpreta la forma JSON de un recibo sin sellar (la que produce `unsealedOf` en TypeScript).
pub fn parse_unsealed(v: &Value) -> Result<Unsealed, Vec<Failure>> {
    let mut c = FailureCollector::default();
    let parsed = (|| {
        let obj = exact_object(Some(v), &UNSEALED_KEYS, "$", &mut c)?;
        let execution_id = read_string(
            obj.get("execution_id"),
            "$.execution_id",
            MAX_EXECUTION_ID_LENGTH,
            &mut c,
            Some(is_execution_id),
        );
        let clock = read_clock(obj.get("causal_clock"), "$.causal_clock", &mut c);
        let manifest_version = read_string(
            obj.get("manifest_version"),
            "$.manifest_version",
            32,
            &mut c,
            Some(is_manifest_version),
        );
        let ingress = read_ingress(obj.get("ingress"), "$.ingress", &mut c);
        let nodes = read_nodes(obj.get("nodes"), "$.nodes", &mut c, false);
        let larsa = read_larsa(obj.get("larsa_commit"), "$.larsa_commit", &mut c);
        let lean = read_lean(obj.get("lean4_proof"), "$.lean4_proof", &mut c);
        let audit = read_audit(obj.get("audit_metrics"), "$.audit_metrics", &mut c);
        Some(Unsealed {
            execution_id: execution_id?,
            clock: clock?,
            manifest_version: manifest_version?,
            ingress: ingress?,
            nodes: nodes?.into_iter().map(|(fields, _)| fields).collect(),
            larsa: larsa?,
            lean: lean?,
            audit: audit?,
        })
    })();
    match parsed {
        Some(u) if c.count() == 0 => Ok(u),
        _ => Err(c.finish()),
    }
}

fn hex0x(data: &[u8]) -> String {
    format!("0x{}", to_hex(data))
}

/// Sella `u` con `key`: hojas, raíz, compromiso del manifiesto, sobre y firma.
pub fn seal(u: &Unsealed, key: &SigningKey) -> Value {
    let refs: Vec<&NodeFields> = u.nodes.iter().collect();
    // `parse_unsealed` garantiza al menos un nodo; sin nodos no existe raíz y se devuelve null.
    let root = dag_merkle_root(&refs).map_or(Value::Null, Value::String);
    let root_text = root.as_str().unwrap_or_default().to_string();
    let phase_one = manifest_hash(&u.execution_id, &u.manifest_version, &u.clock, &u.ingress);
    let envelope = receipt_envelope(&EnvelopeFields {
        execution_id: &u.execution_id,
        clock: u.clock,
        phase_one_manifest_hash: phase_one,
        phase_two_merkle_root: &root_text,
        larsa: u.larsa,
        lean: &u.lean,
        audit: u.audit,
    });
    let signature = key.sign(&signature_input(&envelope));
    json!({
        "execution_id": u.execution_id,
        "manifest_version": u.manifest_version,
        "causal_clock": {
            "policy_epoch": u.clock.policy_epoch,
            "logical_tick": u.clock.logical_tick,
            "seq_id": u.clock.seq_id,
        },
        "ingress": {
            "agent_id": u.ingress.agent_id,
            "policy_profile": u.ingress.policy_profile,
            "payload_raw": u.ingress.payload_raw,
        },
        "execution_dag": u.nodes.iter().map(|n| json!({
            "node_id": n.node_id,
            "parent_ids": n.parent_ids,
            "state_status": n.state_status,
            "smt_verified": n.smt_verified,
            "reduction_steps": n.reduction_steps,
            "state_hash": hex0x(&node_leaf_hash(n)),
            "violation_reason": n.violation_reason,
        })).collect::<Vec<_>>(),
        "cryptographic_seal": {
            "phase_one_manifest_hash": hex0x(&phase_one),
            "phase_two_merkle_root": root,
            "ed25519_public_key": hex0x(key.verifying_key().as_bytes()),
            "ed25519_signature": hex0x(&signature.to_bytes()),
            "larsa_commit": {
                "trace_hash": hex0x(&u.larsa.trace_hash),
                "heuristic_weight": u.larsa.heuristic_weight,
            },
            "lean4_proof": {
                "status": u.lean.status,
                "theorem_ident": u.lean.theorem_ident,
                "sorry_count": u.lean.sorry_count,
            },
        },
        "audit_metrics": {
            "memory_bytes": u.audit.memory_bytes,
            "prev_receipt_hash": hex0x(&u.audit.prev_receipt_hash),
            "worm_txid": hex0x(&u.audit.worm_txid),
        },
    })
}

/// Sella con una semilla de prueba. Una semilla escrita en el código o pasada por la línea de
/// órdenes no protege nada: solo para vectores reproducibles.
pub fn seal_with_test_seed(u: &Unsealed, seed: &[u8; 32]) -> Value {
    seal(u, &SigningKey::from_bytes(seed))
}
