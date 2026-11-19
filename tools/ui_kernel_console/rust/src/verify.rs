//! Verificador fail-closed, réplica de `src/crypto/sealVerifier.ts`: mismas comprobaciones, en
//! el mismo orden, con los mismos códigos de fallo.
//!
//! El ancla de confianza (autoridades admitidas, peso LARSA exigido, punto de control opcional)
//! la aporta quien verifica y es obligatoria. Ninguna entrada provoca un pánico: toda entrada
//! produce un veredicto.

use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap, HashSet};

use ed25519_dalek::{Signature, VerifyingKey};
use serde_json::{json, Value};

use crate::canonical::{
    dag_merkle_root, from_hex_strict, manifest_hash, node_leaf_hash, receipt_envelope,
    receipt_hash, signature_input, to_hex, EnvelopeFields, NodeFields,
};
use crate::json_text::{first_non_integer_number, first_repeated_key, MAX_JSON_TEXT_UTF16};
use crate::point::{classify_point, is_strict_signature_encoding, PointVerdict};
use crate::schema::{
    escape_preview, parse_execution_payload, utf16_len, ExecutionPayload, Failure,
    FailureCollector, MAX_SAFE_INTEGER,
};

/// Máximo de autoridades admitidas en un ancla de confianza.
pub const MAX_ADMITTED_AUTHORITIES: usize = 64;
/// Tamaño máximo del texto de un ancla, en unidades UTF-16 (como `String.length`).
pub const MAX_ANCHOR_UTF16: usize = 1024 * 1024;
/// Tamaño máximo de un recibo en bytes: el texto admitido en UTF-16, en su peor codificación UTF-8.
pub const MAX_RECEIPT_BYTES: usize = 3 * MAX_JSON_TEXT_UTF16;

/// Ancla de confianza ya validada.
#[derive(Debug, Clone)]
struct TrustPolicy {
    authorities: Vec<[u8; 32]>,
    larsa_required_weight: u32,
    previous: Option<([u8; 32], u64)>,
}

/// Recibo que superó todas las comprobaciones locales.
#[derive(Debug, Clone)]
pub struct AcceptedReceipt {
    /// Recibo validado.
    pub payload: ExecutionPayload,
    /// Nodos en orden topológico determinista, con su profundidad causal.
    pub nodes: Vec<(String, usize)>,
    /// BLAKE3 del sobre canónico.
    pub receipt_hash: [u8; 32],
    /// Autoridad admitida cuya firma se comprobó.
    pub signer: [u8; 32],
    /// Peso LARSA exigido por el ancla.
    pub larsa_required_weight: u32,
    /// `true` si el anfitrión aportó punto de control y el encadenamiento coincide.
    pub chain_link_checked: bool,
}

/// Valores recalculados y declarados para el cotejo forense de un rechazo.
#[derive(Debug, Clone, Default)]
pub struct Diagnostics {
    /// Raíz declarada.
    pub declared_merkle_root: Option<String>,
    /// Raíz recalculada.
    pub computed_merkle_root: Option<String>,
    /// Compromiso de fase 1 declarado.
    pub declared_manifest_hash: Option<String>,
    /// Compromiso de fase 1 recalculado.
    pub computed_manifest_hash: Option<String>,
    /// Número de nodos leídos.
    pub node_count: Option<usize>,
}

/// Resultado de una verificación.
#[derive(Debug, Clone)]
pub enum Verdict {
    /// Todas las comprobaciones locales coinciden.
    Accepted(Box<AcceptedReceipt>),
    /// Al menos una comprobación falló.
    Rejected {
        /// Motivos (con tope).
        failures: Vec<Failure>,
        /// Cotejo forense.
        diagnostics: Diagnostics,
    },
}

impl Verdict {
    /// `true` si el recibo se aceptó.
    pub fn is_accepted(&self) -> bool {
        matches!(self, Verdict::Accepted(_))
    }

