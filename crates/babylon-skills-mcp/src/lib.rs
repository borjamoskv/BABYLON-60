//! # `babylon-skills-mcp` — Immutable SEP-2640 Skills Snapshot & Read-Only MCP Gateway (v3.1)
//!
//! Architecture v3.1:
//!   `BABYLON SKILLS REGISTRY (skills-lock.json) -> MCP GATEWAY (3 Stateless Meta-Primitives) -> BABYLON-60 -> GUARD -> EXECUTION`
//!
//! Non-Implication Chain (6 Disjoint States):
//!   `Registered(s) ⇏ Visible(s, p) ⇏ Loaded(s) ⇏ Proposed(a) ⇏ Authorized(a) ⇏ Verified(a)`
//!
//! Checks implemented within the trusted host process:
//! 1. **Immutable Snapshot & Lockfile Verification on Boot:** Files are read once at initialization
//!    via held roots and component-wise `openat | O_NOFOLLOW` descriptors, sealed with SHA-256
//!    digests. When `skills-lock.json` is active, any skill whose `tool_identity_hash` is absent or
//!    mismatched is rejected at startup, including altered policy fields (FL-P08).
//! 2. **Snapshot-based discovery:** `skills/list`, `skills/get`, `resources/read`,
//!    `prompts/list`, `prompts/get`, and the 3 v3.1 orchestration tools (`skills.discover`,
//!    `skills.inspect`, `skills.propose_effect`) serve strictly from memory.
//! 3. **Bounded O(1) MCP Tool Surface:** `tools/list` exposes ONLY three stateless orchestration
//!    meta-primitives (`skills.discover`, `skills.inspect`, `skills.propose_effect`), keeping base
//!    context token footprint fixed regardless of whether the registry holds 107, 131, or 500 skills.
//! 4. **Strict Authority Separation & Flow Control (`ΔSkills ⇏ ΔAuthority`):**
//!    - Chaining `READ_LOCAL` followed by `EXTERNAL_NETWORK` (`READ_EXT` / `EGRESS_REQUIRED`) in the
//!      same turn/trace invalidates automatic capability and returns `PENDING_APPROVAL` (FL-P09).
//!    - Every invocation requires an audience-bound credential (`mcp://babylon-skills-gateway`),
//!      explicit `project_id`, unique `nonce` (anti-replay), and forbids token passthrough (FL-P10).
//!    - Proposals stop at `AUTHORIZED` with zero effects; client-supplied execution evidence is
//!      rejected. Only `execute_with_capability` may reach `Verified` after a host-supplied
//!      executor and independent observer run (FL-P11). These callbacks are trusted code.

#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::File;
use std::io;
use std::os::fd::AsRawFd;
use std::path::Path;
use std::sync::Mutex;

mod confined_fs;
pub use confined_fs::{read_bytes_from_root, read_bytes_nofollow};
use confined_fs::{directory_names, ignorable_entry_error, open_child, read_regular};

use babylon60::capability::{
    sha256_digest, GuardProposalInput, GuardSkillLockBinding, McpCapabilityBroker, McpToolDef,
    ScopedHandle,
};
use babylon60::ontology::babylon::{EffectKind, EffectState, FailureReason, RejectReason};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

/// Excluded directory names during physical skill tree ingestion.
pub const EXCLUDED_NAMES: &[&str] = &["_archive", "archive", ".git", "node_modules", "__pycache__"];

/// Expected audience identifier for audience-bound credentials on the MCP Gateway (FL-P10).
pub const GATEWAY_EXPECTED_AUDIENCE: &str = "mcp://babylon-skills-gateway";

/// Canonical validated roles in `docs/skills.json`.
pub const VALID_SKILL_ROLES: &[&str] = &["arquitecto", "ejecutor", "auditor"];

/// Canonical validated scopes in `docs/skills.json`.
pub const VALID_SKILL_SCOPES: &[&str] = &["workspace", "global", "kernel"];

/// Canonical validated categories in `docs/skills.json`.
pub const VALID_SKILL_CATEGORIES: &[&str] = &[
    "kernel",
    "diagnostics",
    "utilities",
    "meta-kernel",
    "systems",
    "operations",
    "multimedia & dsp",
    "nucleus",
    "socint & web",
    "specialized",
    "governance",
    "workspace",
];

fn default_validated_true() -> bool {
    true
}

/// Effect classification in the v3.1 declarative skill manifest.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EffectClass {
    /// Stateless deterministic computation with zero I/O.
    Pure,
    /// Local read-only inspection within project roots.
    ReadLocal,
    /// External network or cross-boundary read operation.
    ReadExt,
    /// Reversible or compensatable state mutation.
    StateMutation,
    /// Irreversible destructive mutation.
    Destructive,
    /// Unvalidated or unrecognized classification (`=> DENY` in GUARD).
    Unvalidated,
}

impl EffectClass {
    /// Canonical uppercase string representation.
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Pure => "PURE",
            Self::ReadLocal => "READ_LOCAL",
            Self::ReadExt => "READ_EXT",
            Self::StateMutation => "STATE_MUTATION",
            Self::Destructive => "DESTRUCTIVE",
            Self::Unvalidated => "UNVALIDATED",
        }
    }

    /// Map declarative `EffectClass` to canonical `babylon60::ontology::babylon::EffectKind`.
    pub fn to_effect_kind(self) -> EffectKind {
        match self {
            Self::Pure | Self::ReadLocal => EffectKind::FsRead,
            Self::ReadExt => EffectKind::NetTransmit,
            Self::StateMutation => EffectKind::FsMutate,
            Self::Destructive => EffectKind::FsDelete,
            Self::Unvalidated => EffectKind::ProcSpawn,
        }
    }

    /// Parse from a case-insensitive string slice.
    pub fn parse(raw: &str) -> Option<Self> {
        match raw.trim().to_ascii_uppercase().as_str() {
            "PURE" => Some(Self::Pure),
            "READ_LOCAL" => Some(Self::ReadLocal),
            "READ_EXT" | "EXTERNAL_NETWORK" => Some(Self::ReadExt),
            "STATE_MUTATION" => Some(Self::StateMutation),
            "DESTRUCTIVE" => Some(Self::Destructive),
            "UNVALIDATED" => Some(Self::Unvalidated),
            _ => None,
        }
    }
}

/// Reversibility classification in the v3.1 declarative skill manifest.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Reversibility {
    /// Directly reversible without side effects.
    Reversible,
    /// Compensatable via atomic backup or inverse transaction.
    Compensatable,
    /// Irreversible physical or external effect.
    Irreversible,
}

/// Network egress policy for a skill in the v3.1 manifest.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum NetworkEgress {
    /// Zero network egress allowed.
    None,
    /// Outbound network egress required/permitted under policy.
    ExternalNetwork,
}

/// Effect profile of a registered skill.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SkillEffectProfile {
    /// Effect class (`PURE`, `READ_LOCAL`, `READ_EXT`, `STATE_MUTATION`, `DESTRUCTIVE`, `UNVALIDATED`).
    pub class: EffectClass,
    /// Reversibility guarantee (`REVERSIBLE`, `COMPENSATABLE`, `IRREVERSIBLE`).
    pub reversibility: Reversibility,
    /// Whether GUARD requires an explicit action lease before execution.
    pub requires_action_lease: bool,
    /// Network egress requirement (`NONE` or `EXTERNAL_NETWORK`).
    pub network_egress: NetworkEgress,
    /// Whether the structural classification was validated (`false => DENY` in GUARD).
    #[serde(default = "default_validated_true")]
    pub validated: bool,
}

/// Symbolic preconditions and postconditions verified outside the model by GUARD.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SkillGuardInvariants {
    /// Preconditions evaluated prior to issuing an `ActionCapability`.
    pub preconditions: Vec<String>,
    /// Postconditions evaluated by the independent verifier after execution.
    pub postconditions: Vec<String>,
}

/// Deterministic derive of v3.1 `SkillEffectProfile` and `SkillGuardInvariants` from structural metadata.
///
/// Invariant (FASE 1):
/// - Permissions are NEVER inferred from free-text `description`.
/// - Any unvalidated `role`, `scope`, or `category` yields `EffectClass::Unvalidated` (`validated: false`),
///   which GUARD deterministically rejects with `DENY`.
pub fn derive_v31_contract(
    name: &str,
    role: &str,
    category: &str,
    scope: &str,
) -> (SkillEffectProfile, SkillGuardInvariants) {
    let lower_name = name.trim().to_ascii_lowercase();
    let lower_role = role.trim().to_ascii_lowercase();
    let lower_cat = category.trim().to_ascii_lowercase();
    let lower_scope = scope.trim().to_ascii_lowercase();

    let role_valid = VALID_SKILL_ROLES.contains(&lower_role.as_str());
    let scope_valid = VALID_SKILL_SCOPES.contains(&lower_scope.as_str());
    let cat_valid = VALID_SKILL_CATEGORIES.contains(&lower_cat.as_str());
    let validated = !lower_name.is_empty() && role_valid && scope_valid && cat_valid;

    if !validated {
        return (
            SkillEffectProfile {
                class: EffectClass::Unvalidated,
                reversibility: Reversibility::Irreversible,
                requires_action_lease: true,
                network_egress: NetworkEgress::None,
                validated: false,
            },
            SkillGuardInvariants {
                preconditions: vec![
                    "classification.validated == true".to_string(),
                    "target_path WITHIN project.allowed_roots".to_string(),
                ],
                postconditions: vec!["result.status == 'OK'".to_string()],
            },
        );
    }

    let is_network = lower_cat == "socint & web"
        || lower_name.contains("web")
        || lower_name.contains("socint")
        || lower_name.contains("github")
        || lower_name.contains("cloudflare")
        || lower_name.contains("soulseek")
        || lower_name.contains("youtube")
        || lower_name.contains("safari")
        || lower_name.contains("gemini")
        || lower_name.contains("kimi")
        || lower_name.contains("whatsapp");

    let is_destructive = lower_name.contains("purge")
        || lower_name.contains("extinction")
        || lower_name.contains("detonate")
        || lower_name.contains("bomb");

    let is_mutation = lower_name.contains("patch")
        || lower_name.contains("deploy")
        || lower_name.contains("genesis")
        || lower_name.contains("swap")
        || lower_name.contains("production")
        || lower_name.contains("remotion")
        || lower_name.contains("f5tts")
        || lower_name.contains("pika")
        || lower_name.contains("gflow")
        || (lower_role == "ejecutor" && !lower_name.contains("audit"));

    let class = if is_destructive {
        EffectClass::Destructive
    } else if is_network {
        EffectClass::ReadExt
    } else if is_mutation {
        EffectClass::StateMutation
    } else if lower_role == "auditor"
        || lower_cat.contains("audit")
        || lower_cat == "diagnostics"
        || lower_name.contains("audit")
        || lower_name.contains("diagnostics")
        || lower_name.contains("telemetry")
    {
        EffectClass::ReadLocal
    } else {
        EffectClass::Pure
    };

    let reversibility = match class {
        EffectClass::Pure | EffectClass::ReadLocal | EffectClass::ReadExt => {
            Reversibility::Reversible
        }
        EffectClass::StateMutation => Reversibility::Compensatable,
        EffectClass::Destructive | EffectClass::Unvalidated => Reversibility::Irreversible,
    };

    let requires_action_lease = matches!(
        class,
        EffectClass::ReadExt
            | EffectClass::StateMutation
            | EffectClass::Destructive
            | EffectClass::Unvalidated
    );

    let network_egress = if is_network || class == EffectClass::ReadExt {
        NetworkEgress::ExternalNetwork
    } else {
        NetworkEgress::None
    };

    let mut preconditions = vec!["target_path WITHIN project.allowed_roots".to_string()];
    let mut postconditions = vec!["result.status == 'OK'".to_string()];

    if matches!(class, EffectClass::StateMutation | EffectClass::Destructive) {
        preconditions.push("sha256(file(target_path)) == args.expected_pre_hash".to_string());
        postconditions.push("sha256(file(target_path)) == result.observed_post_hash".to_string());
        postconditions.push("result.observed_post_hash != args.expected_pre_hash".to_string());
    } else {
        postconditions.push("sha256(file(target_path)) == args.expected_pre_hash".to_string());
    }

    (
        SkillEffectProfile {
            class,
            reversibility,
            requires_action_lease,
            network_egress,
            validated: true,
        },
        SkillGuardInvariants {
            preconditions,
            postconditions,
        },
    )
}

