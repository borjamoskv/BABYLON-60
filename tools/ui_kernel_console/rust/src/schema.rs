//! Validación estructural estricta de la entrada, réplica de `src/crypto/schema.ts`.
//!
//! - Cada objeto debe tener exactamente las claves esperadas.
//! - Los enteros deben caber en [0, 2^53 − 1], el rango exacto de un número JavaScript.
//! - Las longitudes de texto se miden en unidades UTF-16, como `String.length`.
//! - Los fallos se acumulan con tope; nunca crece la lista sin límite.

use serde_json::{Map, Value};

use crate::canonical::{
    from_hex_strict, AuditMetrics, CausalClock, Ingress, LarsaCommit, Lean4Proof, NodeFields,
};

/// Máximo de nodos del DAG.
pub const MAX_DAG_NODES: usize = 4096;
/// Máximo de padres por nodo.
pub const MAX_PARENTS_PER_NODE: usize = 64;
/// Máximo de aristas del DAG.
pub const MAX_DAG_EDGES: usize = 16384;
/// Longitud máxima de `execution_id`.
pub const MAX_EXECUTION_ID_LENGTH: usize = 128;
/// Longitud máxima de `agent_id`.
pub const MAX_AGENT_ID_LENGTH: usize = 256;
/// Longitud máxima de `payload_raw` (unidades UTF-16).
pub const MAX_PAYLOAD_RAW_LENGTH: usize = 65536;
/// Longitud máxima de `violation_reason` (unidades UTF-16).
pub const MAX_VIOLATION_REASON_LENGTH: usize = 512;
/// Longitud máxima de `theorem_ident`.
pub const MAX_THEOREM_IDENT_LENGTH: usize = 256;
/// Tope de fallos que lista un veredicto negativo.
pub const MAX_REPORTED_FAILURES: usize = 64;
/// Mayor entero representable sin pérdida en JavaScript.
pub const MAX_SAFE_INTEGER: u64 = (1 << 53) - 1;

/// Perfiles de política admitidos.
pub const POLICY_PROFILES: [&str; 3] = [
    "STRICT_DETERMINISTIC",
    "BFT_DEFENSIVE",
    "NEMESIS_ADVERSARIAL",
];
/// Estados de nodo admitidos.
pub const NODE_STATUSES: [&str; 4] = [
    "COMMITTED",
    "REJECTED_POLICY",
    "INTERCEPTED_NEMESIS",
    "PENDING_SEAL",
];
/// Estados Lean 4 admitidos.
pub const LEAN_STATUSES: [&str; 2] = ["VERIFIED_NO_SORRY", "FAILED_INVARIANT"];

/// Un motivo de rechazo.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Failure {
    /// Código estable (el mismo que en TypeScript).
    pub code: &'static str,
    /// Detalle legible; cita la entrada de forma acotada y escapada.
    pub detail: String,
}

/// Acumulador de fallos con tope explícito.
#[derive(Debug, Default)]
pub struct FailureCollector {
    items: Vec<Failure>,
    truncated: bool,
}

impl FailureCollector {
    /// Registra un fallo; por encima del tope solo marca la lista como truncada.
    pub fn fail(&mut self, code: &'static str, detail: impl Into<String>) {
        if self.items.len() < MAX_REPORTED_FAILURES {
            self.items.push(Failure {
                code,
                detail: detail.into(),
            });
        } else {
            self.truncated = true;
        }
    }

    /// Número de fallos retenidos.
    pub fn count(&self) -> usize {
        self.items.len()
    }

    /// `true` si ya no cabe ningún fallo más.
    pub fn full(&self) -> bool {
        self.items.len() >= MAX_REPORTED_FAILURES
    }

    /// Declara que se dejó de examinar la entrada.
    pub fn mark_truncated(&mut self) {
        self.truncated = true;
    }

    /// `true` si hay algún fallo retenido con ese código.
    pub fn has(&self, code: &str) -> bool {
        self.items.iter().any(|f| f.code == code)
    }