    /// Códigos de fallo sin duplicados y ordenados.
    pub fn codes(&self) -> Vec<&'static str> {
        match self {
            Verdict::Accepted(_) => Vec::new(),
            Verdict::Rejected { failures, .. } => {
                let mut codes: Vec<&'static str> = failures.iter().map(|f| f.code).collect();
                codes.sort_unstable();
                codes.dedup();
                codes
            }
        }
    }
}

fn reject(c: FailureCollector, diagnostics: Diagnostics) -> Verdict {
    let mut c = c;
    if c.count() == 0 {
        c.fail("VERIFIER_INTERNAL_ERROR", "rechazo sin causa registrada");
    }
    Verdict::Rejected {
        failures: c.finish(),
        diagnostics,
    }
}

/// Veredicto negativo para fallos previos a la verificación.
pub fn rejection(code: &'static str, detail: &str) -> Verdict {
    let mut c = FailureCollector::default();
    c.fail(code, escape_preview(detail, false));
    reject(c, Diagnostics::default())
}

fn is_hex32_text(v: &Value) -> Option<[u8; 32]> {
    v.as_str()
        .and_then(|s| s.strip_prefix("0x"))
        .and_then(from_hex_strict::<32>)
}

fn only_keys(obj: &serde_json::Map<String, Value>, allowed: &[&str]) -> bool {
    obj.keys().all(|k| allowed.contains(&k.as_str()))
}

fn normalize_policy(policy: &Value, c: &mut FailureCollector) -> Option<TrustPolicy> {
    let mut bad = |detail: &str| {
        c.fail("TRUST_POLICY_INVALID", detail);
        None
    };
    let Some(obj) = policy.as_object().filter(|o| {
        only_keys(
            o,
            &[
                "admitted_authorities",
                "larsa_required_weight",
                "previous_receipt",
            ],
        )
    }) else {
        return bad("el ancla de confianza debe ser { admitted_authorities, larsa_required_weight, previous_receipt? }");
    };
    let Some(raw) = obj
        .get("admitted_authorities")
        .and_then(Value::as_array)
        .filter(|a| !a.is_empty() && a.len() <= MAX_ADMITTED_AUTHORITIES)
    else {
        return bad("admitted_authorities debe ser un array de 1 a 64 claves");
    };
    let mut authorities: Vec<[u8; 32]> = Vec::with_capacity(raw.len());
    for (i, item) in raw.iter().enumerate() {
        let Some(key) = is_hex32_text(item) else {
            return bad(&format!(
                "admitted_authorities[{i}] debe ser 0x + 64 dígitos hex en minúsculas"
            ));
        };
        if authorities.contains(&key) {
            return bad(&format!("admitted_authorities[{i}] repite una clave"));
        }
        let verdict = classify_point(&key);
        if verdict != PointVerdict::Ok {
            return bad(&format!(
                "admitted_authorities[{i}] no es una clave Ed25519 aceptable ({verdict:?})"
            ));
        }
        authorities.push(key);
    }
    let Some(required) = obj
        .get("larsa_required_weight")
        .and_then(anchor_integer)
        .and_then(|w| u32::try_from(w).ok())
        .filter(|w| *w >= 1)
    else {
        return bad("larsa_required_weight debe ser un entero en [1, 2^32-1]");
    };
    let mut previous = None;
    if let Some(raw_prev) = obj.get("previous_receipt") {
        let Some(prev) = raw_prev
            .as_object()
            .filter(|o| only_keys(o, &["receipt_hash", "seq_id"]))
        else {
            return bad("previous_receipt debe ser { receipt_hash, seq_id }");
        };
        let Some(hash) = prev.get("receipt_hash").and_then(is_hex32_text) else {
            return bad("previous_receipt.receipt_hash debe ser 0x + 64 dígitos hex en minúsculas");
        };
        let Some(seq) = prev.get("seq_id").and_then(anchor_integer) else {
            return bad("previous_receipt.seq_id debe ser un entero ≥ 0");
        };
        previous = Some((hash, seq));
    }
    Some(TrustPolicy {
        authorities,
        larsa_required_weight: required,
        previous,
    })
}

