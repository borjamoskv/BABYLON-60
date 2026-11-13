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
use crate::ontology::babylon::{EffectKind, EffectState, FailureReason};

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

/// Bounded, opaque in-process token granting an effect for an MCP tool call.
/// Fields are private to prevent rebinding stale tokens to a new policy revision.
/// This token is not an authenticated on-wire credential.
///
/// ```compile_fail
/// use babylon60::capability::McpCapabilityToken;
/// fn rebind(token: &mut McpCapabilityToken) {
///     token.issued_epoch = 999;
/// }
/// ```
/// Invariant: Execute(e) => ValidCapability(e, t_commit)
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct McpCapabilityToken {
    /// Unique identifier for this capability token.
    token_id: [u8; 32],
    /// Identifier of the issuing / bound MCP server.
    server_id: [u8; 32],
    /// Tool name authorized by this token.
    tool_name: String,
    /// Cryptographic code hash of the tool authorized.
    tool_code_hash: [u8; 32],
    /// Scoped resource URI.
    resource_uri: String,
    /// SHA-256 digest of the evaluated arguments.
    args_digest: [u8; 32],
    /// Granted effect kind under this token.
    granted_effect: EffectKind,
    /// Policy version under which the token was issued.
    policy_version: u64,
    /// Issuance epoch.
    issued_epoch: u64,
    /// Expiration epoch.
    valid_until_epoch: u64,
}

impl McpCapabilityToken {
    /// Opaque causal revision at issuance, usable as the initial commit tick.
    pub fn issued_epoch(&self) -> u64 {
        self.issued_epoch
    }

    /// Identifier accepted by the broker revocation API.
    pub fn token_id(&self) -> &[u8; 32] {
        &self.token_id
    }
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

/// External availability settings never grant broker authority.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum McpPolicyState {
    /// Explicitly available in the external platform.
    Enabled,
    /// Explicitly unavailable in the external platform.
    Disabled,
    /// Inherit the global setting; unresolved inheritance is unavailable.
    Unconfigured,
}

impl McpPolicyState {
    fn enabled(self, global: Self) -> bool {
        match self {
            Self::Enabled => true,
            Self::Disabled => false,
            Self::Unconfigured => global == Self::Enabled,
        }
    }
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
    // Only trusted control-plane methods can modify these grants.
    authorized_tools: HashMap<String, McpToolDef>,
    external_policy: (McpPolicyState, McpPolicyState),
}

/// Cryptographic skill lock binding enforced by GUARD inside [`McpCapabilityBroker`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuardSkillLockBinding {
    /// Canonical skill identifier.
    pub skill_id: String,
    /// Pinned semantic version.
    pub version: String,
    /// Pinned SHA-256 digest of the skill artifact/manifest.
    pub artifact_sha256: [u8; 32],
    /// Pinned tool identity hash (`sha256(v3.1:<skill_id>@<version>:<artifact_sha256>:<class>)`).
    pub tool_identity_hash: [u8; 32],
    /// Canonical substrate effect kind.
    pub effect_kind: EffectKind,
    /// Whether this skill requires/permits outbound network egress.
    pub network_egress: bool,
    /// Whether the skill's effect classification has been canonically validated (`false => DENY`).
    pub validated: bool,
}

/// Record of a local read (`READ_LOCAL` / `FsRead`) in a compositional trace.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompositionalReadRecord {
    /// Skill that performed or proposed the local read.
    pub skill_id: String,
    /// Local resource URI read.
    pub resource_uri: String,
    /// Precondition snapshot digest at the moment of the local read.
    pub precondition_digest: [u8; 32],
    /// Broker epoch of the read.
    pub epoch: u64,
}