    /// Lista final; si hubo recorte, la última entrada lo dice.
    pub fn finish(mut self) -> Vec<Failure> {
        if self.truncated {
            if let Some(last) = self.items.last_mut() {
                last.detail = format!(
                    "{} [lista truncada en el tope de {} fallos; puede haber más]",
                    last.detail, MAX_REPORTED_FAILURES
                );
            }
        }
        self.items
    }
}

/// Cita acotada y escapada de un valor no confiable.
pub fn preview(v: Option<&Value>) -> String {
    match v {
        None => "undefined".to_string(),
        Some(Value::Null) => "null".to_string(),
        Some(Value::Array(_)) => "array".to_string(),
        Some(Value::Object(_)) => "object".to_string(),
        Some(Value::Bool(b)) => b.to_string(),
        Some(Value::Number(n)) => escape_preview(&n.to_string(), false),
        Some(Value::String(s)) => escape_preview(s, true),
    }
}

/// Cita acotada de un texto: ASCII imprimible tal cual; el resto como `\uXXXX`.
pub fn escape_preview(text: &str, quoted: bool) -> String {
    const MAX: usize = 48;
    let units: Vec<u16> = text.encode_utf16().collect();
    let mut out = String::new();
    let mut i = 0;
    while i < units.len() && out.len() < MAX {
        let c = units[i];
        if (0x20..=0x7e).contains(&c) && c != 0x5c && c != 0x22 {
            out.push(char::from(c as u8));
        } else {
            out.push_str(&format!("\\u{c:04x}"));
        }
        i += 1;
    }
    let suffix = if i < units.len() {
        format!("…(+{})", units.len() - i)
    } else {
        String::new()
    };
    if quoted {
        format!("\"{out}{suffix}\"")
    } else {
        format!("{out}{suffix}")
    }
}

/// Longitud en unidades UTF-16.
pub fn utf16_len(s: &str) -> usize {
    s.encode_utf16().count()
}

pub(crate) fn exact_object<'a>(
    v: Option<&'a Value>,
    keys: &[&str],
    path: &str,
    c: &mut FailureCollector,
) -> Option<&'a Map<String, Value>> {
    let Some(Value::Object(obj)) = v else {
        c.fail(
            "SCHEMA_INVALID",
            format!("{path}: se esperaba un objeto, se recibió {}", preview(v)),
        );
        return None;
    };
    if obj.len() > keys.len() + 16 {
        c.fail(
            "SCHEMA_INVALID",
            format!("{path}: {} claves, se esperaban {}", obj.len(), keys.len()),
        );
        return None;
    }
    let mut ok = true;
    for k in obj.keys() {
        if !keys.contains(&k.as_str()) {
            c.fail(
                "SCHEMA_INVALID",
                format!("{path}: clave no admitida {}", escape_preview(k, true)),
            );
            ok = false;
        }
    }
    for k in keys {
        if !obj.contains_key(*k) {
            c.fail(
                "SCHEMA_INVALID",
                format!("{path}.{k}: falta el campo obligatorio"),
            );
            ok = false;
        }
    }
    ok.then_some(obj)
}

pub(crate) fn read_string(
    v: Option<&Value>,
    path: &str,
    max_utf16: usize,
    c: &mut FailureCollector,
    pattern: Option<fn(&str) -> bool>,
) -> Option<String> {
    let Some(Value::String(s)) = v else {
        c.fail(
            "SCHEMA_INVALID",
            format!("{path}: se esperaba una cadena, se recibió {}", preview(v)),
        );
        return None;
    };
    let len = utf16_len(s);
    if len > max_utf16 {
        c.fail(
            "LIMIT_EXCEEDED",
            format!("{path}: longitud {len} supera el máximo {max_utf16}"),
        );
        return None;
    }
    if let Some(check) = pattern {
        if !check(s) {
            c.fail(
                "SCHEMA_INVALID",
                format!("{path}: formato no admitido {}", escape_preview(s, true)),
            );
            return None;
        }
    }
    Some(s.clone())
}

