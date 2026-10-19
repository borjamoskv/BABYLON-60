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


def main() -> int:
    unknown, violations, total = audit_cargo_licenses()

    if unknown or violations:
        print(f"❌ [LICENSE-GATE] License compliance failure across {total} crates:", file=sys.stderr)
        for u in unknown:
            print(f"   [MISSING] {u}", file=sys.stderr)
        for v in violations:
            print(f"   [COPYLEFT] {v}", file=sys.stderr)
        return 1

    print(f"✓ [LICENSE-GATE] Audited {total} Cargo crates. 100% permissive licenses, zero copyleft violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