/// Entero de un ancla, en cualquier escritura JSON que denote un entero seguro (`4`, `4.0`,
/// `4e0`). Así coincide con `Number.isSafeInteger` tras `JSON.parse` en TypeScript.
fn anchor_integer(v: &Value) -> Option<u64> {
    let n = v.as_number()?;
    if let Some(u) = n.as_u64() {
        return (u <= MAX_SAFE_INTEGER).then_some(u);
    }
    let f = n.as_f64()?;
    let max = MAX_SAFE_INTEGER as f64;
    (f.fract() == 0.0 && (0.0..=max).contains(&f)).then_some(f as u64)
}

/// Interpreta el ancla dada como texto: longitud, claves no repetidas y forma. Devuelve el
/// valor JSON o el motivo del rechazo.
pub fn parse_anchor_text(text: &str) -> Result<Value, String> {
    let units = utf16_len(text);
    if units > MAX_ANCHOR_UTF16 {
        return Err(format!(
            "ancla de {units} caracteres supera el máximo {MAX_ANCHOR_UTF16}"
        ));
    }
    let value: Value = serde_json::from_str(text)
        .map_err(|e| format!("el ancla no es JSON válido en la forma admitida: {e}"))?;
    match first_repeated_key(text) {
        Some(key) => Err(format!("clave duplicada en el ancla: {key}")),
        None => Ok(value),
    }
}

/// Verifica un recibo (bytes UTF-8) con un ancla dada como texto. Un ancla que no se puede
/// interpretar produce un veredicto `TRUST_POLICY_INVALID`: toda entrada produce un veredicto.
pub fn verify_with_anchor_text(receipt: &[u8], anchor_text: &str) -> Verdict {
    match parse_anchor_text(anchor_text) {
        Ok(policy) => verify_execution_payload_utf8(receipt, &policy),
        Err(detail) => rejection("TRUST_POLICY_INVALID", &detail),
    }
}

struct Topology {
    acyclic: bool,
    order: Vec<(usize, usize)>,
    unresolved: Vec<usize>,
}

/// Kahn con montículo mínimo por los bytes UTF-8 del identificador. Precondición: ids únicos y
/// padres presentes.
fn topological_order(nodes: &[&NodeFields], index: &HashMap<&str, usize>) -> Topology {
    let n = nodes.len();
    let mut by_id: Vec<usize> = (0..n).collect();
    by_id.sort_by(|a, b| {
        nodes[*a]
            .node_id
            .as_bytes()
            .cmp(nodes[*b].node_id.as_bytes())
    });
    let mut rank = vec![0usize; n];
    for (r, i) in by_id.iter().enumerate() {
        rank[*i] = r;
    }
    let mut in_degree = vec![0usize; n];
    let mut children: Vec<Vec<usize>> = vec![Vec::new(); n];
    for (i, node) in nodes.iter().enumerate() {
        for parent in &node.parent_ids {
            if let Some(p) = index.get(parent.as_str()) {
                in_degree[i] += 1;
                children[*p].push(i);
            }
        }
    }
    let mut depth = vec![0usize; n];
    let mut heap = BinaryHeap::new();
    for i in 0..n {
        if in_degree[i] == 0 {
            heap.push(Reverse(rank[i]));
        }
    }
    let mut order = Vec::with_capacity(n);
    while let Some(Reverse(r)) = heap.pop() {
        let current = by_id[r];
        order.push((current, depth[current]));
        for &child in &children[current] {
            depth[child] = depth[child].max(depth[current] + 1);
            in_degree[child] -= 1;
            if in_degree[child] == 0 {
                heap.push(Reverse(rank[child]));
            }
        }
    }
    let unresolved = if order.len() == n {
        Vec::new()
    } else {
        by_id.into_iter().filter(|i| in_degree[*i] > 0).collect()
    };
    Topology {
        acyclic: order.len() == n,
        order,
        unresolved,
    }
}

