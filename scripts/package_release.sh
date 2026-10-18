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
required = ["install.sh", "scripts/package_release.sh", "pyproject.toml", "uv.lock", "README.md", "LICENSE"]
packages = ["01_KISH_ENGINE/babylon60", "02_EDIN_SWARMS/agents_archi"]
for name in required + packages:
    if not (root / name).exists():
        raise SystemExit(f"Missing release input: {name}")
files = [root / name for name in required]
for name in packages:
    for directory, dirs, names in os.walk(root / name, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in
                         {"__pycache__", "target", "dist", "build", "scratch"}
                         and not (Path(directory) / d).is_symlink())
        for filename in sorted(names):
            path = Path(directory) / filename
            if filename.startswith('.') or path.is_symlink() or path.suffix in {".pyc", ".db", ".db-wal", ".db-shm", ".vtt"}:
                continue
            if path.is_file():
                files.append(path)
for guide in ["docs/03_guides/guide_signed_authorization.md"]:
    if (root / guide).is_file():
        files.append(root / guide)
destination.mkdir(parents=True, exist_ok=True)
output = destination / "Babylon60-v5.0.0-terminal-mcp.zip"
# Atomic publication prevents a failed build replacing a working bundle.
with tempfile.NamedTemporaryFile(dir=destination, suffix=".zip", delete=False) as temporary:
    temp_path = Path(temporary.name)
try:
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(files):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if path.name == "install.sh" else 0o100644) << 16
            bundle.writestr(info, path.read_bytes())
    temp_path.replace(output)
finally:
    temp_path.unlink(missing_ok=True)
print(output)
PY
