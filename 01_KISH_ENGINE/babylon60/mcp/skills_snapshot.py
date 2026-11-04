# -*- coding: utf-8 -*-
"""Immutable in-memory skills snapshot & Architecture v3.1 Gateway for CortexMCPServer (SEP-2640).

Invariants:
- Snapshot is constructed and verified once at server initialization.
- All file descriptors are opened with O_RDONLY | O_NOFOLLOW (anti-TOCTOU).
- After initialization, MCP handlers (skills/list, skills/get, prompts/list,
  prompts/get, resources/read, bft_route_skill) and the 3 v3.1 orchestration
  meta-primitives (skills.discover, skills.inspect, skills.propose_effect)
  serve strictly from RAM.
- Subsequent filesystem mutations or deletions cannot alter served content
  until a new snapshot/server instance is loaded.
- Non-Implication Chain (6 Disjoint States):
  Registered(s) ⇏ Visible(s, p) ⇏ Loaded(s) ⇏ Proposed(a) ⇏ Authorized(a) ⇏ Verified(a)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, cast

import yaml


EXCLUDED_NAMES = frozenset({"_archive", "archive", ".git", "node_modules", "__pycache__"})
GATEWAY_EXPECTED_AUDIENCE = "mcp://babylon-skills-gateway"


def _read_bytes_nofollow(path: Path) -> bytes:
    """Read a regular file using O_RDONLY | O_NOFOLLOW without following terminal symlinks."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(f"Not a regular file: {path}")
        chunks: list[bytes] = []
        for _ in range(1024):
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _guess_mime_type(rel_path: str) -> str:
    lower = rel_path.lower()
    if lower.endswith(".md"):
        return "text/markdown"
    if lower.endswith((".yaml", ".yml")):
        return "application/yaml"
    if lower.endswith(".json"):
        return "application/json"
    if lower.endswith(".py"):
        return "text/x-python"
    if lower.endswith(".rs"):
        return "text/x-rust"
    if lower.endswith(".sh"):
        return "text/x-shellscript"
    return "text/plain"


VALID_SKILL_ROLES = frozenset({"arquitecto", "ejecutor", "auditor"})
VALID_SKILL_SCOPES = frozenset({"workspace", "global", "kernel"})
VALID_SKILL_CATEGORIES = frozenset(
    {
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
    }
)


def derive_v31_contract(
    name: str,
    role: str,
    category: str,
    scope: str = "global",
) -> tuple[dict[str, object], dict[str, list[str]]]:
    """Deterministically derive effect_profile and guard_invariants from structural metadata (never from description)."""
    lower_name = name.strip().lower()
    lower_role = role.strip().lower()
    lower_cat = category.strip().lower()
    lower_scope = scope.strip().lower()

    validated = (
        bool(lower_name)
        and lower_role in VALID_SKILL_ROLES
        and lower_scope in VALID_SKILL_SCOPES
        and lower_cat in VALID_SKILL_CATEGORIES
    )
    if not validated:
        return (
            {
                "class": "UNVALIDATED",
                "reversibility": "IRREVERSIBLE",
                "requires_action_lease": True,
                "network_egress": "NONE",
                "validated": False,
            },
            {
                "preconditions": [
                    "classification.validated == true",
                    "target_path WITHIN project.allowed_roots",
                ],
                "postconditions": ["result.status == 'OK'"],
            },
        )

    is_network = (
        lower_cat == "socint & web"
        or "web" in lower_name
        or "socint" in lower_name
        or "github" in lower_name
        or "cloudflare" in lower_name
        or "soulseek" in lower_name
        or "youtube" in lower_name
        or "safari" in lower_name
        or "gemini" in lower_name
        or "kimi" in lower_name
        or "whatsapp" in lower_name
    )

    is_destructive = (
        "purge" in lower_name
        or "extinction" in lower_name
        or "detonate" in lower_name
        or "bomb" in lower_name
    )

    is_mutation = (
        "patch" in lower_name
        or "deploy" in lower_name
        or "genesis" in lower_name
        or "swap" in lower_name
        or "production" in lower_name
        or "remotion" in lower_name
        or "f5tts" in lower_name
        or "pika" in lower_name
        or "gflow" in lower_name
        or (lower_role == "ejecutor" and "audit" not in lower_name)
    )

    if is_destructive:
        effect_class = "DESTRUCTIVE"
    elif is_network:
        effect_class = "READ_EXT"
    elif is_mutation:
        effect_class = "STATE_MUTATION"
    elif (
        lower_role == "auditor"
        or "audit" in lower_cat
        or lower_cat == "diagnostics"
        or "audit" in lower_name
        or "diagnostics" in lower_name
        or "telemetry" in lower_name
    ):
        effect_class = "READ_LOCAL"
    else:
        effect_class = "PURE"

    if effect_class in {"PURE", "READ_LOCAL", "READ_EXT"}:
        reversibility = "REVERSIBLE"
    elif effect_class == "STATE_MUTATION":
        reversibility = "COMPENSATABLE"
    else:
        reversibility = "IRREVERSIBLE"

    requires_action_lease = effect_class in {"READ_EXT", "STATE_MUTATION", "DESTRUCTIVE", "UNVALIDATED"}
    network_egress = "EXTERNAL_NETWORK" if (is_network or effect_class == "READ_EXT") else "NONE"

    preconditions = ["target_path WITHIN project.allowed_roots"]
    postconditions = ["result.status == 'OK'"]
    if effect_class in {"STATE_MUTATION", "DESTRUCTIVE"}:
        preconditions.append("sha256(file(target_path)) == args.expected_pre_hash")
        postconditions.append("sha256(file(target_path)) == result.observed_post_hash")
        postconditions.append("result.observed_post_hash != args.expected_pre_hash")
    else:
        postconditions.append("sha256(file(target_path)) == args.expected_pre_hash")

    effect_profile: dict[str, object] = {
        "class": effect_class,
        "reversibility": reversibility,
        "requires_action_lease": requires_action_lease,
        "network_egress": network_egress,
        "validated": True,
    }
    guard_invariants: dict[str, list[str]] = {
        "preconditions": preconditions,
        "postconditions": postconditions,
    }
    return effect_profile, guard_invariants