fn check_dag(nodes: &[&NodeFields], c: &mut FailureCollector) -> Option<Vec<(usize, usize)>> {
    let mut index: HashMap<&str, usize> = HashMap::new();
    let mut sound = true;
    for (i, node) in nodes.iter().enumerate() {
        if index.contains_key(node.node_id.as_str()) {
            c.fail(
                "DAG_DUPLICATE_NODE_ID",
                format!("identificador de nodo duplicado: {}", node.node_id),
            );
            sound = false;
        } else {
            index.insert(node.node_id.as_str(), i);
        }
    }
    for node in nodes {
        let mut seen: HashSet<&str> = HashSet::new();
        for parent in &node.parent_ids {
            if !seen.insert(parent.as_str()) {
                c.fail(
                    "DAG_DUPLICATE_PARENT_REF",
                    format!("el nodo {} repite el padre {parent}", node.node_id),
                );
                sound = false;
            }
            if !index.contains_key(parent.as_str()) {
                c.fail(
                    "DAG_DANGLING_PARENT_REF",
                    format!(
                        "el nodo {} referencia un padre inexistente: {parent}",
                        node.node_id
                    ),
                );
                sound = false;
            }
        }
    }
    if !sound {
        return None;
    }
    let topo = topological_order(nodes, &index);
    if !topo.acyclic {
        let shown: Vec<&str> = topo
            .unresolved
            .iter()
            .take(8)
            .map(|i| nodes[*i].node_id.as_str())
            .collect();
        let more = if topo.unresolved.len() > 8 {
            format!(" (+{})", topo.unresolved.len() - 8)
        } else {
            String::new()
        };
        c.fail(
            "DAG_CYCLE_DETECTED",
            format!(
                "ciclo causal: {}/{} nodos ordenables; sin ordenar: {}{more}",
                topo.order.len(),
                nodes.len(),
                shown.join(", ")
            ),
        );
        return None;
    }
    Some(topo.order)
}

fn verify_signature(public_key: &[u8; 32], signature: &[u8; 64], message: &[u8]) -> bool {
    if !is_strict_signature_encoding(signature) {
        return false;
    }
    let Ok(key) = VerifyingKey::from_bytes(public_key) else {
        return false;
    };
    key.verify_strict(message, &Signature::from_bytes(signature))
        .is_ok()
}