pub(crate) fn read_uint(v: Option<&Value>, path: &str, c: &mut FailureCollector) -> Option<u64> {
    match v.and_then(Value::as_u64) {
        Some(n) if n <= MAX_SAFE_INTEGER => Some(n),
        _ => {
            c.fail(
                "SCHEMA_INVALID",
                format!(
                    "{path}: se esperaba un entero en [0, 2^53-1], se recibió {}",
                    preview(v)
                ),
            );
            None
        }
    }
}

pub(crate) fn read_u32(v: Option<&Value>, path: &str, c: &mut FailureCollector) -> Option<u32> {
    let n = read_uint(v, path, c)?;
    match u32::try_from(n) {
        Ok(w) => Some(w),
        Err(_) => {
            c.fail("SCHEMA_INVALID", format!("{path}: {n} excede 2^32-1"));
            None
        }
    }
}

pub(crate) fn read_enum(
    v: Option<&Value>,
    allowed: &[&str],
    path: &str,
    c: &mut FailureCollector,
) -> Option<String> {
    match v {
        Some(Value::String(s)) if allowed.contains(&s.as_str()) => Some(s.clone()),
        _ => {
            c.fail(
                "SCHEMA_INVALID",
                format!("{path}: valor no admitido {}", preview(v)),
            );
            None
        }
    }
}

pub(crate) fn read_bool(v: Option<&Value>, path: &str, c: &mut FailureCollector) -> Option<bool> {
    match v {
        Some(Value::Bool(b)) => Some(*b),
        _ => {
            c.fail(
                "SCHEMA_INVALID",
                format!("{path}: se esperaba un booleano, se recibió {}", preview(v)),
            );
            None
        }
    }
}

fn read_prefixed<const N: usize>(
    v: Option<&Value>,
    prefix: &str,
    path: &str,
    c: &mut FailureCollector,
) -> Option<[u8; N]> {
    let Some(Value::String(s)) = v else {
        c.fail(
            "SCHEMA_MALFORMED_HEX",
            format!(
                "{path}: se esperaba una cadena hex, se recibió {}",
                preview(v)
            ),
        );
        return None;
    };
    let decoded = s.strip_prefix(prefix).and_then(from_hex_strict::<N>);
    if decoded.is_none() {
        c.fail(
            "SCHEMA_MALFORMED_HEX",
            format!(
                "{path}: se esperaba \"{prefix}\" seguido de {} dígitos hex en minúsculas, se recibió {}",
                N * 2,
                preview(v)
            ),
        );
    }
    decoded
}