/// Broker-level compositional flow tracker across multiple skills in a session/trace (FL-P09).
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct CompositionalFlowTrace {
    /// Local reads accumulated in this trace (`READ_LOCAL` / `FsRead`).
    pub local_reads: Vec<CompositionalReadRecord>,
    /// Outbound network destinations targeted in this trace (`EXTERNAL_NETWORK` / `NetTransmit`).
    pub network_destinations: Vec<String>,
    /// Ordered multi-skill effect chain (`(skill_id, EffectKind)`).
    pub effect_chain: Vec<(String, EffectKind)>,
}

/// Input parameters for GUARD effect proposal inside [`McpCapabilityBroker`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuardProposalInput {
    /// Target `skill_id`.
    pub skill_id: String,
    /// Requested skill `version`.
    pub version: String,
    /// Provided `tool_identity_hash`.
    pub tool_identity_hash: [u8; 32],
    /// Snapshot `artifact_sha256`.
    pub artifact_sha256: [u8; 32],
    /// Caller credential `audience`.
    pub audience: String,
    /// Expected gateway `audience`.
    pub expected_audience: String,
    /// Explicit `project_id`.
    pub project_id: String,
    /// Compositional `trace_id`.
    pub trace_id: String,
    /// Single-use `nonce`.
    pub nonce: String,
    /// Optional downstream passthrough token (must be `None`).
    pub passthrough_token: Option<String>,
    /// Target resource URI / path.
    pub resource_uri: String,
    /// Allowed root prefixes from `precondition_snapshot`.
    pub allowed_roots: Vec<String>,
    /// SHA-256 digest of canonicalized arguments.
    pub args_digest: [u8; 32],
    /// SHA-256 digest of `precondition_snapshot`.
    pub precondition_snapshot_hash: [u8; 32],
    /// Expected pre-execution SHA-256 of target resource (required for mutations).
    pub expected_pre_hash: Option<[u8; 32]>,
    /// Observed pre-execution SHA-256 of target resource from current `precondition_snapshot`.
    pub observed_pre_hash: Option<[u8; 32]>,
    /// Optional outbound network destination URI/host.
    pub network_destination: Option<String>,
    /// Current broker epoch at proposal time.
    pub current_epoch: u64,
    /// Expiration epoch for the nonce and issued capability.
    pub expires_at_epoch: u64,
    /// Whether an out-of-band human operator explicitly approved this `(project_id, nonce)`.
    pub human_approved: bool,
}

/// Capability grant issued by [`McpCapabilityBroker::propose_skill_effect`] in state [`EffectState::Authorized`].
///
/// Issuing this grant NEVER executes the underlying effect (`Proposed/Authorized != Executed`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuardCapabilityGrant {
    /// Deterministic 32-byte capability identifier.
    pub capability_id: [u8; 32],
    /// Underlying broker capability token.
    pub token: McpCapabilityToken,
    /// Bound `skill_id`.
    pub skill_id: String,
    /// Bound `version`.
    pub version: String,
    /// Bound `tool_identity_hash`.
    pub tool_identity_hash: [u8; 32],
    /// Bound `audience`.
    pub audience: String,
    /// Bound `project_id`.
    pub project_id: String,
    /// Bound compositional `trace_id`.
    pub trace_id: String,
    /// Bound single-use `nonce`.
    pub nonce: String,
    /// Bound target `resource_uri`.
    pub resource_uri: String,
    /// Bound `args_digest`.
    pub args_digest: [u8; 32],
    /// Bound `precondition_snapshot_hash`.
    pub precondition_snapshot_hash: [u8; 32],
    /// Expected pre-state digest for postcondition comparison.
    pub expected_pre_hash: Option<[u8; 32]>,
    /// Granted substrate `EffectKind`.
    pub effect_kind: EffectKind,
    /// Issuance epoch.
    pub issued_epoch: u64,
    /// Expiration epoch.
    pub expires_at_epoch: u64,
    /// Current [`EffectState`] in the broker state machine.
    pub state: EffectState,
}