def compute_tool_identity_hash(
    skill_id: str,
    version: str,
    artifact_sha256: str,
    effect_class: str,
) -> str:
    seed = f"v3.1:{skill_id}@{version}:{artifact_sha256}:{effect_class}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SkillResourceSnapshot:
    """Immutable in-memory representation of a single file inside a skill."""

    relative_path: str
    uri: str
    mime_type: str
    size_bytes: int
    sha256: str
    text: str


@dataclass(frozen=True)
class SkillEntrySnapshot:
    """Immutable in-memory representation of a skill and its verified resources."""

    name: str
    canonical_alias: str
    display_name: str
    description: str
    role: str
    scope: str
    tier: int
    category: str
    triggers: tuple[str, ...]
    uri: str
    manifest_sha256: str
    skill_md_text: str | None
    frontmatter: dict[str, object]
    resources: tuple[SkillResourceSnapshot, ...]
    version: str = "1.0.0"
    tool_identity_hash: str = ""
    effect_profile: dict[str, object] = field(default_factory=dict)
    guard_invariants: dict[str, list[str]] = field(default_factory=dict)

    def input_json_schema(self) -> dict[str, object]:
        eff_class = str(self.effect_profile.get("class", "PURE"))
        props: dict[str, object] = {
            "task": {
                "type": "string",
                "description": f"Task context or instruction for skill '{self.name}'.",
            },
            "target_path": {
                "type": "string",
                "description": "Target path inside project.allowed_roots.",
            },
        }
        required = ["target_path"]
        if eff_class in {"STATE_MUTATION", "DESTRUCTIVE"}:
            props["expected_pre_hash"] = {
                "type": "string",
                "pattern": "^[a-f0-9]{64}$",
                "description": "Expected SHA-256 hex digest of target_path before mutation.",
            }
            required.append("expected_pre_hash")
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"{self.name}InputSchema",
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": True,
        }


