//! El crate reproduce el recibo dorado de TypeScript: mismas preimágenes, mismo sobre, mismo hash
//! y, con la misma semilla de prueba, el mismo recibo sellado byte a byte.

mod common;

use babylon60_exec_receipt::canonical::{
    manifest_preimage, node_preimage, receipt_envelope, receipt_hash, signature_input, to_hex,
    EnvelopeFields,
};
use babylon60_exec_receipt::schema::{parse_execution_payload, FailureCollector};
use babylon60_exec_receipt::seal::{parse_unsealed, seal_with_test_seed};
use babylon60_exec_receipt::verify::{verdict_json, verify_execution_payload, Verdict};
use common::{golden, unsealed_of};
use serde_json::Value;

fn strip0x(v: &Value) -> String {
    v.as_str()
        .expect("cadena")
        .trim_start_matches("0x")
        .to_string()
}

#[test]
fn accepts_the_golden_receipt_with_typescript_hash_and_order() {
    let g = golden();
    let verdict = verify_execution_payload(&g.receipt, &g.policy);
    let Verdict::Accepted(accepted) = &verdict else {
        panic!("rechazado: {:?}", verdict.codes());
    };
    assert_eq!(
        to_hex(&accepted.receipt_hash),
        strip0x(&g.intermediate["receipt_hash"])
    );
    assert_eq!(
        format!("0x{}", to_hex(&accepted.signer)),
        g.policy["admitted_authorities"][0]
    );
    assert!(!accepted.chain_link_checked);
    let order: Vec<(&str, usize)> = accepted
        .nodes
        .iter()
        .map(|(id, depth)| (id.as_str(), *depth))
        .collect();
    assert_eq!(
        order,
        [
            ("EV_00001048_000000", 0),
            ("EV_00001048_000001", 1),
            ("EV_00001048_000002", 1),
            ("EV_00001048_000003", 2)
        ]
    );
    let out = verdict_json(&verdict);
    assert_eq!(out["ok"], true);
    assert_eq!(out["chain_link"], "NO_VERIFICADO");
    assert_eq!(out["receipt_hash"], g.intermediate["receipt_hash"]);
}

#[test]
fn intermediates_are_byte_identical_to_typescript() {
    let g = golden();
    let mut c = FailureCollector::default();
    let p = parse_execution_payload(&g.receipt, &mut c).expect("recibo dorado interpretable");
    for n in &p.execution_dag {
        let expected = g.intermediate["node_preimages"][&n.fields.node_id]
            .as_str()
            .expect("preimagen");
        assert_eq!(
            to_hex(&node_preimage(&n.fields)),
            expected,
            "preimagen de {}",
            n.fields.node_id
        );
    }
    let manifest = manifest_preimage(
        &p.execution_id,
        &p.manifest_version,
        &p.causal_clock,
        &p.ingress,
    );
    assert_eq!(
        to_hex(&manifest),
        g.intermediate["manifest_preimage"]
            .as_str()
            .expect("manifiesto")
    );
}

#[test]
fn envelope_and_receipt_hash_are_byte_identical_to_typescript() {
    let g = golden();
    let mut c = FailureCollector::default();
    let p = parse_execution_payload(&g.receipt, &mut c).expect("recibo dorado interpretable");
    let fields = EnvelopeFields {
        execution_id: &p.execution_id,
        clock: p.causal_clock,
        phase_one_manifest_hash: p.seal.phase_one_manifest_hash,
        phase_two_merkle_root: &p.seal.phase_two_merkle_root,
        larsa: p.seal.larsa,
        lean: &p.seal.lean,
        audit: p.audit,
    };
    let env = receipt_envelope(&fields);
    assert_eq!(
        to_hex(&env),
        g.intermediate["envelope"].as_str().expect("sobre")
    );
    assert_eq!(
        to_hex(&signature_input(&env)),
        g.intermediate["signature_input"].as_str().expect("entrada")
    );
    assert_eq!(
        to_hex(&receipt_hash(&env)),
        strip0x(&g.intermediate["receipt_hash"])
    );
}

#[test]
fn emitter_with_the_shared_test_seed_reproduces_the_golden_receipt() {
    let g = golden();
    let unsealed = parse_unsealed(&unsealed_of(&g.receipt)).expect("forma sin sellar válida");
    assert_eq!(seal_with_test_seed(&unsealed, &[0x11; 32]), g.receipt);
}
