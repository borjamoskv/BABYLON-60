#!/usr/bin/env bash
# Build a terminal/MCP source release, without invoking installers or desktop apps.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -L)"
LIST_ONLY=0
DIST_DIR="$REPO_ROOT/dist"
if [[ "${1:-}" == "--list-files" ]]; then
  LIST_ONLY=1
elif [[ -n "${1:-}" ]]; then
  DIST_DIR="$1"
fi
python3 - "$REPO_ROOT" "$DIST_DIR" "$LIST_ONLY" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

root = Path(sys.argv[1]).absolute()
destination = Path(sys.argv[2]).absolute()
list_only = sys.argv[3] == "1"

GENERATED_EVIDENCE = {
    "evidence.json",
    "claims.lock",
    "RELEASE_MANIFEST.json",
    "RELEASE_MANIFEST.json.sig",
    "RELEASE_MANIFEST.json.ots",
    "evidence.json.ots",
    "sbom.cargo.cdx.json",
    "sbom.python.cdx.json",
    "scripts/c5_quality_gates/claims_sitrep.json",
    ".github/public_projection_manifest.json",
}
VAULT_ONLY_PREFIXES = (
    ".agents/rules/",
    ".agents/mcp_config.json",
    ".playwright-mcp/",
    "docs/security/evidence/",
    "tools/skill_library/",
    "tests/test_project_skills_regressions.py",
    "tests/test_regulatory_native_evidence.py",
    "tests/test_regulatory_native_validation.py",
    "tests/test_skill_intent_routing.py",
    "tests/test_skill_library_convergence.py",
    "tests/test_skill_maintenance.py",
    "tests/test_swarm100_lot1_private_skill_regressions.py",
    "tests/test_swarm100_lot2_private_skill_regressions.py",
    "tests/test_swarm100_lot2_regressions.py",
    "tests/test_swarm100_lot12_s5_yt_regressions.py",
    "tests/test_swarm100_round2_private_skill_regressions.py",
    "assets/brand/github-art-brut.svg",
    "assets/AppIcon.icns",
    "assets/babylon60_brutalist_logo_1024.png",
)


def is_excluded_from_public_tree(relative: str) -> bool:
    return relative in GENERATED_EVIDENCE or relative.startswith(VAULT_ONLY_PREFIXES)


required = [
    "install.sh", "install.ps1", "scripts/package_release.sh",
    "scripts/c5_quality_gates/experience_pilot.py",
    "scripts/c5_quality_gates/prompt_exergy_oracle.py",
    "babylon.toml", "Cargo.toml", "Cargo.lock", "WHY_BABYLON_60.md",
    "pyproject.toml", "uv.lock", "README.md", "README_ES.md", "LICENSE", "docs/skills.json", "docs/skills-lock.json",
    "docs/03_guides/README_REFERENCE.md", "docs/03_guides/README_REFERENCE_ES.md",
    "SECURITY.md", "CITATION.cff", "docs/COMMERCIAL_LICENSE.md", "assets/brand/github-art-brut.png",
    ".babylon60rules", "AGENTS.md", "docs/03_guides/agent_contracts.md",
    "docs/03_guides/guide_portable_signature.md", "docs/03_guides/guide_agent_workflow.md",
    # Target of the "Matriz de Falsación" links in agent_contracts.md.
    "docs/01_spec/INVARIANTS_RED_TEAM_FALSIFICATION.md",
    "src/ffi.rs",
    "src/shared_manifest_core.rs",
    "src/ffi_oracle.rs",
    "src/larsa_bft.rs",
    "00_ABZU_KERNEL/crates/babylon60-kernel/src/shared_manifest.rs",
]
packages = ["01_KISH_ENGINE/babylon60", "02_EDIN_SWARMS/agents_archi", ".agents/skills"]
# Keep retired namespaces excluded when packaging an older source checkout.
# Independent examples/experiments are outside the selected release packages.
oncology_excludes = {
    "01_KISH_ENGINE/babylon60/oncology_primitives.py",
    "01_KISH_ENGINE/babylon60/cli/onco_transducer.py",
    "01_KISH_ENGINE/babylon60/genomics",
}
def git_ignored(candidates):
    """Walked files that git ignores: local build outputs, never release inputs.

    A developer tree can hold compiled artifacts inside a package directory;
    listing them yields an inventory no clean checkout can reproduce. Outside a
    git checkout (an extracted release) every walked file is already an input.
    """
    if not candidates or not (root / ".git").exists():
        return set()
    relatives = [path.relative_to(root).as_posix() for path in candidates]
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-z", "--stdin"],
            input="\0".join(relatives),
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise SystemExit(f"Cannot ask git which release inputs are ignored: {error}")
    if done.returncode not in (0, 1):  # 0: some ignored, 1: none, anything else: git failed
        raise SystemExit(f"git check-ignore failed: {done.stderr.strip()}")
    return {root / relative for relative in done.stdout.split("\0") if relative}


