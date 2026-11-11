//! Binding WebAssembly (`wasm-bindgen`). Solo verificación: la página recibe un veredicto en JSON
//! y nunca maneja claves privadas. El cruce de frontera es por copia de valor (bytes y texto), sin
//! punteros ni referencias compartidas.

use wasm_bindgen::prelude::wasm_bindgen;

use crate::verify::{rejection, verdict_json, verify_execution_payload_utf8};

/// Verifica un recibo tal como llegó del transporte (bytes UTF-8) contra un ancla de confianza en
/// JSON (`{ admitted_authorities, larsa_required_weight, previous_receipt? }`). Devuelve el
/// veredicto en JSON. Toda entrada produce un veredicto.
#[wasm_bindgen(js_name = verifyReceiptBytes)]
pub fn verify_receipt_bytes(receipt_utf8: &[u8], policy_json: &str) -> String {
    let verdict = match serde_json::from_str::<serde_json::Value>(policy_json) {
        Ok(policy) => verify_execution_payload_utf8(receipt_utf8, &policy),
        Err(_) => rejection(
            "TRUST_POLICY_INVALID",
            "el ancla de confianza no es JSON válido",
        ),
    };
    verdict_json(&verdict).to_string()
}