pub(crate) fn read_hex32(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<[u8; 32]> {
    read_prefixed::<32>(v, "0x", path, c)
}

pub(crate) fn read_hex64(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<[u8; 64]> {
    read_prefixed::<64>(v, "0x", path, c)
}

pub(crate) fn read_b3_root(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<String> {
    read_prefixed::<32>(v, "b3:", path, c)?;
    match v {
        Some(Value::String(s)) => Some(s.clone()),
        _ => None,
    }
}

pub(crate) fn read_array<'a>(
    v: Option<&'a Value>,
    path: &str,
    max: usize,
    c: &mut FailureCollector,
) -> Option<&'a Vec<Value>> {
    let Some(Value::Array(items)) = v else {
        c.fail(
            "SCHEMA_INVALID",
            format!("{path}: se esperaba un array, se recibió {}", preview(v)),
        );
        return None;
    };
    if items.len() > max {
        c.fail(
            "LIMIT_EXCEEDED",
            format!("{path}: {} elementos superan el máximo {max}", items.len()),
        );
        return None;
    }
    Some(items)
}

/// `^[A-Za-z0-9][A-Za-z0-9._:-]*$`
pub fn is_execution_id(s: &str) -> bool {
    let mut chars = s.bytes();
    matches!(chars.next(), Some(c) if c.is_ascii_alphanumeric())
        && chars.all(|c| c.is_ascii_alphanumeric() || matches!(c, b'.' | b'_' | b':' | b'-'))
}

/// `^v(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})$`
pub fn is_manifest_version(s: &str) -> bool {
    let Some(rest) = s.strip_prefix('v') else {
        return false;
    };
    let parts: Vec<&str> = rest.split('.').collect();
    parts.len() == 3
        && parts.iter().all(|p| {
            !p.is_empty()
                && p.len() <= 9
                && p.bytes().all(|b| b.is_ascii_digit())
                && (*p == "0" || !p.starts_with('0'))
        })
}

/// `^[\x21-\x7e]+$`
pub fn is_agent_id(s: &str) -> bool {
    !s.is_empty() && s.bytes().all(|b| (0x21..=0x7e).contains(&b))
}

/// `^[A-Za-z_][A-Za-z0-9_'!?]*(\.[A-Za-z_][A-Za-z0-9_'!?]*)*$`
pub fn is_theorem_ident(s: &str) -> bool {
    s.split('.').all(|segment| {
        let mut b = segment.bytes();
        matches!(b.next(), Some(c) if c.is_ascii_alphabetic() || c == b'_')
            && b.all(|c| c.is_ascii_alphanumeric() || matches!(c, b'_' | b'\'' | b'!' | b'?'))
    })
}

fn is_canonical_padded_decimal(digits: &str, min_width: usize, max: &str) -> bool {
    if digits.len() > min_width && digits.starts_with('0') {
        return false;
    }
    if digits.len() > max.len() {
        return false;
    }
    !(digits.len() == max.len() && digits > max)
}

/// `EV_{tick:08}_{seq:06}` tal como lo emite `generate_canonical_event_id(tick: u64, seq: u32)`.
pub fn is_canonical_event_id(id: &str) -> bool {
    let Some(rest) = id.strip_prefix("EV_") else {
        return false;
    };
    let Some((tick, seq)) = rest.split_once('_') else {
        return false;
    };
    let digits = |s: &str, lo: usize, hi: usize| {
        s.len() >= lo && s.len() <= hi && s.bytes().all(|b| b.is_ascii_digit())
    };
    digits(tick, 8, 20)
        && digits(seq, 6, 10)
        && is_canonical_padded_decimal(tick, 8, "18446744073709551615")
        && is_canonical_padded_decimal(seq, 6, "4294967295")
}

/// Nodo leído de la entrada: campos más el `state_hash` declarado.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Node {
    /// Campos que entran en la preimagen.
    pub fields: NodeFields,
    /// Hash de hoja declarado.
    pub state_hash: [u8; 32],
}

/// Sello declarado.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Seal {
    /// Compromiso de fase 1.
    pub phase_one_manifest_hash: [u8; 32],
    /// Raíz Merkle v1 declarada (`b3:…`).
    pub phase_two_merkle_root: String,
    /// Clave que dice haber firmado.
    pub ed25519_public_key: [u8; 32],
    /// Firma del Sig_structure del sobre.
    pub ed25519_signature: [u8; 64],
    /// Commit LARSA declarado.
    pub larsa: LarsaCommit,
    /// Constancia Lean 4 declarada.
    pub lean: Lean4Proof,
}

/// Recibo con todos sus campos validados estructuralmente (aún sin comprobar hashes ni firma).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExecutionPayload {
    /// Identificador de la ejecución.
    pub execution_id: String,
    /// Reloj lógico.
    pub causal_clock: CausalClock,
    /// Versión del manifiesto.
    pub manifest_version: String,
    /// Manifiesto de entrada.
    pub ingress: Ingress,
    /// Nodos del DAG en el orden de llegada.
    pub execution_dag: Vec<Node>,
    /// Sello.
    pub seal: Seal,
    /// Métricas de auditoría.
    pub audit: AuditMetrics,
}

