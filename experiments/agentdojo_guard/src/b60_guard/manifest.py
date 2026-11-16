"""Provenance manifest and clean-tree verification for campaign runs."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

from b60_guard.effects import load_tool_effect_policy
from b60_guard.native import blake3_hex, resolve_native_library_path


def _repo_root() -> Path:
    return Path(__file__).absolute().parents[4]


def _git_output(args: list[str], cwd: Path) -> str:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    return res.stdout.strip() if res.returncode == 0 else "UNKNOWN"


def campaign_dirty_paths(repo_root: Path | None = None) -> list[str]:
    """Return uncommitted campaign/broker paths (excluding local results/.venv)."""
    root = (repo_root or _repo_root()).absolute()
    res = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            "experiments/agentdojo_guard",
            "src/capability.rs",
            "src/mcp_python.rs",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return ["GIT_STATUS_ERROR"]
    dirty = []
    for line in res.stdout.splitlines():
        path = line[3:].strip()
        if path:
            dirty.append(path)
    return dirty


def build_run_manifest(
    *,
    arm: str,
    suite: str,
    model: str,
    attack: str,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Create a sealed manifest dictionary for a benchmark run."""
    root = _repo_root()
    dirty = campaign_dirty_paths(root)
    if dirty and not allow_dirty:
        raise RuntimeError(f"Refusing benchmark run on dirty campaign paths: {dirty[:5]}")

    lib_path = resolve_native_library_path()
    lib_bytes = lib_path.read_bytes()
    policy = load_tool_effect_policy()
    agentdojo_dist = importlib.metadata.distribution("agentdojo")

    return {
        "arm": arm,
        "suite": suite,
        "model": model,
        "attack": attack,
        "git_commit": _git_output(["rev-parse", "HEAD"], root),
        "campaign_dirty_paths": dirty,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "agentdojo_version": agentdojo_dist.version,
        "benchmark_version": policy.benchmark_version,
        "tool_effects_count": policy.total_tools(),
        "tool_effects_yaml_blake3": policy.blake3_hex,
        "tool_effects_yaml_sha256": policy.sha256_hex,
        "policy_seal_verified": policy.seal_verified,
        "native_library_path": str(lib_path),
        "native_library_blake3": blake3_hex(lib_bytes),
    }


def write_run_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
