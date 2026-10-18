//! # BABYLON-60 v5 — Servicio Independiente de Autoridad (`babylon-authorityd`)
//!
//! Demonio de autoridad separado por proceso (AX-0) que:
//! 1. Carga `SecurityPolicy` desde disco local de solo lectura.
//! 2. Verifica las credenciales del proceso llamante sobre `AF_UNIX` (`getpeereid`).
//! 3. Evalúa determinísticamente la política contra `ProposedIntent`.
//! 4. Emite `SignedAuthorization` en formato canónico `COSE_Sign1` (`INV_C5_ONWIRE_CANON`).

use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::io::AsRawFd;
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use babylon60::executor::ipc::{recv_frame, send_frame, IpcErrorCode};
use babylon60::executor::{
    AuthorizationPayload, ProposedIntent, SecurityPolicy, SignedAuthorization, PROTOCOL_VERSION,
};
use babylon60::receipt::{Ed25519Signer, Signer};
use ed25519_dalek::SigningKey;

#[cfg(target_os = "linux")]
fn peer_effective_uid(stream: &UnixStream) -> Result<u32, String> {
    // SO_PEERCRED supplies kernel credentials for the connected Unix peer.
    let mut credentials: libc::ucred = unsafe { std::mem::zeroed() };
    let mut length = std::mem::size_of::<libc::ucred>() as libc::socklen_t;
    let rc = unsafe {
        libc::getsockopt(
            stream.as_raw_fd(),
            libc::SOL_SOCKET,
            libc::SO_PEERCRED,
            std::ptr::from_mut(&mut credentials).cast(),
            &mut length,
        )
    };
    if rc != 0 || length as usize != std::mem::size_of::<libc::ucred>() {
        return Err("SO_PEERCRED credential lookup failed".into());
    }
    Ok(credentials.uid)
}

#[cfg(not(target_os = "linux"))]
fn peer_effective_uid(stream: &UnixStream) -> Result<u32, String> {
    let mut uid = u32::MAX;
    let mut gid = u32::MAX;
    let rc = unsafe { libc::getpeereid(stream.as_raw_fd(), &mut uid, &mut gid) };
    if rc != 0 {
        return Err("getpeereid credential lookup failed".into());
    }
    Ok(uid)
}

/// Petición de emisión de autorización enviada al demonio `babylon-authorityd`.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AuthoritySigningRequest {
    /// Identidad de la instalación destino.
    pub installation_id: [u8; 32],
    /// Identidad del executor destino.
    pub executor_id: [u8; 32],
    /// Intención propuesta a evaluar contra la política local.
    pub intent: ProposedIntent,
    /// Precondición observada sobre el recurso.
    pub resource_precondition_digest: [u8; 32],
    /// Nonce único de 32 bytes.
    pub nonce: [u8; 32],
    /// Época de autoridad monótona.
    pub authority_epoch: u64,
    /// Segundos de validez solicitados (acotados a <= 300s).
    pub ttl_secs: u64,
    /// Usos máximos solicitados (debe ser 1).
    pub max_uses: u32,
}

/// Respuesta estructurada emitida por `babylon-authorityd`.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum AuthoritySigningResponse {
    /// Autorización COSE_Sign1 firmada junto con la política de solo lectura aplicada.
    Authorized {
        /// Autorización firmada en contenedor COSE_Sign1.
        auth: SignedAuthorization,
        /// Política de seguridad cargada desde disco local.
        policy: SecurityPolicy,
    },
    /// Rechazo determinista fail-closed con código de error tipado.
    Rejected {
        /// Código de error tipado IPC.
        code: IpcErrorCode,
        /// Motivo diagnóstico.
        reason: String,
    },
}

/// Verifica que el proceso par en el socket `AF_UNIX` pertenece al mismo UID efectivo.
pub fn verify_peer_credentials(stream: &UnixStream) -> Result<u32, String> {
    let peer_uid = peer_effective_uid(stream)?;
    let host_uid = unsafe { libc::geteuid() };
    if peer_uid != host_uid {
        return Err(format!(
            "peer UID mismatch: expected {}, got {}",
            host_uid, peer_uid
        ));
    }
    Ok(peer_uid)
}