class ImmutableSkillsSnapshot:
    """Verified in-memory snapshot of the skills catalog and workspace skill files."""

    def __init__(
        self,
        *,
        catalog_data: dict[str, object],
        catalog_sha256: str,
        root_sha256: str,
        skills_by_name: dict[str, SkillEntrySnapshot],
        alias_to_name: dict[str, str],
        resources_by_uri: dict[str, SkillResourceSnapshot],
        workspace_skill_names: tuple[str, ...],
    ) -> None:
        self._catalog_data = catalog_data
        self.catalog_sha256 = catalog_sha256
        self.root_sha256 = root_sha256
        self._skills_by_name = skills_by_name
        self._alias_to_name = alias_to_name
        self._resources_by_uri = resources_by_uri
        self.workspace_skill_names = workspace_skill_names
        self._consumed_nonces: set[tuple[str, str]] = set()
        self._trace_effects: dict[str, list[str]] = {}
        self._project_allowlists: dict[str, set[str]] = {}
        self._human_approved_nonces: set[tuple[str, str]] = set()

    @classmethod
    def load(
        cls,
        skills_json_path: Path | None,
        skills_dir: Path | None,
        *,
        expected_count: int | None = None,
        lockfile_path: Path | None = None,
    ) -> ImmutableSkillsSnapshot:
        catalog_data: dict[str, object] = {
            "version": "26.400",
            "total_skills": 0,
            "average_exergy_density": 0,
            "adjacency": [],
            "entries": [],
        }
        catalog_sha256 = hashlib.sha256(b"").hexdigest()

        if skills_json_path is not None and skills_json_path.is_file():
            raw_catalog = _read_bytes_nofollow(skills_json_path)
            catalog_sha256 = hashlib.sha256(raw_catalog).hexdigest()
            loaded = json.loads(raw_catalog.decode("utf-8"))
            if isinstance(loaded, dict):
                catalog_data = loaded

        # Load physical workspace skills into RAM with O_NOFOLLOW + SHA-256 verification
        ws_entries: dict[str, tuple[dict[str, object], str, tuple[SkillResourceSnapshot, ...], str]] = {}
        workspace_names: list[str] = []
        md_text: str | None

        if skills_dir is not None and skills_dir.is_dir():
            for skill_dir in sorted(skills_dir.iterdir(), key=lambda p: p.name):
                if skill_dir.name in EXCLUDED_NAMES or skill_dir.is_symlink() or not skill_dir.is_dir():
                    continue
                md_path = skill_dir / "SKILL.md"
                if not md_path.is_file() or md_path.is_symlink():
                    continue
                raw_md = _read_bytes_nofollow(md_path)
                md_text = raw_md.decode("utf-8", errors="replace")
                fm: dict[str, object] = {}
                parts = md_text.split("---", 2)
                if md_text.startswith("---") and len(parts) >= 3:
                    parsed = yaml.safe_load(parts[1])
                    if isinstance(parsed, dict):
                        fm = parsed

                sname = str(fm.get("name", skill_dir.name))
                resources: list[SkillResourceSnapshot] = []

                def _walk_dir(current: Path) -> None:
                    for child in sorted(current.iterdir(), key=lambda p: p.name):
                        if child.name in EXCLUDED_NAMES or child.is_symlink():
                            continue
                        if child.is_dir():
                            _walk_dir(child)
                        elif child.is_file():
                            raw_bytes = _read_bytes_nofollow(child)
                            rel = child.relative_to(skill_dir).as_posix()
                            digest = hashlib.sha256(raw_bytes).hexdigest()
                            uri = f"skill://{sname}/{rel}"
                            resources.append(
                                SkillResourceSnapshot(
                                    relative_path=rel,
                                    uri=uri,
                                    mime_type=_guess_mime_type(rel),
                                    size_bytes=len(raw_bytes),
                                    sha256=digest,
                                    text=raw_bytes.decode("utf-8", errors="replace"),
                                )
                            )

                _walk_dir(skill_dir)
                manifest_hasher = hashlib.sha256()
                for res in resources:
                    manifest_hasher.update(f"{res.relative_path}:{res.size_bytes}:{res.sha256}\n".encode("utf-8"))
                ws_entries[sname] = (fm, md_text, tuple(resources), manifest_hasher.hexdigest())
                workspace_names.append(sname)

        skills_by_name: dict[str, SkillEntrySnapshot] = {}
        alias_to_name: dict[str, str] = {}
        resources_by_uri: dict[str, SkillResourceSnapshot] = {}

        catalog_entries = cast(list[dict[str, object]], catalog_data.get("entries", []))
        seen_names: set[str] = set()

        for entry in catalog_entries:
            ename = str(entry.get("name", "")).strip()
            if not ename:
                continue
            if ename in seen_names:
                raise ValueError(f"DUPLICATE_SKILL_ID_IN_CATALOG: {ename}")
            seen_names.add(ename)
            ealias = str(entry.get("canonical_alias") or ename).strip() or ename
            display_name = str(entry.get("display_name") or ename)
            description = str(entry.get("description") or "")
            role = str(entry.get("role") or "ejecutor")
            scope = str(entry.get("scope") or "global")
            version = str(entry.get("version") or "1.0.0")
            raw_tier = entry.get("tier", 18000)
            tier = int(raw_tier) if isinstance(raw_tier, (int, float, str)) else 18000
            category = str(entry.get("category") or "General")
            raw_triggers = entry.get("triggers", [])
            triggers = tuple(str(t) for t in raw_triggers) if isinstance(raw_triggers, list) else ()

            if ename in ws_entries:
                fm, md_text, res_tuple, manifest_sha = ws_entries[ename]
                fm_alias = str(fm.get("canonical_alias", "")).strip()
                if fm_alias:
                    ealias = fm_alias
                fm_desc = str(fm.get("description", "")).strip()
                if fm_desc:
                    description = fm_desc
                for res in res_tuple:
                    resources_by_uri[res.uri] = res
                    if ealias != ename:
                        resources_by_uri[f"skill://{ealias}/{res.relative_path}"] = res
            else:
                fm = {}
                md_text = None
                synth_text = (
                    f"# CORTEX Skill: {display_name}\n"
                    f"- Canonical Alias: `{ealias}` (ID: `{ename}`)\n"
                    f"- Role Triad: `{role}` | Tier: `{tier}` | Scope: `{scope}`\n"
                    f"- Description: {description}\n"
                )
                synth_bytes = synth_text.encode("utf-8")
                synth_sha = hashlib.sha256(synth_bytes).hexdigest()
                synth_res = SkillResourceSnapshot(
                    relative_path="SKILL.md",
                    uri=f"skill://{ename}/SKILL.md",
                    mime_type="text/markdown",
                    size_bytes=len(synth_bytes),
                    sha256=synth_sha,
                    text=synth_text,
                )
                res_tuple = (synth_res,)
                manifest_sha = synth_sha
                resources_by_uri[synth_res.uri] = synth_res
                if ealias != ename:
                    resources_by_uri[f"skill://{ealias}/SKILL.md"] = synth_res

            effect_profile, guard_invariants = derive_v31_contract(ename, role, category, scope)
            tool_identity_hash = compute_tool_identity_hash(
                ename,
                version,
                manifest_sha,
                str(effect_profile["class"]),
            )

            snap = SkillEntrySnapshot(
                name=ename,
                canonical_alias=ealias,
                display_name=display_name,
                description=description,
                role=role,
                scope=scope,
                tier=tier,
                category=category,
                triggers=triggers,
                uri=f"skill://{ename}",
                manifest_sha256=manifest_sha,
                skill_md_text=md_text,
                frontmatter=fm,
                resources=res_tuple,
                version=version,
                tool_identity_hash=tool_identity_hash,
                effect_profile=effect_profile,
                guard_invariants=guard_invariants,
            )
            skills_by_name[ename] = snap
            alias_to_name[ename] = ename
            alias_to_name[ealias] = ename

        # Add any workspace skills that were not listed in docs/skills.json
        for sname in workspace_names:
            if sname in skills_by_name:
                continue
            fm, md_text, res_tuple, manifest_sha = ws_entries[sname]
            salias = str(fm.get("canonical_alias", sname)).strip() or sname
            sdesc = str(fm.get("description", ""))
            srole = str(fm.get("role", "ejecutor"))
            sversion = str(fm.get("version", "1.0.0"))
            for res in res_tuple:
                resources_by_uri[res.uri] = res
                if salias != sname:
                    resources_by_uri[f"skill://{salias}/{res.relative_path}"] = res
            effect_profile, guard_invariants = derive_v31_contract(sname, srole, "Workspace", "workspace")
            tool_identity_hash = compute_tool_identity_hash(
                sname,
                sversion,
                manifest_sha,
                str(effect_profile["class"]),
            )
            snap = SkillEntrySnapshot(
                name=sname,
                canonical_alias=salias,
                display_name=str(fm.get("display_name", sname)),
                description=sdesc,
                role=srole,
                scope="workspace",
                tier=20000,
                category="Workspace",
                triggers=(sname, salias),
                uri=f"skill://{sname}",
                manifest_sha256=manifest_sha,
                skill_md_text=md_text,
                frontmatter=fm,
                resources=res_tuple,
                version=sversion,
                tool_identity_hash=tool_identity_hash,
                effect_profile=effect_profile,
                guard_invariants=guard_invariants,
            )
            skills_by_name[sname] = snap
            alias_to_name[sname] = sname
            alias_to_name[salias] = sname

        if expected_count is not None and len(skills_by_name) != expected_count:
            raise ValueError(
                f"SKILLS_SNAPSHOT_COUNT_MISMATCH: expected {expected_count} skills, found {len(skills_by_name)}"
            )

        root_hasher = hashlib.sha256()
        root_hasher.update(f"catalog:{catalog_sha256}\n".encode("utf-8"))
        for k in sorted(skills_by_name):
            root_hasher.update(f"{k}:{skills_by_name[k].manifest_sha256}\n".encode("utf-8"))

        snapshot = cls(
            catalog_data=catalog_data,
            catalog_sha256=catalog_sha256,
            root_sha256=root_hasher.hexdigest(),
            skills_by_name=skills_by_name,
            alias_to_name=alias_to_name,
            resources_by_uri=resources_by_uri,
            workspace_skill_names=tuple(workspace_names),
        )
        if lockfile_path is not None:
            snapshot.verify_against_lockfile(json.loads(_read_bytes_nofollow(lockfile_path)))
        return snapshot

    @property
    def total_skills(self) -> int:
        return len(self._skills_by_name)

    def to_lockfile(self) -> dict[str, object]:
        skills_map: dict[str, object] = {}
        for name in sorted(self._skills_by_name):
            snap = self._skills_by_name[name]
            skills_map[name] = {
                "skill_id": name,
                "canonical_alias": snap.canonical_alias,
                "version": snap.version,
                "artifact_sha256": snap.manifest_sha256,
                "tool_identity_hash": snap.tool_identity_hash,
                "lockfile_ref": f"skills-lock.json#{name}@{snap.version}",
                "domain": snap.category.lower(),
                "summary": snap.description,
                "tags": list(snap.triggers),
                "effect_profile": snap.effect_profile,
                "guard_invariants": snap.guard_invariants,
            }
        return {
            "schema_version": "3.1.0",
            "catalog_sha256": self.catalog_sha256,
            "snapshot_root_sha256": self.root_sha256,
            "total_skills": len(skills_map),
            "skills": skills_map,
        }

    def verify_against_lockfile(self, lockfile: object) -> None:
        """Pin the whole contract, including classification and guard invariants."""
        if lockfile != self.to_lockfile() or any(
            not entry.effect_profile.get("validated")
            or entry.effect_profile.get("class") == "UNVALIDATED"
            for entry in self._skills_by_name.values()
        ):
            raise ValueError("SKILLS_LOCK_MISMATCH: catalog, artifact or policy differs from the pinned lock")

    def set_project_allowlist(self, project_id: str, allowed_skills: set[str]) -> None:
        self._project_allowlists[project_id] = set(allowed_skills)

    def is_skill_visible(self, project_id: str, skill_id: str) -> bool:
        if skill_id not in self._skills_by_name:
            return False
        if project_id in self._project_allowlists:
            return skill_id in self._project_allowlists[project_id]
        return True

    def discover_skills(self, args: dict[str, object]) -> dict[str, object]:
        """Architecture v3.1 `skills.discover`: returns at most k <= 5 matches."""
        query = str(args.get("query", "")).strip().lower()
        project_id = str(args.get("project_id", "default")).strip() or "default"
        effect_filter = str(args.get("effect_filter", "")).strip().upper()
        if effect_filter == "EXTERNAL_NETWORK":
            effect_filter = "READ_EXT"
        raw_k = args.get("k", 5)
        k = max(1, min(5, int(raw_k) if isinstance(raw_k, (int, float, str)) else 5))

        tokens = [t for t in query.split() if t]
        scored: list[tuple[int, SkillEntrySnapshot]] = []

        for name in sorted(self._skills_by_name):
            snap = self._skills_by_name[name]
            if not self.is_skill_visible(project_id, name):
                continue
            eff_class = str(snap.effect_profile.get("class", "PURE"))
            if effect_filter and eff_class != effect_filter:
                continue

            hay_name = snap.name.lower()
            hay_alias = snap.canonical_alias.lower()
            hay_desc = snap.description.lower()
            hay_cat = snap.category.lower()

            score = 0
            if not tokens:
                score = 1
            else:
                for tok in tokens:
                    if tok in {hay_name, hay_alias}:
                        score += 100
                    elif tok in hay_name or tok in hay_alias:
                        score += 40
                    if any(tok in trig.lower() for trig in snap.triggers):
                        score += 25
                    if tok in hay_desc or tok in hay_cat:
                        score += 10
            if score > 0:
                scored.append((score, snap))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        matches = [
            {
                "skill_id": snap.name,
                "canonical_alias": snap.canonical_alias,
                "version": snap.version,
                "summary": snap.description,
                "effect_profile": {"class": snap.effect_profile.get("class", "PURE")},
            }
            for _, snap in scored[:k]
        ]
        return {
            "isError": False,
            "project_id": project_id,
            "k_limit": k,
            "matches": matches,
        }

    def inspect_skill(self, args: dict[str, object]) -> dict[str, object]:
        """Architecture v3.1 `skills.inspect`: verifies lockfile and returns schema & preconditions."""
        skill_id = str(args.get("skill_id", "")).strip()
        version = str(args.get("version", "1.0.0")).strip() or "1.0.0"
        project_id = str(args.get("project_id", "default")).strip() or "default"

        snap = self.resolve(skill_id)
        if snap is None:
            return {
                "isError": True,
                "status": "DENIED",
                "failure_class": "SKILL_NOT_IN_LOCKFILE",
                "error": f"Skill '{skill_id}' is not registered in skills-lock.json",
            }
        if not self.is_skill_visible(project_id, snap.name):
            return {
                "isError": True,
                "status": "DENIED",
                "failure_class": "PROJECT_POLICY_DENIED",
                "error": f"Skill '{snap.name}' is not visible in project '{project_id}'",
            }
        if snap.version != version:
            return {
                "isError": True,
                "status": "DENIED",
                "failure_class": "TOOL_IDENTITY_MISMATCH",
                "error": "Skill version mismatch against skills-lock.json",
            }
        return {
            "isError": False,
            "skill_id": snap.name,
            "canonical_alias": snap.canonical_alias,
            "version": snap.version,
            "tool_identity_hash": snap.tool_identity_hash,
            "lockfile_ref": f"skills-lock.json#{snap.name}@{snap.version}",
            "effect_profile": snap.effect_profile,
            "input_json_schema": snap.input_json_schema(),
            "preconditions": snap.guard_invariants.get("preconditions", []),
            "postconditions": snap.guard_invariants.get("postconditions", []),
        }

    def propose_skill_effect(self, args: dict[str, object]) -> dict[str, object]:
        """Validate a proposal only; execution still requires the trusted dispatcher and its gate."""
        if "simulated_execution_result" in args:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "UNTRUSTED_EXECUTION_EVIDENCE",
                "error": "FL-P11: Client-supplied execution evidence cannot verify a proposal",
            }
        skill_id = str(args.get("skill_id", "")).strip()
        version = args.get("version")
        provided_hash = args.get("tool_identity_hash")
        raw_curr_epoch = args.get("current_epoch", 1_761_334_400)
        current_epoch = int(raw_curr_epoch) if isinstance(raw_curr_epoch, (int, float, str)) else 1_761_334_400

        cred = args.get("credential")
        if not isinstance(cred, dict):
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "MISSING_AUDIENCE_CREDENTIAL",
                "error": "FL-P10: Missing audience-bound credential",
            }

        passthrough = cred.get("passthrough_token")
        if passthrough is not None and str(passthrough).strip() != "":
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOKEN_PASSTHROUGH_FORBIDDEN",
                "error": "FL-P10: Downstream token passthrough is strictly forbidden",
            }

        audience = str(cred.get("audience", "")).strip()
        project_id = str(cred.get("project_id", "")).strip()
        nonce = str(cred.get("nonce", "")).strip()
        if audience != GATEWAY_EXPECTED_AUDIENCE or not project_id or not nonce:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "INVALID_AUDIENCE_OR_NONCE",
                "error": "FL-P10: Credential must bind exact audience, non-empty project_id, and unique nonce",
            }

        raw_exp = cred.get("expires_at_epoch", current_epoch + 300)
        expires_at_epoch = int(raw_exp) if isinstance(raw_exp, (int, float, str)) else 0
        if expires_at_epoch <= 0 or current_epoch > expires_at_epoch:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "CREDENTIAL_EXPIRED",
                "error": "FL-P10: Credential has expired or lacks a valid expiration epoch",
            }

        snap = self.resolve(skill_id)
        if snap is None:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOOL_SHADOWING_OR_UNREGISTERED",
                "error": f"FL-P08: Skill '{skill_id}' is not registered in skills-lock.json",
            }

        if not bool(snap.effect_profile.get("validated", True)) or str(snap.effect_profile.get("class")) == "UNVALIDATED":
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "UNVALIDATED_EFFECT_CLASSIFICATION",
                "error": f"FL-P08: Skill '{snap.name}' has an unvalidated effect classification; fail-closed DENY",
            }

        if snap.version != version or provided_hash != snap.tool_identity_hash:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "TOOL_IDENTITY_MISMATCH",
                "error": "FL-P08: tool_identity_hash or version mismatch against skills-lock.json",
            }

        if not self.is_skill_visible(project_id, snap.name):
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "PROJECT_POLICY_DENIED",
                "error": f"Skill '{snap.name}' is not allowed for project '{project_id}'",
            }

        call_args_raw = args.get("arguments", {})
        call_args = call_args_raw if isinstance(call_args_raw, dict) else {}
        pre_snap_raw = args.get("precondition_snapshot", {})
        pre_snap = pre_snap_raw if isinstance(pre_snap_raw, dict) else {}

        target_path = str(call_args.get("target_path", "")).strip()
        raw_roots = pre_snap.get("allowed_roots", ["workspace://", "/workspace", "."])
        allowed_roots = [str(r) for r in raw_roots] if isinstance(raw_roots, list) else ["workspace://"]

        path_ok = (
            bool(target_path)
            and ".." not in target_path
            and any(
                target_path == r.rstrip("/")
                or target_path.startswith(r.rstrip("/") + "/")
                or r == "."
                for r in allowed_roots
            )
        )
        if not path_ok:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "PRECONDITION_MISMATCH",
                "error": "Precondition failed: target_path WITHIN project.allowed_roots",
            }

        eff_class = str(snap.effect_profile.get("class", "PURE"))
        if eff_class in {"STATE_MUTATION", "DESTRUCTIVE"}:
            expected_pre_hash = str(call_args.get("expected_pre_hash", "")).strip()
            observed_pre_hash = str(
                pre_snap.get("observed_pre_hash") or pre_snap.get("file_sha256") or ""
            ).strip()
            if not expected_pre_hash or expected_pre_hash != observed_pre_hash:
                return {
                    "isError": True,
                    "status": "DENIED",
                    "decision": "DENIED",
                    "failure_class": "PRECONDITION_MISMATCH",
                    "error": "Precondition failed: sha256(file(target_path)) == args.expected_pre_hash",
                }

        nonce_key = (project_id, nonce)
        if nonce_key in self._consumed_nonces:
            return {
                "isError": True,
                "status": "DENIED",
                "decision": "DENIED",
                "failure_class": "NONCE_REPLAY_DETECTED",
                "error": "FL-P10: Nonce has already been consumed",
            }

        trace_id = str(args.get("trace_id") or project_id)
        prior_effects = self._trace_effects.setdefault(trace_id, [])
        has_prior_sensitive_read = "READ_LOCAL" in prior_effects
        explicit_net_dest = str(
            call_args.get("network_destination") or call_args.get("endpoint") or ""
        ).strip()
        requests_external_network = (
            eff_class == "READ_EXT"
            or str(snap.effect_profile.get("network_egress", "NONE")) == "EXTERNAL_NETWORK"
            or bool(explicit_net_dest)
        )
        if (
            has_prior_sensitive_read
            and requests_external_network
            and nonce_key not in self._human_approved_nonces
        ):
            return {
                "isError": False,
                "status": "PENDING_APPROVAL",
                "decision": "DENIED",
                "failure_class": "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK",
                "error": "FL-P09: Chaining READ_LOCAL followed by EXTERNAL_NETWORK in the same trace requires explicit human approval",
            }

        self._consumed_nonces.add(nonce_key)
        prior_effects.append(eff_class)

        arg_digest = hashlib.sha256(
            json.dumps(call_args, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        pre_digest = hashlib.sha256(
            json.dumps(pre_snap, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        cap_seed = f"{snap.name}:{snap.version}:{snap.tool_identity_hash}:{project_id}:{nonce}:{arg_digest}"
        capability = {
            "capability_id": hashlib.sha256(cap_seed.encode("utf-8")).hexdigest(),
            "skill_id": snap.name,
            "version": snap.version,
            "tool_identity_hash": snap.tool_identity_hash,
            "project_id": project_id,
            "trace_id": trace_id,
            "audience": audience,
            "target_resource": target_path,
            "nonce": nonce,
            "issued_epoch": current_epoch,
            "expires_at_epoch": expires_at_epoch,
            "argument_digest": arg_digest,
            "precondition_snapshot_hash": pre_digest,
            "effect_class": eff_class,
        }

        return {
            "isError": False,
            "status": "AUTHORIZED",
            "decision": "ALLOW",
            "effects_executed": 0,
            "action_capability": capability,
            "evidence": {
                "verification_scope": "proposal_only",
                "lockfile_ref": f"skills-lock.json#{snap.name}@{snap.version}",
                "postconditions_checked": [],
            },
        }

    def catalog_dict(self) -> dict[str, object]:
        """Return a shallow copy of the frozen catalog dictionary."""
        if not self._skills_by_name and not self._catalog_data.get("entries"):
            raise FileNotFoundError(
                "CORTEX_SKILLS_CATALOG_MISSING: docs/skills.json not found in checkout or package resources."
            )
        return dict(self._catalog_data)

    def resolve(self, identifier: str) -> SkillEntrySnapshot | None:
        cleaned = identifier.strip()
        if cleaned.startswith("skill://"):
            cleaned = cleaned[len("skill://") :].strip("/")
        canonical_name = self._alias_to_name.get(cleaned)
        if canonical_name is None:
            return None
        return self._skills_by_name.get(canonical_name)

    def read_skill_resource(self, uri: str) -> SkillResourceSnapshot | None:
        cleaned = uri.strip()
        if cleaned in self._resources_by_uri:
            return self._resources_by_uri[cleaned]
        if cleaned.startswith("skill://") and cleaned.count("/") == 2:
            return self._resources_by_uri.get(f"{cleaned}/SKILL.md")
        return None

    def list_skills(self, *, scope: str = "all", use_canonical_names: bool = False) -> dict[str, object]:
        """SEP-2640 skills/list implementation served purely from memory."""
        scope_norm = scope.strip().lower() if scope else "all"
        items: list[dict[str, object]] = []
        for name in sorted(self._skills_by_name):
            snap = self._skills_by_name[name]
            if scope_norm != "all" and snap.scope.lower() != scope_norm:
                continue
            primary = snap.canonical_alias if use_canonical_names else snap.name
            items.append(
                {
                    "name": primary,
                    "canonical_alias": snap.canonical_alias,
                    "legacy_name": snap.name,
                    "version": snap.version,
                    "uri": snap.uri,
                    "description": snap.description,
                    "role": snap.role,
                    "scope": snap.scope,
                    "tier": snap.tier,
                    "manifest_sha256": f"sha256:{snap.manifest_sha256}",
                    "tool_identity_hash": snap.tool_identity_hash,
                    "effect_profile": snap.effect_profile,
                    "resources": [
                        {
                            "path": r.relative_path,
                            "uri": r.uri,
                            "mimeType": r.mime_type,
                            "size": r.size_bytes,
                            "digest": f"sha256:{r.sha256}",
                        }
                        for r in snap.resources
                    ],
                }
            )
        return {
            "snapshot_root": f"sha256:{self.root_sha256}",
            "total": len(items),
            "skills": items,
        }

    def get_skill(self, identifier: str) -> dict[str, object] | None:
        """SEP-2640 skills/get implementation served purely from memory."""
        snap = self.resolve(identifier)
        if snap is None:
            return None
        return {
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
            "manifest_sha256": f"sha256:{snap.manifest_sha256}",
            "tool_identity_hash": snap.tool_identity_hash,
            "effect_profile": snap.effect_profile,
            "guard_invariants": snap.guard_invariants,
            "resources": [
                {
                    "path": r.relative_path,
                    "uri": r.uri,
                    "mimeType": r.mime_type,
                    "size": r.size_bytes,
                    "digest": f"sha256:{r.sha256}",
                }
                for r in snap.resources
            ],
        }

    def list_workspace_prompts(self, *, use_canonical_names: bool = False) -> list[dict[str, object]]:
        prompts: list[dict[str, object]] = []
        for sname in self.workspace_skill_names:
            snap = self._skills_by_name.get(sname)
            if snap is None:
                continue
            fm: dict[str, Any] = snap.frontmatter
            legacy_name = str(fm.get("name", sname))
            alias = str(fm.get("canonical_alias", legacy_name)).strip() or legacy_name
            primary_name = alias if use_canonical_names else legacy_name
            prompts.append(
                {
                    "name": primary_name,
                    "canonical_alias": alias,
                    "legacy_name": legacy_name,
                    "description": f"[{alias}] {fm.get('description', '')}",
                    "arguments": [
                        {
                            "name": "task",
                            "description": "Optional task or target context to execute with this CORTEX skill.",
                            "required": False,
                        }
                    ],
                }
            )
        return prompts
