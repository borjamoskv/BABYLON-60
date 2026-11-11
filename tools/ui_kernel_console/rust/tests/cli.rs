//! CLI: códigos de salida y formato de `verify` y `batch`.

mod common;

use std::io::Write;
use std::process::{Command, Stdio};

use common::{golden, unsealed_of};
use serde_json::{json, Value};

fn run(args: &[&str], stdin: &[u8]) -> (i32, String) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_b60-exec-receipt"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .expect("CLI");
    child
        .stdin
        .take()
        .expect("stdin")
        .write_all(stdin)
        .expect("escritura");
    let out = child.wait_with_output().expect("salida");
    (
        out.status.code().expect("código"),
        String::from_utf8(out.stdout).expect("UTF-8"),
    )
}

fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}

#[test]
fn verify_exit_codes() {
    let g = golden();
    let policy = g.policy.to_string();
    let text = g.receipt.to_string();
    let (code, out) = run(&["verify", "--policy", &policy], text.as_bytes());
    assert_eq!(code, 0);
    assert_eq!(
        serde_json::from_str::<Value>(&out).expect("JSON")["ok"],
        true
    );
    let (code, out) = run(&["verify", "--policy", &policy], b"{}");
    assert_eq!(code, 1);
    assert_eq!(
        serde_json::from_str::<Value>(&out).expect("JSON")["ok"],
        false
    );
    assert_eq!(run(&["verify"], b"").0, 2);
    // Un ancla que no es JSON no es un uso incorrecto: produce un veredicto rechazado.
    assert_eq!(run(&["verify", "--policy", "no-json"], b"{}").0, 1);
    assert_eq!(run(&["desconocida"], b"").0, 2);
}

#[test]
fn batch_answers_one_line_per_request() {
    let g = golden();
    let requests = [
        json!({ "op": "verify", "receipt_hex": hex(g.receipt.to_string().as_bytes()), "policy": g.policy }),
        json!({ "op": "seal", "unsealed": unsealed_of(&g.receipt), "test_seed_hex": "11".repeat(32) }),
        json!({ "op": "verify", "receipt_hex": "zz", "policy": g.policy }),
    ];
    let input: String = requests.iter().map(|r| format!("{r}\n")).collect();
    let (code, out) = run(&["batch"], input.as_bytes());
    assert_eq!(code, 0);
    let lines: Vec<Value> = out
        .lines()
        .map(|l| serde_json::from_str(l).expect("JSON"))
        .collect();
    assert_eq!(lines.len(), 3);
    assert_eq!(lines[0]["ok"], true);
    assert_eq!(lines[1]["receipt"], g.receipt);
    assert!(lines[2]["error"].is_string());
}

#[cfg(unix)]
#[test]
fn non_utf8_policy_argument_is_a_usage_error() {
    use std::os::unix::ffi::OsStrExt;
    let output = Command::new(env!("CARGO_BIN_EXE_b60-exec-receipt"))
        .arg("verify")
        .arg("--policy")
        .arg(std::ffi::OsStr::from_bytes(b"\xff"))
        .stdin(Stdio::null())
        .output()
        .expect("CLI");
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
}

#[cfg(unix)]
#[test]
fn closed_stdout_is_an_io_error_not_a_panic() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_b60-exec-receipt"))
        .args(["verify", "--policy", "{}"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("CLI");
    drop(child.stdout.take());
    child
        .stdin
        .take()
        .expect("stdin")
        .write_all(b"{}")
        .expect("escritura");
    let output = child.wait_with_output().expect("salida");
    assert_eq!(
        output.status.code(),
        Some(2),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn oversize_input_is_rejected_with_an_honest_detail() {
    let big = vec![b'x'; 16 * 1024 * 1024 + 1];
    let (code, out) = run(&["verify", "--policy", "{}"], &big);
    assert_eq!(code, 1);
    let verdict: Value = serde_json::from_str(&out).expect("JSON");
    let detail = verdict["failures"][0]["detail"].as_str().expect("detalle");
    assert!(detail.contains("supera 16777216 bytes"), "{detail}");
}

#[test]
fn an_unreadable_anchor_is_a_rejected_verdict_not_a_usage_error() {
    let text = golden().receipt.to_string();
    let (code, out) = run(
        &["verify", "--policy", "{\"larsa_required_weight\":1e400}"],
        text.as_bytes(),
    );
    assert_eq!(code, 1);
    let verdict: Value = serde_json::from_str(&out).expect("JSON");
    assert_eq!(verdict["failures"][0]["code"], "TRUST_POLICY_INVALID");
}

#[test]
fn batch_takes_the_anchor_as_text_and_reports_invalid_anchors_as_verdicts() {
    let g = golden();
    let receipt_hex = hex(g.receipt.to_string().as_bytes());
    let requests = [
        json!({ "op": "verify", "receipt_hex": receipt_hex, "policy": g.policy.to_string() }),
        json!({ "op": "verify", "receipt_hex": receipt_hex, "policy": "{\"larsa_required_weight\":1e400}" }),
        json!({ "op": "verify", "receipt_hex": receipt_hex, "policy": g.policy }),
    ];
    let input: String = requests.iter().map(|r| format!("{r}\n")).collect();
    let (code, out) = run(&["batch"], input.as_bytes());
    assert_eq!(code, 0);
    let lines: Vec<Value> = out
        .lines()
        .map(|l| serde_json::from_str(l).expect("JSON"))
        .collect();
    assert_eq!(lines.len(), 3);
    assert_eq!(lines[0]["ok"], true);
    assert_eq!(lines[1]["codes"], json!(["TRUST_POLICY_INVALID"]));
    assert_eq!(lines[2]["ok"], true);
}

#[test]
fn batch_answers_a_line_with_a_repeated_key_with_an_error() {
    let (code, out) = run(
        &["batch"],
        b"{\"op\":\"verify\",\"op\":\"verify\",\"receipt_hex\":\"\",\"policy\":{}}\n",
    );
    assert_eq!(code, 0);
    assert_eq!(out.trim(), r#"{"error":"clave duplicada: op"}"#);
}
