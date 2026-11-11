//! Ancla de confianza como texto: cualquier escritura de un entero seguro vale, y lo que no es un
//! ancla válido produce un veredicto `TRUST_POLICY_INVALID`.

mod common;

use babylon60_exec_receipt::verify::verify_with_anchor_text;
use common::golden;

fn anchor_with(extra: &str, weight: &str) -> String {
    let g = golden();
    let key = g.policy["admitted_authorities"][0]
        .as_str()
        .expect("clave admitida")
        .to_owned();
    format!(r#"{{"admitted_authorities":["{key}"],"larsa_required_weight":{weight}{extra}}}"#)
}

fn receipt_bytes() -> Vec<u8> {
    serde_json::to_vec(&golden().receipt).expect("serializable")
}

#[test]
fn integral_weights_are_accepted_in_any_spelling() {
    let receipt = receipt_bytes();
    for weight in ["4", "4.0", "4e0", "0.4e1", "4.000"] {
        assert!(
            verify_with_anchor_text(&receipt, &anchor_with("", weight)).is_accepted(),
            "{weight}"
        );
    }
}

#[test]
fn non_integral_zero_or_out_of_range_weights_are_rejected() {
    let receipt = receipt_bytes();
    for weight in [
        "4.5",
        "0",
        "0.0",
        "-4",
        "4294967296",
        "9007199254740993",
        "1e400",
    ] {
        let verdict = verify_with_anchor_text(&receipt, &anchor_with("", weight));
        assert_eq!(verdict.codes(), ["TRUST_POLICY_INVALID"], "{weight}");
    }
}

#[test]
fn previous_receipt_sequence_follows_the_same_rule() {
    let receipt = receipt_bytes();
    let chain = |seq: &str| {
        anchor_with(
            &format!(
                r#","previous_receipt":{{"receipt_hash":"0x{}","seq_id":{seq}}}"#,
                "ab".repeat(32)
            ),
            "4",
        )
    };
    for seq in ["0.0", "0e0", "-0.0"] {
        assert_eq!(
            verify_with_anchor_text(&receipt, &chain(seq)).codes(),
            ["CHAIN_LINK_MISMATCH"],
            "{seq}"
        );
    }
    for seq in ["0.5", "-1", "1e400"] {
        assert_eq!(
            verify_with_anchor_text(&receipt, &chain(seq)).codes(),
            ["TRUST_POLICY_INVALID"],
            "{seq}"
        );
    }
}

#[test]
fn a_repeated_key_in_the_anchor_is_rejected() {
    let receipt = receipt_bytes();
    let verdict =
        verify_with_anchor_text(&receipt, &anchor_with(r#","larsa_required_weight":1"#, "4"));
    assert_eq!(verdict.codes(), ["TRUST_POLICY_INVALID"]);
}

#[test]
fn an_anchor_that_is_not_json_is_a_verdict_not_a_panic() {
    let receipt = receipt_bytes();
    for text in ["", "no es json", "[1,2]", "\u{feff}{}"] {
        assert_eq!(
            verify_with_anchor_text(&receipt, text).codes(),
            ["TRUST_POLICY_INVALID"],
            "{text:?}"
        );
    }
}