/// Entry in `skills-lock.json` (BABYLON SKILLS REGISTRY v3.1 lockfile).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SkillLockEntry {
    /// Canonical skill identifier.
    pub skill_id: String,
    /// Functional canonical alias.
    pub canonical_alias: String,
    /// Semantic version string.
    pub version: String,
    /// Immutable SHA-256 digest of the skill's resources (`manifest_sha256`).
    pub artifact_sha256: String,
    /// Bound tool identity hash (`sha256(skill_id || version || artifact_sha256 || effect_class)`).
    pub tool_identity_hash: String,
    /// Lockfile reference URI (`skills-lock.json#<skill_id>@<version>`).
    pub lockfile_ref: String,
    /// Domain category.
    pub domain: String,
    /// Concise summary for `skills.discover`.
    pub summary: String,
    /// Discovery tags.
    pub tags: Vec<String>,
    /// Declarative effect profile.
    pub effect_profile: SkillEffectProfile,
    /// Symbolic preconditions and postconditions enforced by GUARD.
    pub guard_invariants: SkillGuardInvariants,
}

/// Root structure of `skills-lock.json`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SkillsLockfile {
    /// Schema version (`3.1.0`).
    pub schema_version: String,
    /// SHA-256 digest of `docs/skills.json`.
    pub catalog_sha256: String,
    /// Merkle/root SHA-256 digest across all locked skills.
    pub snapshot_root_sha256: String,
    /// Total number of locked skills.
    pub total_skills: usize,
    /// Deterministic map of `skill_id -> SkillLockEntry`.
    pub skills: BTreeMap<String, SkillLockEntry>,
}

/// Typed status returned by `skills.propose_effect` and GUARD verification in Architecture v3.1.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ProposeEffectStatus {
    /// Proposal validated by GUARD and capability issued without executing any side effect (`Authorized(a)`).
    Authorized,
    /// Execution succeeded with valid capability and independent verifier confirmed postconditions (`Verified(a)`).
    Verified,
    /// Execution halted awaiting explicit human/operator approval (e.g., FL-P09 composition escalation).
    PendingApproval,
    /// Execution or capability issuance denied by GUARD policy, lockfile, or precondition mismatch.
    Denied,
    /// Postcondition verification failed after tool reported success (FL-P11) or outcome is indeterminate.
    Failed,
    /// Indeterminate execution state.
    Unknown,
}

/// Audience-bound credential attached to every stateless MCP Gateway call (FL-P10).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AudienceBoundCredential {
    /// Target audience URI; must equal [`GATEWAY_EXPECTED_AUDIENCE`].
    pub audience: String,
    /// Explicit project identifier (`project_id`).
    pub project_id: String,
    /// Unique per-request cryptographic nonce.
    pub nonce: String,
    /// Optional expiration epoch for the credential/nonce.
    #[serde(default)]
    pub expires_at_epoch: Option<u64>,
    /// Optional downstream passthrough token; MUST be `None` (token passthrough is forbidden).
    #[serde(default)]
    pub passthrough_token: Option<String>,
}

/// Candidate `ActionCapability` evaluated and issued by GUARD during `skills.propose_effect`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ActionCapability {
    /// Unique capability identifier (`sha256` hex).
    pub capability_id: String,
    /// Bound `skill_id`.
    pub skill_id: String,
    /// Bound `version`.
    pub version: String,
    /// Bound `tool_identity_hash` verified against `skills-lock.json`.
    pub tool_identity_hash: String,
    /// Bound `project_id`.
    pub project_id: String,
    /// Bound compositional `trace_id`.
    pub trace_id: String,
    /// Bound single-use `nonce`.
    pub nonce: String,
    /// Issuance epoch in the broker.
    pub issued_epoch: u64,
    /// Expiration epoch in the broker.
    pub expires_at_epoch: u64,
    /// Target resource URI / path.
    pub target_resource: String,
    /// SHA-256 digest of canonicalized arguments (`argument_digest`).
    pub argument_digest: String,
    /// Precondition snapshot hash observed in the current turn.
    pub precondition_snapshot_hash: String,
    /// Granted effect class.
    pub effect_class: EffectClass,
}

fn guess_mime_type(rel_path: &str) -> &'static str {
    let lower = rel_path.to_ascii_lowercase();
    if lower.ends_with(".md") {
        "text/markdown"
    } else if lower.ends_with(".yaml") || lower.ends_with(".yml") {
        "application/yaml"
    } else if lower.ends_with(".json") {
        "application/json"
    } else if lower.ends_with(".py") {
        "text/x-python"
    } else if lower.ends_with(".rs") {
        "text/x-rust"
    } else if lower.ends_with(".sh") {
        "text/x-shellscript"
    } else {
        "text/plain"
    }
}

/// Compute the deterministic `tool_identity_hash` for a skill entry.
pub fn compute_tool_identity_hash(
    skill_id: &str,
    version: &str,
    artifact_sha256: &str,
    effect_class: EffectClass,
) -> String {
    let seed = format!(
        "v3.1:{skill_id}@{version}:{artifact_sha256}:{}",
        effect_class.as_str()
    );
    hex::encode(sha256_digest(seed.as_bytes()))
}

/// Immutable in-memory snapshot of a single skill resource file.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SkillResourceSnapshot {
    /// Relative path inside the skill folder (e.g. `SKILL.md`, `contract.yaml`).
    pub relative_path: String,
    /// Canonical MCP resource URI (`skill://<skill>/<relative_path>`).
    pub uri: String,
    /// Detected MIME type.
    pub mime_type: String,
    /// Exact byte length.
    pub size_bytes: usize,
    /// Hex-encoded SHA-256 digest of the raw file bytes.
    pub sha256_hex: String,
    /// UTF-8 content frozen in memory.
    pub text: String,
}

/// Immutable in-memory snapshot of a single skill entry and its verified resources.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SkillEntrySnapshot {
    /// Skill identifier (`name`).
    pub name: String,
    /// Functional canonical alias (`canonical_alias`).
    pub canonical_alias: String,
    /// Semantic version string (`1.0.0` default).
    pub version: String,
    /// Human-readable display title.
    pub display_name: String,
    /// Concise capability description.
    pub description: String,
    /// Role triad (`arquitecto`, `ejecutor`, `auditor`).
    pub role: String,
    /// Scope (`workspace`, `global`, `kernel`).
    pub scope: String,
    /// Exergy tier score.
    pub tier: u64,
    /// Domain category.
    pub category: String,
    /// Deterministic trigger phrases.
    pub triggers: Vec<String>,
    /// Canonical skill URI (`skill://<name>`).
    pub uri: String,
    /// Hex-encoded SHA-256 manifest digest across all resources of this skill.
    pub manifest_sha256_hex: String,
    /// Hex-encoded SHA-256 `tool_identity_hash` bound in `skills-lock.json`.
    pub tool_identity_hash: String,
    /// Declarative v3.1 effect profile.
    pub effect_profile: SkillEffectProfile,
    /// Declarative v3.1 GUARD preconditions and postconditions.
    pub guard_invariants: SkillGuardInvariants,
    /// Raw `SKILL.md` text if physically present in the workspace distribution.
    pub skill_md_text: Option<String>,
    /// Verified resource files belonging to this skill.
    pub resources: Vec<SkillResourceSnapshot>,
}

impl SkillEntrySnapshot {
    /// Generate the JSON Schema for `skills.inspect` on demand.
    pub fn input_json_schema(&self) -> Value {
        let mut props = serde_json::Map::new();
        props.insert(
            "task".to_string(),
            json!({
                "type": "string",
                "description": format!("Task context or instruction for skill '{}'.", self.name)
            }),
        );
        props.insert(
            "target_path".to_string(),
            json!({
                "type": "string",
                "description": "Target path inside project.allowed_roots."
            }),
        );
        let mut required = vec!["target_path"];
        if matches!(
            self.effect_profile.class,
            EffectClass::StateMutation | EffectClass::Destructive
        ) {
            props.insert(
                "expected_pre_hash".to_string(),
                json!({
                    "type": "string",
                    "pattern": "^[a-f0-9]{64}$",
                    "description": "Expected SHA-256 hex digest of target_path before mutation."
                }),
            );
            required.push("expected_pre_hash");
        }
        json!({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": format!("{}InputSchema", self.name),
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": true
        })
    }
}

/// Verified, immutable in-memory snapshot of the skills catalog and workspace tree.
#[derive(Debug, Clone)]
pub struct ImmutableSkillsSnapshot {
    /// Hex-encoded SHA-256 digest of `docs/skills.json`.
    pub catalog_sha256_hex: String,
    /// Hex-encoded SHA-256 root digest of the entire snapshot.
    pub root_sha256_hex: String,
    /// Skills indexed deterministically by canonical `name`.
    skills_by_name: BTreeMap<String, SkillEntrySnapshot>,
    /// Lookup table mapping both `name` and `canonical_alias` to `name`.
    alias_to_name: HashMap<String, String>,
    /// Lookup table mapping `skill://...` URIs to frozen resource snapshots.
    resources_by_uri: HashMap<String, SkillResourceSnapshot>,
    /// Ordered list of workspace skill names physically loaded from disk.
    pub workspace_skill_names: Vec<String>,
}

fn parse_simple_frontmatter(md_text: &str) -> HashMap<String, String> {
    fn insert_scalar(
        map: &mut HashMap<String, String>,
        key: &mut String,
        value: &mut String,
    ) {
        let mut scalar = std::mem::take(value);
        if scalar.len() >= 2
            && ((scalar.starts_with('\'') && scalar.ends_with('\''))
                || (scalar.starts_with('"') && scalar.ends_with('"')))
        {
            scalar = scalar[1..scalar.len() - 1].to_owned();
        }
        let name = std::mem::take(key);
        if !name.is_empty() && !scalar.is_empty() {
            map.insert(name, scalar);
        }
    }

    let mut map = HashMap::new();
    let mut lines = md_text.lines();
    if !lines.next().is_some_and(|line| line.trim_end() == "---") {
        return map;
    }
    let mut key = String::new();
    let mut value = String::new();
    for line in lines {
        // Only a delimiter on its own line terminates frontmatter, not scalar text.
        if line.trim_end() == "---" {
            insert_scalar(&mut map, &mut key, &mut value);
            return map;
        }
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        if line.starts_with(char::is_whitespace) {
            // Only an active scalar accepts continuations. Empty mapping/list
            // declarations never promote nested keys into top-level metadata.
            if !key.is_empty() {
                value.push(' ');
                value.push_str(trimmed);
            }
            continue;
        }
        insert_scalar(&mut map, &mut key, &mut value);
        if let Some((name, scalar)) = trimmed.split_once(':') {
            if !name.trim().is_empty() && !scalar.trim().is_empty() {
                key.push_str(name.trim());
                value.push_str(scalar.trim());
            }
        }
    }
    // An unterminated header is not metadata and must not consume body fields.
    HashMap::new()
}

fn walk_skill_resources(
    skill_name: &str,
    current_dir: &File,
    relative_dir: &Path,
    out: &mut Vec<SkillResourceSnapshot>,
) -> io::Result<()> {
    for name in directory_names(current_dir.as_raw_fd())? {
        if EXCLUDED_NAMES.contains(&name.as_str()) {
            continue;
        }
        let child = match open_child(current_dir.as_raw_fd(), Path::new(&name)) {
            Ok(child) => child,
            Err(error) if ignorable_entry_error(&error) => continue,
            Err(error) => return Err(error),
        };
        let relative = relative_dir.join(&name);
        if child.metadata()?.is_dir() {
            walk_skill_resources(skill_name, &child, &relative, out)?;
        } else {
            let raw = read_regular(child)?;
            let rel = relative.to_str().expect("directory names validated as UTF8").to_owned();
            let digest_hex = hex::encode(sha256_digest(&raw));
            let uri = format!("skill://{skill_name}/{rel}");
            out.push(SkillResourceSnapshot {
                mime_type: guess_mime_type(&rel).to_string(),
                relative_path: rel,
                uri,
                size_bytes: raw.len(),
                sha256_hex: digest_hex,
                text: String::from_utf8_lossy(&raw).into_owned(),
            });
        }
    }
    Ok(())
}

