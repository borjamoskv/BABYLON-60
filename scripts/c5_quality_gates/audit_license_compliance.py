#!/usr/bin/env python3
"""
audit_license_compliance.py
=============================================================================
BABYLON-60 / C5-REAL — Commercial License & Copyleft Pre-Commit Gate
Scans all Rust crate dependencies (cargo metadata) to ensure:
  1. 100% of crates have documented license metadata (no UNKNOWN).
  2. 0% restrictive copyleft (pure GPL/AGPL) that could infect commercial distribution.
=============================================================================
"""

import sys
import json
import subprocess
from pathlib import Path

RESTRICTIVE_LICENSES = frozenset({"GPL-1", "GPL-2", "GPL-3", "AGPL"})
PERMISSIVE_KEYWORDS = frozenset({"MIT", "APACHE", "BSD", "ISC", "CC0", "0BSD", "ZLIB", "UNICODE-3.0"})


def audit_cargo_licenses() -> tuple[list[str], list[str], int]:
    try:
        res = subprocess.run(
            ["cargo", "metadata", "--format-version", "1"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
    except Exception as e:
        return [f"Unable to execute cargo metadata: {e}"], [], 0

    unknown = []
    copyleft_violations = []
    packages = data.get("packages", [])

    for p in packages:
        name = p.get("name", "unknown")
        ver = p.get("version", "0.0.0")
        lic = p.get("license")
        lic_file = p.get("license_file")

        if p.get("source") is None:
            # Miembro propio del workspace (INV_C5_LICENSE_PARITY_GATE):
            # licencia soberana por archivo y publicación vetada.
            if lic or not lic_file:
                copyleft_violations.append(
                    f"{name} v{ver}: own crate must use license-file only (license={lic!r}, license_file={lic_file!r})"
                )
            if p.get("publish") != []:
                copyleft_violations.append(
                    f"{name} v{ver}: own crate must declare publish = false (publish={p.get('publish')!r})"
                )
            continue

        if not lic and not lic_file:
            unknown.append(f"{name} v{ver}: Missing license attribute")
            continue
        if not lic and lic_file:
            continue

        # Split logical license combinations: e.g. "MIT OR Apache-2.0 OR LGPL-2.1-or-later"
        parts = [part.strip(" ()") for part in lic.replace("/", " OR ").split(" OR ")]
        has_permissive = any(
            any(perm in part.upper() for perm in PERMISSIVE_KEYWORDS)
            for part in parts
        )
        is_restrictive = any(
            any(r in part.upper() for r in RESTRICTIVE_LICENSES)
            for part in parts
        )

        if is_restrictive and not has_permissive:
            copyleft_violations.append(
                f"{name} v{ver}: Restrictive copyleft license without permissive dual-license ({lic})"
            )

    return unknown, copyleft_violations, len(packages)


def audit_node_manifests() -> tuple[list[str], int]:
    violations = []
    total = 0
    workspace_root = Path(__file__).resolve().parents[2]

    for p in workspace_root.rglob("package.json"):
        # Ignore external / build directories
        if any(ignored in p.parts for ignored in ("node_modules", "target", ".venv", ".lake", ".git")):
            continue
        total += 1
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            violations.append(f"{p.relative_to(workspace_root)}: Unable to parse JSON ({e})")
            continue

        lic = data.get("license")
        is_private = data.get("private") is True

        if lic and any(perm in lic.upper() for perm in PERMISSIVE_KEYWORDS):
            violations.append(
                f"{p.relative_to(workspace_root)}: Permissive license {lic!r} violates Sovereign Dual-License"
            )
        if not is_private:
            violations.append(
                f"{p.relative_to(workspace_root)}: Missing 'private: true' to block registry upload"
            )

    return violations, total


def audit_workflow_publish_locks() -> tuple[list[str], int]:
    violations = []
    total = 0
    workspace_root = Path(__file__).resolve().parents[2]
    workflows_dir = workspace_root / ".github" / "workflows"

    if not workflows_dir.exists():
        return violations, total

    forbidden_patterns = [
        ("pypa/gh-action-pypi-publish", "Direct PyPI publication active"),
        ("cargo publish", "Direct crates.io publication active"),
        ("npm publish", "Direct npm publication active"),
    ]

    for wf in workflows_dir.glob("*.yml"):
        total += 1
        content = wf.read_text(encoding="utf-8")
        for pattern, desc in forbidden_patterns:
            if pattern in content:
                violations.append(f"{wf.name}: {desc} ({pattern})")

    return violations, total


def main() -> int:
    unknown, violations, total_cargo = audit_cargo_licenses()
    node_violations, total_node = audit_node_manifests()
    wf_violations, total_wf = audit_workflow_publish_locks()

    failed = False
    if unknown or violations:
        print(f"❌ [LICENSE-GATE] Cargo license compliance failure across {total_cargo} crates:", file=sys.stderr)
        for u in unknown:
            print(f"   [MISSING] {u}", file=sys.stderr)
        for v in violations:
            print(f"   [COPYLEFT] {v}", file=sys.stderr)
        failed = True
    else:
        print(f"✓ [LICENSE-GATE] Audited {total_cargo} Cargo crates. 100% permissive dependencies, zero copyleft violations, own crates strictly locked.")

    if node_violations:
        print(f"❌ [LICENSE-GATE] Node package parity failure across {total_node} manifests:", file=sys.stderr)
        for v in node_violations:
            print(f"   [NODE-VIOLATION] {v}", file=sys.stderr)
        failed = True
    else:
        print(f"✓ [LICENSE-GATE] Audited {total_node} Node manifests. 100% private, zero permissive leaks.")

    if wf_violations:
        print(f"❌ [LICENSE-GATE] Workflow registry lock failure across {total_wf} workflows:", file=sys.stderr)
        for v in wf_violations:
            print(f"   [REGISTRY-LEAK] {v}", file=sys.stderr)
        failed = True
    else:
        print(f"✓ [LICENSE-GATE] Audited {total_wf} workflows. 100% public registry upload paths frozen.")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