const NODE_KEYS: [&str; 7] = [
    "node_id",
    "parent_ids",
    "state_status",
    "smt_verified",
    "reduction_steps",
    "state_hash",
    "violation_reason",
];
pub(crate) const UNSEALED_NODE_KEYS: [&str; 6] = [
    "node_id",
    "parent_ids",
    "state_status",
    "smt_verified",
    "reduction_steps",
    "violation_reason",
];
const ROOT_KEYS: [&str; 7] = [
    "execution_id",
    "causal_clock",
    "manifest_version",
    "ingress",
    "execution_dag",
    "cryptographic_seal",
    "audit_metrics",
];
pub(crate) const CLOCK_KEYS: [&str; 3] = ["policy_epoch", "logical_tick", "seq_id"];
pub(crate) const INGRESS_KEYS: [&str; 3] = ["agent_id", "policy_profile", "payload_raw"];
const SEAL_KEYS: [&str; 6] = [
    "phase_one_manifest_hash",
    "phase_two_merkle_root",
    "ed25519_public_key",
    "ed25519_signature",
    "larsa_commit",
    "lean4_proof",
];
pub(crate) const LARSA_KEYS: [&str; 2] = ["trace_hash", "heuristic_weight"];
pub(crate) const LEAN_KEYS: [&str; 3] = ["status", "theorem_ident", "sorry_count"];
pub(crate) const AUDIT_KEYS: [&str; 3] = ["memory_bytes", "prev_receipt_hash", "worm_txid"];

/// Lee los campos de un nodo; `with_state_hash` decide si se espera `state_hash`.
pub(crate) fn read_node_fields(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
    with_state_hash: bool,
) -> Option<(NodeFields, Option<[u8; 32]>)> {
    let keys: &[&str] = if with_state_hash {
        &NODE_KEYS
    } else {
        &UNSEALED_NODE_KEYS
    };
    let obj = exact_object(v, keys, path, c)?;

    let node_id = read_string(obj.get("node_id"), &format!("{path}.node_id"), 40, c, None)
        .and_then(|id| {
            if is_canonical_event_id(&id) {
                Some(id)
            } else {
                c.fail(
                    "SCHEMA_INVALID",
                    format!(
                    "{path}.node_id: no es un identificador canónico EV_{{tick:08}}_{{seq:06}}: {}",
                    escape_preview(&id, true)
                ),
                );
                None
            }
        });

    let mut parent_ids: Option<Vec<String>> = None;
    if let Some(raw) = read_array(
        obj.get("parent_ids"),
        &format!("{path}.parent_ids"),
        MAX_PARENTS_PER_NODE,
        c,
    ) {
        let mut parents = Vec::with_capacity(raw.len());
        let mut ok = true;
        for (i, item) in raw.iter().enumerate() {
            let p_path = format!("{path}.parent_ids[{i}]");
            let Some(p) = read_string(Some(item), &p_path, 40, c, None) else {
                ok = false;
                break;
            };
            if !is_canonical_event_id(&p) {
                c.fail(
                    "SCHEMA_INVALID",
                    format!(
                        "{p_path}: no es un identificador canónico: {}",
                        escape_preview(&p, true)
                    ),
                );
                ok = false;
                break;
            }
            parents.push(p);
        }
        if ok {
            parent_ids = Some(parents);
        }
    }

    let state_status = read_enum(
        obj.get("state_status"),
        &NODE_STATUSES,
        &format!("{path}.state_status"),
        c,
    );
    let smt_verified = read_bool(obj.get("smt_verified"), &format!("{path}.smt_verified"), c);
    let reduction_steps = read_uint(
        obj.get("reduction_steps"),
        &format!("{path}.reduction_steps"),
        c,
    );
    let state_hash = if with_state_hash {
        Some(read_hex32(
            obj.get("state_hash"),
            &format!("{path}.state_hash"),
            c,
        ))
    } else {
        None
    };

    let reason_path = format!("{path}.violation_reason");
    let violation_reason: Option<Option<String>> = match obj.get("violation_reason") {
        Some(Value::Null) => Some(None),
        other => match read_string(other, &reason_path, MAX_VIOLATION_REASON_LENGTH, c, None) {
            Some(r) if r.is_empty() => {
                c.fail(
                    "SCHEMA_INVALID",
                    format!("{reason_path}: cadena vacía; use null si no hay violación"),
                );
                None
            }
            Some(r) => Some(Some(r)),
            None => None,
        },
    };

    let fields = NodeFields {
        node_id: node_id?,
        parent_ids: parent_ids?,
        state_status: state_status?,
        smt_verified: smt_verified?,
        reduction_steps: reduction_steps?,
        violation_reason: violation_reason?,
    };
    match state_hash {
        Some(Some(h)) => Some((fields, Some(h))),
        Some(None) => None,
        None => Some((fields, None)),
    }
}

