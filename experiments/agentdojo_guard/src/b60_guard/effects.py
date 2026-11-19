"""Tool effect policy loader, seal verification, and schema extraction."""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from agentdojo.functions_runtime import Function

from b60_guard.contracts import ToolKind, ToolSpec
from b60_guard.native import blake3_bytes

VALID_EFFECTS = frozenset(
    {
        "FsRead",
        "FsMutate",
        "FsDelete",
        "FsChmod",
        "FsRename",
        "NetTransmit",
        "ProcSpawn",
        "ProcTerminate",
        "KeyDestroy",
        "LedgerAppend",
    }
)


def default_policy_dir() -> Path:
    return Path(__file__).absolute().parents[2] / "policy"


@dataclass(frozen=True)
class ToolPolicyEntry:
    kind: ToolKind
    effect: str | None
    rationale: str


@dataclass(frozen=True)
class ToolEffectPolicy:
    """Sealed classification of all AgentDojo suite tools into read vs write effects."""

    version: int
    benchmark_version: str
    suites: dict[str, dict[str, ToolPolicyEntry]]
    blake3_hex: str
    sha256_hex: str
    seal_verified: bool

    def get(self, suite_name: str, tool_name: str) -> ToolPolicyEntry:
        suite_map = self.suites.get(suite_name)
        if suite_map is None:
            raise KeyError(f"Unknown suite in tool_effects.yaml: {suite_name}")
        entry = suite_map.get(tool_name)
        if entry is None:
            raise KeyError(f"Unclassified tool (fail-closed): {suite_name}.{tool_name}")
        return entry

    def total_tools(self) -> int:
        return sum(len(tools) for tools in self.suites.values())


def load_tool_effect_policy(
    policy_path: Path | None = None,
    seal_path: Path | None = None,
    *,
    blake3_fn: Callable[[bytes], bytes] = blake3_bytes,
    verify_seal: bool = True,
) -> ToolEffectPolicy:
    """Load ``tool_effects.yaml`` and verify its BLAKE3/SHA-256 against ``manifest_seal.json``."""
    p_dir = default_policy_dir()
    p_path = (policy_path or (p_dir / "tool_effects.yaml")).absolute()
    s_path = (seal_path or (p_dir / "manifest_seal.json")).absolute()

    raw = p_path.read_bytes()
    b3_hex = blake3_fn(raw).hex()
    s256_hex = hashlib.sha256(raw).hexdigest()

    seal_verified = False
    if s_path.is_file():
        seal_data = json.loads(s_path.read_text(encoding="utf-8"))
        b3_ok = seal_data.get("tool_effects_yaml_blake3") == b3_hex
        s256_ok = seal_data.get("tool_effects_yaml_sha256") == s256_hex
        seal_verified = bool(b3_ok and s256_ok)
        if verify_seal and not seal_verified:
            raise ValueError(
                f"tool_effects.yaml seal mismatch: expected blake3={seal_data.get('tool_effects_yaml_blake3')}, got {b3_hex}"
            )
    elif verify_seal:
        raise FileNotFoundError(f"Missing policy seal file: {s_path}")

    doc: dict[str, Any] = yaml.safe_load(raw)
    suites: dict[str, dict[str, ToolPolicyEntry]] = {}
    for suite_name, tools in doc["suites"].items():
        suite_entries: dict[str, ToolPolicyEntry] = {}
        for tool_name, item in tools.items():
            kind = item["kind"]
            effect = item.get("effect")
            if kind == "read":
                if effect is not None:
                    raise ValueError(f"Read tool {suite_name}.{tool_name} must not declare effect {effect}")
            elif kind == "write":
                if effect not in VALID_EFFECTS:
                    raise ValueError(f"Invalid EffectKind {effect!r} for {suite_name}.{tool_name}")
            else:
                raise ValueError(f"Invalid kind {kind!r} for {suite_name}.{tool_name}")
            suite_entries[tool_name] = ToolPolicyEntry(
                kind=kind,
                effect=effect,
                rationale=str(item.get("rationale", "")),
            )
        suites[suite_name] = suite_entries

    return ToolEffectPolicy(
        version=int(doc["version"]),
        benchmark_version=str(doc["benchmark_version"]),
        suites=suites,
        blake3_hex=b3_hex,
        sha256_hex=s256_hex,
        seal_verified=seal_verified,
    )


def compute_tool_code_hash(fn: Function, *, blake3_fn: Callable[[bytes], bytes] = blake3_bytes) -> bytes:
    """Compute the Ring-0 32-byte BLAKE3 code hash over ``fn.run`` source."""
    source = inspect.getsource(fn.run).encode("utf-8")
    digest = blake3_fn(source)
    if len(digest) != 32:
        raise ValueError(f"Expected 32-byte BLAKE3 digest for {fn.name}, got {len(digest)}")
    return digest


def extract_tool_specs(
    suite_name: str,
    functions: Mapping[str, Function],
    policy: ToolEffectPolicy,
    *,
    blake3_fn: Callable[[bytes], bytes] = blake3_bytes,
) -> dict[str, ToolSpec]:
    """Build immutable ``ToolSpec`` records from runtime functions and policy."""
    specs: dict[str, ToolSpec] = {}
    for name, fn in functions.items():
        entry = policy.get(suite_name, name)
        specs[name] = ToolSpec(
            name=name,
            description=fn.description,
            parameters_schema=fn.parameters.model_json_schema(),
            parameters_model=fn.parameters,
            code_hash=compute_tool_code_hash(fn, blake3_fn=blake3_fn),
            kind=entry.kind,
            effect=entry.effect,
            scope=f"agentdojo://{suite_name}/{name}",
        )
    return specs