/// Sovereign Capability Broker enforcing:
/// Tool Available != Tool Authorized != Effect Authorized
/// and Execute(e) => ValidCapability(e, t_commit).
/// `commit_execution` validates admission and emits a receipt; the caller must
/// mediate the actual effect and serialize it with policy changes.
///
/// ```compile_fail
/// use babylon60::capability::McpCapabilityBroker;
/// fn bypass(broker: &mut McpCapabilityBroker) {
///     broker.servers.clear();
/// }
/// ```
#[derive(Debug, Default, Clone)]
pub struct McpCapabilityBroker {
    /// Map of registered MCP servers by server ID.
    servers: HashMap<[u8; 32], McpServerRecord>,
    /// Revocation tombstone table for invalidated tokens.
    revoked_tokens: HashMap<[u8; 32], bool>,
    revision: u64,
    /// Locked skills registered from `skills-lock.json` (`skill_id -> GuardSkillLockBinding`).
    locked_skills: HashMap<String, GuardSkillLockBinding>,
    /// Single-use consumed nonces (`nonce_digest -> consumed_epoch`) for FL-P10 anti-replay.
    consumed_nonces: HashMap<[u8; 32], u64>,
    /// Compositional taint & flow tracker (`trace_id -> CompositionalFlowTrace`) for FL-P09.
    compositional_traces: HashMap<String, CompositionalFlowTrace>,
    /// Issued GUARD capability grants (`capability_id -> GuardCapabilityGrant`).
    guard_capabilities: HashMap<[u8; 32], GuardCapabilityGrant>,
    /// Canonical [`EffectState`] transition log (`request_or_cap_id -> EffectState`).
    effect_states: HashMap<[u8; 32], EffectState>,
}

impl McpCapabilityBroker {
    /// Current causal revision for an out-of-band, exact-call approval.
    pub fn policy_revision(&self, server_id: &[u8; 32]) -> Result<u64, RejectReason> {
        self.servers.get(server_id).map(|server| server.current_epoch)
            .ok_or(RejectReason::ServerDisabled)
    }

    /// Creates a new empty capability broker.
    pub fn new() -> Self {
        Self {
            servers: HashMap::new(),
            revoked_tokens: HashMap::new(),
            revision: 0,
            locked_skills: HashMap::new(),
            consumed_nonces: HashMap::new(),
            compositional_traces: HashMap::new(),
            guard_capabilities: HashMap::new(),
            effect_states: HashMap::new(),
        }
    }

    // Never reuse a revision, including across re-registration and ABA changes.
    fn next_revision(&mut self) -> u64 {
        self.revision = self
            .revision
            .checked_add(1)
            .expect("MCP revision exhausted");
        self.revision
    }

    /// Registers external availability only; re-registration discards grants.
    pub fn register_server(&mut self, server_id: [u8; 32], enabled: bool, policy_version: u64) {
        let epoch = self.next_revision();
        self.servers.insert(
            server_id,
            McpServerRecord {
                server_id,
                enabled,
                current_epoch: epoch,
                policy_version,
                tools: HashMap::new(),
                authorized_tools: HashMap::new(),
                external_policy: (
                    if enabled {
                        McpPolicyState::Enabled
                    } else {
                        McpPolicyState::Disabled
                    },
                    McpPolicyState::Unconfigured,
                ),
            },
        );
    }

    /// Sets external availability, preserving the explicit grant ceiling.
    pub fn set_server_enabled(
        &mut self,
        server_id: &[u8; 32],
        enabled: bool,
    ) -> Result<(), RejectReason> {
        self.update_external_policy(
            server_id,
            if enabled {
                McpPolicyState::Enabled
            } else {
                McpPolicyState::Disabled
            },
            McpPolicyState::Unconfigured,
        )
    }

