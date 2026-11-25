//! Typed Python bridge to the canonical Rust broker (no duplicate policy engine).
use crate::capability::{McpCapabilityBroker, McpCapabilityToken, McpPolicyState, McpToolDef};
use crate::ontology::babylon::{EffectKind, RejectReason};
use crate::secure_fs::{EffectTxOrchestrator, NativeSecureFs, SecureFsError};
use pyo3::exceptions::{PyPermissionError, PyValueError};
use pyo3::prelude::*;
use std::path::Path;

const SERVER: [u8; 32] = [0xC1; 32];

fn denied(reason: RejectReason) -> PyErr {
    PyPermissionError::new_err(format!("MCP admission rejected: {reason:?}"))
}

fn secure_fs_denied(err: SecureFsError) -> PyErr {
    PyPermissionError::new_err(format!("MCP EffectTx quarantine rejected: {err}"))
}

fn policy(value: &str) -> PyResult<McpPolicyState> {
    match value {
        "Enabled" => Ok(McpPolicyState::Enabled),
        "Disabled" => Ok(McpPolicyState::Disabled),
        "Unconfigured" => Ok(McpPolicyState::Unconfigured),
        _ => Err(PyValueError::new_err("Unknown external policy state")),
    }
}

fn effect_kind(effect: &str) -> PyResult<EffectKind> {
    Ok(match effect {
        "FsRead" => EffectKind::FsRead,
        "FsMutate" => EffectKind::FsMutate,
        "FsDelete" => EffectKind::FsDelete,
        "FsChmod" => EffectKind::FsChmod,
        "FsRename" => EffectKind::FsRename,
        "NetTransmit" => EffectKind::NetTransmit,
        "ProcSpawn" => EffectKind::ProcSpawn,
        "ProcTerminate" => EffectKind::ProcTerminate,
        "KeyDestroy" => EffectKind::KeyDestroy,
        "LedgerAppend" => EffectKind::LedgerAppend,
        _ => return Err(PyValueError::new_err("Unknown MCP effect")),
    })
}

/// `scope=None` keeps the historical `mcp://cortex/{name}` scope.
fn definition(name: &str, hash: Vec<u8>, effect: &str, scope: Option<&str>) -> PyResult<McpToolDef> {
    let effect = effect_kind(effect)?;
    if name.is_empty() || !name.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_') {
        return Err(PyValueError::new_err("Invalid canonical tool name"));
    }
    let target_resource_scope = match scope {
        Some("") => return Err(PyValueError::new_err("Empty resource scope")),
        Some(value) => value.to_owned(),
        None => format!("mcp://cortex/{name}"),
    };
    Ok(McpToolDef {
        name: name.into(),
        code_hash: hash
            .try_into()
            .map_err(|_| PyValueError::new_err("Expected 32-byte hash"))?,
        allowed_effects: vec![effect],
        target_resource_scope,
    })
}

/// Opaque token; Python cannot construct or rebind it.
#[pyclass(frozen)]
pub struct McpToken {
    inner: McpCapabilityToken,
}

#[pymethods]
impl McpToken {
    /// Read-only identifier, usable for audit records.
    #[getter]
    fn token_id(&self) -> Vec<u8> {
        self.inner.token_id().to_vec()
    }
}

/// Trusted in-process control plane. Never publish its methods as MCP tools.
#[pyclass]
pub struct McpBroker {
    inner: McpCapabilityBroker,
}

#[pymethods]
impl McpBroker {
    #[new]
    fn new() -> Self {
        let mut inner = McpCapabilityBroker::new();
        // Availability only. There are no initial grants.
        inner.register_server(SERVER, true, 1);
        Self { inner }
    }

    fn revision(&self) -> PyResult<u64> {
        self.inner.policy_revision(&SERVER).map_err(denied)
    }

    fn update_policy(&mut self, feature: &str, global: &str) -> PyResult<()> {
        self.inner
            .update_external_policy(&SERVER, policy(feature)?, policy(global)?)
            .map_err(denied)
    }

    #[pyo3(signature = (name, hash, effect, scope=None))]
    fn discover(&mut self, name: &str, hash: Vec<u8>, effect: &str, scope: Option<&str>) -> PyResult<()> {
        self.inner
            .register_tool(&SERVER, definition(name, hash, effect, scope)?)
            .map_err(denied)
    }

    #[pyo3(signature = (name, hash, effect, scope=None))]
    fn authorize(&mut self, name: &str, hash: Vec<u8>, effect: &str, scope: Option<&str>) -> PyResult<()> {
        self.inner
            .authorize_tool(&SERVER, definition(name, hash, effect, scope)?)
            .map_err(denied)
    }

    fn revoke(&mut self, name: &str) -> PyResult<()> {
        // Also invalidate approvals when no tool grant has yet been issued.
        self.inner.revoke_tool(&SERVER, name).map_err(denied)?;
        self.inner.advance_server_epoch(&SERVER).map_err(denied)?;
        Ok(())
    }

