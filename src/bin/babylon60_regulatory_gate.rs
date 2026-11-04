//! Restricted EU AI Act approval gate. JSON stdin; policy and ledger are operator supplied.
//! No mocked or remote fallback. `anchor` is explicit and separate from approval.
#[cfg(all(feature = "cortex-persist", feature = "halt-receipt"))]
mod gate {
    use babylon60::ring0::{self, AttestationTier, CausalEnvelope, GateTrap};
    #[cfg(target_os = "macos")]
    use babylon60::ring0::{HardwareReceipt, HardwareSecurityGate};
    use base64ct::{Base64, Encoding};
    use ed25519_dalek::{Signature, VerifyingKey};
    use rusqlite::{params, Connection, OpenFlags};
    use serde_json::{json, Value};
    use sha2::{Digest, Sha256};
    use std::{
        io::Read,
        path::Path,
        time::{SystemTime, UNIX_EPOCH},
    };

    const CATALOGUE: &[u8] = include_bytes!(
        "../../01_KISH_ENGINE/babylon60/compliance_exporter/regulatory_catalogue.json"
    );
    const DOMAIN: i64 = 0x4555;
    fn hash(bytes: &[u8]) -> String {
        hex::encode(Sha256::digest(bytes))
    }
    fn canonical(value: &Value) -> Result<Vec<u8>, String> {
        fn check(v: &Value) -> bool {
            match v {
                Value::Number(n) => n.is_i64() || n.is_u64(),
                Value::Array(a) => a.iter().all(check),
                Value::Object(o) => o.values().all(check),
                _ => true,
            }
        }
        if !check(value) {
            return Err("Noncanonical number".into());
        }
        serde_json::to_vec(value).map_err(|e| e.to_string())
    }
    fn bytes32(value: &Value) -> Result<[u8; 32], String> {
        hex::decode(value.as_str().ok_or("Missing digest")?)
            .map_err(|_| "Invalid hex")?
            .try_into()
            .map_err(|_| "Digest must have 32 bytes".into())
    }
    #[cfg(target_os = "macos")]
    fn pinned_key(policy: &Value) -> Result<Vec<u8>, String> {
        let key = hex::decode(
            policy["hardware_public_key_hex"]
                .as_str()
                .ok_or("Missing pinned hardware key")?,
        )
        .map_err(|e| e.to_string())?;
        if key.len() != 65 || key[0] != 4 {
            return Err("Hardware pin must be an uncompressed SEC1 P-256 point".into());
        }
        p256::ecdsa::VerifyingKey::from_sec1_bytes(&key).map_err(|_| "Invalid P-256 pin")?;
        Ok(key)
    }
    #[cfg(target_os = "macos")]
    fn check_backend(backend: &Value) -> Result<String, String> {
        use std::os::unix::fs::MetadataExt;
        for (path_field, hash_field) in [
            ("helper_path", "helper_sha256"),
            ("key_path", "key_record_sha256"),
        ] {
            let path = Path::new(
                backend[path_field]
                    .as_str()
                    .ok_or("Missing native backend path")?,
            );
            let metadata = std::fs::symlink_metadata(path).map_err(|e| e.to_string())?;
            if !path.is_absolute()
                || !metadata.is_file()
                || metadata.mode() & 0o022 != 0
                || metadata.uid() != unsafe { libc::getuid() }
                || (path_field == "key_path" && metadata.mode() & 0o777 != 0o600)
            {
                return Err("Native backend must use owned, protected regular files".into());
            }
            bytes32(&backend[hash_field])?;
            if backend[hash_field] != hash(&std::fs::read(path).map_err(|e| e.to_string())?) {
                return Err("Native backend changed after provisioning".into());
            }
        }
        Ok(hash(&canonical(backend)?))
    }
    #[cfg(target_os = "macos")]
    fn configured_signer(
        policy: &Value,
    ) -> Result<(babylon60::enclave::AppleSecureEnclave, String), String> {
        let key = pinned_key(policy)?;
        let backend_digest = check_backend(&policy["hardware_backend"])?;
        // This standalone, single-threaded process takes paths only from operator policy.
        std::env::set_var(
            "C5_BIOMETRIC_GATE_PATH",
            policy["hardware_backend"]["helper_path"]
                .as_str()
                .ok_or("Missing helper")?,
        );
        std::env::set_var(
            "BABYLON_ENCLAVE_KEY_PATH",
            policy["hardware_backend"]["key_path"]
                .as_str()
                .ok_or("Missing key path")?,
        );
        Ok((
            babylon60::enclave::AppleSecureEnclave::new().with_public_key_der(key),
            backend_digest,
        ))
    }
    fn now() -> Result<u64, String> {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .map_err(|e| e.to_string())
    }
    fn review(record: &Value, policy: &Value, time: u64) -> Result<(), String> {
        let s = &record["statement"];
        let who = s["reviewer"].as_str().ok_or("Missing reviewer")?;
        let reviewer = &policy["reviewers"][who];
        let cat: Value = serde_json::from_slice(CATALOGUE).map_err(|e| e.to_string())?;
        let mut ids: Vec<&str> = cat["requirements"]
            .as_array()
            .ok_or("Invalid catalogue")?
            .iter()
            .filter(|r| r["blocking"] == true)
            .filter_map(|r| r["id"].as_str())
            .collect();
        ids.sort();
        if s["schema"] != "babylon60.euai.review.v1"
            || s["classification"] != "high_risk"
            || s["gate_eligible"] != true
            || s["catalogue_digest"] != hash(CATALOGUE)
            || s["blocking_ids"] != json!(ids)
            || s["expires_at"].as_u64().unwrap_or(0) <= time
            || reviewer["revoked"] == true
            || !reviewer["scopes"]
                .as_array()
                .is_some_and(|a| a.contains(&json!("assessment")))
            || !reviewer["system_ids"]
                .as_array()
                .is_some_and(|a| a.contains(&s["system_id"]))
            || reviewer["name"]
                .as_str()
                .is_none_or(|v| v.trim().is_empty())
        {
            return Err("Review scope, expiry, authority or eligibility invalid".into());
        }
        for field in ["profile_digest", "assessment_digest", "requirements_digest"] {
            bytes32(&s[field])?;
        }
        let id = hash(&canonical(record)?);
        if policy["revoked_reviews"]
            .as_array()
            .is_some_and(|a| a.contains(&json!(id)))
        {
            return Err("Review revoked".into());
        }
        let key = VerifyingKey::from_bytes(&bytes32(&reviewer["public_key_hex"])?)
            .map_err(|e| e.to_string())?;
        let signature = Base64::decode_vec(
            record["signature"]
                .as_str()
                .ok_or("Missing review signature")?,
        )
        .map_err(|e| e.to_string())?;
        let signature = Signature::from_slice(&signature).map_err(|e| e.to_string())?;
        key.verify_strict(&canonical(s)?, &signature)
            .map_err(|_| "Invalid review signature".to_string())
    }

