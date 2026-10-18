use std::os::unix::ffi::OsStrExt;
use std::os::unix::io::RawFd;
use std::path::Path;
use libc;

use crate::ontology::babylon::RejectReason;

/// (FL-008) Scoped Capability Handle.
/// Replaces string paths with an unforgeable descriptor-based root.
#[derive(Debug)]
pub struct ScopedHandle {
    /// The unique identity of the requester / causal parent.
    pub requester_id: [u8; 32],
    /// The file descriptor pointing to the base directory.
    pub dirfd: RawFd,
    /// Physical device ID of the directory.
    pub dev: u64,
    /// Physical inode of the directory.
    pub ino: u64,
}

impl ScopedHandle {
    /// Creates a new scoped handle by opening the directory securely.
    pub fn new(path: &Path, requester_id: [u8; 32]) -> Result<Self, std::io::Error> {
        let c_path = std::ffi::CString::new(path.as_os_str().as_bytes())?;
        
        let fd = unsafe {
            libc::open(
                c_path.as_ptr(),
                libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC | libc::O_NOFOLLOW
            )
        };
        
        if fd < 0 {
            return Err(std::io::Error::last_os_error());
        }
        
        let mut stat: libc::stat = unsafe { std::mem::zeroed() };
        if unsafe { libc::fstat(fd, &mut stat) } < 0 {
            let err = std::io::Error::last_os_error();
            unsafe { libc::close(fd) };
            return Err(err);
        }
        
        Ok(Self {
            requester_id,
            dirfd: fd,
            dev: stat.st_dev as u64,
            ino: stat.st_ino as u64,
        })
    }

    /// Verifies that the capability is claimed by its legitimate causal parent.
    /// If not, it returns a ConfusedDeputyAttempt rejection.
    pub fn verify_causal_parent(&self, claimant_id: &[u8; 32]) -> Result<(), RejectReason> {
        if &self.requester_id != claimant_id {
            Err(RejectReason::ConfusedDeputyAttempt)
        } else {
            Ok(())
        }
    }
}

impl Drop for ScopedHandle {
    fn drop(&mut self) {
        if self.dirfd >= 0 {
            unsafe { libc::close(self.dirfd) };
        }
    }
}

// ---------------------------------------------------------------------------
// FL-008: MCP CAPABILITY BROKER (Capability Activation != Execution Authority)
// ---------------------------------------------------------------------------

use std::collections::HashMap;
use sha2::{Digest, Sha256};
use crate::ontology::babylon::EffectKind;

/// Helper to compute SHA-256 digest in silicio.
pub fn sha256_digest(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

/// Conservative, component-aware resource scope check.
///
/// Resource scopes are opaque normalized URI/path identifiers, not filesystem
/// authorization. The OS-level executor must independently resolve resources
/// via directory descriptors. Reject ambiguous encodings and dot segments.
fn resource_in_scope(resource_uri: &str, scope: &str) -> bool {
    fn unambiguous(value: &str) -> bool {
        if value.is_empty() || value.contains('\\') || value.contains('%')
            || value.contains('?') || value.contains('#') || value.contains('\0')
            || value.chars().any(char::is_control)
        {
            return false;
        }
        let path = match value.split_once("://") {
            Some((_, path)) => path,
            None => value,
        };
        !path.contains("//") && !path.split('/').any(|c| c == "." || c == "..")
    }
    if !unambiguous(resource_uri) || !unambiguous(scope) {
        return false;
    }
    let root = scope.trim_end_matches('/');
    if root.is_empty() {
        return false;
    }
    resource_uri == root
        || resource_uri.strip_prefix(root).is_some_and(|rest| rest.starts_with('/'))
}


/// Definition of an MCP tool registered in the capability broker.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct McpToolDef {
    /// Name of the tool (e.g. read_fixture, mutate_fixture).
    pub name: String,
    /// Cryptographic hash of the tool's implementation or schema.
    pub code_hash: [u8; 32],
    /// Allowed effect kinds (e.g. FsRead, FsMutate, FsDelete).
    pub allowed_effects: Vec<EffectKind>,
    /// Permitted target resource URI scope / prefix.
    pub target_resource_scope: String,
}

/// Bounded authorization token granting an effect for an MCP tool call.
/// Invariant: Execute(e) => ValidCapability(e, t_commit)
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct McpCapabilityToken {
    /// Unique identifier for this capability token.
    pub token_id: [u8; 32],
    /// Identifier of the issuing / bound MCP server.
    pub server_id: [u8; 32],
    /// Tool name authorized by this token.
    pub tool_name: String,
    /// Cryptographic code hash of the tool authorized.
    pub tool_code_hash: [u8; 32],
    /// Scoped resource URI.
    pub resource_uri: String,
    /// SHA-256 digest of the evaluated arguments.
    pub args_digest: [u8; 32],
    /// Granted effect kind under this token.
    pub granted_effect: EffectKind,
    /// Policy version under which the token was issued.
    pub policy_version: u64,
    /// Issuance epoch.
    pub issued_epoch: u64,
    /// Expiration epoch.
    pub valid_until_epoch: u64,
}