    /// `resource=None` binds the token to the tool scope itself.
    #[pyo3(signature = (name, hash, effect, args, scope=None, resource=None, nonce=None))]
    #[allow(clippy::too_many_arguments)]
    fn issue(
        &self,
        name: &str,
        hash: Vec<u8>,
        effect: &str,
        args: Vec<u8>,
        scope: Option<&str>,
        resource: Option<&str>,
        nonce: Option<Vec<u8>>,
    ) -> PyResult<McpToken> {
        let tool = definition(name, hash, effect, scope)?;
        let resource = resource.unwrap_or(&tool.target_resource_scope);
        let result = match nonce {
            Some(nonce_bytes) => {
                let nonce_arr: [u8; 32] = nonce_bytes
                    .try_into()
                    .map_err(|_| PyValueError::new_err("Expected 32-byte invocation nonce"))?;
                self.inner.request_capability_with_nonce(
                    &SERVER,
                    name,
                    &tool.code_hash,
                    &args,
                    resource,
                    tool.allowed_effects[0],
                    1,
                    &nonce_arr,
                )
            }
            None => self.inner.request_capability(
                &SERVER,
                name,
                &tool.code_hash,
                &args,
                resource,
                tool.allowed_effects[0],
                1,
            ),
        };
        result.map(|inner| McpToken { inner }).map_err(denied)
    }

    /// Reusable validation within the token epoch (historical contract).
    #[pyo3(signature = (token, name, hash, effect, args, scope=None, resource=None))]
    #[allow(clippy::too_many_arguments)]
    fn validate(
        &self,
        token: PyRef<'_, McpToken>,
        name: &str,
        hash: Vec<u8>,
        effect: &str,
        args: Vec<u8>,
        scope: Option<&str>,
        resource: Option<&str>,
    ) -> PyResult<()> {
        let tool = definition(name, hash, effect, scope)?;
        let resource = resource.unwrap_or(&tool.target_resource_scope);
        self.inner
            .commit_execution(
                &token.inner,
                &SERVER,
                name,
                &tool.code_hash,
                &args,
                resource,
                tool.allowed_effects[0],
                token.inner.issued_epoch(),
            )
            .map(|_| ())
            .map_err(denied)
    }

    /// Single-use commit: returns the 32-byte evidence id; replay is rejected.
    #[pyo3(signature = (token, name, hash, effect, args, scope=None, resource=None))]
    #[allow(clippy::too_many_arguments)]
    fn commit_once(
        &mut self,
        token: PyRef<'_, McpToken>,
        name: &str,
        hash: Vec<u8>,
        effect: &str,
        args: Vec<u8>,
        scope: Option<&str>,
        resource: Option<&str>,
    ) -> PyResult<Vec<u8>> {
        let tool = definition(name, hash, effect, scope)?;
        let resource = resource.unwrap_or(&tool.target_resource_scope);
        self.inner
            .commit_execution_once(
                &token.inner,
                &SERVER,
                name,
                &tool.code_hash,
                &args,
                resource,
                tool.allowed_effects[0],
                token.inner.issued_epoch(),
            )
            .map(|evidence| evidence.evidence_id.to_vec())
            .map_err(denied)
    }
}

/// Ring-0 canonical BLAKE3 digest (32 bytes) for tool code and manifests.
#[pyfunction]
fn blake3_digest(data: &[u8]) -> Vec<u8> {
    blake3::hash(data).as_bytes().to_vec()
}

/// Quarantine, post-rename verify `(dev, ino, sha256)`, and destroy a relative regular file
/// under `EffectTxOrchestrator` (`O_DIRECTORY | O_NOFOLLOW`, `.effect_wal.bin` & `.consumed_nonces.bin`).
/// Returns `(dev, ino, pre_sha256_bytes)` on `EffectTxState::Committed`.
#[pyfunction]
#[pyo3(signature = (root_dir, rel_path, nonce, expected_sha256=None))]
fn quarantine_and_destroy(
    root_dir: &str,
    rel_path: &str,
    nonce: Vec<u8>,
    expected_sha256: Option<Vec<u8>>,
) -> PyResult<(u64, u64, Vec<u8>)> {
    let nonce_arr: [u8; 32] = nonce
        .try_into()
        .map_err(|_| PyValueError::new_err("Expected 32-byte EffectTx nonce"))?;
    let expected_arr: Option<[u8; 32]> = match expected_sha256 {
        Some(bytes) => Some(
            bytes
                .try_into()
                .map_err(|_| PyValueError::new_err("Expected 32-byte SHA-256 digest"))?,
        ),
        None => None,
    };
    let orchestrator =
        EffectTxOrchestrator::<NativeSecureFs>::new(Path::new(root_dir)).map_err(secure_fs_denied)?;
    let identity = orchestrator
        .quarantine_and_destroy_relative(Path::new(root_dir), rel_path, SERVER, nonce_arr, expected_arr)
        .map_err(secure_fs_denied)?;
    Ok((
        identity.locator.dev,
        identity.locator.ino,
        identity.state.hash.to_vec(),
    ))
}

/// Additional extension entry point in the kernel cdylib.
#[pymodule]
fn _babylon60_mcp(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<McpBroker>()?;
    m.add_class::<McpToken>()?;
    m.add_function(wrap_pyfunction!(blake3_digest, m)?)?;
    m.add_function(wrap_pyfunction!(quarantine_and_destroy, m)?)?;
    Ok(())
}