/// Verifica un recibo ya interpretado como JSON.
pub fn verify_execution_payload(input: &Value, policy: &Value) -> Verdict {
    let mut c = FailureCollector::default();
    let mut d = Diagnostics::default();

    let Some(trust) = normalize_policy(policy, &mut c) else {
        return reject(c, d);
    };
    let Some(payload) = parse_execution_payload(input, &mut c) else {
        return reject(c, d);
    };

    let seal = &payload.seal;
    let fields: Vec<&NodeFields> = payload.execution_dag.iter().map(|n| &n.fields).collect();
    d.node_count = Some(fields.len());
    d.declared_merkle_root = Some(seal.phase_two_merkle_root.clone());
    d.declared_manifest_hash = Some(format!("0x{}", to_hex(&seal.phase_one_manifest_hash)));

    // 1. Forma del DAG.
    let order = check_dag(&fields, &mut c);

    // 2. Coherencia nodo-SMT.
    for node in &fields {
        if node.state_status == "COMMITTED" && !node.smt_verified {
            c.fail(
                "COMMITTED_WITHOUT_SMT",
                format!(
                    "nodo {} marcado COMMITTED con smt_verified=false",
                    node.node_id
                ),
            );
        }
    }

    // 3. Hojas y raíz Merkle v1.
    for node in &payload.execution_dag {
        let expected = node_leaf_hash(&node.fields);
        if expected != node.state_hash {
            c.fail(
                "LEAF_HASH_MISMATCH",
                format!(
                    "nodo {}: state_hash recalculado 0x{}, recibido 0x{}",
                    node.fields.node_id,
                    to_hex(&expected),
                    to_hex(&node.state_hash)
                ),
            );
        }
    }
    if !c.has("DAG_DUPLICATE_NODE_ID") {
        match dag_merkle_root(&fields) {
            Ok(root) => {
                if root != seal.phase_two_merkle_root {
                    c.fail(
                        "MERKLE_ROOT_MISMATCH",
                        format!(
                            "raíz recalculada {root}, declarada {}",
                            seal.phase_two_merkle_root
                        ),
                    );
                }
                d.computed_merkle_root = Some(root);
            }
            Err(e) => c.fail("VERIFIER_INTERNAL_ERROR", format!("raíz Merkle: {e}")),
        }
    }

    // 4. Fase 1: compromiso con el manifiesto de entrada.
    let computed_manifest = manifest_hash(
        &payload.execution_id,
        &payload.manifest_version,
        &payload.causal_clock,
        &payload.ingress,
    );
    d.computed_manifest_hash = Some(format!("0x{}", to_hex(&computed_manifest)));
    if computed_manifest != seal.phase_one_manifest_hash {
        c.fail(
            "MANIFEST_HASH_MISMATCH",
            format!(
                "hash de manifiesto recalculado 0x{}, declarado 0x{}",
                to_hex(&computed_manifest),
                to_hex(&seal.phase_one_manifest_hash)
            ),
        );
    }

    // 5. Declaraciones del emisor; el peso exigido lo fija el ancla.
    if seal.larsa.heuristic_weight < trust.larsa_required_weight {
        c.fail(
            "QUORUM_INSUFFICIENT",
            format!(
                "peso heurístico LARSA declarado {} < peso exigido por el ancla {}",
                seal.larsa.heuristic_weight, trust.larsa_required_weight
            ),
        );
    }
    if seal.lean.status != "VERIFIED_NO_SORRY" || seal.lean.sorry_count != 0 {
        c.fail(
            "LEAN4_PROOF_INVALID",
            format!(
                "constancia Lean 4 declarada {} con sorry_count={}",
                seal.lean.status, seal.lean.sorry_count
            ),
        );
    }

    // 6. Firma del sobre por una autoridad admitida.
    let envelope = receipt_envelope(&EnvelopeFields {
        execution_id: &payload.execution_id,
        clock: payload.causal_clock,
        phase_one_manifest_hash: seal.phase_one_manifest_hash,
        phase_two_merkle_root: &seal.phase_two_merkle_root,
        larsa: seal.larsa,
        lean: &seal.lean,
        audit: payload.audit,
    });
    let signer_hex = format!("0x{}", to_hex(&seal.ed25519_public_key));
    if !trust.authorities.contains(&seal.ed25519_public_key) {
        c.fail(
            "AUTHORITY_NOT_ADMITTED",
            format!(
                "la clave firmante {signer_hex} no figura entre las {} autoridades admitidas",
                trust.authorities.len()
            ),
        );
    } else if !verify_signature(
        &seal.ed25519_public_key,
        &seal.ed25519_signature,
        &signature_input(&envelope),
    ) {
        c.fail(
            "ED25519_SIGNATURE_INVALID",
            format!("firma inválida de la autoridad {signer_hex} sobre el sobre canónico"),
        );
    }

    // 7. Encadenamiento con el punto de control del anfitrión.
    if let Some((prev_hash, prev_seq)) = trust.previous {
        if payload.audit.prev_receipt_hash != prev_hash {
            c.fail(
                "CHAIN_LINK_MISMATCH",
                format!(
                    "prev_receipt_hash 0x{} no coincide con el punto de control 0x{}",
                    to_hex(&payload.audit.prev_receipt_hash),
                    to_hex(&prev_hash)
                ),
            );
        }
        if payload.causal_clock.seq_id <= prev_seq {
            c.fail(
                "CHAIN_LINK_MISMATCH",
                format!(
                    "seq_id {} no es posterior al del punto de control ({prev_seq})",
                    payload.causal_clock.seq_id
                ),
            );
        }
    }

    let Some(order) = order.filter(|_| c.count() == 0) else {
        return reject(c, d);
    };
    let nodes = order
        .into_iter()
        .map(|(i, depth)| (fields[i].node_id.clone(), depth))
        .collect();
    Verdict::Accepted(Box::new(AcceptedReceipt {
        nodes,
        receipt_hash: receipt_hash(&envelope),
        signer: seal.ed25519_public_key,
        larsa_required_weight: trust.larsa_required_weight,
        chain_link_checked: trust.previous.is_some(),
        payload,
    }))
}

