//! Binding WebAssembly (`wasm-bindgen`). Solo verificación: la página recibe un veredicto en JSON
//! y nunca maneja claves privadas.
//!
//! La entrada llega como objetos JS, no como copias: `wasm-bindgen` copiaría un `&[u8]` completo a
//! memoria lineal antes de llamar a Rust, y una entrada de 2 GiB provocaría un trap en lugar de un
//! veredicto. Aquí el tamaño se mide en el objeto JS y solo después se copia lo admitido.

use js_sys::{JsString, Uint8Array};
use wasm_bindgen::prelude::wasm_bindgen;
use wasm_bindgen::{JsCast, JsValue};

use crate::verify::{
    rejection, verdict_json, verify_with_anchor_text, MAX_ANCHOR_UTF16, MAX_RECEIPT_BYTES,
};

/// Verifica un recibo (`Uint8Array` con UTF-8) contra un ancla de confianza dada como texto JSON
/// (`{ admitted_authorities, larsa_required_weight, previous_receipt? }`). Devuelve el veredicto
/// en JSON. Toda entrada produce un veredicto, también las enormes o las que no son texto.
#[wasm_bindgen(js_name = verifyReceiptBytes)]
pub fn verify_receipt_bytes(receipt: &Uint8Array, anchor: &JsValue) -> String {
    let verdict = if receipt.length() as usize > MAX_RECEIPT_BYTES {
        rejection(
            "SCHEMA_INVALID",
            "la entrada supera el máximo admitido y no se interpreta",
        )
    } else if !anchor.is_string() {
        rejection("TRUST_POLICY_INVALID", "el ancla debe llegar como texto")
    } else if anchor.unchecked_ref::<JsString>().length() as usize > MAX_ANCHOR_UTF16 {
        rejection("TRUST_POLICY_INVALID", "el ancla supera el máximo admitido")
    } else {
        match anchor.as_string() {
            Some(text) => verify_with_anchor_text(&receipt.to_vec(), &text),
            None => rejection("TRUST_POLICY_INVALID", "el ancla debe llegar como texto"),
        }
    };
    verdict_json(&verdict).to_string()
}
