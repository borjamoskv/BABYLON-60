//! Cotas y ramas de la política de confianza, con los mismos valores que produce TypeScript (las
//! referencias salen de `sealReceipt` y `verifyExecutionPayloadUtf8`). Cada caso fija el conjunto
//! exacto de códigos: una regresión que añada un código espurio también falla.
//!
//! Los recibos fuera de cota se sellan con `Unsealed` directo: el emisor de prueba valida cotas
//! antes de sellar, y aquí interesa el veredicto del verificador sobre un recibo que ya existe.

use std::collections::BTreeSet;

use babylon60_exec_receipt::canonical::{
    AuditMetrics, CausalClock, Ingress, LarsaCommit, Lean4Proof, NodeFields,
};
use babylon60_exec_receipt::json_text::MAX_JSON_TEXT_UTF16;
use babylon60_exec_receipt::seal::{seal_with_test_seed, Unsealed};
use babylon60_exec_receipt::verify::{
    verify_execution_payload, verify_execution_payload_json, Verdict,
};
use serde_json::{json, Value};

const SEED: [u8; 32] = [0x11; 32];

fn id(tick: u64, seq: u64) -> String {
    format!("EV_{tick:08}_{seq:06}")
}

fn node(i: u64, parent_ids: Vec<String>) -> NodeFields {
    NodeFields {
        node_id: id(2, i),
        parent_ids,
        state_status: "COMMITTED".into(),
        smt_verified: true,
        reduction_steps: 1,
        violation_reason: None,
    }
}

/// Sella sin validar cotas, igual que TypeScript.
fn seal_unchecked(execution_id: &str, nodes: Vec<NodeFields>, clock_seq: u64) -> Value {
    let unsealed = Unsealed {
        execution_id: execution_id.into(),
        clock: CausalClock {
            policy_epoch: 1,
            logical_tick: 2,
            seq_id: clock_seq,
        },
        manifest_version: "v1.0.0".into(),
        ingress: Ingress {
            agent_id: "agent://x".into(),
            policy_profile: "STRICT_DETERMINISTIC".into(),
            payload_raw: "{}".into(),
        },
        nodes,
        larsa: LarsaCommit {
            trace_hash: [0x11; 32],
            heuristic_weight: 2,
        },
        lean: Lean4Proof {
            status: "VERIFIED_NO_SORRY".into(),
            theorem_ident: "Babylon.T".into(),
            sorry_count: 0,
        },
        audit: AuditMetrics {
            memory_bytes: 1,
            prev_receipt_hash: [0; 32],
            worm_txid: [0; 32],
        },
    };
    seal_with_test_seed(&unsealed, &SEED)
}

fn seal_nodes(nodes: Vec<NodeFields>) -> Value {
    seal_unchecked("b60-exec-limits-01", nodes, 3)
}

/// Clave pública de la semilla `[byte; 32]`, en la forma `0x…` del ancla.
fn public_key(byte: u8) -> String {
    let key = ed25519_dalek::SigningKey::from_bytes(&[byte; 32]);
    let hex: String = key
        .verifying_key()
        .to_bytes()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    format!("0x{hex}")
}

fn admitted_policy() -> Value {
    json!({ "admitted_authorities": [public_key(0x11)], "larsa_required_weight": 1 })
}

fn code_set(verdict: &Verdict) -> BTreeSet<&'static str> {
    verdict.codes().into_iter().collect()
}