impl ImmutableSkillsSnapshot {
    /// Load and verify the immutable snapshot at startup.
    ///
    /// Uses `ScopedHandle` (`O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW`) on `skills_dir`
    /// when present and `read_bytes_nofollow` on every regular file.
    pub fn load(
        skills_json_path: Option<&Path>,
        skills_dir: Option<&Path>,
        expected_count: Option<usize>,
    ) -> Result<Self, String> {
        let root = skills_dir
            .map(|path| ScopedHandle::new(path, [0xB6; 32]).map_err(|e| {
                format!("Failed to open skills root {}: {e}", path.display())
            }))
            .transpose()?;
        Self::load_from_root(skills_json_path, root.as_ref(), expected_count)
    }

    /// Load from an already authorized directory object, retaining its identity across renames.
    /// Enumeration, metadata and resource reads use only this root and its held child descriptors.
    pub fn load_from_root(
        skills_json_path: Option<&Path>,
        skills_root: Option<&ScopedHandle>,
        expected_count: Option<usize>,
    ) -> Result<Self, String> {
        let mut catalog_entries: Vec<Value> = Vec::new();
        let mut catalog_sha256_hex = hex::encode(sha256_digest(b""));

        if let Some(json_path) = skills_json_path {
            let raw = match read_bytes_nofollow(json_path) {
                Ok(raw) => Some(raw),
                Err(error) if error.kind() == io::ErrorKind::NotFound => None,
                Err(error) => return Err(format!("Failed to read catalog {}: {error}", json_path.display())),
            };
            if let Some(raw) = raw {
                catalog_sha256_hex = hex::encode(sha256_digest(&raw));
                let parsed: Value = serde_json::from_slice(&raw)
                    .map_err(|e| format!("Invalid JSON in {}: {e}", json_path.display()))?;
                if let Some(arr) = parsed.get("entries").and_then(Value::as_array) {
                    catalog_entries = arr.clone();
                }
            }
        }

        // Map of workspace skill name -> (frontmatter, md_text, resources, manifest_sha256_hex)
        #[allow(clippy::type_complexity)]
        let mut ws_loaded: BTreeMap<
            String,
            (
                HashMap<String, String>,
                String,
                Vec<SkillResourceSnapshot>,
                String,
            ),
        > = BTreeMap::new();
        let mut workspace_skill_names = Vec::new();

        if let Some(root) = skills_root {
            for dir_name in directory_names(root.dirfd)
                .map_err(|e| format!("read skills root: {e}"))?
            {
                if EXCLUDED_NAMES.contains(&dir_name.as_str()) {
                    continue;
                }
                let skill_folder = match open_child(root.dirfd, Path::new(&dir_name)) {
                    Ok(folder) => folder,
                    Err(error) if ignorable_entry_error(&error) => continue,
                    Err(error) => return Err(format!("open skill {dir_name}: {error}")),
                };
                if !skill_folder.metadata().map_err(|e| e.to_string())?.is_dir() {
                    continue;
                }
                let md_file = match open_child(skill_folder.as_raw_fd(), Path::new("SKILL.md")) {
                    Ok(file) => file,
                    Err(error) if ignorable_entry_error(&error) => continue,
                    Err(error) => return Err(format!("open skill metadata {dir_name}: {error}")),
                };
                let raw_md = read_regular(md_file)
                    .map_err(|e| format!("read skill metadata {dir_name}: {e}"))?;
                let md_text = String::from_utf8_lossy(&raw_md).into_owned();
                let fm = parse_simple_frontmatter(&md_text);
                let sname = fm.get("name").cloned().unwrap_or_else(|| dir_name.clone());

                let mut resources = Vec::new();
                walk_skill_resources(&sname, &skill_folder, Path::new(""), &mut resources)
                    .map_err(|e| format!("Failed walking skill {sname}: {e}"))?;

                let mut manifest_seed = String::new();
                for r in &resources {
                    manifest_seed.push_str(&format!(
                        "{}:{}:{}\n",
                        r.relative_path, r.size_bytes, r.sha256_hex
                    ));
                }
                let manifest_sha = hex::encode(sha256_digest(manifest_seed.as_bytes()));
                ws_loaded.insert(sname.clone(), (fm, md_text, resources, manifest_sha));
                workspace_skill_names.push(sname);
            }
        }

        let mut skills_by_name = BTreeMap::new();
        let mut alias_to_name = HashMap::new();
        let mut resources_by_uri = HashMap::new();

        for item in &catalog_entries {
            let Some(ename) = item.get("name").and_then(Value::as_str).map(str::trim) else {
                continue;
            };
            if ename.is_empty() {
                continue;
            }
            if skills_by_name.contains_key(ename) {
                return Err(format!("DUPLICATE_SKILL_ID_IN_CATALOG: {ename}"));
            }
            let mut ealias = item
                .get("canonical_alias")
                .and_then(Value::as_str)
                .map(str::trim)
                .filter(|s| !s.is_empty())
                .unwrap_or(ename)
                .to_string();
            let display_name = item
                .get("display_name")
                .and_then(Value::as_str)
                .unwrap_or(ename)
                .to_string();
            let mut description = item
                .get("description")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_string();
            let role = item
                .get("role")
                .and_then(Value::as_str)
                .unwrap_or("ejecutor")
                .to_string();
            let scope = item
                .get("scope")
                .and_then(Value::as_str)
                .unwrap_or("global")
                .to_string();
            let version = item
                .get("version")
                .and_then(Value::as_str)
                .unwrap_or("1.0.0")
                .to_string();
            let tier = item.get("tier").and_then(Value::as_u64).unwrap_or(18000);
            let category = item
                .get("category")
                .and_then(Value::as_str)
                .unwrap_or("General")
                .to_string();
            let triggers: Vec<String> = item
                .get("triggers")
                .and_then(Value::as_array)
                .map(|arr| {
                    arr.iter()
                        .filter_map(Value::as_str)
                        .map(String::from)
                        .collect()
                })
                .unwrap_or_default();

            let (skill_md_text, resources, manifest_sha256_hex) =
                if let Some((fm, md_text, res_vec, m_sha)) = ws_loaded.get(ename) {
                    if let Some(a) = fm.get("canonical_alias").filter(|s| !s.is_empty()) {
                        ealias = a.clone();
                    }
                    if let Some(d) = fm.get("description").filter(|s| !s.is_empty()) {
                        description = d.clone();
                    }
                    for r in res_vec {
                        resources_by_uri.insert(r.uri.clone(), r.clone());
                        if ealias != ename {
                            resources_by_uri
                                .insert(format!("skill://{ealias}/{}", r.relative_path), r.clone());
                        }
                    }
                    (Some(md_text.clone()), res_vec.clone(), m_sha.clone())
                } else {
                    let synth_text = format!(
                        "# CORTEX Skill: {display_name}\n\
                         - Canonical Alias: `{ealias}` (ID: `{ename}`)\n\
                         - Role Triad: `{role}` | Tier: `{tier}` | Scope: `{scope}`\n\
                         - Description: {description}\n"
                    );
                    let synth_sha = hex::encode(sha256_digest(synth_text.as_bytes()));
                    let synth_res = SkillResourceSnapshot {
                        relative_path: "SKILL.md".to_string(),
                        uri: format!("skill://{ename}/SKILL.md"),
                        mime_type: "text/markdown".to_string(),
                        size_bytes: synth_text.len(),
                        sha256_hex: synth_sha.clone(),
                        text: synth_text,
                    };
                    resources_by_uri.insert(synth_res.uri.clone(), synth_res.clone());
                    if ealias != ename {
                        resources_by_uri
                            .insert(format!("skill://{ealias}/SKILL.md"), synth_res.clone());
                    }
                    (None, vec![synth_res], synth_sha)
                };

            let (effect_profile, guard_invariants) =
                derive_v31_contract(ename, &role, &category, &scope);
            let tool_identity_hash = compute_tool_identity_hash(
                ename,
                &version,
                &manifest_sha256_hex,
                effect_profile.class,
            );

            let snap = SkillEntrySnapshot {
                name: ename.to_string(),
                canonical_alias: ealias.clone(),
                version,
                display_name,
                description,
                role,
                scope,
                tier,
                category,
                triggers,
                uri: format!("skill://{ename}"),
                manifest_sha256_hex,
                tool_identity_hash,
                effect_profile,
                guard_invariants,
                skill_md_text,
                resources,
            };
            skills_by_name.insert(ename.to_string(), snap);
            alias_to_name.insert(ename.to_string(), ename.to_string());
            alias_to_name.insert(ealias, ename.to_string());
        }

        for sname in &workspace_skill_names {
            if skills_by_name.contains_key(sname) {
                continue;
            }
            if let Some((fm, md_text, res_vec, m_sha)) = ws_loaded.get(sname) {
                let salias = fm
                    .get("canonical_alias")
                    .cloned()
                    .filter(|s| !s.is_empty())
                    .unwrap_or_else(|| sname.clone());
                let sdesc = fm.get("description").cloned().unwrap_or_default();
                let srole = fm
                    .get("role")
                    .cloned()
                    .unwrap_or_else(|| "ejecutor".to_string());
                let sversion = fm
                    .get("version")
                    .cloned()
                    .unwrap_or_else(|| "1.0.0".to_string());
                let sdisplay = fm
                    .get("display_name")
                    .cloned()
                    .unwrap_or_else(|| sname.clone());
                for r in res_vec {
                    resources_by_uri.insert(r.uri.clone(), r.clone());
                    if salias != *sname {
                        resources_by_uri
                            .insert(format!("skill://{salias}/{}", r.relative_path), r.clone());
                    }
                }
                let (effect_profile, guard_invariants) =
                    derive_v31_contract(sname, &srole, "Workspace", "workspace");
                let tool_identity_hash =
                    compute_tool_identity_hash(sname, &sversion, m_sha, effect_profile.class);
                let snap = SkillEntrySnapshot {
                    name: sname.clone(),
                    canonical_alias: salias.clone(),
                    version: sversion,
                    display_name: sdisplay,
                    description: sdesc,
                    role: srole,
                    scope: "workspace".to_string(),
                    tier: 20000,
                    category: "Workspace".to_string(),
                    triggers: vec![sname.clone(), salias.clone()],
                    uri: format!("skill://{sname}"),
                    manifest_sha256_hex: m_sha.clone(),
                    tool_identity_hash,
                    effect_profile,
                    guard_invariants,
                    skill_md_text: Some(md_text.clone()),
                    resources: res_vec.clone(),
                };
                skills_by_name.insert(sname.clone(), snap);
                alias_to_name.insert(sname.clone(), sname.clone());
                alias_to_name.insert(salias, sname.clone());
            }
        }

        if let Some(expected) = expected_count {
            if skills_by_name.len() != expected {
                return Err(format!(
                    "SKILLS_SNAPSHOT_COUNT_MISMATCH: expected {expected} skills, found {}",
                    skills_by_name.len()
                ));
            }
        }

        let mut root_seed = format!("catalog:{catalog_sha256_hex}\n");
        for (name, snap) in &skills_by_name {
            root_seed.push_str(&format!("{name}:{}\n", snap.manifest_sha256_hex));
        }
        let root_sha256_hex = hex::encode(sha256_digest(root_seed.as_bytes()));

        Ok(Self {
            catalog_sha256_hex,
            root_sha256_hex,
            skills_by_name,
            alias_to_name,
            resources_by_uri,
            workspace_skill_names,
        })
    }

    /// Generate a deterministic `SkillsLockfile` (`skills-lock.json`) from this verified snapshot.
    pub fn to_lockfile(&self) -> SkillsLockfile {
        let mut skills = BTreeMap::new();
        for (name, snap) in &self.skills_by_name {
            skills.insert(
                name.clone(),
                SkillLockEntry {
                    skill_id: name.clone(),
                    canonical_alias: snap.canonical_alias.clone(),
                    version: snap.version.clone(),
                    artifact_sha256: snap.manifest_sha256_hex.clone(),
                    tool_identity_hash: snap.tool_identity_hash.clone(),
                    lockfile_ref: format!("skills-lock.json#{}@{}", name, snap.version),
                    domain: snap.category.to_ascii_lowercase(),
                    summary: snap.description.clone(),
                    tags: snap.triggers.clone(),
                    effect_profile: snap.effect_profile.clone(),
                    guard_invariants: snap.guard_invariants.clone(),
                },
            );
        }
        SkillsLockfile {
            schema_version: "3.1.0".to_string(),
            catalog_sha256: self.catalog_sha256_hex.clone(),
            snapshot_root_sha256: self.root_sha256_hex.clone(),
            total_skills: skills.len(),
            skills,
        }
    }

