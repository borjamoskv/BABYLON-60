#!/usr/bin/env bash
# Build a terminal/MCP source release, without invoking installers or desktop apps.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -L)"
DIST_DIR="${1:-$REPO_ROOT/dist}"
python3 - "$REPO_ROOT" "$DIST_DIR" <<'PY'
import os
from pathlib import Path
import sys
import tempfile
import zipfile

root = Path(sys.argv[1]).absolute()
destination = Path(sys.argv[2]).absolute()
required = [
    "install.sh", "install.ps1", "scripts/package_release.sh",
    "scripts/c5_quality_gates/experience_pilot.py",
    "scripts/c5_quality_gates/prompt_exergy_oracle.py",
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
    "docs/security/governance-comparison-2026-10-24.md",
    "docs/03_guides/guide_signed_authorization.md",
    "docs/03_guides/guide_codex_first_use.md",
    "docs/03_guides/guide_first_conversation_pilot.md",
]:
    if (root / guide).is_file():
        files.append(root / guide)
destination.mkdir(parents=True, exist_ok=True)
output = destination / "Babylon60-v5.1.0-terminal-mcp.zip"
# Atomic publication prevents a failed build replacing a working bundle.
with tempfile.NamedTemporaryFile(dir=destination, suffix=".zip", delete=False) as temporary:
    temp_path = Path(temporary.name)
try:
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(files):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if path.name in {"install.sh", "verify.sh", "verify_release.sh"} else 0o100644) << 16
            bundle.writestr(info, path.read_bytes())
    temp_path.replace(output)
finally:
    temp_path.unlink(missing_ok=True)
print(output)
PY
