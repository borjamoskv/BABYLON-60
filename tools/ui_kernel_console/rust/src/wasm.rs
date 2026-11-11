//! Binding WebAssembly (`wasm-bindgen`). Solo verificación: la página recibe un veredicto en JSON
//! y nunca maneja claves privadas. El cruce de frontera es por copia de valor (bytes y texto), sin
//! punteros ni referencias compartidas.

use wasm_bindgen::prelude::wasm_bindgen;

use crate::verify::{verdict_json, verify_with_anchor_text};

/// Verifica un recibo tal como llegó del transporte (bytes UTF-8) contra un ancla de confianza en
/// JSON (`{ admitted_authorities, larsa_required_weight, previous_receipt? }`). Devuelve el
/// veredicto en JSON. Toda entrada produce un veredicto.
#[wasm_bindgen(js_name = verifyReceiptBytes)]
pub fn verify_receipt_bytes(receipt_utf8: &[u8], policy_json: &str) -> String {
    let verdict = verify_with_anchor_text(receipt_utf8, policy_json);
    verdict_json(&verdict).to_string()
}