fn expect_codes(verdict: &Verdict, expected: &[&'static str]) {
    let want: BTreeSet<&'static str> = expected.iter().copied().collect();
    assert_eq!(
        code_set(verdict),
        want,
        "códigos distintos de los de TypeScript"
    );
}

#[test]
fn node_count_limit_is_4096() {
    let at_limit = seal_nodes((0..4096).map(|i| node(i, vec![])).collect());
    assert!(verify_execution_payload(&at_limit, &admitted_policy()).is_accepted());
    let over = seal_nodes((0..4097).map(|i| node(i, vec![])).collect());
    expect_codes(
        &verify_execution_payload(&over, &admitted_policy()),
        &["LIMIT_EXCEEDED"],
    );
}

#[test]
fn parents_per_node_limit_is_64() {
    // Hijo con n padres distintos: 64 se admiten; 65 superan la cota por nodo.
    let with_parents = |n: u64| {
        let mut nodes: Vec<NodeFields> = (0..65).map(|i| node(i, vec![])).collect();
        nodes[64] = node(64, (0..n).map(|k| id(2, k)).collect());
        nodes
    };
    let at_limit = seal_nodes(with_parents(64));
    let over = seal_nodes(with_parents(65));
    expect_codes(
        &verify_execution_payload(&over, &admitted_policy()),
        &["LIMIT_EXCEEDED"],
    );
    assert!(
        !code_set(&verify_execution_payload(&at_limit, &admitted_policy()))
            .contains("LIMIT_EXCEEDED")
    );
}

#[test]
fn edge_limit_is_16384() {
    // 17370 aristas: por encima de 16384.
    let dense: Vec<NodeFields> = (0..320)
        .map(|i| node(i, (0..i.min(60)).map(|k| id(2, i - 1 - k)).collect()))
        .collect();
    let receipt = seal_nodes(dense);
    expect_codes(
        &verify_execution_payload(&receipt, &admitted_policy()),
        &["LIMIT_EXCEEDED"],
    );
}

#[test]
fn execution_id_longer_than_128_is_limit_exceeded() {
    let receipt = seal_unchecked(&"x".repeat(129), vec![node(0, vec![])], 3);
    expect_codes(
        &verify_execution_payload(&receipt, &admitted_policy()),
        &["LIMIT_EXCEEDED"],
    );
}

#[test]
fn failure_list_is_truncated_at_64_with_a_note() {
    let nodes: Vec<NodeFields> = (0..70)
        .map(|i| NodeFields {
            smt_verified: false,
            ..node(i, vec![])
        })
        .collect();
    let verdict = verify_execution_payload(&seal_nodes(nodes), &admitted_policy());
    let Verdict::Rejected { failures, .. } = &verdict else {
        panic!("debía rechazarse");
    };
    assert_eq!(failures.len(), 64);
    assert!(failures
        .last()
        .expect("fallo")
        .detail
        .contains("lista truncada"));
    expect_codes(&verdict, &["COMMITTED_WITHOUT_SMT"]);
}

#[test]
fn admitted_authorities_limit_is_64_and_duplicates_are_rejected() {
    let keys: Vec<String> = (1..=65u8).map(public_key).collect();
    let receipt = seal_nodes(vec![node(0, vec![])]);
    let sixty_four = json!({ "admitted_authorities": keys[..64], "larsa_required_weight": 1 });
    let sixty_five = json!({ "admitted_authorities": keys, "larsa_required_weight": 1 });
    let repeated =
        json!({ "admitted_authorities": [keys[0], keys[0]], "larsa_required_weight": 1 });
    // Sesenta y cuatro claves válidas: el ancla es aceptable (la firmante no está entre ellas, así
    // que el veredicto no es TRUST_POLICY_INVALID).
    assert!(!code_set(&verify_execution_payload(&receipt, &sixty_four))
        .contains("TRUST_POLICY_INVALID"));
    expect_codes(
        &verify_execution_payload(&receipt, &sixty_five),
        &["TRUST_POLICY_INVALID"],
    );
    expect_codes(
        &verify_execution_payload(&receipt, &repeated),
        &["TRUST_POLICY_INVALID"],
    );
}

#[test]
fn each_anchor_shape_branch_is_rejected_as_trust_policy_invalid() {
    let receipt = seal_nodes(vec![node(0, vec![])]);
    let base = admitted_policy();
    let with_prev = |prev: Value| {
        let mut p = base.clone();
        p["previous_receipt"] = prev;
        p
    };
    let hash = format!("0x{}", "ab".repeat(32));
    let mut weight_string = base.clone();
    weight_string["larsa_required_weight"] = json!("4");
    let mut weight_fraction = base.clone();
    weight_fraction["larsa_required_weight"] = json!(4.5);
    let mut authorities_object = base.clone();
    authorities_object["admitted_authorities"] = json!({ "k": 1 });
    let mut authorities_upper = base.clone();
    authorities_upper["admitted_authorities"] = json!([public_key(0x11).to_uppercase()]);
    let mut extra_top = base.clone();
    extra_top["comment"] = json!("x");
    let anchors = [
        weight_string,
        weight_fraction,
        authorities_object,
        authorities_upper,
        extra_top,
        with_prev(Value::Null),
        with_prev(json!({ "receipt_hash": hash, "seq_id": 1, "x": 1 })),
        with_prev(json!({ "receipt_hash": "0xAB", "seq_id": 1 })),
        with_prev(json!({ "receipt_hash": hash, "seq_id": -1 })),
        with_prev(json!({ "receipt_hash": hash })),
    ];
    for policy in anchors {
        expect_codes(
            &verify_execution_payload(&receipt, &policy),
            &["TRUST_POLICY_INVALID"],
        );
    }
}

#[test]
fn the_receipt_text_limit_is_exactly_the_utf16_maximum() {
    let receipt = seal_nodes(vec![node(0, vec![])]);
    let text = serde_json::to_string(&receipt).expect("serializable");
    // Espacios tras la llave de apertura: whitespace JSON válido, sin cambiar el recibo.
    let padded = |n: usize| format!("{{{}{}", " ".repeat(n), &text[1..]);
    let exact = padded(MAX_JSON_TEXT_UTF16 - text.len());
    assert_eq!(exact.encode_utf16().count(), MAX_JSON_TEXT_UTF16);
    assert!(verify_execution_payload_json(&exact, &admitted_policy()).is_accepted());
    let one_more = padded(MAX_JSON_TEXT_UTF16 - text.len() + 1);
    expect_codes(
        &verify_execution_payload_json(&one_more, &admitted_policy()),
        &["SCHEMA_INVALID"],
    );
}

#[test]
fn integers_above_the_safe_range_are_schema_errors() {
    let above = seal_unchecked(
        "b60-exec-limits-01",
        vec![node(0, vec![])],
        9_007_199_254_740_992,
    );
    expect_codes(
        &verify_execution_payload(&above, &admitted_policy()),
        &["SCHEMA_INVALID"],
    );
    let at_max = seal_unchecked(
        "b60-exec-limits-01",
        vec![node(0, vec![])],
        9_007_199_254_740_991,
    );
    // Sellado con ese mismo valor, el recibo es coherente y se acepta: 2^53-1 es el máximo admitido.
    assert!(verify_execution_payload(&at_max, &admitted_policy()).is_accepted());
}

#[test]
fn a_chain_checkpoint_with_an_equal_sequence_is_chain_link_mismatch() {
    let receipt = seal_nodes(vec![node(0, vec![])]);
    // El hash previo coincide, pero el punto de control tiene la misma secuencia: no es posterior.
    let policy = json!({
        "admitted_authorities": [public_key(0x11)],
        "larsa_required_weight": 1,
        "previous_receipt": { "receipt_hash": format!("0x{}", "00".repeat(32)), "seq_id": 3 },
    });
    expect_codes(
        &verify_execution_payload(&receipt, &policy),
        &["CHAIN_LINK_MISMATCH"],
    );
}

#[test]
fn a_duplicate_node_id_is_only_dag_duplicate_node_id() {
    let receipt = seal_nodes(vec![node(0, vec![]), node(0, vec![])]);
    expect_codes(
        &verify_execution_payload(&receipt, &admitted_policy()),
        &["DAG_DUPLICATE_NODE_ID"],
    );
}
