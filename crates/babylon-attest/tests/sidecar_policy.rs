//! The `serve` sidecar applies the same licence policy as the `attest` command and only accepts
//! a bearer secret provisioned by the operator. Temporary fixtures only.
#![cfg(unix)]

use babylon_attest::license::{LicensePayload, SignedLicense};
use ed25519_dalek::{Signer, SigningKey};
use std::fs;
use std::io::{Read, Write};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const VENDOR_SEED: [u8; 32] = [0x11; 32];
const TOKEN: &str = "operator-provisioned-token";

fn signed_licence(valid_until: u64) -> String {
    let payload = LicensePayload {
        org: "Fixture Org".into(),
        tier: "enterprise-byoc".into(),
        max_agents: 5,
        valid_until,
        features: vec!["attest".into()],
    };
    let signature =
        SigningKey::from_bytes(&VENDOR_SEED).sign(&serde_json::to_vec(&payload).unwrap());
    serde_json::to_string(&SignedLicense {
        payload,
        signature_hex: hex::encode(signature.to_bytes()),
    })
    .unwrap()
}

fn tomorrow() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
        + 86_400
}

struct Sidecar {
    child: Child,
    home: PathBuf,
}

impl Drop for Sidecar {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
        let _ = fs::remove_dir_all(&self.home);
    }
}

impl Sidecar {
    /// Starts `babylon-attest serve` on a fresh home, optionally with a licence and a token.
    fn start(licence: Option<&str>, token: Option<&str>) -> Self {
        static SEQ: AtomicU64 = AtomicU64::new(0);
        let home = std::env::temp_dir().join(format!(
            "b60-sidecar-{}-{}",
            std::process::id(),
            SEQ.fetch_add(1, Ordering::Relaxed)
        ));
        let _ = fs::remove_dir_all(&home);
        fs::create_dir_all(&home).unwrap();
        if let Some(licence) = licence {
            fs::write(home.join("license.key"), licence).unwrap();
        }
        let vendor_pub = hex::encode(
            SigningKey::from_bytes(&VENDOR_SEED)
                .verifying_key()
                .to_bytes(),
        );
        let mut cmd = Command::new(env!("CARGO_BIN_EXE_babylon-attest"));
        cmd.env("BABYLON_HOME", &home)
            .env_remove("BABYLON60_LICENSE_VENDOR_SEED")
            .env("BABYLON60_LICENSE_VENDOR_PUBLIC_KEY", vendor_pub)
            .env_remove("BABYLON_ATTEST_TOKEN")
            .args(["serve", "--socket"])
            .arg(home.join("s.sock"))
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        if let Some(token) = token {
            cmd.env("BABYLON_ATTEST_TOKEN", token);
        }
        Self {
            child: cmd.spawn().expect("spawn babylon-attest serve"),
            home,
        }
    }

    /// POSTs `/attest` with the given token header value and returns the HTTP status line.
    fn attest(&self, token: &str) -> String {
        let body = r#"{"action":"sidecar"}"#;
        let raw = format!(
            "POST /attest HTTP/1.1\r\nHost: localhost\r\nX-Babylon-Token: {token}\r\nContent-Length: {}\r\n\r\n{body}",
            body.len()
        );
        for _ in 0..100 {
            if let Ok(mut stream) = UnixStream::connect(self.home.join("s.sock")) {
                stream
                    .set_read_timeout(Some(Duration::from_secs(10)))
                    .unwrap();
                stream.write_all(raw.as_bytes()).unwrap();
                let mut response = String::new();
                let _ = stream.read_to_string(&mut response);
                return response.lines().next().unwrap_or("").to_string();
            }
            std::thread::sleep(Duration::from_millis(100));
        }
        panic!("sidecar socket never became connectable");
    }

    fn blocks(&self) -> usize {
        chain_len(&self.home)
    }
}

fn chain_len(home: &Path) -> usize {
    fs::read_to_string(home.join("ledger").join("chain.jsonl"))
        .map(|t| t.lines().filter(|l| !l.trim().is_empty()).count())
        .unwrap_or(0)
}

#[test]
fn valid_token_and_licence_append_a_block() {
    let sidecar = Sidecar::start(Some(&signed_licence(tomorrow())), Some(TOKEN));
    assert!(sidecar.attest(TOKEN).starts_with("HTTP/1.1 200"));
    assert_eq!(sidecar.blocks(), 1);
}

#[test]
fn expired_licence_halts_sidecar_appends() {
    let sidecar = Sidecar::start(Some(&signed_licence(1)), Some(TOKEN));
    assert!(sidecar.attest(TOKEN).starts_with("HTTP/1.1 403"));
    assert_eq!(sidecar.blocks(), 0);
}

#[test]
fn invalid_licence_halts_sidecar_appends() {
    let sidecar = Sidecar::start(Some("not a licence"), Some(TOKEN));
    assert!(sidecar.attest(TOKEN).starts_with("HTTP/1.1 403"));
    assert_eq!(sidecar.blocks(), 0);
}

#[test]
fn licence_contents_are_not_a_credential_when_no_token_is_provisioned() {
    let licence = signed_licence(tomorrow());
    let sidecar = Sidecar::start(Some(&licence), None);
    assert!(sidecar.attest(&licence).starts_with("HTTP/1.1 401"));
    assert_eq!(sidecar.blocks(), 0);
}

#[test]
fn wrong_or_licence_token_is_rejected_when_a_token_is_provisioned() {
    let licence = signed_licence(tomorrow());
    let sidecar = Sidecar::start(Some(&licence), Some(TOKEN));
    for presented in ["wrong", &licence, "operator-provisioned-tokeN", ""] {
        assert!(
            sidecar.attest(presented).starts_with("HTTP/1.1 401"),
            "{presented:?}"
        );
    }
    assert_eq!(sidecar.blocks(), 0);
}