    #[cfg(target_os = "macos")]
    struct NativeGate {
        signer: babylon60::enclave::AppleSecureEnclave,
        expires_at: u64,
        backend: Value,
    }
    #[cfg(target_os = "macos")]
    impl HardwareSecurityGate for NativeGate {
        fn attest_transition(
            &mut self,
            envelope: &CausalEnvelope,
        ) -> Result<HardwareReceipt, GateTrap> {
            use babylon60::receipt::Signer;
            let failure = || GateTrap::SiliconAttestationFailure {
                backend: "AppleSecureEnclave",
                errno: -40,
                code: ring0::FAIL_STOP_CODE,
            };
            if envelope.attestation_tier != AttestationTier::HumanBiometricPresence {
                return Err(failure());
            }
            let payload = envelope.canonical_digest();
            let signature = self.signer.sign(&payload).map_err(|_| failure())?;
            if !self.signer.verify(&payload, &signature)
                || now().map_err(|_| failure())? >= self.expires_at
                || check_backend(&self.backend).is_err()
            {
                return Err(failure());
            }
            Ok(HardwareReceipt {
                signature: signature.try_into().map_err(|_| failure())?,
                public_key_id: Sha256::digest(self.signer.get_public_key()).into(),
                // Secure Enclave does not expose a PCR measurement through this API.
                pcr_or_enclave_measurement: [0; 32],
            })
        }
    }

