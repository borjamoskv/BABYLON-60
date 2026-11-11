//! Entradas de texto y de bytes: las reglas que también aplica TypeScript antes de interpretar.

mod common;

use babylon60_exec_receipt::verify::{
    verify_execution_payload_json, verify_execution_payload_utf8, Verdict,
};
use common::golden;

fn golden_text() -> (String, serde_json::Value) {
    let g = golden();
    (
        serde_json::to_string(&g.receipt).expect("serializable"),
        g.policy,
    )
}

#[test]
fn golden_text_and_bytes_are_accepted() {
    let (text, policy) = golden_text();
    assert!(verify_execution_payload_json(&text, &policy).is_accepted());
    assert!(verify_execution_payload_utf8(text.as_bytes(), &policy).is_accepted());
}

#[test]
fn non_integer_number_tokens_are_rejected_before_the_schema() {
    let (text, policy) = golden_text();
    for replacement in [
        "\"reduction_steps\":14.0",
        "\"reduction_steps\":1.4e1",
        "\"reduction_steps\":14E0",
    ] {
        let altered = text.replacen("\"reduction_steps\":14", replacement, 1);
        assert_ne!(altered, text);
        assert_eq!(
            verify_execution_payload_json(&altered, &policy).codes(),
            ["SCHEMA_INVALID"],
            "{replacement}"
        );
    }
}

#[test]
fn unpaired_surrogate_escapes_bom_and_invalid_utf8_are_rejected() {
    let (text, policy) = golden_text();
    let lone = text.replacen("\"op\\\"", "\"\\ud800op\\\"", 1);
    assert_ne!(lone, text);
    assert_eq!(
        verify_execution_payload_json(&lone, &policy).codes(),
        ["SCHEMA_INVALID"]
    );
    let bom = format!("\u{feff}{text}");
    assert_eq!(
        verify_execution_payload_json(&bom, &policy).codes(),
        ["SCHEMA_INVALID"]
    );
    let mut bytes = text.into_bytes();
    bytes.push(0xff);
    assert_eq!(
        verify_execution_payload_utf8(&bytes, &policy).codes(),
        ["SCHEMA_INVALID"]
    );
}

#[test]
fn nesting_limit_is_127_containers() {
    let (_, policy) = golden_text();
    let nested = |n: usize| format!("{}{}", "[".repeat(n), "]".repeat(n));
    let detail_of = |text: &str| match verify_execution_payload_json(text, &policy) {
        Verdict::Rejected { failures, .. } => failures[0].detail.clone(),
        Verdict::Accepted(_) => panic!("no debía aceptarse"),
    };
    // 127 contenedores: serde_json los lee y el esquema los rechaza por forma.
    let inside = detail_of(&nested(127));
    assert!(!inside.contains("no es JSON v"), "{inside}");
    // 128 contenedores: serde_json ya no los lee, y el motivo es el de texto no admitido.
    let outside = detail_of(&nested(128));
    // El detalle escapa las no ASCII («á» sale como \u00e1): se compara el tramo ASCII.
    assert!(outside.contains("no es JSON v"), "{outside}");
}

#[test]
fn a_repeated_key_in_the_receipt_is_rejected_even_when_the_last_copy_is_valid() {
    let (text, policy) = golden_text();
    let id = golden().receipt["execution_id"]
        .as_str()
        .expect("id")
        .to_owned();
    let forged = text.replacen(
        &format!("\"execution_id\":\"{id}\""),
        &format!("\"execution_id\":\"FORGED-first\",\"execution_id\":\"{id}\""),
        1,
    );
    assert_ne!(forged, text);
    assert_eq!(
        verify_execution_payload_json(&forged, &policy).codes(),
        ["SCHEMA_INVALID"]
    );
}