/// Carga `SecurityPolicy` desde disco exigiendo permisos de solo lectura (sin bits de escritura `0o222`).
pub fn load_readonly_policy(path: &Path) -> Result<SecurityPolicy, String> {
    let meta = fs::metadata(path).map_err(|e| format!("cannot stat policy file: {}", e))?;
    let mode = meta.permissions().mode() & 0o777;
    if mode & 0o222 != 0 {
        return Err(format!(
            "fail-closed: policy file {} is writable (mode {:o}); must be read-only (0400/0444)",
            path.display(),
            mode
        ));
    }
    let raw = fs::read(path).map_err(|e| format!("cannot read policy file: {}", e))?;
    serde_json::from_slice(&raw).map_err(|e| format!("malformed SecurityPolicy JSON: {}", e))
}

/// Evalúa la petición contra la política local y emite el `COSE_Sign1` si es válida.
pub fn evaluate_and_sign<S: Signer>(
    req: &AuthoritySigningRequest,
    policy: &SecurityPolicy,
    signer: &S,
    now_secs: u64,
) -> AuthoritySigningResponse {
    if req.max_uses != 1 || req.max_uses > policy.max_allowed_uses {
        return AuthoritySigningResponse::Rejected {
            code: IpcErrorCode::PolicyOrPreconditionViolation,
            reason: format!("invalid max_uses {}", req.max_uses),
        };
    }
    if req.intent.action_name != policy.allowed_action {
        return AuthoritySigningResponse::Rejected {
            code: IpcErrorCode::PolicyOrPreconditionViolation,
            reason: format!(
                "action '{}' not permitted by policy (allowed: '{}')",
                req.intent.action_name, policy.allowed_action
            ),
        };
    }
    if policy.admitted_authority_key != signer.get_public_key() {
        return AuthoritySigningResponse::Rejected {
            code: IpcErrorCode::Unauthorized,
            reason: "signer public key does not match policy admitted_authority_key".into(),
        };
    }
    let bounded_ttl = req.ttl_secs.clamp(1, 300);
    let payload = AuthorizationPayload {
        protocol_version: PROTOCOL_VERSION,
        installation_id: req.installation_id,
        executor_id: req.executor_id,
        intent_digest: req.intent.compute_digest(),
        policy_digest: policy.compute_digest(),
        resource_precondition_digest: req.resource_precondition_digest,
        nonce: req.nonce,
        authority_epoch: req.authority_epoch,
        expires_at: now_secs.saturating_add(bounded_ttl),
        max_uses: 1,
    };

    match SignedAuthorization::new_cose(&payload, signer) {
        Ok(auth) => AuthoritySigningResponse::Authorized {
            auth,
            policy: policy.clone(),
        },
        Err(e) => AuthoritySigningResponse::Rejected {
            code: IpcErrorCode::Unauthorized,
            reason: format!("COSE_Sign1 signing failed: {}", e),
        },
    }
}

fn parse_operational_signer(seed: Option<&str>) -> Result<Ed25519Signer, String> {
    let encoded = seed.ok_or("private key missing: provision BABYLON_AUTHORITY_ED25519_SEED")?;
    if encoded.len() != 64 {
        return Err("private key must contain exactly 64 hexadecimal characters".into());
    }
    let decoded = hex::decode(encoded).map_err(|_| "private key is not valid hexadecimal")?;
    let seed_bytes: [u8; 32] = decoded.try_into().map_err(|_| "private key must be 32 bytes")?;
    if seed_bytes == [0; 32] {
        return Err("private key must not be the all-zero placeholder".into());
    }
    Ok(Ed25519Signer::from_signing_key(SigningKey::from_bytes(&seed_bytes)))
}