for name in required + packages:
    if not (root / name).exists():
        raise SystemExit(f"Missing release input: {name}")
files = [root / name for name in required]
walked = []
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
                walked.append(path)
ignored = git_ignored(walked)
files.extend(path for path in walked if path not in ignored)
for guide in [
    "verify.sh",
    "scripts/verify_release.sh",
    "RELEASE_MANIFEST.json",
    "RELEASE_MANIFEST.json.sig",
    "evidence.json",
    "claims.lock",
    "CLAIMS.toml",
    "sbom.cargo.cdx.json",
    "sbom.python.cdx.json",
    "docs/security/governance-comparison-2026-10-24.md",
    "docs/03_guides/guide_signed_authorization.md",
    "docs/03_guides/guide_codex_first_use.md",
    "docs/03_guides/guide_first_conversation_pilot.md",
    "docs/03_guides/BEFORE_AND_AFTER.md",
    "docs/03_guides/USER_GUIDE.md",
]:
    if (root / guide).is_file():
        files.append(root / guide)

sorted_files = sorted(set(files))
source_files = [path.relative_to(root).as_posix() for path in sorted_files]

if list_only:
    for rel in source_files:
        print(rel)
    raise SystemExit(0)

output = destination / "Babylon60-v5.1.0-terminal-mcp.zip"


def bundle_tree_digest() -> str:
    digest = hashlib.sha256()
    for path, rel in zip(sorted_files, source_files):
        if is_excluded_from_public_tree(rel):
            continue
        payload = path.read_bytes()
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def manifest_payload_for_zip(raw_bytes: bytes) -> bytes:
    """Keep signed manifests byte-identical; populate unsigned release_bundle inventory."""
    manifest = json.loads(raw_bytes.decode("utf-8"))
    if manifest.get("signature") is not None:
        return raw_bytes
    bundle_doc = manifest.get("release_bundle")
    if isinstance(bundle_doc, dict) and isinstance(bundle_doc.get("source_files"), list) and bundle_doc.get("tree_digest"):
        return raw_bytes
    manifest["release_bundle"] = {
        "name": output.name,
        "tree_digest": bundle_tree_digest(),
        "source_files": source_files,
    }
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


destination.mkdir(parents=True, exist_ok=True)
# Atomic publication prevents a failed build replacing a working bundle.
with tempfile.NamedTemporaryFile(dir=destination, suffix=".zip", delete=False) as temporary:
    temp_path = Path(temporary.name)
try:
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path, rel in zip(sorted_files, source_files):
            info = zipfile.ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if path.name in {"install.sh", "verify.sh", "verify_release.sh"} else 0o100644) << 16
            payload = manifest_payload_for_zip(path.read_bytes()) if rel == "RELEASE_MANIFEST.json" else path.read_bytes()
            bundle.writestr(info, payload)
    temp_path.replace(output)
finally:
    temp_path.unlink(missing_ok=True)
print(output)
PY
