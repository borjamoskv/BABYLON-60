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
    assert_eq!(run(&["verify", "--policy", "no-json"], b"").0, 2);
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
