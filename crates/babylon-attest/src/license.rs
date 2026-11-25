use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Read;
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

// This seed was previously public. It is retained ONLY to reject its key, never to sign.
const RETIRED_PUBLIC_SEED: &[u8; 32] = b"AGENTS_ARCHI_SOVEREIGN_KEY_2026!";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct LicensePayload {
    pub org: String,
    pub tier: String,
    pub max_agents: u32,
    pub valid_until: u64, // Unix timestamp in seconds
    pub features: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedLicense {
    pub payload: LicensePayload,
    pub signature_hex: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum LicenseStatus {
    Active(LicensePayload),
    CommunityEvaluation {
        events_count: usize,
        max_events: usize,
    },
    Expired {
        org: String,
        expired_at: u64,
    },
    Invalid(String),
}

fn parse_vendor_key(encoded: Option<&str>) -> Result<VerifyingKey, String> {
    let raw = hex::decode(encoded.ok_or("Vendor public key is not provisioned")?)
        .map_err(|_| "Invalid vendor public key hex")?;
    let bytes: [u8; 32] = raw
        .try_into()
        .map_err(|_| "Vendor public key must be 32 bytes")?;
    let key = VerifyingKey::from_bytes(&bytes).map_err(|_| "Invalid vendor public key")?;
    if key.is_weak() || key == SigningKey::from_bytes(RETIRED_PUBLIC_SEED).verifying_key() {
        return Err("Retired publicly compromised vendor key is forbidden".into());
    }
    Ok(key)
}

fn configured_vendor_key() -> Result<VerifyingKey, String> {
    let encoded = std::env::var("BABYLON60_LICENSE_VENDOR_PUBLIC_KEY").ok();
    parse_vendor_key(encoded.as_deref())
}

// Kept for source compatibility; verification itself handles missing provisioning without panic.
pub fn get_vendor_verifying_key() -> VerifyingKey {
    configured_vendor_key().expect("Vendor public key is not safely provisioned")
}

pub fn generate_license(
    org: &str,
    tier: &str,
    max_agents: u32,
    days: u64,
    features: Vec<String>,
    seed: Option<&[u8; 32]>,
) -> SignedLicense {
    try_generate_license(org, tier, max_agents, days, features, seed)
        .expect("Vendor licence signing is not safely provisioned")
}

pub fn try_generate_license(
    org: &str,
    tier: &str,
    max_agents: u32,
    days: u64,
    features: Vec<String>,
    seed: Option<&[u8; 32]>,
) -> Result<SignedLicense, String> {
    if org.trim().is_empty() || max_agents == 0 || days == 0 {
        return Err("Invalid licence scope".into());
    }
    let configured;
    let actual_seed = match seed {
        Some(value) => value,
        None => {
            let encoded = std::env::var("BABYLON60_LICENSE_VENDOR_SEED")
                .map_err(|_| "Vendor signing seed is not provisioned")?;
            let raw = hex::decode(encoded).map_err(|_| "Invalid vendor signing seed")?;
            configured = <[u8; 32]>::try_from(raw).map_err(|_| "Vendor seed must be 32 bytes")?;
            &configured
        }
    };
    if actual_seed == RETIRED_PUBLIC_SEED {
        return Err("Retired publicly compromised vendor seed is forbidden".into());
    }
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("BFT Fallback")
        .as_secs();
    let valid_until = days
        .checked_mul(86400)
        .and_then(|duration| now.checked_add(duration))
        .ok_or("Licence expiry overflow")?;

    let payload = LicensePayload {
        org: org.to_string(),
        tier: tier.to_string(),
        max_agents,
        valid_until,
        features,
    };

    let canonical_bytes = serde_json::to_vec(&payload).expect("Serialization failed");
    let sk = SigningKey::from_bytes(actual_seed);
    let sig: Signature = sk.sign(&canonical_bytes);

    Ok(SignedLicense {
        payload,
        signature_hex: hex::encode(sig.to_bytes()),
    })
}

fn read_claim(path: &Path) -> Result<Option<String>, String> {
    let mut options = fs::OpenOptions::new();
    options.read(true);
    #[cfg(unix)]
    // Reject special files after opening without waiting for a FIFO writer.
    options.custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK);
    let file = match options.open(path) {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err("Cannot open licence file safely".into()),
    };
    if !file
        .metadata()
        .map_err(|_| "Cannot inspect licence file")?
        .is_file()
    {
        return Err("Licence must be a regular file".into());
    }
    let mut content = String::new();
    file.take(8193)
        .read_to_string(&mut content)
        .map_err(|_| "Cannot read licence file")?;
    if content.len() > 8192 {
        return Err("Licence file too large".into());
    }
    Ok(Some(content))
}

pub fn check_license_file<P: AsRef<Path>>(path: P, current_events_count: usize) -> LicenseStatus {
    let content = match read_claim(path.as_ref()) {
        Ok(Some(content)) => content,
        Ok(None) => {
            return LicenseStatus::CommunityEvaluation {
                events_count: current_events_count,
                max_events: 1000,
            }
        }
        Err(error) => return LicenseStatus::Invalid(error),
    };
    let key = match configured_vendor_key() {
        Ok(key) => key,
        Err(error) => return LicenseStatus::Invalid(error),
    };
    validate_claim(&content, &key)
}

#[cfg(test)]
fn check_license_with_key<P: AsRef<Path>>(
    path: P,
    current_events_count: usize,
    vk: &VerifyingKey,
) -> LicenseStatus {
    match read_claim(path.as_ref()) {
        Ok(Some(content)) => validate_claim(&content, vk),
        Ok(None) => LicenseStatus::CommunityEvaluation {
            events_count: current_events_count,
            max_events: 1000,
        },
        Err(error) => LicenseStatus::Invalid(error),
    }
}

fn validate_claim(content: &str, vk: &VerifyingKey) -> LicenseStatus {
    let signed: SignedLicense = match serde_json::from_str(content) {
        Ok(s) => s,
        Err(e) => return LicenseStatus::Invalid(format!("Malformed license JSON: {}", e)),
    };

    let canonical_bytes = match serde_json::to_vec(&signed.payload) {
        Ok(b) => b,
        Err(e) => return LicenseStatus::Invalid(format!("Canonical serialization failed: {}", e)),
    };

    let sig_bytes = match hex::decode(&signed.signature_hex) {
        Ok(b) => b,
        Err(e) => return LicenseStatus::Invalid(format!("Invalid signature hex: {}", e)),
    };

    if sig_bytes.len() != 64 {
        return LicenseStatus::Invalid("Signature must be 64 bytes".to_string());
    }

    let mut sig_arr = [0u8; 64];
    sig_arr.copy_from_slice(&sig_bytes);
    let signature = Signature::from_bytes(&sig_arr);

    if let Err(e) = vk.verify_strict(&canonical_bytes, &signature) {
        return LicenseStatus::Invalid(format!("Signature verification failed: {}", e));
    }

    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("BFT Fallback")
        .as_secs();

    if now >= signed.payload.valid_until {
        return LicenseStatus::Expired {
            org: signed.payload.org,
            expired_at: signed.payload.valid_until,
        };
    }

    if signed.payload.org.trim().is_empty() || signed.payload.max_agents == 0 {
        return LicenseStatus::Invalid("Invalid signed licence scope".into());
    }
    LicenseStatus::Active(signed.payload)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn malformed_and_wrong_vendor_claims_fail() {
        let fixture = SigningKey::from_bytes(&[0x42; 32]).verifying_key();
        assert!(matches!(
            validate_claim("{}", &fixture),
            LicenseStatus::Invalid(_)
        ));
        let licence = generate_license(
            "Fixture",
            "enterprise-byoc",
            1,
            1,
            vec![],
            Some(&[0x43; 32]),
        );
        assert!(matches!(
            validate_claim(&serde_json::to_string(&licence).unwrap(), &fixture),
            LicenseStatus::Invalid(_)
        ));
        let mut expired = licence;
        expired.payload.valid_until = 0;
        let signature = SigningKey::from_bytes(&[0x42; 32])
            .sign(&serde_json::to_vec(&expired.payload).unwrap());
        expired.signature_hex = hex::encode(signature.to_bytes());
        assert!(matches!(
            validate_claim(&serde_json::to_string(&expired).unwrap(), &fixture),
            LicenseStatus::Expired { .. }
        ));
    }

    #[cfg(unix)]
    #[test]
    fn licence_symlinks_are_rejected() {
        let path = std::env::temp_dir().join(format!("b60-license-link-{}", std::process::id()));
        let _ = fs::remove_file(&path);
        std::os::unix::fs::symlink("/dev/null", &path).unwrap();
        assert!(matches!(
            check_license_file(&path, 0),
            LicenseStatus::Invalid(_)
        ));
        fs::remove_file(path).unwrap();
    }

    #[cfg(unix)]
    #[test]
    fn licence_fifo_is_rejected_without_waiting_for_a_writer() {
        use std::ffi::CString;
        use std::os::unix::ffi::OsStrExt;
        use std::sync::mpsc;
        use std::time::Duration;

        let path = std::env::temp_dir().join(format!("b60-license-fifo-{}", std::process::id()));
        let _ = fs::remove_file(&path);
        let name = CString::new(path.as_os_str().as_bytes()).unwrap();
        assert_eq!(unsafe { libc::mkfifo(name.as_ptr(), 0o600) }, 0);
        let (sender, receiver) = mpsc::channel();
        let worker_path = path.clone();
        let worker = std::thread::spawn(move || {
            sender.send(read_claim(&worker_path)).unwrap();
        });
        let result = receiver.recv_timeout(Duration::from_secs(1));
        if result.is_err() {
            // Unblock a regressed blocking open before failing, leaving no stuck thread.
            let writer = fs::OpenOptions::new()
                .write(true)
                .custom_flags(libc::O_NONBLOCK)
                .open(&path)
                .unwrap();
            receiver
                .recv_timeout(Duration::from_secs(1))
                .unwrap()
                .unwrap_err();
            drop(writer);
        }
        worker.join().unwrap();
        fs::remove_file(path).unwrap();
        assert!(
            matches!(result, Ok(Err(_))),
            "FIFO open waited for a writer"
        );
    }

    #[test]
    fn publicly_known_default_must_not_be_trusted() {
        let retired = SigningKey::from_bytes(RETIRED_PUBLIC_SEED).verifying_key();
        assert!(parse_vendor_key(Some(&hex::encode(retired.as_bytes()))).is_err());
        assert!(try_generate_license(
            "Fixture",
            "enterprise-byoc",
            1,
            1,
            vec![],
            Some(RETIRED_PUBLIC_SEED)
        )
        .is_err());
    }

    #[test]
    fn missing_or_malformed_public_key_is_denied() {
        assert!(parse_vendor_key(None).is_err());
        assert!(parse_vendor_key(Some("invalid")).is_err());
        assert!(parse_vendor_key(Some("abcd")).is_err());
    }

    #[test]
    fn test_license_cycle() {
        let lic = generate_license(
            "Test Corp",
            "enterprise-byoc",
            50,
            30,
            vec!["attest".into(), "scitt".into()],
            Some(&[0x42; 32]),
        );
        let tmp = std::env::temp_dir().join("test_lic.key");
        fs::write(
            &tmp,
            serde_json::to_string_pretty(&lic).expect("BFT Fallback"),
        )
        .expect("BFT Fallback");

        let status = check_license_with_key(
            &tmp,
            0,
            &SigningKey::from_bytes(&[0x42; 32]).verifying_key(),
        );
        assert!(matches!(status, LicenseStatus::Active(_)));
        if let LicenseStatus::Active(p) = status {
            assert_eq!(p.org, "Test Corp");
            assert_eq!(p.max_agents, 50);
        }
        let _ = fs::remove_file(tmp);
    }

    #[test]
    fn test_tampered_license() {
        let mut lic = generate_license(
            "Acme",
            "enterprise-byoc",
            10,
            30,
            vec!["attest".into()],
            Some(&[0x42; 32]),
        );
        // Tamper with payload
        lic.payload.max_agents = 9999;

        let tmp = std::env::temp_dir().join("tampered_lic.key");
        fs::write(
            &tmp,
            serde_json::to_string_pretty(&lic).expect("BFT Fallback"),
        )
        .expect("BFT Fallback");

        let status = check_license_with_key(
            &tmp,
            0,
            &SigningKey::from_bytes(&[0x42; 32]).verifying_key(),
        );
        assert!(matches!(status, LicenseStatus::Invalid(_)));
        let _ = fs::remove_file(tmp);
    }
}