/// Cryptographic receipt / execution evidence generated when Execute(e) commits.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct McpExecutionEvidence {
    /// Unique evidence identifier.
    pub evidence_id: [u8; 32],
    /// Backing capability token ID.
    pub token_id: [u8; 32],
    /// Server identifier.
    pub server_id: [u8; 32],
    /// Executed tool name.
    pub tool_name: String,
    /// Executed effect kind.
    pub effect_kind: EffectKind,
    /// Target resource URI.
    pub resource_uri: String,
    /// Epoch timestamp at commit time.
    pub commit_epoch: u64,
    /// SHA-256 digest of execution evidence.
    pub evidence_digest: [u8; 32],
}

/// Registered state of an MCP server.
#[derive(Debug, Clone)]
pub struct McpServerRecord {
    /// Unique server identifier.
    pub server_id: [u8; 32],
    /// Whether the server is actively enabled in the environment.
    pub enabled: bool,
    /// Current monotonic epoch of the server.
    pub current_epoch: u64,
    /// Active policy version governing this server.
    pub policy_version: u64,
    /// Map of registered tool definitions.
    pub tools: HashMap<String, McpToolDef>,
}

/// Sovereign Capability Broker enforcing:
/// Tool Available != Tool Authorized != Effect Authorized
/// and Execute(e) => ValidCapability(e, t_commit)
#[derive(Debug, Default)]
pub struct McpCapabilityBroker {
    /// Map of registered MCP servers by server ID.
    pub servers: HashMap<[u8; 32], McpServerRecord>,
    /// Revocation tombstone table for invalidated tokens.
    pub revoked_tokens: HashMap<[u8; 32], bool>,
}

impl McpCapabilityBroker {
    /// Creates a new empty capability broker.
    pub fn new() -> Self {
        Self {
            servers: HashMap::new(),
            revoked_tokens: HashMap::new(),
        }
    }

    /// Registers a new MCP server in the broker.
    pub fn register_server(&mut self, server_id: [u8; 32], enabled: bool, policy_version: u64) {
        self.servers.insert(
            server_id,
            McpServerRecord {
                server_id,
                enabled,
                current_epoch: 1,
                policy_version,
                tools: HashMap::new(),
            },
        );
    }

    /// Sets the operational status (enabled/disabled) of an MCP server.
    pub fn set_server_enabled(&mut self, server_id: &[u8; 32], enabled: bool) -> Result<(), RejectReason> {
        let server = self.servers.get_mut(server_id).ok_or_else(|| {
            RejectReason::ResourceNotFound("Server not registered in broker".to_string())
        })?;
        server.enabled = enabled;
        Ok(())
    }

    /// Registers an MCP tool definition under an existing server.
    pub fn register_tool(&mut self, server_id: &[u8; 32], tool: McpToolDef) -> Result<(), RejectReason> {
        let server = self.servers.get_mut(server_id).ok_or_else(|| {
            RejectReason::ResourceNotFound("Server not registered in broker".to_string())
        })?;
        server.tools.insert(tool.name.clone(), tool);
        Ok(())
    }

    /// Advances the epoch of an MCP server, invalidating previous epoch tokens.
    pub fn advance_server_epoch(&mut self, server_id: &[u8; 32]) -> Result<u64, RejectReason> {
        let server = self.servers.get_mut(server_id).ok_or_else(|| {
            RejectReason::ResourceNotFound("Server not registered in broker".to_string())
        })?;
        server.current_epoch += 1;
        Ok(server.current_epoch)
    }

    /// Updates the policy version of an MCP server, invalidating tokens bound to older versions.
    pub fn update_policy_version(&mut self, server_id: &[u8; 32], new_version: u64) -> Result<(), RejectReason> {
        let server = self.servers.get_mut(server_id).ok_or_else(|| {
            RejectReason::ResourceNotFound("Server not registered in broker".to_string())
        })?;
        server.policy_version = new_version;
        Ok(())
    }

    /// Explicitly revokes a capability token prior to its expiration.
    pub fn revoke_token(&mut self, token_id: &[u8; 32]) {
        self.revoked_tokens.insert(*token_id, true);
    }

