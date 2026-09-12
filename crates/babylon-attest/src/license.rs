use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

pub const DEFAULT_VENDOR_SEED: &[u8; 32] = b"AGENTS_ARCHI_SOVEREIGN_KEY_2026!";

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
    CommunityEvaluation { events_count: usize, max_events: usize },
    Expired { org: String, expired_at: u64 },
    Invalid(String),
}

pub fn get_vendor_verifying_key() -> VerifyingKey {
    let sk = SigningKey::from_bytes(DEFAULT_VENDOR_SEED);
    sk.verifying_key()
}

pub fn generate_license(
    org: &str,
    tier: &str,
    max_agents: u32,
    days: u64,
    features: Vec<String>,
    seed: Option<&[u8; 32]>,
) -> SignedLicense {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    let valid_until = now + (days * 86400);

    let payload = LicensePayload {
        org: org.to_string(),
        tier: tier.to_string(),
        max_agents,
        valid_until,
        features,
    };

    let canonical_bytes = serde_json::to_vec(&payload).expect("Serialization failed");
    let actual_seed = seed.unwrap_or(DEFAULT_VENDOR_SEED);
    let sk = SigningKey::from_bytes(actual_seed);
    let sig: Signature = sk.sign(&canonical_bytes);

    SignedLicense {
        payload,
        signature_hex: hex::encode(sig.to_bytes()),
    }
}

pub fn check_license_file<P: AsRef<Path>>(path: P, current_events_count: usize) -> LicenseStatus {
    let path = path.as_ref();
    if !path.exists() {
        return LicenseStatus::CommunityEvaluation {
            events_count: current_events_count,
            max_events: 1000,
        };
    }

    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(e) => return LicenseStatus::Invalid(format!("Error reading license file: {}", e)),
    };

    let signed: SignedLicense = match serde_json::from_str(&content) {
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

    let vk = get_vendor_verifying_key();
    if let Err(e) = vk.verify(&canonical_bytes, &signature) {
        return LicenseStatus::Invalid(format!("Signature verification failed: {}", e));
    }

    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();

    if now > signed.payload.valid_until {
        return LicenseStatus::Expired {
            org: signed.payload.org,
            expired_at: signed.payload.valid_until,
        };
    }

    LicenseStatus::Active(signed.payload)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_license_cycle() {
        let lic = generate_license(
            "Test Corp",
            "enterprise-byoc",
            50,
            30,
            vec!["attest".into(), "scitt".into()],
            None,
        );
        let tmp = std::env::temp_dir().join("test_lic.key");
        fs::write(&tmp, serde_json::to_string_pretty(&lic).unwrap()).unwrap();

        let status = check_license_file(&tmp, 0);
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
            None,
        );
        // Tamper with payload
        lic.payload.max_agents = 9999;

        let tmp = std::env::temp_dir().join("tampered_lic.key");
        fs::write(&tmp, serde_json::to_string_pretty(&lic).unwrap()).unwrap();

        let status = check_license_file(&tmp, 0);
        assert!(matches!(status, LicenseStatus::Invalid(_)));
        let _ = fs::remove_file(tmp);
    }
}