    /// Observe platform defaults/inheritance. Even a change with the same effective
    /// availability invalidates tokens; an identical refresh is idempotent.
    pub fn update_external_policy(
        &mut self,
        server_id: &[u8; 32],
        feature: McpPolicyState,
        global: McpPolicyState,
    ) -> Result<(), RejectReason> {
        let revision = self.next_revision();
        let server = self.server_mut(server_id)?;
        if server.external_policy != (feature, global) {
            server.external_policy = (feature, global);
            server.enabled = feature.enabled(global);
            server.current_epoch = revision;
        }
        Ok(())
    }

    fn server_mut(&mut self, server_id: &[u8; 32]) -> Result<&mut McpServerRecord, RejectReason> {
        self.servers.get_mut(server_id).ok_or_else(|| {
            RejectReason::ResourceNotFound("Server not registered in broker".to_string())
        })
    }

    /// Discovery is untrusted input; this method never authorizes a tool.
    pub fn register_tool(
        &mut self,
        server_id: &[u8; 32],
        tool: McpToolDef,
    ) -> Result<(), RejectReason> {
        let revision = self.next_revision();
        let server = self.server_mut(server_id)?;
        if server.tools.get(&tool.name) != Some(&tool) {
            server.current_epoch = revision;
            server.tools.insert(tool.name.clone(), tool);
        }
        Ok(())
    }

    /// Trusted control plane only: explicitly approve a reviewed tool definition.
    /// Do not expose this method to discovery, policy sync, or agent tool calls.
    /// This is an in-process grant, not hardware attestation or OS confinement.
    pub fn authorize_tool(
        &mut self,
        server_id: &[u8; 32],
        grant: McpToolDef,
    ) -> Result<(), RejectReason> {
        let revision = self.next_revision();
        let server = self.server_mut(server_id)?;
        if server.tools.get(&grant.name) != Some(&grant) {
            return Err(RejectReason::ToolIdentityMismatch);
        }
        if server.authorized_tools.get(&grant.name) != Some(&grant) {
            server.current_epoch = revision;
            server.authorized_tools.insert(grant.name.clone(), grant);
        }
        Ok(())
    }

    /// Revoke explicit authority and invalidate outstanding tokens.
    pub fn revoke_tool(
        &mut self,
        server_id: &[u8; 32],
        tool_name: &str,
    ) -> Result<(), RejectReason> {
        let revision = self.next_revision();
        let server = self.server_mut(server_id)?;
        if server.authorized_tools.remove(tool_name).is_some() {
            server.current_epoch = revision;
        }
        Ok(())
    }

    fn check_authority(
        server: &McpServerRecord,
        tool_name: &str,
        code_hash: &[u8; 32],
        resource_uri: &str,
        effect: EffectKind,
    ) -> Result<(), RejectReason> {
        let grant = server.authorized_tools.get(tool_name).ok_or_else(|| {
            RejectReason::PolicyDenied("Tool lacks explicit broker authorization".into())
        })?;
        if &grant.code_hash != code_hash
            || !grant.allowed_effects.contains(&effect)
            || !resource_in_scope(resource_uri, &grant.target_resource_scope)
        {
            return Err(RejectReason::CapabilityEscalation);
        }
        Ok(())
    }

    /// Advances the epoch, invalidating previous tokens.
    pub fn advance_server_epoch(&mut self, server_id: &[u8; 32]) -> Result<u64, RejectReason> {
        let revision = self.next_revision();
        self.server_mut(server_id)?.current_epoch = revision;
        Ok(revision)
    }

