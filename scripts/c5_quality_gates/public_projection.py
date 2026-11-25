"""Read-only parser for the bounded public projection manifest (fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_REL_PATH = Path(".github/public_projection_manifest.json")
SCHEMA_VERSION = "BABYLON60:PUBLIC_PROJECTION:v1"
ALLOWED_OMITTED_PREFIXES = frozenset(
    {
        ".agents/rules",
        "docs/security/evidence",
        "tools/skill_library",
    }
)


def load_omitted_prefixes(repo_root: Path) -> frozenset[str]:
    """Return explicitly declared omitted prefixes, or empty set in VAULT.

    Malformed manifests, undeclared prefixes, or declared prefixes still
    present on disk fail closed with ValueError.
    """
    manifest = repo_root / MANIFEST_REL_PATH
    if not manifest.is_file():
        return frozenset()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"{manifest}: invalid public projection schema")
    omitted = payload.get("omitted_prefixes")
    if not isinstance(omitted, list) or not all(isinstance(item, str) for item in omitted):
        raise ValueError(f"{manifest}: omitted_prefixes must be a list of strings")
    result = frozenset(omitted)
    unknown = result - ALLOWED_OMITTED_PREFIXES
    if unknown:
        raise ValueError(f"{manifest}: unsupported omitted prefixes: {sorted(unknown)}")
    for prefix in result:
        if (repo_root / prefix).exists():
            raise ValueError(f"{manifest}: prefix declared omitted is present on disk: {prefix}")
    return result