    /// Verify this snapshot against a pinned `SkillsLockfile` (FL-P08 Tool Shadowing & Tamper gate).
    pub fn verify_against_lockfile(&self, lockfile: &SkillsLockfile) -> Result<(), RejectReason> {
        if &self.to_lockfile() != lockfile {
            return Err(RejectReason::ToolIdentityMismatch);
        }
        for (name, snap) in &self.skills_by_name {
            let Some(locked) = lockfile.skills.get(name) else {
                return Err(RejectReason::ToolIdentityMismatch);
            };
            if locked.artifact_sha256 != snap.manifest_sha256_hex
                || locked.tool_identity_hash != snap.tool_identity_hash
                || locked.version != snap.version
                || !locked.effect_profile.validated
                || locked.effect_profile.class == EffectClass::Unvalidated
            {
                return Err(RejectReason::ToolIdentityMismatch);
            }
        }
        Ok(())
    }

    /// Total number of unique skills sealed in this snapshot.
    pub fn total_skills(&self) -> usize {
        self.skills_by_name.len()
    }

    /// Resolve a skill by `name`, `canonical_alias`, or `skill://<identifier>`.
    pub fn resolve(&self, identifier: &str) -> Option<&SkillEntrySnapshot> {
        let trimmed = identifier.trim();
        let key = trimmed
            .strip_prefix("skill://")
            .unwrap_or(trimmed)
            .trim_matches('/');
        let canonical = self.alias_to_name.get(key)?;
        self.skills_by_name.get(canonical)
    }

    /// Read a specific resource URI (`skill://<skill>/<path>`) from RAM.
    pub fn read_resource(&self, uri: &str) -> Option<&SkillResourceSnapshot> {
        let trimmed = uri.trim();
        if let Some(res) = self.resources_by_uri.get(trimmed) {
            return Some(res);
        }
        if let Some(rest) = trimmed.strip_prefix("skill://") {
            if !rest.contains('/') {
                return self
                    .resources_by_uri
                    .get(&format!("skill://{rest}/SKILL.md"));
            }
        }
        None
    }

    /// Register all skills in this snapshot into `McpCapabilityBroker` as untrusted discovery
    /// definitions (`register_tool` ONLY — never `authorize_tool`).
    ///
    /// Proves invariant: `ΔSkills ⇏ ΔAuthority`.
    pub fn register_discovery_only(
        &self,
        broker: &mut McpCapabilityBroker,
        server_id: &[u8; 32],
    ) -> Result<usize, RejectReason> {
        let mut count = 0usize;
        for (name, snap) in &self.skills_by_name {
            let mut hash = [0u8; 32];
            if let Ok(decoded) = hex::decode(&snap.manifest_sha256_hex) {
                if decoded.len() == 32 {
                    hash.copy_from_slice(&decoded);
                }
            }
            let tool_def = McpToolDef {
                name: name.clone(),
                code_hash: hash,
                allowed_effects: vec![EffectKind::FsRead],
                target_resource_scope: snap.uri.clone(),
            };
            broker.register_tool(server_id, tool_def)?;
            count += 1;
        }
        Ok(count)
    }
}

/// Flow-policy, anti-replay, and broker state inside GUARD for Architecture v3.1 (FL-P08..FL-P11).
#[derive(Debug, Default, Clone)]
pub struct GuardRuntimeState {
    /// Underlying `babylon60::capability::McpCapabilityBroker` state machine.
    broker: McpCapabilityBroker,
    /// Project whitelist mapping `project_id -> allowed skill_ids` (if empty for a project, all locked skills are visible).
    project_allowlists: HashMap<String, HashSet<String>>,
    /// Explicitly human-approved `(project_id, nonce)` pairs for escalated flows.
    human_approved_nonces: HashSet<(String, String)>,
}

impl GuardRuntimeState {
    fn from_lockfile(lockfile: &SkillsLockfile) -> Self {
        let mut broker = McpCapabilityBroker::new();
        for (skill_id, entry) in &lockfile.skills {
            let mut art_hash = [0u8; 32];
            if let Ok(b) = hex::decode(&entry.artifact_sha256) {
                if b.len() == 32 {
                    art_hash.copy_from_slice(&b);
                }
            }
            let mut id_hash = [0u8; 32];
            if let Ok(b) = hex::decode(&entry.tool_identity_hash) {
                if b.len() == 32 {
                    id_hash.copy_from_slice(&b);
                }
            }
            broker.register_skill_lock_binding(GuardSkillLockBinding {
                skill_id: skill_id.clone(),
                version: entry.version.clone(),
                artifact_sha256: art_hash,
                tool_identity_hash: id_hash,
                effect_kind: entry.effect_profile.class.to_effect_kind(),
                network_egress: entry.effect_profile.network_egress
                    == NetworkEgress::ExternalNetwork,
                validated: entry.effect_profile.validated
                    && entry.effect_profile.class != EffectClass::Unvalidated,
            });
        }
        Self {
            broker,
            project_allowlists: HashMap::new(),
            human_approved_nonces: HashSet::new(),
        }
    }
}

/// MCP Gateway serving `ImmutableSkillsSnapshot` over JSON-RPC 2.0 (SEP-2640 + Architecture v3.1).
#[derive(Debug)]
pub struct SkillsMcpGateway {
    snapshot: ImmutableSkillsSnapshot,
    lockfile: SkillsLockfile,
    use_canonical_names: bool,
    guard_state: Mutex<GuardRuntimeState>,
}

impl Clone for SkillsMcpGateway {
    fn clone(&self) -> Self {
        let cloned_guard = self
            .guard_state
            .lock()
            .map(|g| g.clone())
            .unwrap_or_default();
        Self {
            snapshot: self.snapshot.clone(),
            lockfile: self.lockfile.clone(),
            use_canonical_names: self.use_canonical_names,
            guard_state: Mutex::new(cloned_guard),
        }
    }
}

impl SkillsMcpGateway {
    /// Create a new MCP gateway bound to an immutable snapshot and its derived `skills-lock.json`.
    pub fn new(snapshot: ImmutableSkillsSnapshot, use_canonical_names: bool) -> Self {
        let lockfile = snapshot.to_lockfile();
        let guard = GuardRuntimeState::from_lockfile(&lockfile);
        Self {
            snapshot,
            lockfile,
            use_canonical_names,
            guard_state: Mutex::new(guard),
        }
    }

    /// Create a gateway bound to an explicit `SkillsLockfile`, failing closed if the snapshot diverges (FL-P08).
    pub fn with_lockfile(
        snapshot: ImmutableSkillsSnapshot,
        lockfile: SkillsLockfile,
        use_canonical_names: bool,
    ) -> Result<Self, RejectReason> {
        snapshot.verify_against_lockfile(&lockfile)?;
        let guard = GuardRuntimeState::from_lockfile(&lockfile);
        Ok(Self {
            snapshot,
            lockfile,
            use_canonical_names,
            guard_state: Mutex::new(guard),
        })
    }

    /// Configure a project allowlist for `Visible(s, p)` filtering.
    pub fn set_project_allowlist<I, S>(&self, project_id: &str, allowed_skills: I)
    where
        I: IntoIterator<Item = S>,
        S: Into<String>,
    {
        if let Ok(mut guard) = self.guard_state.lock() {
            guard.project_allowlists.insert(
                project_id.to_string(),
                allowed_skills.into_iter().map(Into::into).collect(),
            );
        }
    }

    /// Record an out-of-band human approval for a specific `(project_id, nonce)` invocation.
    pub fn approve_invocation(&self, project_id: &str, nonce: &str) {
        if let Ok(mut guard) = self.guard_state.lock() {
            guard
                .human_approved_nonces
                .insert((project_id.to_string(), nonce.to_string()));
        }
    }

    /// Access the underlying immutable snapshot.
    pub fn snapshot(&self) -> &ImmutableSkillsSnapshot {
        &self.snapshot
    }

    /// Access the active `SkillsLockfile`.
    pub fn lockfile(&self) -> &SkillsLockfile {
        &self.lockfile
    }

    /// Validate whether a skill is visible to `project_id` (`Visible(s, p)`).
    fn is_skill_visible(&self, project_id: &str, skill_id: &str) -> bool {
        if !self.lockfile.skills.contains_key(skill_id) {
            return false;
        }
        if let Ok(guard) = self.guard_state.lock() {
            if let Some(allowlist) = guard.project_allowlists.get(project_id) {
                return allowlist.contains(skill_id);
            }
        }
        true
    }