    pub fn run() -> Result<Value, String> {
        let args: Vec<String> = std::env::args().collect();
        if args.len() != 5 || args[1] != "--policy" || args[3] != "--ledger" {
            return Err("Usage: babylon60_regulatory_gate --policy trusted.json --ledger existing.sqlite < request.json".into());
        }
        let policy: Value =
            serde_json::from_slice(&std::fs::read(&args[2]).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        let mut data = Vec::new();
        std::io::stdin()
            .take(4 * 1024 * 1024 + 1)
            .read_to_end(&mut data)
            .map_err(|e| e.to_string())?;
        if data.len() > 4 * 1024 * 1024 {
            return Err("Request too large".into());
        }
        let request: Value = serde_json::from_slice(&data).map_err(|e| e.to_string())?;
        canonical(&request)?;
        let mode = request["mode"].as_str().ok_or("Missing mode")?;
        if mode == "init" {
            let conn = Connection::open(&args[4]).map_err(|e| e.to_string())?;
            ring0::init_l0_schema(&conn).map_err(|e| e.to_string())?;
            return Ok(json!({"schema":"babylon60.euai.init.v1","initialized":true}));
        }
        if mode == "validate-hardware" {
            if cfg!(feature = "test_mock_hardware") {
                return Err(
                    "Mock-enabled binaries cannot produce native validation evidence".into(),
                );
            }
            bytes32(&request["nonce"])?;
            #[cfg(target_os = "macos")]
            {
                use babylon60::receipt::Signer;
                let binary = std::env::current_exe().map_err(|e| e.to_string())?;
                let (signer, backend_digest) = configured_signer(&policy)?;
                let challenge = json!({"schema":"babylon60.euai.native_validation.v1",
                    "binary_sha256":hash(&std::fs::read(binary).map_err(|e| e.to_string())?),
                    "backend_digest": backend_digest,
                    "nonce":request["nonce"], "purpose":"INDEPENDENT_VALIDATION_ONLY"});
                let payload = canonical(&challenge)?;
                let signature = signer.sign(&payload)?;
                if !signer.verify(&payload, &signature) {
                    return Err("Validation signature invalid".into());
                }
                check_backend(&policy["hardware_backend"])?;
                return Ok(
                    json!({"challenge":challenge, "signature_hex":hex::encode(signature),
                    "public_key_hex":hex::encode(signer.get_public_key()),
                    "measurement_status":"UNAVAILABLE", "publication_authorized":false,
                    "status":"REQUIRES_INDEPENDENT_REVIEW"}),
                );
            }
            #[cfg(not(target_os = "macos"))]
            return Err("NO_VERIFICADO: native validation requires macOS Secure Enclave".into());
        }
        review(&request["source_record"], &policy, now()?)?;
        let fact = Sha256::digest(canonical(&request["source_record"])?);
        // No CREATE and no schema initialization in a protected operation.
        let mut conn =
            Connection::open_with_flags(Path::new(&args[4]), OpenFlags::SQLITE_OPEN_READ_WRITE)
                .map_err(|e| e.to_string())?;
        if mode == "anchor" {
            let tx = conn
                .transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)
                .map_err(|e| e.to_string())?;
            let (tick, _) = ring0::read_l0_tip(&tx).map_err(|e| format!("{e:?}"))?;
            let existing: bool = tx.query_row("SELECT EXISTS(SELECT 1 FROM l0_anchored_facts WHERE fact_hash=?1 AND payload_hash=?1 AND domain_tag=?2)", params![&fact[..], DOMAIN], |r| r.get(0)).map_err(|e| e.to_string())?;
            if !existing {
                tx.execute("INSERT INTO l0_anchored_facts(fact_hash, anchored_tick, domain_tag, payload_hash) VALUES (?1,?2,?3,?1)", params![&fact[..], tick as i64, DOMAIN]).map_err(|e| e.to_string())?;
            }
            tx.commit().map_err(|e| e.to_string())?;
            return Ok(
                json!({"schema":"babylon60.euai.anchor.v1", "source_fact_hash":hex::encode(fact), "anchored":true}),
            );
        }
        if !["approve", "authorize-release"].contains(&mode) {
            return Err("Unknown operation".into());
        }
        if cfg!(feature = "test_mock_hardware") {
            return Err("Mock-enabled binaries cannot approve or authorize releases".into());
        }
        let auth = &request["authorization"];
        let fields = [
            "schema",
            "action",
            "source_fact_hash",
            "profile_digest",
            "commit",
            "artifact_sha256",
            "destination",
            "run_id",
            "run_attempt",
            "expires_at",
            "native_validation_digest",
        ];
        if !auth.as_object().is_some_and(|object| {
            object.len() == fields.len() && fields.iter().all(|field| object.contains_key(*field))
        }) {
            return Err("Invalid authorization schema".into());
        }
        if auth["schema"] != "babylon60.euai.authorization.v1"
            || auth["action"] != mode
            || auth["source_fact_hash"] != hex::encode(fact)
            || auth["profile_digest"] != request["source_record"]["statement"]["profile_digest"]
            || auth["native_validation_digest"] != hash(&canonical(&policy["native_validation"])?)
            || auth["expires_at"].as_u64().unwrap_or(0) <= now()?
            || auth["expires_at"].as_u64().unwrap_or(u64::MAX)
                > request["source_record"]["statement"]["expires_at"]
                    .as_u64()
                    .unwrap_or(0)
            || auth["expires_at"].as_u64().unwrap_or(u64::MAX) > now()?.saturating_add(3600)
        {
            return Err("Authorization binding or validity invalid".into());
        }
        bytes32(&auth["artifact_sha256"])?;
        for field in ["commit", "destination", "run_id", "run_attempt"] {
            if auth[field].as_str().is_none_or(|s| s.trim().is_empty()) {
                return Err(format!("Missing {field}"));
            }
        }
        let commit = auth["commit"].as_str().ok_or("Missing commit")?;
        if ![40, 64].contains(&commit.len())
            || !commit
                .bytes()
                .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
        {
            return Err("Invalid commit digest".into());
        }
        let payload: [u8; 32] = Sha256::digest(canonical(auth)?).into();
        if policy["revoked_authorizations"]
            .as_array()
            .is_some_and(|a| a.contains(&json!(hex::encode(payload))))
        {
            return Err("Authorization revoked".into());
        }
        let (tick, root) = ring0::read_l0_tip(&conn).map_err(|e| format!("{e:?}"))?;
        let envelope = CausalEnvelope {
            logical_tick: tick.checked_add(1).ok_or("Tick exhausted")?,
            prev_merkle_root: root,
            source_fact_hash: fact.into(),
            effect_payload_hash: payload,
            token_count: 0,
            attestation_tier: AttestationTier::HumanBiometricPresence,
        };
        let known: bool = conn.query_row("SELECT EXISTS(SELECT 1 FROM l0_anchored_facts WHERE fact_hash=?1 AND payload_hash=?1 AND domain_tag=?2 AND anchored_tick < ?3)", params![&fact[..], DOMAIN, i64::try_from(envelope.logical_tick).map_err(|_| "Tick exhausted")?], |r| r.get(0)).map_err(|e| e.to_string())?;
        if !known {
            return Err(format!(
                "{:?}",
                GateTrap::UnanchoredCausalLineage {
                    missing_fact: fact.into(),
                    code: ring0::FAIL_STOP_CODE
                }
            ));
        }
        let reused: bool = conn
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM l0_causal_ledger WHERE effect_payload_hash=?1)",
                params![&payload[..]],
                |r| r.get(0),
            )
            .map_err(|e| e.to_string())?;
        if reused {
            return Err("Authorization already committed".into());
        }
        let exe = std::env::current_exe().map_err(|e| e.to_string())?;
        if policy["native_validation"]["status"] != "VERIFIED"
            || policy["native_validation"]["binary_sha256"]
                != hash(&std::fs::read(exe).map_err(|e| e.to_string())?)
        {
            return Err(
                "NO_VERIFICADO: independent native validation required for this binary".into(),
            );
        }
        bytes32(&policy["native_validation"]["evidence_sha256"])?;
        #[cfg(target_os = "macos")]
        {
            use babylon60::receipt::Signer;
            let (signer, backend_digest) = configured_signer(&policy)?;
            if policy["native_validation"]["backend_digest"] != backend_digest {
                return Err("NO_VERIFICADO: backend configuration changed".into());
            }
            let mut hardware = NativeGate {
                signer,
                expires_at: auth["expires_at"].as_u64().ok_or("Invalid expiry")?,
                backend: policy["hardware_backend"].clone(),
            };
            let committed = ring0::commit_ring0_transition(&mut conn, &mut hardware, &envelope)
                .map_err(|e| format!("{e:?}"))?;
            Ok(
                json!({"schema":"babylon60.euai.receipt.v1", "authorization":auth,
                "envelope_hex":hex::encode(envelope.to_canonical_bytes()), "signature_hex":hex::encode(committed.receipt.signature),
                "public_key_hex":hex::encode(hardware.signer.get_public_key()), "merkle_root":hex::encode(committed.curr_merkle_root),
                "backend":"apple_secure_enclave", "simulated":false, "measurement_status":"UNAVAILABLE",
                "source_record":request["source_record"], "native_validation":policy["native_validation"]}),
            )
        }
        #[cfg(not(target_os = "macos"))]
        {
            Err("NO_VERIFICADO: native approval backend requires macOS Secure Enclave".into())
        }
    }
}

fn main() {
    #[cfg(all(feature = "cortex-persist", feature = "halt-receipt"))]
    match gate::run() {
        Ok(result) => println!("{}", result),
        Err(error) => {
            eprintln!(
                "{{\"status\":\"REJECTED\",\"code\":\"0xDEAD_6060\",\"error\":{}}}",
                serde_json::to_string(&error).unwrap()
            );
            std::process::exit(2);
        }
    }
    #[cfg(not(all(feature = "cortex-persist", feature = "halt-receipt")))]
    {
        eprintln!("Required features unavailable; approval rejected");
        std::process::exit(2);
    }
}
