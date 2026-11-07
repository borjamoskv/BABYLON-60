//! Typed Python bridge to the canonical Rust broker (no duplicate policy engine).
use crate::capability::{McpCapabilityBroker, McpCapabilityToken, McpPolicyState, McpToolDef};
use crate::ontology::babylon::{EffectKind, RejectReason};
use pyo3::exceptions::{PyPermissionError, PyValueError};
use pyo3::prelude::*;

const SERVER: [u8; 32] = [0xC1; 32];

fn denied(reason: RejectReason) -> PyErr {
    PyPermissionError::new_err(format!("MCP admission rejected: {reason:?}"))
}

fn policy(value: &str) -> PyResult<McpPolicyState> {
    match value {
        "Enabled" => Ok(McpPolicyState::Enabled),
        "Disabled" => Ok(McpPolicyState::Disabled),
        "Unconfigured" => Ok(McpPolicyState::Unconfigured),
        _ => Err(PyValueError::new_err("Unknown external policy state")),
    }
}

fn definition(name: &str, hash: Vec<u8>, effect: &str) -> PyResult<McpToolDef> {
    let effect = match effect {
        "LedgerAppend" => EffectKind::LedgerAppend,
        "ProcSpawn" => EffectKind::ProcSpawn,
        "NetTransmit" => EffectKind::NetTransmit,
        _ => return Err(PyValueError::new_err("Unknown MCP effect")),
    };
    if name.is_empty() || !name.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_') {
        return Err(PyValueError::new_err("Invalid canonical tool name"));
    }
    Ok(McpToolDef {
        name: name.into(),
        code_hash: hash
            .try_into()
            .map_err(|_| PyValueError::new_err("Expected 32-byte hash"))?,
        allowed_effects: vec![effect],
        target_resource_scope: format!("mcp://cortex/{name}"),
    })
}

/// Opaque token; Python cannot construct or rebind it.
#[pyclass(frozen)]
pub struct McpToken {
    inner: McpCapabilityToken,
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

    fn discover(&mut self, name: &str, hash: Vec<u8>, effect: &str) -> PyResult<()> {
        self.inner
            .register_tool(&SERVER, definition(name, hash, effect)?)
            .map_err(denied)
    }

    fn authorize(&mut self, name: &str, hash: Vec<u8>, effect: &str) -> PyResult<()> {
        self.inner
            .authorize_tool(&SERVER, definition(name, hash, effect)?)
            .map_err(denied)
    }

    fn revoke(&mut self, name: &str) -> PyResult<()> {
        // Also invalidate approvals when no tool grant has yet been issued.
        self.inner.revoke_tool(&SERVER, name).map_err(denied)?;
        self.inner.advance_server_epoch(&SERVER).map_err(denied)?;
        Ok(())
    }

    fn issue(&self, name: &str, hash: Vec<u8>, effect: &str, args: Vec<u8>) -> PyResult<McpToken> {
        let tool = definition(name, hash, effect)?;
        self.inner
            .request_capability(
                &SERVER,
                name,
                &tool.code_hash,
                &args,
                &tool.target_resource_scope,
                tool.allowed_effects[0],
                1,
            )
            .map(|inner| McpToken { inner })
            .map_err(denied)
    }

    fn validate(
        &self,
        token: PyRef<'_, McpToken>,
        name: &str,
        hash: Vec<u8>,
        effect: &str,
        args: Vec<u8>,
    ) -> PyResult<()> {
        let tool = definition(name, hash, effect)?;
        self.inner
            .commit_execution(
                &token.inner,
                &SERVER,
                name,
                &tool.code_hash,
                &args,
                &tool.target_resource_scope,
                tool.allowed_effects[0],
                token.inner.issued_epoch(),
            )
            .map(|_| ())
            .map_err(denied)
    }
}

/// Additional extension entry point in the kernel cdylib.
#[pymodule]
fn _babylon60_mcp(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<McpBroker>()?;
    m.add_class::<McpToken>()?;
    Ok(())
}