    /// A policy change invalidates tokens even if its version is later restored.
    pub fn update_policy_version(
        &mut self,
        server_id: &[u8; 32],
        new_version: u64,
    ) -> Result<(), RejectReason> {
        let revision = self.next_revision();
        let server = self.server_mut(server_id)?;
        if server.policy_version != new_version {
            server.policy_version = new_version;
            server.current_epoch = revision;
        }
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
        let server = self
            .servers
            .get(server_id)
            .ok_or_else(|| RejectReason::ResourceNotFound("Server not registered".to_string()))?;

        if !server.enabled {
            return Err(RejectReason::ServerDisabled);
        }

        let tool = server
            .tools
            .get(tool_name)
            .ok_or(RejectReason::ToolIdentityMismatch)?;

        if &tool.code_hash != tool_code_hash {
            return Err(RejectReason::ToolIdentityMismatch);
        }

        if !tool.allowed_effects.contains(&requested_effect) {
            return Err(RejectReason::CapabilityEscalation);
        }

        if !resource_in_scope(resource_uri, &tool.target_resource_scope) {
            return Err(RejectReason::PolicyDenied(
                "Target resource outside tool scope".to_string(),
            ));
        }

        Self::check_authority(
            server,
            tool_name,
            tool_code_hash,
            resource_uri,
            requested_effect,
        )?;
        let valid_until_epoch = server
            .current_epoch
            .checked_add(valid_duration_epochs)
            .ok_or(RejectReason::StaleCapability)?;
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
            valid_until_epoch,
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
        let server = self
            .servers
            .get(server_id)
            .ok_or(RejectReason::ServerDisabled)?;
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

        let server_tool = server
            .tools
            .get(tool_name)
            .ok_or(RejectReason::ToolIdentityMismatch)?;
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

        Self::check_authority(server, tool_name, tool_code_hash, resource_uri, effect)?;

        // 7. Policy version drift check
        if server.policy_version != token.policy_version {
            return Err(RejectReason::ConfigurationDrift);
        }

        // 8. Stale epoch / validity window check at t_commit
        if server.current_epoch != token.issued_epoch {
            return Err(RejectReason::StaleCapability);
        }
        if t_commit < token.issued_epoch || t_commit > token.valid_until_epoch {
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

    // -----------------------------------------------------------------------
    // GUARD v3.1: Lockfile Binding, Compositional Flow & Postcondition State Machine
    // -----------------------------------------------------------------------

    /// Register a `skills-lock.json` binding and revoke pending grants if it changed.
    pub fn register_skill_lock_binding(&mut self, binding: GuardSkillLockBinding) {
        if self
            .locked_skills
            .get(&binding.skill_id)
            .is_some_and(|current| current != &binding)
        {
            for grant in self.guard_capabilities.values_mut().filter(|grant| {
                grant.skill_id == binding.skill_id && grant.state == EffectState::Authorized
            }) {
                // Keep the revocation even if the previous binding is restored.
                self.revoked_tokens.insert(grant.capability_id, true);
                grant.state = EffectState::Rejected(RejectReason::StaleCapability);
                self.effect_states
                    .insert(grant.capability_id, grant.state.clone());
            }
        }
        self.locked_skills.insert(binding.skill_id.clone(), binding);
    }

    /// Inspect the compositional flow trace for a given `trace_id`.
    pub fn compositional_trace(&self, trace_id: &str) -> Option<&CompositionalFlowTrace> {
        self.compositional_traces.get(trace_id)
    }

    /// Inspect the canonical [`EffectState`] recorded for a request or capability ID.
    pub fn guard_effect_state(&self, id: &[u8; 32]) -> Option<&EffectState> {
        self.effect_states.get(id)
    }

    /// Evaluate a skill effect proposal through GUARD without executing any side effect.
    ///
    /// Transitions: `EffectState::Requested -> EffectState::Validated -> EffectState::Authorized`
    /// (or `EffectState::Rejected(RejectReason)` on any policy, identity, nonce, expiration,
    /// precondition, unvalidated classification, or `READ_LOCAL -> NETWORK` compositional violation).
    pub fn propose_skill_effect(
        &mut self,
        input: GuardProposalInput,
    ) -> Result<GuardCapabilityGrant, RejectReason> {
        let mut req_seed = Vec::with_capacity(128);
        req_seed.extend_from_slice(input.skill_id.as_bytes());
        req_seed.extend_from_slice(input.version.as_bytes());
        req_seed.extend_from_slice(&input.tool_identity_hash);
        req_seed.extend_from_slice(input.project_id.as_bytes());
        req_seed.extend_from_slice(input.nonce.as_bytes());
        req_seed.extend_from_slice(&input.args_digest);
        let candidate_id = sha256_digest(&req_seed);

        self.effect_states
            .insert(candidate_id, EffectState::Requested);

        // 1. Audience, identity, passthrough, and expiration validation (FL-P10)
        if input
            .passthrough_token
            .as_ref()
            .is_some_and(|t| !t.trim().is_empty())
        {
            let reason =
                RejectReason::PolicyDenied("TOKEN_PASSTHROUGH_FORBIDDEN".to_string());
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        if input.audience != input.expected_audience
            || input.project_id.trim().is_empty()
            || input.nonce.trim().is_empty()
        {
            let reason = RejectReason::ConfusedDeputyAttempt;
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        if input.expires_at_epoch == 0 || input.current_epoch > input.expires_at_epoch {
            let reason = RejectReason::StaleCapability;
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        // 2. Skill lock binding & classification validation (FL-P08 & Unvalidated => DENY)
        let Some(binding) = self.locked_skills.get(&input.skill_id).cloned() else {
            let reason = RejectReason::ToolIdentityMismatch;
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        };

        if !binding.validated {
            let reason = RejectReason::PolicyDenied(
                "UNVALIDATED_EFFECT_CLASSIFICATION".to_string(),
            );
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        if binding.version != input.version
            || binding.tool_identity_hash != input.tool_identity_hash
            || binding.artifact_sha256 != input.artifact_sha256
        {
            let reason = RejectReason::ToolIdentityMismatch;
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        // 3. Precondition snapshot verification
        let path_ok = !input.resource_uri.is_empty()
            && !input.resource_uri.contains("..")
            && input.allowed_roots.iter().any(|root| {
                let r = root.trim_end_matches('/');
                r == "."
                    || input.resource_uri == r
                    || input.resource_uri.starts_with(&format!("{r}/"))
                    || resource_in_scope(&input.resource_uri, root)
            });
        if !path_ok {
            let reason = RejectReason::PreconditionMismatch;
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        if matches!(
            binding.effect_kind,
            EffectKind::FsMutate | EffectKind::FsDelete
        ) {
            match (input.expected_pre_hash, input.observed_pre_hash) {
                (Some(exp), Some(obs)) if exp == obs => {}
                _ => {
                    let reason = RejectReason::PreconditionMismatch;
                    self.effect_states
                        .insert(candidate_id, EffectState::Rejected(reason.clone()));
                    return Err(reason);
                }
            }
        }

        self.effect_states
            .insert(candidate_id, EffectState::Validated);

        // 4. Single-use nonce anti-replay check (FL-P10)
        let nonce_seed = format!(
            "{}:{}:{}",
            input.audience,
            input.project_id.trim(),
            input.nonce.trim()
        );
        let nonce_digest = sha256_digest(nonce_seed.as_bytes());
        if self.consumed_nonces.contains_key(&nonce_digest) {
            let reason = RejectReason::NonceAlreadyConsumed(nonce_digest);
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        // 5. Compositional flow tracking READ_LOCAL -> NETWORK across skills (FL-P09)
        let requests_network = binding.network_egress
            || binding.effect_kind == EffectKind::NetTransmit
            || input
                .network_destination
                .as_ref()
                .is_some_and(|d| !d.trim().is_empty());

        let has_prior_local_read = self
            .compositional_traces
            .get(&input.trace_id)
            .is_some_and(|trace| !trace.local_reads.is_empty());

        if has_prior_local_read && requests_network && !input.human_approved {
            let reason = RejectReason::PolicyDenied(
                "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK".to_string(),
            );
            self.effect_states
                .insert(candidate_id, EffectState::Rejected(reason.clone()));
            return Err(reason);
        }

        // 6. Consume single-use nonce and update compositional trace in broker
        self.consumed_nonces
            .insert(nonce_digest, input.current_epoch);
        let trace = self
            .compositional_traces
            .entry(input.trace_id.clone())
            .or_default();
        if binding.effect_kind == EffectKind::FsRead {
            trace.local_reads.push(CompositionalReadRecord {
                skill_id: input.skill_id.clone(),
                resource_uri: input.resource_uri.clone(),
                precondition_digest: input.precondition_snapshot_hash,
                epoch: input.current_epoch,
            });
        }
        if requests_network {
            let dest = input
                .network_destination
                .clone()
                .unwrap_or_else(|| input.resource_uri.clone());
            trace.network_destinations.push(dest);
        }
        trace
            .effect_chain
            .push((input.skill_id.clone(), binding.effect_kind));

        // 7. Issue Authorized capability grant (without executing any effect)
        let server_id = sha256_digest(input.expected_audience.as_bytes());
        let token = McpCapabilityToken {
            token_id: candidate_id,
            server_id,
            tool_name: input.skill_id.clone(),
            tool_code_hash: input.tool_identity_hash,
            resource_uri: input.resource_uri.clone(),
            args_digest: input.args_digest,
            granted_effect: binding.effect_kind,
            policy_version: 1,
            issued_epoch: input.current_epoch,
            valid_until_epoch: input.expires_at_epoch,
        };

        let grant = GuardCapabilityGrant {
            capability_id: candidate_id,
            token,
            skill_id: input.skill_id,
            version: input.version,
            tool_identity_hash: input.tool_identity_hash,
            audience: input.audience,
            project_id: input.project_id,
            trace_id: input.trace_id,
            nonce: input.nonce,
            resource_uri: input.resource_uri,
            args_digest: input.args_digest,
            precondition_snapshot_hash: input.precondition_snapshot_hash,
            expected_pre_hash: input.expected_pre_hash,
            effect_kind: binding.effect_kind,
            issued_epoch: input.current_epoch,
            expires_at_epoch: input.expires_at_epoch,
            state: EffectState::Authorized,
        };

        self.effect_states
            .insert(candidate_id, EffectState::Authorized);
        self.guard_capabilities
            .insert(candidate_id, grant.clone());

        Ok(grant)
    }

    /// Execute an effect exclusively with a valid [`GuardCapabilityGrant`] and verify postconditions
    /// independently against physical substrate state (FL-P11).
    ///
    /// Transitions: `EffectState::Authorized -> EffectState::Executing -> EffectState::Executed -> EffectState::Verified`
    /// (or `EffectState::Failed(FailureReason::DivergenceDetected)` when independent postconditions fail).
    #[allow(clippy::too_many_arguments)]
    pub fn execute_and_verify_skill_effect<F, V>(
        &mut self,
        capability_id: &[u8; 32],
        audience: &str,
        project_id: &str,
        resource_uri: &str,
        args_digest: &[u8; 32],
        commit_epoch: u64,
        execute_fn: F,
        verify_post_hash_fn: V,
    ) -> Result<(McpExecutionEvidence, EffectState), RejectReason>
    where
        F: FnOnce() -> Result<[u8; 32], FailureReason>,
        V: FnOnce() -> Result<[u8; 32], FailureReason>,
    {
        if self.revoked_tokens.contains_key(capability_id) {
            return Err(RejectReason::StaleCapability);
        }

        let Some(grant) = self.guard_capabilities.get(capability_id).cloned() else {
            return Err(RejectReason::PolicyDenied(
                "Execution requires a valid broker-issued capability".to_string(),
            ));
        };

        if grant.state != EffectState::Authorized {
            return Err(RejectReason::StaleCapability);
        }

        if commit_epoch < grant.issued_epoch || commit_epoch > grant.expires_at_epoch {
            self.effect_states.insert(
                *capability_id,
                EffectState::Rejected(RejectReason::StaleCapability),
            );
            return Err(RejectReason::StaleCapability);
        }

        if grant.audience != audience || grant.project_id != project_id {
            self.effect_states.insert(
                *capability_id,
                EffectState::Rejected(RejectReason::ConfusedDeputyAttempt),
            );
            return Err(RejectReason::ConfusedDeputyAttempt);
        }

        if grant.resource_uri != resource_uri || &grant.args_digest != args_digest {
            self.effect_states.insert(
                *capability_id,
                EffectState::Rejected(RejectReason::ConfigurationDrift),
            );
            return Err(RejectReason::ConfigurationDrift);
        }

        // Single-use capability consumption prior to dispatching effect
        self.revoked_tokens.insert(*capability_id, true);
        if let Some(g) = self.guard_capabilities.get_mut(capability_id) {
            g.state = EffectState::Executing;
        }
        self.effect_states
            .insert(*capability_id, EffectState::Executing);

        let mut evidence_seed = Vec::with_capacity(128);
        evidence_seed.extend_from_slice(capability_id);
        evidence_seed.extend_from_slice(&grant.token.server_id);
        evidence_seed.extend_from_slice(grant.skill_id.as_bytes());
        evidence_seed.extend_from_slice(&(grant.effect_kind as u32).to_le_bytes());
        evidence_seed.extend_from_slice(resource_uri.as_bytes());
        evidence_seed.extend_from_slice(&commit_epoch.to_le_bytes());
        let evidence_digest = sha256_digest(&evidence_seed);
        let evidence_id = sha256_digest(&[evidence_digest, [0xEE; 32]].concat());

        let evidence = McpExecutionEvidence {
            evidence_id,
            token_id: *capability_id,
            server_id: grant.token.server_id,
            tool_name: grant.skill_id.clone(),
            effect_kind: grant.effect_kind,
            resource_uri: resource_uri.to_string(),
            commit_epoch,
            evidence_digest,
        };

        // Dispatch effect handler
        let reported_post_hash = match execute_fn() {
            Ok(h) => h,
            Err(fail) => {
                let st = EffectState::Failed(fail);
                if let Some(g) = self.guard_capabilities.get_mut(capability_id) {
                    g.state = st.clone();
                }
                self.effect_states.insert(*capability_id, st.clone());
                return Ok((evidence, st));
            }
        };

        if let Some(g) = self.guard_capabilities.get_mut(capability_id) {
            g.state = EffectState::Executed;
        }
        self.effect_states
            .insert(*capability_id, EffectState::Executed);

        // Independent postcondition verification (FL-P11)
        let actual_post_hash = match verify_post_hash_fn() {
            Ok(h) => h,
            Err(fail) => {
                let st = EffectState::Failed(fail);
                if let Some(g) = self.guard_capabilities.get_mut(capability_id) {
                    g.state = st.clone();
                }
                self.effect_states.insert(*capability_id, st.clone());
                return Ok((evidence, st));
            }
        };

        let postcondition_ok = match grant.effect_kind {
            EffectKind::FsMutate | EffectKind::FsDelete => {
                actual_post_hash == reported_post_hash
                    && grant
                        .expected_pre_hash
                        .is_none_or(|pre| actual_post_hash != pre)
            }
            _ => grant
                .expected_pre_hash
                .is_none_or(|pre| actual_post_hash == pre),
        };

        let final_state = if postcondition_ok {
            EffectState::Verified
        } else {
            EffectState::Failed(FailureReason::DivergenceDetected {
                expected_hash: reported_post_hash,
                actual_hash: actual_post_hash,
            })
        };

        if let Some(g) = self.guard_capabilities.get_mut(capability_id) {
            g.state = final_state.clone();
        }
        self.effect_states
            .insert(*capability_id, final_state.clone());

        Ok((evidence, final_state))
    }
}