    /// Evaluates whether a tool capability may be requested and issued.
    #[allow(clippy::too_many_arguments)]
    pub fn request_capability(
        &self,
        server_id: &[u8; 32],
        tool_name: &str,
        tool_code_hash: &[u8; 32],
        args: &[u8],
        resource_uri: &str,
        requested_effect: EffectKind,
        valid_duration_epochs: u64,
    ) -> Result<McpCapabilityToken, RejectReason> {
        let server = self.servers.get(server_id).ok_or_else(|| {
            RejectReason::ResourceNotFound("Server not registered".to_string())
        })?;

        if !server.enabled {
            return Err(RejectReason::ServerDisabled);
        }

        let tool = server.tools.get(tool_name).ok_or(RejectReason::ToolIdentityMismatch)?;

        if &tool.code_hash != tool_code_hash {
            return Err(RejectReason::ToolIdentityMismatch);
        }

        if !tool.allowed_effects.contains(&requested_effect) {
            return Err(RejectReason::CapabilityEscalation);
        }

        if !resource_in_scope(resource_uri, &tool.target_resource_scope) {
            return Err(RejectReason::PolicyDenied("Target resource outside tool scope".to_string()));
        }

        let args_digest = sha256_digest(args);

        // Compute unique deterministic token ID:
        let mut token_seed = Vec::with_capacity(128);
        token_seed.extend_from_slice(server_id);
        token_seed.extend_from_slice(tool_name.as_bytes());
        token_seed.extend_from_slice(tool_code_hash);
        token_seed.extend_from_slice(&args_digest);
        token_seed.extend_from_slice(&server.current_epoch.to_le_bytes());
        token_seed.extend_from_slice(&(requested_effect as u32).to_le_bytes());
        let token_id = sha256_digest(&token_seed);

        Ok(McpCapabilityToken {
            token_id,
            server_id: *server_id,
            tool_name: tool_name.to_string(),
            tool_code_hash: *tool_code_hash,
            resource_uri: resource_uri.to_string(),
            args_digest,
            granted_effect: requested_effect,
            policy_version: server.policy_version,
            issued_epoch: server.current_epoch,
            valid_until_epoch: server.current_epoch + valid_duration_epochs,
        })
    }

    /// Evaluates commit binding at t_commit:
    /// Invariant: Execute(e) => ValidCapability(e, t_commit)
    #[allow(clippy::too_many_arguments)]
    pub fn commit_execution(
        &self,
        token: &McpCapabilityToken,
        server_id: &[u8; 32],
        tool_name: &str,
        tool_code_hash: &[u8; 32],
        args: &[u8],
        resource_uri: &str,
        effect: EffectKind,
        t_commit: u64,
    ) -> Result<McpExecutionEvidence, RejectReason> {
        // 1. Explicit revocation check
        if self.revoked_tokens.contains_key(&token.token_id) {
            return Err(RejectReason::StaleCapability);
        }

        // 2. Server presence & enabled check
        let server = self.servers.get(server_id).ok_or(RejectReason::ServerDisabled)?;
        if !server.enabled {
            return Err(RejectReason::ServerDisabled);
        }

        // 3. Causal origin & confused deputy check
        if &token.server_id != server_id {
            return Err(RejectReason::ConfusedDeputyAttempt);
        }

        // 4. Tool identity check (name and cryptographic code hash)
        if token.tool_name != tool_name {
            return Err(RejectReason::ToolIdentityMismatch);
        }
        if &token.tool_code_hash != tool_code_hash {
            return Err(RejectReason::ToolIdentityMismatch);
        }

        let server_tool = server.tools.get(tool_name).ok_or(RejectReason::ToolIdentityMismatch)?;
        if &server_tool.code_hash != tool_code_hash {
            return Err(RejectReason::ToolIdentityMismatch);
        }

        // 5. Capability escalation check
        if token.granted_effect != effect {
            return Err(RejectReason::CapabilityEscalation);
        }
        if !server_tool.allowed_effects.contains(&effect) {
            return Err(RejectReason::CapabilityEscalation);
        }

        // 6. Configuration / TOCTOU drift check (resource and args)
        if token.resource_uri != resource_uri {
            return Err(RejectReason::ConfigurationDrift);
        }
        if !resource_in_scope(resource_uri, &server_tool.target_resource_scope) {
            return Err(RejectReason::ConfigurationDrift);
        }
        let current_args_digest = sha256_digest(args);
        if token.args_digest != current_args_digest {
            return Err(RejectReason::ConfigurationDrift);
        }

        // 7. Policy version drift check
        if server.policy_version != token.policy_version {
            return Err(RejectReason::ConfigurationDrift);
        }

        // 8. Stale epoch / validity window check at t_commit
        if server.current_epoch != token.issued_epoch {
            return Err(RejectReason::StaleCapability);
        }
        if t_commit > token.valid_until_epoch {
            return Err(RejectReason::StaleCapability);
        }

        // All 8 gates passed. Execute(e) verified:
        let mut evidence_seed = Vec::with_capacity(128);
        evidence_seed.extend_from_slice(&token.token_id);
        evidence_seed.extend_from_slice(server_id);
        evidence_seed.extend_from_slice(tool_name.as_bytes());
        evidence_seed.extend_from_slice(&(effect as u32).to_le_bytes());
        evidence_seed.extend_from_slice(resource_uri.as_bytes());
        evidence_seed.extend_from_slice(&t_commit.to_le_bytes());
        let evidence_digest = sha256_digest(&evidence_seed);

        let mut id_seed = Vec::with_capacity(64);
        id_seed.extend_from_slice(&evidence_digest);
        id_seed.extend_from_slice(&[0xEE; 32]);
        let evidence_id = sha256_digest(&id_seed);

        Ok(McpExecutionEvidence {
            evidence_id,
            token_id: token.token_id,
            server_id: *server_id,
            tool_name: tool_name.to_string(),
            effect_kind: effect,
            resource_uri: resource_uri.to_string(),
            commit_epoch: t_commit,
            evidence_digest,
        })
    }
}

