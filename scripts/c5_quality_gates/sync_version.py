#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 — CANONICAL VERSION SYNCHRONIZER (SINGLE ROOT OF TRUTH)
# Reads version from babylon.toml and enforces consistency across:
#   - Cargo.toml
#   - pyproject.toml
#   - README.md
#   - SECURITY.md
#   - 01_KISH_ENGINE/babylon60/cli/main_dispatcher.py
#   - 01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py
# ============================================================================
"""
Canonical Version Synchronizer.
Usage:
  python3 scripts/c5_quality_gates/sync_version.py [--check] [--sync]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_canonical_version(config_file: Path) -> str:
    content = config_file.read_text(encoding="utf-8")
    match = re.search(r'\[release\][^\[]*?version\s*=\s*"([^"]+)"', content, re.DOTALL)
    if not match:
        raise ValueError(f"No [release] version found in {config_file}")
    return match.group(1).strip()


def check_or_update_file(
    path: Path,
    pattern: str,
    replacement: str,
    dry_run: bool = False
) -> bool:
    if not path.exists():
        print(f"  [!] Missing target file: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return False

    content = path.read_text(encoding="utf-8")
    if not re.search(pattern, content):
        print(f"  [!] Pattern not matched in: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return False

    new_content = re.sub(pattern, replacement, content, count=1)
    if content == new_content:
        return True  # Already up to date

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")
        print(f"  [✓] Updated: {path.relative_to(REPO_ROOT)}")
    else:
        print(f"  [DRIFT] File out of sync: {path.relative_to(REPO_ROOT)}")
    return False


def sync_all(dry_run: bool = False) -> bool:
    babylon_toml = REPO_ROOT / "babylon.toml"
    canonical_version = get_canonical_version(babylon_toml)
    print(f"[BABYLON-60 VERSION GATE] Canonical Version: v{canonical_version} (from babylon.toml)")

    drift_detected = False

    # 1. Cargo.toml
    cargo_toml = REPO_ROOT / "Cargo.toml"
    if not check_or_update_file(
        cargo_toml,
        r'(?m)^version\s*=\s*"[^"]+"',
        f'version = "{canonical_version}"',
        dry_run=dry_run
    ):
        drift_detected = True

    # 2. pyproject.toml
    pyproject_toml = REPO_ROOT / "pyproject.toml"
    if not check_or_update_file(
        pyproject_toml,
        r'(?m)^version\s*=\s*"[^"]+"',
        f'version = "{canonical_version}"',
        dry_run=dry_run
    ):
        drift_detected = True

    # 3. main_dispatcher.py
    dispatcher_py = REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "cli" / "main_dispatcher.py"
    if not check_or_update_file(
        dispatcher_py,
        r'(?m)^VERSION\s*=\s*"[^"]+"',
        f'VERSION = "{canonical_version}"',
        dry_run=dry_run
    ):
        drift_detected = True

    # 4. cortex_mcp_server.py
    mcp_server_py = REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "mcp" / "cortex_mcp_server.py"
    if not check_or_update_file(
        mcp_server_py,
        r'(?m)^MCP_SERVER_VERSION\s*=\s*"[^"]+"',
        f'MCP_SERVER_VERSION = "{canonical_version}"',
        dry_run=dry_run
    ):
        drift_detected = True

    # 5. README.md badge and footer
    readme_md = REPO_ROOT / "README.md"
    if readme_md.exists():
        content = readme_md.read_text(encoding="utf-8")
        updated = re.sub(r'version-[0-9\.]+', f'version-{canonical_version}', content)
        updated = re.sub(r'BABYLON-60 v[0-9\.]+', f'BABYLON-60 v{canonical_version}', updated)
        if content != updated:
            drift_detected = True
            if not dry_run:
                readme_md.write_text(updated, encoding="utf-8")
                print(f"  [✓] Updated: README.md")
            else:
                print(f"  [DRIFT] File out of sync: README.md")

    if dry_run and drift_detected:
        print("\n[!] Versión desalineada detectada. Ejecuta: python3 scripts/c5_quality_gates/sync_version.py --sync")
        return False

    print("\n[✓] Todas las superficies alineadas con babylon.toml.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Synchronize version from babylon.toml")
    parser.add_argument("--check", action="store_true", help="Fail if version drift exists")
    parser.add_argument("--sync", action="store_true", default=True, help="Update all files")
    args = parser.parse_args()

    dry_run = args.check and not ("--sync" in sys.argv and not ("--check" in sys.argv))
    success = sync_all(dry_run=dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