/// Verifica un recibo recibido como texto JSON, con las comprobaciones de texto de `json_text`.
pub fn verify_execution_payload_json(text: &str, policy: &Value) -> Verdict {
    let units = utf16_len(text);
    if units > MAX_JSON_TEXT_UTF16 {
        return rejection(
            "SCHEMA_INVALID",
            &format!("texto JSON de {units} caracteres supera el máximo {MAX_JSON_TEXT_UTF16}"),
        );
    }
    let value: Value = match serde_json::from_str(text) {
        Ok(v) => v,
        Err(_) => {
            return rejection(
                "SCHEMA_INVALID",
                "el texto recibido no es JSON válido en la forma admitida",
            )
        }
    };
    if let Some(token) = first_non_integer_number(text) {
        return rejection(
            "SCHEMA_INVALID",
            &format!("número no entero o no canónico en el texto: {token}"),
        );
    }
    if let Some(key) = first_repeated_key(text) {
        return rejection("SCHEMA_INVALID", &format!("clave duplicada: {key}"));
    }
    verify_execution_payload(&value, policy)
}

/// Verifica un recibo tal como llegó del transporte: bytes que deben ser UTF-8 válido.
pub fn verify_execution_payload_utf8(bytes: &[u8], policy: &Value) -> Verdict {
    if bytes.len() > MAX_RECEIPT_BYTES {
        return rejection(
            "SCHEMA_INVALID",
            &format!("{} bytes superan el máximo admitido", bytes.len()),
        );
    }
    match std::str::from_utf8(bytes) {
        Ok(text) => verify_execution_payload_json(text, policy),
        Err(_) => rejection("SCHEMA_INVALID", "el recibo no es UTF-8 válido"),
    }
}

fn opt_json(v: &Option<String>) -> Value {
    v.as_ref().map_or(Value::Null, |s| Value::String(s.clone()))
}

/// Veredicto como JSON (formato estable de la CLI y del binding WebAssembly).
pub fn verdict_json(verdict: &Verdict) -> Value {
    match verdict {
        Verdict::Accepted(r) => json!({
            "ok": true,
            "receipt_hash": format!("0x{}", to_hex(&r.receipt_hash)),
            "signer": format!("0x{}", to_hex(&r.signer)),
            "larsa_required_weight": r.larsa_required_weight,
            "chain_link": if r.chain_link_checked { "COINCIDE" } else { "NO_VERIFICADO" },
            "nodes": r.nodes.iter().map(|(id, depth)| json!({ "node_id": id, "depth": depth })).collect::<Vec<_>>(),
            "failures": [],
        }),
        Verdict::Rejected {
            failures,
            diagnostics,
        } => json!({
            "ok": false,
            "failures": failures.iter().map(|f| json!({ "code": f.code, "detail": f.detail })).collect::<Vec<_>>(),
            "diagnostics": {
                "declared_merkle_root": opt_json(&diagnostics.declared_merkle_root),
                "computed_merkle_root": opt_json(&diagnostics.computed_merkle_root),
                "declared_manifest_hash": opt_json(&diagnostics.declared_manifest_hash),
                "computed_manifest_hash": opt_json(&diagnostics.computed_manifest_hash),
                "node_count": diagnostics.node_count,
            },
        }),
    }
}
