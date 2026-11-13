#!/usr/bin/env bash
# Build a terminal/MCP source release, without invoking installers or desktop apps.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -L)"
DIST_DIR="${1:-$REPO_ROOT/dist}"
python3 - "$REPO_ROOT" "$DIST_DIR" <<'PY'
import os
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import zipfile

root = Path(sys.argv[1]).absolute()
destination = Path(sys.argv[2]).absolute()
required = [
    "install.sh", "install.ps1", "scripts/package_release.sh",
    "scripts/c5_quality_gates/experience_pilot.py",
    "scripts/c5_quality_gates/prompt_exergy_oracle.py",
    "babylon.toml", "Cargo.toml", "Cargo.lock", "WHY_BABYLON_60.md",
    "pyproject.toml", "uv.lock", "README.md", "LICENSE", "docs/skills.json", "docs/skills-lock.json",
    ".babylon60rules", "AGENTS.md", "docs/03_guides/agent_contracts.md",
    "docs/03_guides/guide_portable_signature.md", "docs/03_guides/guide_agent_workflow.md",
    # Target of the "Matriz de Falsación" links in agent_contracts.md.
    "docs/01_spec/INVARIANTS_RED_TEAM_FALSIFICATION.md",
]
packages = ["01_KISH_ENGINE/babylon60", "02_EDIN_SWARMS/agents_archi", ".agents/skills"]
# Keep retired namespaces excluded when packaging an older source checkout.
# Independent examples/experiments are outside the selected release packages.
oncology_excludes = {
    "01_KISH_ENGINE/babylon60/oncology_primitives.py",
    "01_KISH_ENGINE/babylon60/cli/onco_transducer.py",
    "01_KISH_ENGINE/babylon60/genomics",
}
for name in required + packages:
    if not (root / name).exists():
        raise SystemExit(f"Missing release input: {name}")
files = [root / name for name in required]
for name in packages:
    for directory, dirs, names in os.walk(root / name, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in
                         {"__pycache__", "target", "dist", "build", "scratch"}
                         and (Path(directory) / d).relative_to(root).as_posix() not in oncology_excludes
                         and not (Path(directory) / d).is_symlink())
        for filename in sorted(names):
            path = Path(directory) / filename
            if path.relative_to(root).as_posix() in oncology_excludes:
                continue
            if filename.startswith('.') or path.is_symlink() or path.suffix in {".pyc", ".db", ".db-wal", ".db-shm", ".vtt"}:
                continue
            if path.is_file():
                files.append(path)
for guide in [
    "verify.sh",
    "scripts/verify_release.sh",
    "CLAIMS.toml",
    "docs/security/governance-comparison-2026-10-24.md",
    "docs/03_guides/guide_signed_authorization.md",
    "docs/03_guides/guide_codex_first_use.md",
    "docs/03_guides/guide_first_conversation_pilot.md",
]:
    if (root / guide).is_file():
        files.append(root / guide)
destination.mkdir(parents=True, exist_ok=True)
version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
if not isinstance(version, str) or not re.fullmatch(r"[0-9][A-Za-z0-9.+-]*", version):
    raise SystemExit("Invalid release version")
output = destination / f"Babylon60-v{version}-terminal-mcp.zip"
# Capture each input once: the inventory describes the bytes actually archived.
# Release attestations are generated AFTER this ZIP and distributed beside it;
# embedding an older manifest would bind the archive to a different artifact.
payloads = {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(set(files))}
source_commit = None
source_state = "unversioned"
if (root / ".git").exists():
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    # Producing detached evidence must not change the next source archive.
    detached_evidence = {
        "RELEASE_MANIFEST.json", "RELEASE_MANIFEST.json.sig", "RELEASE_MANIFEST.json.ots",
        "evidence.json", "evidence.json.ots", "claims.lock", "sbom.cargo.cdx.json", "sbom.python.cdx.json",
        "scripts/c5_quality_gates/claims_sitrep.json",
    }
    changed_paths = subprocess.check_output(["git", "diff", "HEAD", "--name-only", "-z"], cwd=root).split(b"\0")
    untracked_paths = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root).split(b"\0")
    changed = any(name and os.fsdecode(name) not in detached_evidence for name in changed_paths)
    changed = changed or any(os.fsdecode(name) in payloads for name in untracked_paths if name)
    source_state = "modified" if changed else "clean"
inventory = {
    "format": "babylon60.source-bundle.v1",
    "version": version,
    "source_commit": source_commit,
    "source_state": source_state,
    "authority": "unsigned_content_inventory",
    "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()},
}
payloads["SOURCE_MANIFEST.json"] = (json.dumps(inventory, sort_keys=True, indent=2) + "\n").encode("utf-8")
# Atomic publication prevents a failed build replacing a working bundle.
with tempfile.NamedTemporaryFile(dir=destination, suffix=".zip", delete=False) as temporary:
    temp_path = Path(temporary.name)
try:
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if Path(name).name in {"install.sh", "verify.sh", "verify_release.sh"} else 0o100644) << 16
            bundle.writestr(info, data)
    temp_path.replace(output)
finally:
    temp_path.unlink(missing_ok=True)
print(output)
PY
