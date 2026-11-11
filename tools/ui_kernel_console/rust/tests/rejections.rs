//! Cada alteración de un recibo válido se rechaza con el código que también emite TypeScript.

mod common;

use babylon60_exec_receipt::verify::{verify_execution_payload, Verdict};
use common::golden;
use serde_json::{json, Value};

fn codes_after(change: impl FnOnce(&mut Value)) -> Vec<&'static str> {
    let g = golden();
    let mut receipt = g.receipt.clone();
    change(&mut receipt);
    verify_execution_payload(&receipt, &g.policy).codes()
}

fn codes_with_policy(change: impl FnOnce(&mut Value)) -> (Vec<&'static str>, Verdict) {
    let g = golden();
    let mut policy = g.policy.clone();
    change(&mut policy);
    let verdict = verify_execution_payload(&g.receipt, &policy);
    (verdict.codes(), verdict)
}

#[test]
fn covered_fields_without_their_own_check_fall_to_the_signature() {
    assert_eq!(
        codes_after(|r| r["audit_metrics"]["memory_bytes"] = json!(1)),
        ["ED25519_SIGNATURE_INVALID"]
    );
    assert_eq!(
        codes_after(|r| r["cryptographic_seal"]["larsa_commit"]["heuristic_weight"] = json!(9)),
        ["ED25519_SIGNATURE_INVALID"]
    );
}

#[test]
fn manifest_fields_are_bound_by_the_phase_one_commitment() {
    // El reloj causal entra en el manifiesto y también en el sobre: fallan ambas comprobaciones.
    assert_eq!(
        codes_after(|r| r["causal_clock"]["seq_id"] = json!(4097)),
        ["ED25519_SIGNATURE_INVALID", "MANIFEST_HASH_MISMATCH"]
    );
    assert_eq!(
        codes_after(|r| r["ingress"]["payload_raw"] = json!("{}")),
        ["MANIFEST_HASH_MISMATCH"]
    );
}

#[test]
fn node_changes_break_the_leaf_and_the_root() {
    let codes = codes_after(|r| r["execution_dag"][3]["reduction_steps"] = json!(32));
    assert_eq!(codes, ["LEAF_HASH_MISMATCH", "MERKLE_ROOT_MISMATCH"]);
    let codes = codes_after(|r| r["execution_dag"][0]["smt_verified"] = json!(false));
    assert!(codes.contains(&"COMMITTED_WITHOUT_SMT"), "{codes:?}");
}

#[test]
fn dag_shape_rules() {
    let dangling =
        codes_after(|r| r["execution_dag"][1]["parent_ids"] = json!(["EV_00001048_000009"]));
    assert!(
        dangling.contains(&"DAG_DANGLING_PARENT_REF"),
        "{dangling:?}"
    );
    let cycle =
        codes_after(|r| r["execution_dag"][0]["parent_ids"] = json!(["EV_00001048_000003"]));
    assert!(cycle.contains(&"DAG_CYCLE_DETECTED"), "{cycle:?}");
    let dup = codes_after(|r| {
        r["execution_dag"][1]["parent_ids"] = json!(["EV_00001048_000000", "EV_00001048_000000"])
    });
    assert!(dup.contains(&"DAG_DUPLICATE_PARENT_REF"), "{dup:?}");
    let empty = codes_after(|r| r["execution_dag"] = json!([]));
    assert!(empty.contains(&"DAG_EMPTY"), "{empty:?}");
}

#[test]
fn declared_lean_status_must_be_clean() {
    let codes = codes_after(|r| r["cryptographic_seal"]["lean4_proof"]["sorry_count"] = json!(1));
    assert!(codes.contains(&"LEAN4_PROOF_INVALID"), "{codes:?}");
}

#[test]
fn unknown_keys_and_wrong_types_are_schema_failures() {
    let extra = codes_after(|r| {
        r.as_object_mut()
            .expect("objeto")
            .insert("extra".into(), json!(1));
    });
    assert_eq!(extra, ["SCHEMA_INVALID"]);
    assert_eq!(
        codes_after(|r| r["causal_clock"]["seq_id"] = json!("4096")),
        ["SCHEMA_INVALID"]
    );
    assert_eq!(
        codes_after(|r| r["audit_metrics"]["worm_txid"] = json!("0xABCD")),
        ["SCHEMA_MALFORMED_HEX"]
    );
}

#[test]
fn trust_policy_sets_quorum_and_chain_checkpoint() {
    let g = golden();
    let weight = g.receipt["cryptographic_seal"]["larsa_commit"]["heuristic_weight"]
        .as_u64()
        .expect("peso");
    let (codes, _) = codes_with_policy(|p| p["larsa_required_weight"] = json!(weight + 1));
    assert_eq!(codes, ["QUORUM_INSUFFICIENT"]);
    let (codes, _) = codes_with_policy(|p| p["larsa_required_weight"] = json!(0));
    assert_eq!(codes, ["TRUST_POLICY_INVALID"]);
    let (codes, _) = codes_with_policy(|p| p["admitted_authorities"] = json!([]));
    assert_eq!(codes, ["TRUST_POLICY_INVALID"]);

    let prev = g.receipt["audit_metrics"]["prev_receipt_hash"].clone();
    let seq = g.receipt["causal_clock"]["seq_id"].as_u64().expect("seq");
    let (codes, verdict) = codes_with_policy(|p| {
        p["previous_receipt"] = json!({ "receipt_hash": prev, "seq_id": seq - 1 })
    });
    assert!(codes.is_empty(), "{codes:?}");
    let Verdict::Accepted(accepted) = verdict else {
        unreachable!()
    };
    assert!(accepted.chain_link_checked);
    let (codes, _) = codes_with_policy(|p| {
        p["previous_receipt"] = json!({ "receipt_hash": prev, "seq_id": seq })
    });
    assert_eq!(codes, ["CHAIN_LINK_MISMATCH"]);
}