fn load_operational_signer() -> Result<Ed25519Signer, String> {
    let seed = std::env::var("BABYLON_AUTHORITY_ED25519_SEED")
        .map_err(|_| "private key missing or invalid: provision BABYLON_AUTHORITY_ED25519_SEED")?;
    parse_operational_signer(Some(&seed))
}

fn main() {
    let mut socket_path = PathBuf::from("/tmp/babylon-authorityd.sock");
    let mut policy_path = PathBuf::from("/etc/babylon60/security_policy.json");
    let mut once = false;

    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--socket" => {
                if let Some(v) = args.next() {
                    socket_path = PathBuf::from(v);
                }
            }
            "--policy" => {
                if let Some(v) = args.next() {
                    policy_path = PathBuf::from(v);
                }
            }
            "--once" => {
                once = true;
            }
            _ => {}
        }
    }

    let policy = match load_readonly_policy(&policy_path) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("[BABYLON-AUTHORITYD FAIL-STOP] {}", e);
            std::process::exit(1);
        }
    };

    let signer = match load_operational_signer() {
        Ok(signer) => signer,
        Err(reason) => {
            eprintln!("[BABYLON-AUTHORITYD FAIL-STOP] {}", reason);
            std::process::exit(1);
        }
    };
    if policy.admitted_authority_key != signer.get_public_key() {
        eprintln!("[BABYLON-AUTHORITYD FAIL-STOP] private key does not match policy authority");
        std::process::exit(1);
    }
    let _ = fs::remove_file(&socket_path);
    let listener = match UnixListener::bind(&socket_path) {
        Ok(l) => l,
        Err(e) => {
            eprintln!(
                "[BABYLON-AUTHORITYD FAIL-STOP] cannot bind {}: {}",
                socket_path.display(),
                e
            );
            std::process::exit(1);
        }
    };
    let _ = fs::set_permissions(&socket_path, fs::Permissions::from_mode(0o600));

    for mut stream in listener.incoming().flatten() {
        let resp = match verify_peer_credentials(&stream) {
            Err(reason) => AuthoritySigningResponse::Rejected {
                code: IpcErrorCode::Unauthorized,
                reason,
            },
            Ok(_) => match recv_frame::<_, AuthoritySigningRequest>(&mut stream) {
                Ok(req) => {
                    let now = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap_or_default()
                        .as_secs();
                    evaluate_and_sign(&req, &policy, &signer, now)
                }
                Err(e) => AuthoritySigningResponse::Rejected {
                    code: IpcErrorCode::Unauthorized,
                    reason: format!("invalid IPC request frame: {}", e),
                },
            },
        };
        let _ = send_frame(&mut stream, &resp);
        if once {
            break;
        }
    }
}

#[cfg(test)]
mod key_tests {
    use super::*;

    #[test]
    fn unix_peer_credentials_are_read_from_the_kernel() {
        let (client, server) = UnixStream::pair().unwrap();
        let expected_uid = unsafe { libc::geteuid() };
        assert_eq!(verify_peer_credentials(&client).unwrap(), expected_uid);
        assert_eq!(verify_peer_credentials(&server).unwrap(), expected_uid);
    }

    #[test]
    fn no_public_fallback_or_malformed_key() {
        for value in [None, Some(""), Some("short"), Some(&"g".repeat(64)), Some(&"0".repeat(64))] {
            assert!(parse_operational_signer(value).is_err());
        }
    }

    #[test]
    fn explicit_software_test_key_preserves_identity_and_signature() {
        let seed = [19u8; 32];
        let signer = parse_operational_signer(Some(&hex::encode(seed))).unwrap();
        let expected = SigningKey::from_bytes(&seed).verifying_key().to_bytes();
        assert_eq!(signer.get_public_key(), expected);
        let signature = signer.sign(b"isolated software fixture").unwrap();
        assert!(signer.verify(b"isolated software fixture", &signature));
        assert!(!signer.verify(b"altered", &signature));
    }
}