pub(crate) fn read_clock(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<CausalClock> {
    let obj = exact_object(v, &CLOCK_KEYS, path, c)?;
    let policy_epoch = read_uint(obj.get("policy_epoch"), &format!("{path}.policy_epoch"), c);
    let logical_tick = read_uint(obj.get("logical_tick"), &format!("{path}.logical_tick"), c);
    let seq_id = read_uint(obj.get("seq_id"), &format!("{path}.seq_id"), c);
    Some(CausalClock {
        policy_epoch: policy_epoch?,
        logical_tick: logical_tick?,
        seq_id: seq_id?,
    })
}

pub(crate) fn read_ingress(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<Ingress> {
    let obj = exact_object(v, &INGRESS_KEYS, path, c)?;
    let agent_id = read_string(
        obj.get("agent_id"),
        &format!("{path}.agent_id"),
        MAX_AGENT_ID_LENGTH,
        c,
        Some(is_agent_id),
    );
    let policy_profile = read_enum(
        obj.get("policy_profile"),
        &POLICY_PROFILES,
        &format!("{path}.policy_profile"),
        c,
    );
    let payload_raw = read_string(
        obj.get("payload_raw"),
        &format!("{path}.payload_raw"),
        MAX_PAYLOAD_RAW_LENGTH,
        c,
        None,
    );
    Some(Ingress {
        agent_id: agent_id?,
        policy_profile: policy_profile?,
        payload_raw: payload_raw?,
    })
}

pub(crate) fn read_larsa(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<LarsaCommit> {
    let obj = exact_object(v, &LARSA_KEYS, path, c)?;
    let trace_hash = read_hex32(obj.get("trace_hash"), &format!("{path}.trace_hash"), c);
    let heuristic_weight = read_u32(
        obj.get("heuristic_weight"),
        &format!("{path}.heuristic_weight"),
        c,
    );
    Some(LarsaCommit {
        trace_hash: trace_hash?,
        heuristic_weight: heuristic_weight?,
    })
}

pub(crate) fn read_lean(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<Lean4Proof> {
    let obj = exact_object(v, &LEAN_KEYS, path, c)?;
    let status = read_enum(
        obj.get("status"),
        &LEAN_STATUSES,
        &format!("{path}.status"),
        c,
    );
    let theorem_ident = read_string(
        obj.get("theorem_ident"),
        &format!("{path}.theorem_ident"),
        MAX_THEOREM_IDENT_LENGTH,
        c,
        Some(is_theorem_ident),
    );
    let sorry_count = read_uint(obj.get("sorry_count"), &format!("{path}.sorry_count"), c);
    Some(Lean4Proof {
        status: status?,
        theorem_ident: theorem_ident?,
        sorry_count: sorry_count?,
    })
}

pub(crate) fn read_audit(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
) -> Option<AuditMetrics> {
    let obj = exact_object(v, &AUDIT_KEYS, path, c)?;
    let memory_bytes = read_uint(obj.get("memory_bytes"), &format!("{path}.memory_bytes"), c);
    let prev_receipt_hash = read_hex32(
        obj.get("prev_receipt_hash"),
        &format!("{path}.prev_receipt_hash"),
        c,
    );
    let worm_txid = read_hex32(obj.get("worm_txid"), &format!("{path}.worm_txid"), c);
    Some(AuditMetrics {
        memory_bytes: memory_bytes?,
        prev_receipt_hash: prev_receipt_hash?,
        worm_txid: worm_txid?,
    })
}

/// Lee los nodos de un array: `None` si alguno falla; sigue recorriendo hasta el tope de fallos.
pub(crate) fn read_nodes(
    v: Option<&Value>,
    path: &str,
    c: &mut FailureCollector,
    with_state_hash: bool,
) -> Option<Vec<(NodeFields, Option<[u8; 32]>)>> {
    let raw = read_array(v, path, MAX_DAG_NODES, c)?;
    if raw.is_empty() {
        c.fail(
            "DAG_EMPTY",
            format!("{path}: un recibo sin nodos no tiene raíz Merkle definida"),
        );
        return None;
    }
    let mut nodes = Some(Vec::with_capacity(raw.len()));
    let mut edges = 0usize;
    for (i, item) in raw.iter().enumerate() {
        match read_node_fields(Some(item), &format!("{path}[{i}]"), c, with_state_hash) {
            None => {
                nodes = None;
                if c.full() {
                    if i < raw.len() - 1 {
                        c.mark_truncated();
                    }
                    break;
                }
            }
            Some(node) => {
                edges += node.0.parent_ids.len();
                if edges > MAX_DAG_EDGES {
                    c.fail(
                        "LIMIT_EXCEEDED",
                        format!("{path}: más de {MAX_DAG_EDGES} aristas"),
                    );
                    return None;
                }
                if let Some(list) = nodes.as_mut() {
                    list.push(node);
                }
            }
        }
    }
    nodes
}

/// Interpreta `input` como recibo. `None` tras registrar cada motivo de rechazo en `c`.
pub fn parse_execution_payload(
    input: &Value,
    c: &mut FailureCollector,
) -> Option<ExecutionPayload> {
    let root = exact_object(Some(input), &ROOT_KEYS, "$", c)?;

    let execution_id = read_string(
        root.get("execution_id"),
        "$.execution_id",
        MAX_EXECUTION_ID_LENGTH,
        c,
        Some(is_execution_id),
    );
    let manifest_version = read_string(
        root.get("manifest_version"),
        "$.manifest_version",
        32,
        c,
        Some(is_manifest_version),
    );
    let causal_clock = read_clock(root.get("causal_clock"), "$.causal_clock", c);
    let ingress = read_ingress(root.get("ingress"), "$.ingress", c);
    let execution_dag = read_nodes(root.get("execution_dag"), "$.execution_dag", c, true);

    let mut seal: Option<Seal> = None;
    if let Some(obj) = exact_object(
        root.get("cryptographic_seal"),
        &SEAL_KEYS,
        "$.cryptographic_seal",
        c,
    ) {
        let p = "$.cryptographic_seal";
        let phase_one = read_hex32(
            obj.get("phase_one_manifest_hash"),
            &format!("{p}.phase_one_manifest_hash"),
            c,
        );
        let phase_two = read_b3_root(
            obj.get("phase_two_merkle_root"),
            &format!("{p}.phase_two_merkle_root"),
            c,
        );
        let public_key = read_hex32(
            obj.get("ed25519_public_key"),
            &format!("{p}.ed25519_public_key"),
            c,
        );
        let signature = read_hex64(
            obj.get("ed25519_signature"),
            &format!("{p}.ed25519_signature"),
            c,
        );
        let larsa = read_larsa(obj.get("larsa_commit"), &format!("{p}.larsa_commit"), c);
        let lean = read_lean(obj.get("lean4_proof"), &format!("{p}.lean4_proof"), c);
        if let (Some(a), Some(b), Some(d), Some(e), Some(f), Some(g)) =
            (phase_one, phase_two, public_key, signature, larsa, lean)
        {
            seal = Some(Seal {
                phase_one_manifest_hash: a,
                phase_two_merkle_root: b,
                ed25519_public_key: d,
                ed25519_signature: e,
                larsa: f,
                lean: g,
            });
        }
    }

    let audit = read_audit(root.get("audit_metrics"), "$.audit_metrics", c);

    let execution_dag = execution_dag?
        .into_iter()
        .map(|(fields, hash)| hash.map(|state_hash| Node { fields, state_hash }))
        .collect::<Option<Vec<Node>>>()?;
    Some(ExecutionPayload {
        execution_id: execution_id?,
        causal_clock: causal_clock?,
        manifest_version: manifest_version?,
        ingress: ingress?,
        execution_dag,
        seal: seal?,
        audit: audit?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn event_identifiers_follow_the_kernel_format() {
        for ok in [
            "EV_00000000_000000",
            "EV_00001048_000003",
            "EV_100000000_000000",
            "EV_00000001_1000000",
            "EV_18446744073709551615_4294967295",
        ] {
            assert!(is_canonical_event_id(ok), "{ok}");
        }
        for bad in [
            "",
            "EV_1048_0",
            "EV_000001048_000003",
            "EV_00001048_0000003",
            "EV_18446744073709551616_000000",
            "EV_00000001_4294967296",
            "EV_00001048_000003 ",
            "EV_0000104a_000003",
            "EV_00001048-000003",
            "EV_00001048_000003_1",
        ] {
            assert!(!is_canonical_event_id(bad), "{bad:?}");
        }
    }

    #[test]
    fn identifier_patterns_match_the_typescript_regexes() {
        assert!(is_execution_id(
            "b60-exec-01931a7c-8f00-7000-8000-000000000060"
        ));
        for bad in ["", "-a", "a|b", "a b", "ñ"] {
            assert!(!is_execution_id(bad), "{bad:?}");
        }
        assert!(
            is_manifest_version("v5.1.0")
                && is_manifest_version("v0.0.0")
                && is_manifest_version("v123456789.0.1")
        );
        for bad in [
            "5.1.0",
            "v05.1.0",
            "v1.0",
            "v1.0.0-rc1",
            "v1.0.00",
            "v1234567890.0.0",
            "V1.0.0",
        ] {
            assert!(!is_manifest_version(bad), "{bad:?}");
        }
        assert!(
            is_theorem_ident("Fixture.Synthetic.transition_soundness")
                && is_theorem_ident("a'!?._b")
        );
        for bad in ["", " ", "1abc", "a..b", "a.", ".a", "Thm|x", "ñ"] {
            assert!(!is_theorem_ident(bad), "{bad:?}");
        }
        assert!(is_agent_id("agent://cortex/rea-auditor-01"));
        for bad in ["", "a b", "a\tb", "agente://ñ"] {
            assert!(!is_agent_id(bad), "{bad:?}");
        }
    }

    #[test]
    fn integers_must_be_exact_in_javascript() {
        let mut c = FailureCollector::default();
        assert_eq!(
            read_uint(Some(&serde_json::json!(MAX_SAFE_INTEGER)), "$", &mut c),
            Some(MAX_SAFE_INTEGER)
        );
        assert_eq!(
            read_uint(Some(&serde_json::json!(MAX_SAFE_INTEGER + 1)), "$", &mut c),
            None
        );
        assert_eq!(read_uint(Some(&serde_json::json!(1.0)), "$", &mut c), None);
        assert_eq!(read_uint(Some(&serde_json::json!(-1)), "$", &mut c), None);
        assert_eq!(read_uint(Some(&serde_json::json!("1")), "$", &mut c), None);
        assert_eq!(c.count(), 4);
    }
}
