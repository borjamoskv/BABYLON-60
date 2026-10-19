#!/usr/bin/env python3
"""Deterministic CycloneDX 1.5 SBOM Generator from Cargo.lock and uv.lock.

Generates reproducible, offline-verifiable Software Bills of Materials (SBOMs)
for both the Rust Ring-0 TCB (`Cargo.lock` -> `sbom.cargo.cdx.json`) and the
Python Ring-1/2 orchestration substrate (`uv.lock` -> `sbom.python.cdx.json`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).absolute().parents[1]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_cargo_cyclonedx(cargo_lock_path: Path) -> Dict[str, Any]:
    """Parse Cargo.lock and return a deterministic CycloneDX 1.5 BOM dict."""
    raw = cargo_lock_path.read_bytes()
    lock_sha256 = _sha256_bytes(raw)
    parsed = tomllib.loads(raw.decode("utf-8"))
    packages: List[Dict[str, Any]] = parsed.get("package", [])

    components: List[Dict[str, Any]] = []
    for pkg in sorted(packages, key=lambda p: (str(p.get("name", "")), str(p.get("version", "")))):
        name = str(pkg.get("name", ""))
        version = str(pkg.get("version", ""))
        checksum = str(pkg.get("checksum", ""))
        source = str(pkg.get("source", "workspace"))
        comp: Dict[str, Any] = {
            "type": "library",
            "bom-ref": f"pkg:cargo/{name}@{version}",
            "name": name,
            "version": version,
            "purl": f"pkg:cargo/{name}@{version}",
            "properties": [{"name": "cargo:source", "value": source}],
        }
        if checksum and len(checksum) == 64:
            comp["hashes"] = [{"alg": "SHA-256", "content": checksum}]
        components.append(comp)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": "pkg:cargo/babylon60_root@5.0.0",
                "name": "babylon60_root",
                "version": "5.0.0",
            },
            "properties": [
                {"name": "babylon60:lockfile", "value": "Cargo.lock"},
                {"name": "babylon60:lockfile_sha256", "value": lock_sha256},
            ],
        },
        "components": components,
    }


def _extract_uv_pkg_sha256(pkg: Dict[str, Any]) -> str:
    sdist = pkg.get("sdist")
    if isinstance(sdist, dict):
        h = str(sdist.get("hash", ""))
        if h.startswith("sha256:"):
            return h.split("sha256:", 1)[1]
    wheels = pkg.get("wheels")
    if isinstance(wheels, list) and wheels:
        first = wheels[0]
        if isinstance(first, dict):
            h = str(first.get("hash", ""))
            if h.startswith("sha256:"):
                return h.split("sha256:", 1)[1]
    return ""


def build_uv_cyclonedx(uv_lock_path: Path) -> Dict[str, Any]:
    """Parse uv.lock and return a deterministic CycloneDX 1.5 BOM dict."""
    raw = uv_lock_path.read_bytes()
    lock_sha256 = _sha256_bytes(raw)
    parsed = tomllib.loads(raw.decode("utf-8"))
    packages: List[Dict[str, Any]] = parsed.get("package", [])

    components: List[Dict[str, Any]] = []
    for pkg in sorted(packages, key=lambda p: (str(p.get("name", "")), str(p.get("version", "")))):
        name = str(pkg.get("name", ""))
        version = str(pkg.get("version", ""))
        sha256_hex = _extract_uv_pkg_sha256(pkg)
        comp: Dict[str, Any] = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{name}@{version}",
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{name}@{version}",
        }
        if sha256_hex and len(sha256_hex) == 64:
            comp["hashes"] = [{"alg": "SHA-256", "content": sha256_hex}]
        components.append(comp)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": "pkg:pypi/babylon60@5.0.0",
                "name": "babylon60",
                "version": "5.0.0",
            },
            "properties": [
                {"name": "babylon60:lockfile", "value": "uv.lock"},
                {"name": "babylon60:lockfile_sha256", "value": lock_sha256},
            ],
        },
        "components": components,
    }


def generate_sboms(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> Dict[str, Any]:
    """Generate both CycloneDX SBOM files and return summary metadata."""
    target_dir = output_dir if output_dir is not None else repo_root
    target_dir.mkdir(parents=True, exist_ok=True)

    cargo_bom = build_cargo_cyclonedx(repo_root / "Cargo.lock")
    cargo_bytes = (json.dumps(cargo_bom, indent=2, sort_keys=True) + "\n").encode("utf-8")
    cargo_out = target_dir / "sbom.cargo.cdx.json"
    cargo_out.write_bytes(cargo_bytes)

    uv_bom = build_uv_cyclonedx(repo_root / "uv.lock")
    uv_bytes = (json.dumps(uv_bom, indent=2, sort_keys=True) + "\n").encode("utf-8")
    uv_out = target_dir / "sbom.python.cdx.json"
    uv_out.write_bytes(uv_bytes)

    return {
        "format": "CycloneDX-1.5",
        "cargo_sbom_path": str(cargo_out.relative_to(repo_root))
        if cargo_out.is_relative_to(repo_root)
        else str(cargo_out),
        "cargo_sbom_sha256": _sha256_bytes(cargo_bytes),
        "cargo_components": len(cargo_bom["components"]),
        "python_sbom_path": str(uv_out.relative_to(repo_root)) if uv_out.is_relative_to(repo_root) else str(uv_out),
        "python_sbom_sha256": _sha256_bytes(uv_bytes),
        "python_components": len(uv_bom["components"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CycloneDX 1.5 SBOMs for BABYLON-60")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    summary = generate_sboms(repo_root=args.repo_root.absolute(), output_dir=args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