    /// Return the 3 stateless orchestration primitives exposed by `tools/list` ($O(1)$ complexity).
    pub fn v31_orchestration_tools() -> Vec<Value> {
        vec![
            json!({
                "name": "skills.discover",
                "description": "Filter the locked skills catalog by project policy and semantic query, returning at most k <= 5 lightweight matches without loading full schemas.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": { "type": "string", "description": "Search query across skill_id, summary, and triggers." },
                        "effect_filter": { "type": "string", "description": "Optional effect class filter (PURE, READ_LOCAL, READ_EXT, STATE_MUTATION, DESTRUCTIVE)." },
                        "project_id": { "type": "string", "description": "Active project identifier for Visible(s, p) policy evaluation." },
                        "k": { "type": "integer", "maximum": 5, "default": 5 }
                    },
                    "required": ["query", "project_id"]
                }
            }),
            json!({
                "name": "skills.inspect",
                "description": "Load on-demand the input JSON schema, symbolic preconditions, and tool_identity_hash for a single skill pinned in skills-lock.json.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill_id": { "type": "string", "description": "Exact skill_id or canonical_alias." },
                        "version": { "type": "string", "description": "Expected version string (e.g. '1.0.0')." },
                        "project_id": { "type": "string", "description": "Active project identifier." }
                    },
                    "required": ["skill_id", "version", "project_id"]
                }
            }),
            json!({
                "name": "skills.propose_effect",
                "description": "Validate a proposal and issue an ActionCapability candidate without execution. Only a trusted executor may verify postconditions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill_id": { "type": "string" },
                        "version": { "type": "string" },
                        "tool_identity_hash": { "type": "string" },
                        "arguments": { "type": "object" },
                        "precondition_snapshot": { "type": "object" },
                        "credential": {
                            "type": "object",
                            "properties": {
                                "audience": { "type": "string" },
                                "project_id": { "type": "string" },
                                "nonce": { "type": "string" },
                                "passthrough_token": { "type": ["string", "null"] }
                            },
                            "required": ["audience", "project_id", "nonce"]
                        },
                        "trace_id": { "type": "string" }
                    },
                    "required": ["skill_id", "version", "tool_identity_hash", "arguments", "precondition_snapshot", "credential"]
                }
            }),
        ]
    }

    /// Execute `skills.discover`: returns at most $k \le 5$ lightweight matches (`Visible(s, p)`).
    pub fn handle_skills_discover(&self, args: & serde_json::Map<String, Value>) -> Value {
        let query = args
            .get("query")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim()
            .to_ascii_lowercase();
        let project_id = args
            .get("project_id")
            .and_then(Value::as_str)
            .unwrap_or("default")
            .trim();
        let effect_filter = args
            .get("effect_filter")
            .and_then(Value::as_str)
            .and_then(EffectClass::parse);
        let requested_k = args.get("k").and_then(Value::as_u64).unwrap_or(5);
        let k = requested_k.clamp(1, 5) as usize;

        let query_tokens: Vec<&str> = query.split_whitespace().filter(|t| !t.is_empty()).collect();
        let mut scored: Vec<(u64, &SkillEntrySnapshot)> = Vec::new();

        for (name, snap) in &self.snapshot.skills_by_name {
            if !self.is_skill_visible(project_id, name) {
                continue;
            }
            if let Some(ef) = effect_filter {
                if snap.effect_profile.class != ef {
                    continue;
                }
            }

            let hay_name = snap.name.to_ascii_lowercase();
            let hay_alias = snap.canonical_alias.to_ascii_lowercase();
            let hay_desc = snap.description.to_ascii_lowercase();
            let hay_cat = snap.category.to_ascii_lowercase();

            let mut score = 0u64;
            if query_tokens.is_empty() {
                score = 1;
            } else {
                for tok in &query_tokens {
                    if hay_name == *tok || hay_alias == *tok {
                        score += 100;
                    } else if hay_name.contains(tok) || hay_alias.contains(tok) {
                        score += 40;
                    }
                    if snap
                        .triggers
                        .iter()
                        .any(|t| t.to_ascii_lowercase().contains(tok))
                    {
                        score += 25;
                    }
                    if hay_desc.contains(tok) || hay_cat.contains(tok) {
                        score += 10;
                    }
                }
            }

            if score > 0 {
                scored.push((score, snap));
            }
        }

        scored.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.name.cmp(&b.1.name)));

        let matches: Vec<Value> = scored
            .into_iter()
            .take(k)
            .map(|(_, snap)| {
                json!({
                    "skill_id": snap.name,
                    "canonical_alias": snap.canonical_alias,
                    "version": snap.version,
                    "summary": snap.description,
                    "effect_profile": {
                        "class": snap.effect_profile.class.as_str()
                    }
                })
            })
            .collect();

        json!({
            "isError": false,
            "project_id": project_id,
            "k_limit": k,
            "matches": matches
        })
    }

    /// Execute `skills.inspect`: verifies `skills-lock.json` and returns schema + preconditions (`Loaded(s)`).
    pub fn handle_skills_inspect(&self, args: &serde_json::Map<String, Value>) -> Value {
        let skill_id = args
            .get("skill_id")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim();
        let version = args
            .get("version")
            .and_then(Value::as_str)
            .unwrap_or("1.0.0")
            .trim();
        let project_id = args
            .get("project_id")
            .and_then(Value::as_str)
            .unwrap_or("default")
            .trim();

        let Some(snap) = self.snapshot.resolve(skill_id) else {
            return json!({
                "isError": true,
                "status": "DENIED",
                "failure_class": "SKILL_NOT_IN_LOCKFILE",
                "error": format!("Skill '{skill_id}' is not registered in skills-lock.json")
            });
        };

        if !self.is_skill_visible(project_id, &snap.name) {
            return json!({
                "isError": true,
                "status": "DENIED",
                "failure_class": "PROJECT_POLICY_DENIED",
                "error": format!("Skill '{}' is not visible in project '{project_id}'", snap.name)
            });
        }

        let Some(locked) = self.lockfile.skills.get(&snap.name) else {
            return json!({
                "isError": true,
                "status": "DENIED",
                "failure_class": "SKILL_NOT_IN_LOCKFILE",
                "error": format!("Skill '{}' missing from skills-lock.json", snap.name)
            });
        };

        if locked.version != version
            || locked.tool_identity_hash != snap.tool_identity_hash
            || locked.artifact_sha256 != snap.manifest_sha256_hex
        {
            return json!({
                "isError": true,
                "status": "DENIED",
                "failure_class": "TOOL_IDENTITY_MISMATCH",
                "error": "Skill version or tool_identity_hash does not match skills-lock.json"
            });
        }

        json!({
            "isError": false,
            "skill_id": snap.name,
            "canonical_alias": snap.canonical_alias,
            "version": snap.version,
            "tool_identity_hash": snap.tool_identity_hash,
            "lockfile_ref": locked.lockfile_ref,
            "effect_profile": snap.effect_profile,
            "input_json_schema": snap.input_json_schema(),
            "preconditions": snap.guard_invariants.preconditions,
            "postconditions": snap.guard_invariants.postconditions
        })
    }

    /// Execute `skills.propose_effect`: validates FL-P08, FL-P09, FL-P10, and FL-P11 via `McpCapabilityBroker` without executing side effects.
    pub fn handle_skills_propose_effect(&self, args: &serde_json::Map<String, Value>) -> Value {
        if args.contains_key("simulated_execution_result") {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "UNTRUSTED_EXECUTION_EVIDENCE",
                "error": "FL-P11: Client-supplied execution evidence cannot verify a proposal"
            });
        }
        let skill_id = args
            .get("skill_id")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim();
        let version = args
            .get("version")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim();
        let provided_identity_hash = args
            .get("tool_identity_hash")
            .and_then(Value::as_str)
            .map(str::trim);

        // --- 1. FL-P10: Audience-bound credential, explicit project_id, nonce, expiration & zero passthrough ---
        let Some(cred_obj) = args.get("credential").and_then(Value::as_object) else {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "MISSING_AUDIENCE_CREDENTIAL",
                "error": "FL-P10: Missing audience-bound credential"
            });
        };

        let passthrough_token = cred_obj
            .get("passthrough_token")
            .and_then(|v| {
                if v.is_null() {
                    None
                } else {
                    Some(v.as_str().unwrap_or("non-string").to_string())
                }
            })
            .filter(|s| !s.trim().is_empty());

        if passthrough_token.is_some() {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOKEN_PASSTHROUGH_FORBIDDEN",
                "error": "FL-P10: Downstream token passthrough is strictly forbidden"
            });
        }

        let audience = cred_obj
            .get("audience")
            .and_then(Value::as_str)
            .unwrap_or("");
        let project_id = cred_obj
            .get("project_id")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim();
        let nonce = cred_obj
            .get("nonce")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim();
        let current_epoch = cred_obj
            .get("current_epoch")
            .or_else(|| args.get("current_epoch"))
            .and_then(Value::as_u64)
            .unwrap_or(1);
        let expires_at_epoch = cred_obj
            .get("expires_at_epoch")
            .or_else(|| args.get("expires_at_epoch"))
            .and_then(Value::as_u64)
            .unwrap_or(current_epoch.saturating_add(60));

        if audience != GATEWAY_EXPECTED_AUDIENCE || project_id.is_empty() || nonce.is_empty() {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "INVALID_AUDIENCE_OR_NONCE",
                "error": "FL-P10: Credential must bind exact audience, non-empty project_id, and unique nonce"
            });
        }

        if expires_at_epoch == 0 || current_epoch > expires_at_epoch {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "CREDENTIAL_EXPIRED",
                "error": "FL-P10: Audience-bound credential or nonce lease has expired"
            });
        }

        // --- 2. FL-P08: Lockfile, Tool Shadowing & Classification validation ---
        let Some(snap) = self.snapshot.resolve(skill_id) else {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOOL_SHADOWING_OR_UNREGISTERED",
                "error": format!("FL-P08: Skill '{skill_id}' is not registered in skills-lock.json")
            });
        };

        let Some(locked) = self.lockfile.skills.get(&snap.name) else {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOOL_SHADOWING_OR_UNREGISTERED",
                "error": format!("FL-P08: Skill '{}' is absent from skills-lock.json", snap.name)
            });
        };

        if !snap.effect_profile.validated
            || snap.effect_profile.class == EffectClass::Unvalidated
            || !locked.effect_profile.validated
            || locked.effect_profile.class == EffectClass::Unvalidated
        {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "UNVALIDATED_EFFECT_CLASSIFICATION",
                "error": format!("FASE 1 / GUARD: Skill '{}' has unvalidated effect classification => DENY", snap.name)
            });
        }

        if locked.version != version
            || locked.tool_identity_hash != snap.tool_identity_hash
            || provided_identity_hash != Some(locked.tool_identity_hash.as_str())
        {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOOL_IDENTITY_MISMATCH",
                "error": "FL-P08: tool_identity_hash or version mismatch against skills-lock.json"
            });
        }

        if !self.is_skill_visible(project_id, &snap.name) {
            return json!({
                "isError": true,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "PROJECT_POLICY_DENIED",
                "error": format!("Skill '{}' is not allowed for project '{project_id}'", snap.name)
            });
        }

        // --- 3. Precondition evaluation (`precondition_snapshot` vs `arguments`) ---
        let call_args = args
            .get("arguments")
            .and_then(Value::as_object)
            .cloned()
            .unwrap_or_default();
        let pre_snap = args
            .get("precondition_snapshot")
            .and_then(Value::as_object)
            .cloned()
            .unwrap_or_default();

        let target_path = call_args
            .get("target_path")
            .and_then(Value::as_str)
            .unwrap_or("");
        let allowed_roots: Vec<String> = pre_snap
            .get("allowed_roots")
            .and_then(Value::as_array)
            .map(|arr| {
                arr.iter()
                    .filter_map(Value::as_str)
                    .map(String::from)
                    .collect()
            })
            .unwrap_or_else(|| {
                vec![
                    "workspace://".to_string(),
                    "/workspace".to_string(),
                    ".".to_string(),
                ]
            });

        let parse_hex32 = |s: &str| -> Option<[u8; 32]> {
            let b = hex::decode(s.trim()).ok()?;
            if b.len() == 32 {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(&b);
                Some(arr)
            } else {
                None
            }
        };

        let expected_pre_str = call_args
            .get("expected_pre_hash")
            .and_then(Value::as_str)
            .unwrap_or("");
        let observed_pre_str = pre_snap
            .get("observed_pre_hash")
            .or_else(|| pre_snap.get("file_sha256"))
            .and_then(Value::as_str)
            .unwrap_or("");

        let expected_pre_hash = if expected_pre_str.is_empty() {
            None
        } else {
            Some(
                parse_hex32(expected_pre_str)
                    .unwrap_or_else(|| sha256_digest(expected_pre_str.as_bytes())),
            )
        };
        let observed_pre_hash = if observed_pre_str.is_empty() {
            None
        } else {
            Some(
                parse_hex32(observed_pre_str)
                    .unwrap_or_else(|| sha256_digest(observed_pre_str.as_bytes())),
            )
        };

        let arg_bytes = serde_json::to_vec(&call_args).unwrap_or_default();
        let pre_bytes = serde_json::to_vec(&pre_snap).unwrap_or_default();
        let args_digest_bytes = sha256_digest(&arg_bytes);
        let pre_digest_bytes = sha256_digest(&pre_bytes);
        let argument_digest = hex::encode(args_digest_bytes);
        let precondition_snapshot_hash = hex::encode(pre_digest_bytes);

        let trace_id = args
            .get("trace_id")
            .and_then(Value::as_str)
            .unwrap_or(project_id)
            .to_string();

        let network_destination = call_args
            .get("network_destination")
            .or_else(|| call_args.get("endpoint"))
            .and_then(Value::as_str)
            .map(String::from);

        let tool_id_bytes = parse_hex32(&snap.tool_identity_hash)
            .unwrap_or_else(|| sha256_digest(snap.tool_identity_hash.as_bytes()));
        let artifact_bytes = parse_hex32(&snap.manifest_sha256_hex)
            .unwrap_or_else(|| sha256_digest(snap.manifest_sha256_hex.as_bytes()));

        // --- 4. Delegate GUARD evaluation & compositional flow check to `McpCapabilityBroker` ---
        let mut guard = self.guard_state.lock().expect("guard mutex");
        let nonce_key = (project_id.to_string(), nonce.to_string());
        let is_human_approved = guard.human_approved_nonces.contains(&nonce_key);

        let proposal_input = GuardProposalInput {
            skill_id: snap.name.clone(),
            version: snap.version.clone(),
            tool_identity_hash: tool_id_bytes,
            artifact_sha256: artifact_bytes,
            audience: audience.to_string(),
            expected_audience: GATEWAY_EXPECTED_AUDIENCE.to_string(),
            project_id: project_id.to_string(),
            trace_id: trace_id.clone(),
            nonce: nonce.to_string(),
            passthrough_token: None,
            resource_uri: target_path.to_string(),
            allowed_roots,
            args_digest: args_digest_bytes,
            precondition_snapshot_hash: pre_digest_bytes,
            expected_pre_hash,
            observed_pre_hash,
            network_destination,
            current_epoch,
            expires_at_epoch,
            human_approved: is_human_approved,
        };

        let grant = match guard.broker.propose_skill_effect(proposal_input) {
            Ok(g) => g,
            Err(RejectReason::PreconditionMismatch) => {
                let err_msg = if matches!(
                    snap.effect_profile.class,
                    EffectClass::StateMutation | EffectClass::Destructive
                ) && (expected_pre_str.is_empty()
                    || expected_pre_str != observed_pre_str)
                {
                    "Precondition failed: sha256(file(target_path)) == args.expected_pre_hash"
                } else {
                    "Precondition failed: target_path WITHIN project.allowed_roots"
                };
                return json!({
                    "isError": true,
                    "status": "DENIED",
                    "decision": "DENIED",
                    "failure_class": "PRECONDITION_MISMATCH",
                    "error": err_msg
                });
            }
            Err(RejectReason::NonceAlreadyConsumed(_)) => {
                return json!({
                    "isError": true,
                    "status": "DENIED",
                    "decision": "DENIED",
                    "failure_class": "NONCE_REPLAY_DETECTED",
                    "error": "FL-P10: Nonce has already been consumed"
                });
            }
            Err(RejectReason::StaleCapability) => {
                return json!({
                    "isError": true,
                    "status": "DENIED",
                    "decision": "DENIED",
                    "failure_class": "CREDENTIAL_EXPIRED",
                    "error": "FL-P10: Capability or nonce expired"
                });
            }
            Err(RejectReason::PolicyDenied(ref code))
                if code == "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK" =>
            {
                return json!({
                    "isError": false,
                    "status": "PENDING_APPROVAL",
                    "decision": "DENIED",
                    "failure_class": "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK",
                    "error": "FL-P09: Chaining READ_LOCAL followed by EXTERNAL_NETWORK in the same trace requires explicit human approval"
                });
            }
            Err(other) => {
                return json!({
                    "isError": true,
                    "status": "DENIED",
                    "decision": "DENIED",
                    "failure_class": "POLICY_DENIED",
                    "error": format!("GUARD rejected proposal: {other:?}")
                });
            }
        };

        let capability = ActionCapability {
            capability_id: hex::encode(grant.capability_id),
            skill_id: snap.name.clone(),
            version: snap.version.clone(),
            tool_identity_hash: snap.tool_identity_hash.clone(),
            project_id: project_id.to_string(),
            trace_id: trace_id.clone(),
            nonce: nonce.to_string(),
            issued_epoch: grant.issued_epoch,
            expires_at_epoch: grant.expires_at_epoch,
            target_resource: target_path.to_string(),
            argument_digest,
            precondition_snapshot_hash,
            effect_class: snap.effect_profile.class,
        };

        json!({
            "isError": false,
            "status": "AUTHORIZED",
            "decision": "ALLOW",
            "broker_state": "Authorized",
            "effects_executed": 0,
            "action_capability": capability,
            "evidence": {
                "verification_scope": "proposal_only",
                "lockfile_ref": locked.lockfile_ref,
                "postconditions_checked": []
            }
        })
    }

    /// Execute a side effect exclusively when presented with a valid `ActionCapability` issued by `propose_effect`,
    /// followed by independent physical postcondition verification (FASE 3 & FL-P11).
    #[allow(clippy::too_many_arguments)]
    pub fn execute_with_capability<FExec, FVerify>(
        &self,
        capability: &ActionCapability,
        audience: &str,
        current_epoch: u64,
        execute_fn: FExec,
        independent_verifier_fn: FVerify,
    ) -> Result<EffectState, RejectReason>
    where
        FExec: FnOnce() -> Result<[u8; 32], FailureReason>,
        FVerify: FnOnce() -> Result<[u8; 32], FailureReason>,
    {
        let parse_hex32 = |s: &str| -> Result<[u8; 32], RejectReason> {
            let b = hex::decode(s.trim()).map_err(|_| RejectReason::StaleCapability)?;
            if b.len() == 32 {
                let mut arr = [0u8; 32];
                arr.copy_from_slice(&b);
                Ok(arr)
            } else {
                Err(RejectReason::StaleCapability)
            }
        };

        let cap_id = parse_hex32(&capability.capability_id)?;
        let args_digest = parse_hex32(&capability.argument_digest)?;

        let mut guard = self
            .guard_state
            .lock()
            .map_err(|_| RejectReason::PolicyDenied("GUARD_MUTEX_POISONED".into()))?;
        let (_, state) = guard.broker.execute_and_verify_skill_effect(
            &cap_id,
            audience,
            &capability.project_id,
            &capability.target_resource,
            &args_digest,
            current_epoch,
            execute_fn,
            independent_verifier_fn,
        )?;
        Ok(state)
    }

    /// Process a single JSON-RPC 2.0 request and return a JSON-RPC 2.0 response.
    pub fn process_request(&self, request: &Value) -> Option<Value> {
        let method = request.get("method").and_then(Value::as_str).unwrap_or("");
        let id = request.get("id").cloned();
        let params = request
            .get("params")
            .and_then(Value::as_object)
            .cloned()
            .unwrap_or_default();

        let result = match method {
            "initialize" => json!({
                "protocolVersion": "2026-07-28",
                "capabilities": {
                    "tools": { "listChanged": false },
                    "resources": { "subscribe": false, "listChanged": false },
                    "prompts": { "listChanged": false },
                    "skills": { "version": "SEP-2640", "readOnly": true, "architecture": "v3.1" }
                },
                "serverInfo": {
                    "name": "babylon-skills-mcp",
                    "version": env!("CARGO_PKG_VERSION"),
                    "snapshotRoot": format!("sha256:{}", self.snapshot.root_sha256_hex)
                }
            }),
            "initialized" | "notifications/initialized" | "ping" => json!({}),
            "tools/list" => json!({
                "tools": Self::v31_orchestration_tools()
            }),
            "tools/call" => {
                let tool_name = params.get("name").and_then(Value::as_str).unwrap_or("");
                let tool_args = params
                    .get("arguments")
                    .and_then(Value::as_object)
                    .cloned()
                    .unwrap_or_default();
                match tool_name {
                    "skills.discover" => self.handle_skills_discover(&tool_args),
                    "skills.inspect" => self.handle_skills_inspect(&tool_args),
                    "skills.propose_effect" => self.handle_skills_propose_effect(&tool_args),
                    other => json!({
                        "isError": true,
                        "status": "DENIED",
                        "error": format!("Unknown or unexposed gateway tool: {other}")
                    }),
                }
            }
            "skills.discover" => self.handle_skills_discover(&params),
            "skills.inspect" => self.handle_skills_inspect(&params),
            "skills.propose_effect" => self.handle_skills_propose_effect(&params),
            "skills/list" => {
                let scope = params
                    .get("scope")
                    .and_then(Value::as_str)
                    .unwrap_or("all")
                    .to_ascii_lowercase();
                let mut skills = Vec::new();
                for snap in self.snapshot.skills_by_name.values() {
                    if scope != "all" && snap.scope.to_ascii_lowercase() != scope {
                        continue;
                    }
                    let primary = if self.use_canonical_names {
                        &snap.canonical_alias
                    } else {
                        &snap.name
                    };
                    let res_list: Vec<Value> = snap
                        .resources
                        .iter()
                        .map(|r| {
                            json!({
                                "path": r.relative_path,
                                "uri": r.uri,
                                "mimeType": r.mime_type,
                                "size": r.size_bytes,
                                "digest": format!("sha256:{}", r.sha256_hex)
                            })
                        })
                        .collect();
                    skills.push(json!({
                        "name": primary,
                        "canonical_alias": snap.canonical_alias,
                        "legacy_name": snap.name,
                        "version": snap.version,
                        "uri": snap.uri,
                        "description": snap.description,
                        "role": snap.role,
                        "scope": snap.scope,
                        "tier": snap.tier,
                        "manifest_sha256": format!("sha256:{}", snap.manifest_sha256_hex),
                        "tool_identity_hash": snap.tool_identity_hash,
                        "effect_profile": snap.effect_profile,
                        "resources": res_list
                    }));
                }
                json!({
                    "snapshot_root": format!("sha256:{}", self.snapshot.root_sha256_hex),
                    "total": skills.len(),
                    "skills": skills
                })
            }
            "skills/get" => {
                let id_str = params
                    .get("uri")
                    .or_else(|| params.get("name"))
                    .and_then(Value::as_str)
                    .unwrap_or("");
                if let Some(snap) = self.snapshot.resolve(id_str) {
                    let res_list: Vec<Value> = snap
                        .resources
                        .iter()
                        .map(|r| {
                            json!({
                                "path": r.relative_path,
                                "uri": r.uri,
                                "mimeType": r.mime_type,
                                "size": r.size_bytes,
                                "digest": format!("sha256:{}", r.sha256_hex)
                            })
                        })
                        .collect();
                    json!({
                        "isError": false,
                        "skill": {
                            "name": snap.name,
                            "canonical_alias": snap.canonical_alias,
                            "version": snap.version,
                            "display_name": snap.display_name,
                            "uri": snap.uri,
                            "description": snap.description,
                            "role": snap.role,
                            "scope": snap.scope,
                            "tier": snap.tier,
                            "category": snap.category,
                            "manifest_sha256": format!("sha256:{}", snap.manifest_sha256_hex),
                            "tool_identity_hash": snap.tool_identity_hash,
                            "effect_profile": snap.effect_profile,
                            "guard_invariants": snap.guard_invariants,
                            "resources": res_list
                        }
                    })
                } else {
                    json!({
                        "isError": true,
                        "skill": Value::Null,
                        "error": format!("Unknown skill: {id_str}")
                    })
                }
            }
            "resources/read" => {
                let uri = params.get("uri").and_then(Value::as_str).unwrap_or("");
                if let Some(res) = self.snapshot.read_resource(uri) {
                    json!({
                        "contents": [{
                            "uri": uri,
                            "mimeType": res.mime_type,
                            "text": res.text,
                            "_meta": {
                                "digest": format!("sha256:{}", res.sha256_hex),
                                "size": res.size_bytes
                            }
                        }]
                    })
                } else {
                    json!({
                        "contents": [{
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": format!("Unknown resource: {uri}")
                        }],
                        "isError": true
                    })
                }
            }
            "prompts/list" => {
                let mut prompts = Vec::new();
                for sname in &self.snapshot.workspace_skill_names {
                    if let Some(snap) = self.snapshot.skills_by_name.get(sname) {
                        let primary = if self.use_canonical_names {
                            &snap.canonical_alias
                        } else {
                            &snap.name
                        };
                        prompts.push(json!({
                            "name": primary,
                            "canonical_alias": snap.canonical_alias,
                            "legacy_name": snap.name,
                            "description": format!("[{}] {}", snap.canonical_alias, snap.description),
                            "arguments": [{
                                "name": "task",
                                "description": "Optional task or target context to execute with this CORTEX skill.",
                                "required": false
                            }]
                        }));
                    }
                }
                json!({ "prompts": prompts })
            }
            "prompts/get" => {
                let target = params.get("name").and_then(Value::as_str).unwrap_or("");
                let task_arg = params
                    .get("arguments")
                    .and_then(Value::as_object)
                    .and_then(|a| a.get("task"))
                    .and_then(Value::as_str)
                    .unwrap_or("")
                    .trim();
                if let Some(snap) = self.snapshot.resolve(target) {
                    let mut body = snap.skill_md_text.clone().unwrap_or_else(|| {
                        format!(
                            "# CORTEX Skill: {}\n- Canonical Alias: `{}` (ID: `{}`)\n- Role Triad: `{}` | Tier: `{}` | Scope: `{}`\n- Description: {}\n",
                            snap.display_name, snap.canonical_alias, snap.name, snap.role, snap.tier, snap.scope, snap.description
                        )
                    });
                    if !task_arg.is_empty() {
                        body.push_str(&format!("\n\n## Active Operator Task\n{task_arg}\n"));
                    }
                    json!({
                        "description": snap.description,
                        "messages": [{
                            "role": "user",
                            "content": { "type": "text", "text": body }
                        }]
                    })
                } else {
                    json!({
                        "description": format!("Unknown skill prompt: {target}"),
                        "messages": [],
                        "isError": true
                    })
                }
            }
            _ => {
                let id_val = id?;
                return Some(json!({
                    "jsonrpc": "2.0",
                    "id": id_val,
                    "error": {
                        "code": -32601,
                        "message": format!("Method not found: {method}")
                    }
                }));
            }
        };

        let id_val = id?;
        Some(json!({
            "jsonrpc": "2.0",
            "id": id_val,
            "result": result
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn frontmatter_folds_plain_description_continuations() {
        let fields = parse_simple_frontmatter(
            "---\nname: sample\ndescription: Primera línea\n  y segunda línea\n  con detalle: verificable.\nrole: auditor\n---\n# Body\n",
        );
        assert_eq!(fields["name"], "sample");
        assert_eq!(
            fields["description"],
            "Primera línea y segunda línea con detalle: verificable."
        );
        assert_eq!(fields["role"], "auditor");
    }

    #[test]
    fn frontmatter_folds_quoted_description_before_removing_outer_quotes() {
        let fields = parse_simple_frontmatter(
            "---\nname: sample\ndescription: 'Enruta módulos: primero\n  y después la frase \"--- sigue\"\n  sin perder el cierre.'\nrole: auditor\n---\n",
        );
        assert_eq!(
            fields["description"],
            "Enruta módulos: primero y después la frase \"--- sigue\" sin perder el cierre."
        );
        assert_eq!(fields["role"], "auditor");
    }

    #[test]
    fn frontmatter_keeps_nested_fields_out_of_top_level_scalars() {
        let fields = parse_simple_frontmatter(
            "---\nname: sample\ndescription: 'Una línea: completa.'\nrole: auditor\nallowed_roles:\n  - ejecutor\ndirectives:\n  name: nested-name\n  role: ejecutor\n  handoff:\n    phase: verification\n---\nrole: body-role\n",
        );
        assert_eq!(fields["name"], "sample");
        assert_eq!(fields["description"], "Una línea: completa.");
        assert_eq!(fields["role"], "auditor");
        assert!(!fields.contains_key("phase"));
        assert!(!fields.contains_key("handoff"));
    }

    #[test]
    fn snapshot_enforces_toctou_immunity_and_no_authority_escalation() {
        let tmp = TempDir::new().expect("tempdir");
        let skills_dir = tmp.path().join("skills");
        let popeye_dir = skills_dir.join("popeye-strength");
        std::fs::create_dir_all(&popeye_dir).expect("mkdir");

        let skill_md_path = popeye_dir.join("SKILL.md");
        std::fs::write(
            &skill_md_path,
            "---\nname: popeye-strength\ncanonical_alias: spinach-transducer\ndescription: 'Fuerza agéntica gobernada.'\nrole: ejecutor\n---\n# Popeye Strength\nOriginal verified instructions.\n",
        )
        .expect("write SKILL.md");

        let contract_path = popeye_dir.join("contract.yaml");
        std::fs::write(&contract_path, "schema_version: '1'\nskill: popeye-strength\n")
            .expect("write contract.yaml");

        let catalog_path = tmp.path().join("skills.json");
        std::fs::write(
            &catalog_path,
            serde_json::to_vec(&json!({
                "version": "26.400",
                "total_skills": 1,
                "entries": [{
                    "name": "popeye-strength",
                    "canonical_alias": "spinach-transducer",
                    "display_name": "Popeye Strength",
                    "description": "Fuerza agéntica gobernada.",
                    "role": "ejecutor",
                    "scope": "workspace",
                    "tier": 20000,
                    "category": "Kernel",
                    "triggers": ["popeye", "espinacas"]
                }]
            }))
            .unwrap(),
        )
        .expect("write catalog");

        // 1. Cardinality mismatch must fail closed
        let mismatch = ImmutableSkillsSnapshot::load(
            Some(&catalog_path),
            Some(&skills_dir),
            Some(107),
        );
        assert!(mismatch.is_err());

        // 2. Load valid snapshot (expected = 1)
        let snapshot = ImmutableSkillsSnapshot::load(
            Some(&catalog_path),
            Some(&skills_dir),
            Some(1),
        )
        .expect("snapshot load");
        assert_eq!(snapshot.total_skills(), 1);

        // 3. Mutate SKILL.md and delete contract.yaml on disk AFTER snapshot load
        std::fs::write(&skill_md_path, "# COMPROMISED ON DISK\n").expect("tamper");
        std::fs::remove_file(&contract_path).expect("unlink contract");

        let gateway = SkillsMcpGateway::new(snapshot.clone(), false);

        // 4. Verify skills/list and resources/read still serve the frozen RAM snapshot
        let list_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "skills/list",
                "params": {}
            }))
            .expect("response");
        assert_eq!(list_resp["result"]["total"], 1);
        assert_eq!(
            list_resp["result"]["skills"][0]["resources"]
                .as_array()
                .unwrap()
                .len(),
            2
        );

        let read_md = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": { "uri": "skill://popeye-strength/SKILL.md" }
            }))
            .expect("response");
        let text = read_md["result"]["contents"][0]["text"]
            .as_str()
            .unwrap();
        assert!(text.contains("Original verified instructions."));
        assert!(!text.contains("COMPROMISED ON DISK"));

        let read_contract = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": { "uri": "skill://popeye-strength/contract.yaml" }
            }))
            .expect("response");
        assert!(read_contract["result"]["contents"][0]["text"]
            .as_str()
            .unwrap()
            .contains("schema_version: '1'"));

        // 5. Verify ΔSkills ⇏ ΔAuthority on McpCapabilityBroker
        let mut broker = McpCapabilityBroker::new();
        let server_id = [0x55u8; 32];
        broker.register_server(server_id, true, 1);
        let registered = snapshot
            .register_discovery_only(&mut broker, &server_id)
            .expect("register_discovery_only");
        assert_eq!(registered, 1);

        let snap_entry = snapshot.resolve("popeye-strength").unwrap();
        let mut code_hash = [0u8; 32];
        code_hash.copy_from_slice(&hex::decode(&snap_entry.manifest_sha256_hex).unwrap());

        // Attempting to request a capability without explicit control-plane `authorize_tool` MUST fail closed
        let cap_attempt = broker.request_capability(
            &server_id,
            "popeye-strength",
            &code_hash,
            b"{}",
            "skill://popeye-strength/SKILL.md",
            EffectKind::FsRead,
            5,
        );
        assert!(matches!(cap_attempt, Err(RejectReason::PolicyDenied(_))));
    }

    #[test]
    fn loads_real_babylon60_catalog_and_workspace_skills() {
        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap();
        let catalog_path = repo_root.join("docs/skills.json");
        let skills_dir = repo_root.join(".agents/skills");

        let snapshot = ImmutableSkillsSnapshot::load(
            Some(&catalog_path),
            Some(&skills_dir),
            Some(131),
        )
        .expect("real catalog snapshot load");

        assert_eq!(snapshot.total_skills(), 131);
        assert_eq!(snapshot.workspace_skill_names.len(), 26);

        let root_lock: SkillsLockfile = serde_json::from_slice(
            &std::fs::read(repo_root.join("skills-lock.json")).expect("read skills-lock.json"),
        )
        .expect("parse skills-lock.json");
        let docs_lock: SkillsLockfile = serde_json::from_slice(
            &std::fs::read(repo_root.join("docs/skills-lock.json"))
                .expect("read docs/skills-lock.json"),
        )
        .expect("parse docs/skills-lock.json");
        assert_eq!(root_lock, docs_lock);
        assert_eq!(root_lock, snapshot.to_lockfile());
        snapshot
            .verify_against_lockfile(&root_lock)
            .expect("verify on-disk skills-lock.json");

        let gateway = SkillsMcpGateway::new(snapshot, false);
        let get_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 10,
                "method": "skills/get",
                "params": { "uri": "skill://epistemic-simplifier" }
            }))
            .expect("skills/get response");
        assert_eq!(get_resp["result"]["isError"], false);
        assert_eq!(get_resp["result"]["skill"]["name"], "wait-what");

        let read_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 11,
                "method": "resources/read",
                "params": { "uri": "skill://wait-what/SKILL.md" }
            }))
            .expect("resources/read response");
        assert!(read_resp["result"]["contents"][0]["text"]
            .as_str()
            .unwrap()
            .contains("wait-what"));
    }

    #[test]
    fn v31_gateway_exposes_only_3_meta_primitives_and_checks_fl_p08_to_fl_p11() {
        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap();
        let catalog_path = repo_root.join("docs/skills.json");
        let skills_dir = repo_root.join(".agents/skills");

        let snapshot = ImmutableSkillsSnapshot::load(
            Some(&catalog_path),
            Some(&skills_dir),
            Some(131),
        )
        .expect("snapshot load");
        let lockfile = snapshot.to_lockfile();
        let gateway = SkillsMcpGateway::with_lockfile(snapshot.clone(), lockfile.clone(), false)
            .expect("gateway with lockfile");

        // 0. Verify O(1) MCP surface: tools/list exposes ONLY the 3 orchestration meta-primitives
        let tools_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 100,
                "method": "tools/list",
                "params": {}
            }))
            .expect("tools/list");
        let tools_arr = tools_resp["result"]["tools"].as_array().unwrap();
        assert_eq!(tools_arr.len(), 3);
        let tool_names: Vec<&str> = tools_arr
            .iter()
            .map(|t| t["name"].as_str().unwrap())
            .collect();
        assert_eq!(
            tool_names,
            vec!["skills.discover", "skills.inspect", "skills.propose_effect"]
        );

        // 1. skills.discover returns k <= 5 lightweight matches
        let disc_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 101,
                "method": "tools/call",
                "params": {
                    "name": "skills.discover",
                    "arguments": {
                        "query": "kernel seqlock audit",
                        "project_id": "babylon60",
                        "k": 99
                    }
                }
            }))
            .expect("discover");
        let matches = disc_resp["result"]["matches"].as_array().unwrap();
        assert!(matches.len() <= 5 && !matches.is_empty());

        // 2. FL-P08: Tool Shadowing / Skill 108 injection rejected if absent or mismatched in skills-lock.json
        let shadow_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 108,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "skill-108-shadow-injected",
                        "version": "1.0.0",
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p08-a"
                        }
                    }
                }
            }))
            .expect("FL-P08 unindexed");
        assert_eq!(shadow_resp["result"]["status"], "DENIED");
        assert_eq!(
            shadow_resp["result"]["failure_class"],
            "TOOL_SHADOWING_OR_UNREGISTERED"
        );

        // Also test tampered tool_identity_hash on an existing skill (collision / shadowing attempt)
        let collision_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 109,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": "0000000000000000000000000000000000000000000000000000000000000000",
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p08-b"
                        }
                    }
                }
            }))
            .expect("FL-P08 hash collision");
        assert_eq!(collision_resp["result"]["status"], "DENIED");
        assert_eq!(
            collision_resp["result"]["failure_class"],
            "TOOL_IDENTITY_MISMATCH"
        );

        // 3. FL-P09: Composition Escalation (READ_LOCAL followed by EXTERNAL_NETWORK in the same trace)
        let read_local_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 110,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "trace_id": "trace-fl-p09",
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p09-step1"
                        }
                    }
                }
            }))
            .expect("FL-P09 step 1 READ_LOCAL");
        assert_eq!(read_local_resp["result"]["status"], "AUTHORIZED");

        let net_ext_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 111,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "c5-socint-extraction-suite",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("c5-socint-extraction-suite").unwrap().tool_identity_hash,
                        "trace_id": "trace-fl-p09",
                        "arguments": { "target_path": "workspace://docs/README.md" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p09-step2"
                        }
                    }
                }
            }))
            .expect("FL-P09 step 2 EXTERNAL_NETWORK");
        assert_eq!(net_ext_resp["result"]["status"], "PENDING_APPROVAL");
        assert_eq!(
            net_ext_resp["result"]["failure_class"],
            "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK"
        );

        // 4. FL-P10: Handle reuse (nonce replay) and Token Passthrough rejected immediately
        let passthrough_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 112,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p10-pass",
                            "passthrough_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                        }
                    }
                }
            }))
            .expect("FL-P10 passthrough");
        assert_eq!(passthrough_resp["result"]["status"], "DENIED");
        assert_eq!(
            passthrough_resp["result"]["failure_class"],
            "TOKEN_PASSTHROUGH_FORBIDDEN"
        );

        // Replay nonce from step 1 (`nonce-fl-p09-step1`)
        let replay_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 113,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p09-step1"
                        }
                    }
                }
            }))
            .expect("FL-P10 nonce replay");
        assert_eq!(replay_resp["result"]["status"], "DENIED");
        assert_eq!(
            replay_resp["result"]["failure_class"],
            "NONCE_REPLAY_DETECTED"
        );

        // 5. FL-P11: False positive from downstream MCP tool (returns 200 OK without mutating state)
        let pre_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
        let false_positive_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 114,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "c5-neural-face-swap-cuadrilla",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("c5-neural-face-swap-cuadrilla").unwrap().tool_identity_hash,
                        "trace_id": "trace-fl-p11",
                        "arguments": {
                            "target_path": "workspace://src/lib.rs",
                            "expected_pre_hash": pre_hash
                        },
                        "precondition_snapshot": {
                            "allowed_roots": ["workspace://"],
                            "observed_pre_hash": pre_hash
                        },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "nonce-fl-p11-fp"
                        },
                        "simulated_execution_result": {
                            "http_status": 200,
                            "observed_post_hash": pre_hash,
                            "actual_file_sha256": pre_hash
                        }
                    }
                }
            }))
            .expect("FL-P11 false positive");
        assert_eq!(false_positive_resp["result"]["status"], "DENIED");
        assert_eq!(false_positive_resp["result"]["decision"], "DENIED");
        assert_eq!(
            false_positive_resp["result"]["failure_class"],
            "UNTRUSTED_EXECUTION_EVIDENCE"
        );
    }

    #[test]
    fn fl_p08_tool_shadowing_and_unvalidated_classification_denied() {
        let tmp = TempDir::new().expect("tempdir");
        let fixture = tmp.path().join("protected.txt");
        std::fs::write(&fixture, b"IMMUTABLE_P08").expect("write fixture");
        let pre_hash = hex::encode(sha256_digest(b"IMMUTABLE_P08"));

        let catalog_path = tmp.path().join("skills.json");
        std::fs::write(
            &catalog_path,
            serde_json::to_vec(&json!({
                "version": "26.400",
                "total_skills": 2,
                "entries": [
                    {
                        "name": "thermo-audit",
                        "canonical_alias": "thermo-audit",
                        "display_name": "Thermo Audit",
                        "description": "Contains http and api words that MUST NOT infer network permissions.",
                        "role": "auditor",
                        "scope": "workspace",
                        "tier": 20000,
                        "category": "Diagnostics",
                        "triggers": ["audit"]
                    },
                    {
                        "name": "rogue-unvalidated-skill",
                        "canonical_alias": "rogue-unvalidated-skill",
                        "display_name": "Rogue Unvalidated",
                        "description": "Unvalidated role must fail closed.",
                        "role": "untrusted_shadow_role",
                        "scope": "workspace",
                        "tier": 20000,
                        "category": "UnknownCategory",
                        "triggers": ["rogue"]
                    }
                ]
            }))
            .unwrap(),
        )
        .expect("write catalog");

        let snapshot = ImmutableSkillsSnapshot::load(Some(&catalog_path), None, Some(2))
            .expect("load snapshot");

        // Verify description did NOT infer network permissions for `thermo-audit`
        let thermo = snapshot.resolve("thermo-audit").unwrap();
        assert_eq!(thermo.effect_profile.class, EffectClass::ReadLocal);
        assert_eq!(thermo.effect_profile.network_egress, NetworkEgress::None);

        // Verify unvalidated classification produced EffectClass::Unvalidated (validated == false)
        let rogue = snapshot.resolve("rogue-unvalidated-skill").unwrap();
        assert!(!rogue.effect_profile.validated);
        assert_eq!(rogue.effect_profile.class, EffectClass::Unvalidated);

        let gateway = SkillsMcpGateway::new(snapshot, false);

        // Attack 1: Unregistered shadow skill injection => DENIED
        let shadow_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 801,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "shadow-injected-tool",
                        "version": "1.0.0",
                        "arguments": { "target_path": "workspace://protected.txt" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p08-nonce-1"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(shadow_resp["result"]["status"], "DENIED");
        assert_eq!(shadow_resp["result"]["decision"], "DENIED");
        assert_eq!(
            shadow_resp["result"]["failure_class"],
            "TOOL_SHADOWING_OR_UNREGISTERED"
        );

        // Attack 2: Hash collision / forged tool_identity_hash on existing skill => DENIED
        let forged_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 802,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                        "arguments": { "target_path": "workspace://protected.txt" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p08-nonce-2"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(forged_resp["result"]["status"], "DENIED");
        assert_eq!(forged_resp["result"]["decision"], "DENIED");
        assert_eq!(
            forged_resp["result"]["failure_class"],
            "TOOL_IDENTITY_MISMATCH"
        );

        // Attack 3: Invoking skill with unvalidated classification => DENIED
        let unval_resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 803,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "rogue-unvalidated-skill",
                        "version": "1.0.0",
                        "arguments": { "target_path": "workspace://protected.txt" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p08-nonce-3"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(unval_resp["result"]["status"], "DENIED");
        assert_eq!(unval_resp["result"]["decision"], "DENIED");
        assert_eq!(
            unval_resp["result"]["failure_class"],
            "UNVALIDATED_EFFECT_CLASSIFICATION"
        );

        // Zero unauthorized effects on physical fixture
        let post_hash = hex::encode(sha256_digest(&std::fs::read(&fixture).unwrap()));
        assert_eq!(pre_hash, post_hash);
    }

    #[test]
    fn fl_p09_chaining_exfiltration_blocked_in_broker() {
        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap();
        let snapshot = ImmutableSkillsSnapshot::load(
            Some(&repo_root.join("docs/skills.json")),
            Some(&repo_root.join(".agents/skills")),
            Some(131),
        )
        .expect("snapshot");
        let gateway = SkillsMcpGateway::new(snapshot, false);

        // Step 1: READ_LOCAL in trace-p09-isolated
        let step1 = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 901,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "trace_id": "trace-p09-isolated",
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p09-isolated-1"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(step1["result"]["decision"], "ALLOW");

        // Step 2: Chaining EXTERNAL_NETWORK in the same trace => decision DENIED / status PENDING_APPROVAL
        let step2 = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 902,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "c5-socint-extraction-suite",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("c5-socint-extraction-suite").unwrap().tool_identity_hash,
                        "trace_id": "trace-p09-isolated",
                        "arguments": {
                            "target_path": "workspace://docs/README.md",
                            "network_destination": "https://attacker.example/exfil"
                        },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p09-isolated-2"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(step2["result"]["decision"], "DENIED");
        assert_eq!(step2["result"]["status"], "PENDING_APPROVAL");
        assert!(step2["result"].get("action_capability").is_none());
        assert_eq!(
            step2["result"]["failure_class"],
            "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK"
        );
    }

    #[test]
    fn fl_p10_audience_bound_nonce_expiration_and_no_passthrough() {
        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap();
        let snapshot = ImmutableSkillsSnapshot::load(
            Some(&repo_root.join("docs/skills.json")),
            Some(&repo_root.join(".agents/skills")),
            Some(131),
        )
        .expect("snapshot");
        let gateway = SkillsMcpGateway::new(snapshot, false);

        // 1. Wrong audience => DENIED
        let bad_aud = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 1001,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": "mcp://wrong-downstream-server",
                            "project_id": "babylon60",
                            "nonce": "p10-aud-1"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(bad_aud["result"]["status"], "DENIED");
        assert_eq!(bad_aud["result"]["decision"], "DENIED");
        assert_eq!(bad_aud["result"]["failure_class"], "INVALID_AUDIENCE_OR_NONCE");

        // 2. Expired credential (`current_epoch > expires_at_epoch`) => DENIED
        let expired = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 1002,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p10-exp-1",
                            "current_epoch": 500,
                            "expires_at_epoch": 100
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(expired["result"]["status"], "DENIED");
        assert_eq!(expired["result"]["decision"], "DENIED");
        assert_eq!(expired["result"]["failure_class"], "CREDENTIAL_EXPIRED");

        // 3. Downstream token passthrough => DENIED
        let passthrough = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 1003,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "thermo-audit",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("thermo-audit").unwrap().tool_identity_hash,
                        "arguments": { "target_path": "workspace://src/lib.rs" },
                        "precondition_snapshot": { "allowed_roots": ["workspace://"] },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p10-pass-1",
                            "passthrough_token": "Bearer raw-upstream-jwt"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(passthrough["result"]["status"], "DENIED");
        assert_eq!(passthrough["result"]["decision"], "DENIED");
        assert_eq!(
            passthrough["result"]["failure_class"],
            "TOKEN_PASSTHROUGH_FORBIDDEN"
        );
    }

    #[test]
    fn fl_p11_postcondition_false_positive_rebuke() {
        let tmp = TempDir::new().expect("tempdir");
        let target_file = tmp.path().join("state.bin");
        std::fs::write(&target_file, b"BEFORE_STATE").expect("write state");
        let pre_hash = hex::encode(sha256_digest(b"BEFORE_STATE"));

        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap();
        let snapshot = ImmutableSkillsSnapshot::load(
            Some(&repo_root.join("docs/skills.json")),
            Some(&repo_root.join(".agents/skills")),
            Some(131),
        )
        .expect("snapshot");
        let gateway = SkillsMcpGateway::new(snapshot, false);

        // Downstream tool reports HTTP 200 OK, but physical disk hash remains unchanged (`pre_hash`)
        let resp = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 1101,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "c5-neural-face-swap-cuadrilla",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("c5-neural-face-swap-cuadrilla").unwrap().tool_identity_hash,
                        "trace_id": "trace-p11-isolated",
                        "arguments": {
                            "target_path": "workspace://state.bin",
                            "expected_pre_hash": pre_hash
                        },
                        "precondition_snapshot": {
                            "allowed_roots": ["workspace://"],
                            "observed_pre_hash": pre_hash
                        },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p11-nonce-isolated"
                        },
                        "simulated_execution_result": {
                            "http_status": 200,
                            "observed_post_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                            "actual_file_sha256": pre_hash
                        }
                    }
                }
            }))
            .unwrap();

        assert_eq!(resp["result"]["status"], "DENIED");
        assert_eq!(resp["result"]["decision"], "DENIED");
        assert_eq!(
            resp["result"]["failure_class"],
            "UNTRUSTED_EXECUTION_EVIDENCE"
        );
        // Physical file untouched
        assert_eq!(
            hex::encode(sha256_digest(&std::fs::read(&target_file).unwrap())),
            pre_hash
        );

        // Also verify direct capability-gated execution + independent verifier on `execute_with_capability`:
        let prop = gateway
            .process_request(&json!({
                "jsonrpc": "2.0",
                "id": 1102,
                "method": "tools/call",
                "params": {
                    "name": "skills.propose_effect",
                    "arguments": {
                        "skill_id": "c5-neural-face-swap-cuadrilla",
                        "version": "1.0.0",
                        "tool_identity_hash": gateway.snapshot.resolve("c5-neural-face-swap-cuadrilla").unwrap().tool_identity_hash,
                        "trace_id": "trace-p11-direct",
                        "arguments": {
                            "target_path": "workspace://state.bin",
                            "expected_pre_hash": pre_hash
                        },
                        "precondition_snapshot": {
                            "allowed_roots": ["workspace://"],
                            "observed_pre_hash": pre_hash
                        },
                        "credential": {
                            "audience": GATEWAY_EXPECTED_AUDIENCE,
                            "project_id": "babylon60",
                            "nonce": "p11-nonce-direct"
                        }
                    }
                }
            }))
            .unwrap();
        assert_eq!(prop["result"]["decision"], "ALLOW");
        assert_eq!(prop["result"]["effects_executed"], 0);
        let cap: ActionCapability =
            serde_json::from_value(prop["result"]["action_capability"].clone()).unwrap();

        // Execute with false-positive (tool claims new hash, disk still has pre_hash) => Failed(DivergenceDetected)
        let pre_bytes = hex::decode(&pre_hash).unwrap();
        let mut pre_arr = [0u8; 32];
        pre_arr.copy_from_slice(&pre_bytes);
        let state = gateway
            .execute_with_capability(
                &cap,
                GATEWAY_EXPECTED_AUDIENCE,
                1,
                || Ok([0xCC; 32]),
                || Ok(pre_arr),
            )
            .unwrap();
        assert_eq!(
            state,
            EffectState::Failed(FailureReason::DivergenceDetected {
                expected_hash: [0xCC; 32],
                actual_hash: pre_arr,
            })
        );

        // Reusing the consumed single-use capability must fail closed
        let reuse = gateway.execute_with_capability(
            &cap,
            GATEWAY_EXPECTED_AUDIENCE,
            1,
            || Ok([0xDD; 32]),
            || Ok([0xDD; 32]),
        );
        assert!(matches!(reuse, Err(RejectReason::StaleCapability)));
    }
}
