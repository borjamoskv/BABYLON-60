#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 — EVIDENCE & RELEASE MANIFEST COMPILER (v5.0)
# Machine-Readable Epistemology:
#   CLAIMS.toml -> Tests & Evidence -> evidence.json -> claims.lock ->
#   SHA3-256 Merkle Root -> Ed25519 Signed RELEASE_MANIFEST.json
# ============================================================================
"""
Evidence & Release Manifest Compiler.
Usage:
  python3 scripts/c5_quality_gates/compile_claims_manifest.py [--fresh]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(REPO_ROOT / "01_KISH_ENGINE"))

from babylon60.bft.cortex_crypto_kernel import build_merkle_tree  # noqa: E402

sys.path.insert(0, str(REPO_ROOT))
from scripts.c5_quality_gates.verify_claims import (  # noqa: E402
    audit_invariants_alignment,
    is_excluded_from_public_tree,
    source_tree_digest,
)

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: E402


def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def load_babylon_release_spec() -> Dict[str, Any]:
    babylon_toml = REPO_ROOT / "babylon.toml"
    if not babylon_toml.exists():
        raise FileNotFoundError("babylon.toml not found")
    data = tomllib.loads(babylon_toml.read_text(encoding="utf-8"))
    return dict(data.get("release", {}))


MANIFEST_SCHEMA = "babylon60.release.v5"

# Raíces de gobierno cuyo digest se expone individualmente. source_tree_digest
# ya vincula todos los archivos rastreados; esta lista solo facilita la lectura.
RELEASE_ARTIFACTS = (
    ".babylon60rules",
    "CLAIMS.toml",
    "babylon.toml",
    "Cargo.toml",
    "Cargo.lock",
    "pyproject.toml",
    "uv.lock",
    "LICENSE",
    "README.md",
    "WHY_BABYLON_60.md",
)


def _toml_version(path: Path, *keys: str) -> str | None:
    if not path.is_file():
        return None
    node: Any = tomllib.loads(path.read_text(encoding="utf-8"))
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return str(node) if isinstance(node, str) else None


def collect_version_sync(version: str) -> Dict[str, str | None]:
    """Lee la versión declarada en cada superficie y falla si alguna diverge."""
    surfaces: Dict[str, str | None] = {
        "babylon_toml": version,
        "claims_toml": _toml_version(REPO_ROOT / "CLAIMS.toml", "metadata", "version"),
        "cargo_workspace": _toml_version(REPO_ROOT / "Cargo.toml", "workspace", "package", "version"),
        "pyproject": _toml_version(REPO_ROOT / "pyproject.toml", "project", "version"),
    }
    drift = {name: value for name, value in surfaces.items() if value is not None and value != version}
    if drift:
        raise ValueError(f"Version drift against babylon.toml {version}: {drift}")
    return surfaces


def collect_artifact_digests() -> Dict[str, str]:
    digests: Dict[str, str] = {}
    for relative in RELEASE_ARTIFACTS:
        path = REPO_ROOT / relative
        if path.is_file():
            digests[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def load_prior_release() -> Dict[str, Any] | None:
    """Encadena con el manifiesto anterior antes de sobrescribirlo."""
    path = REPO_ROOT / "RELEASE_MANIFEST.json"
    if not path.is_file():
        return None
    raw = path.read_bytes()
    previous = json.loads(raw)
    return {
        "version": previous.get("version", previous.get("release")),
        "commit": previous.get("commit", previous.get("prior_commit")),
        "manifest_schema": previous.get("manifest_schema"),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }


def compile_claims_evidence(run_fresh: bool = False) -> Dict[str, Any]:
    claims_sitrep_path = REPO_ROOT / "scripts" / "c5_quality_gates" / "claims_sitrep.json"

    if run_fresh or not claims_sitrep_path.exists():
        print("[COMPILER] Ejecutando verificación fresca de claims en silicio...")
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "c5_quality_gates" / "verify_claims.py")],
            cwd=REPO_ROOT,
            check=True,
        )

    sitrep = json.loads(claims_sitrep_path.read_text(encoding="utf-8"))
    claims_list: List[Dict[str, Any]] = sitrep.get("claims", [])
    manifest_path = REPO_ROOT / "CLAIMS.toml"
    full_manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    declared = full_manifest["claim"]
    declared_invariants = full_manifest.get("invariants", {})
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    ids = [claim["id"] for claim in claims_list]
    if sitrep.get("source_commit") != get_git_commit():
        raise ValueError("Claim evidence does not match the current clean source commit")
    if sitrep.get("source_tree_digest") != source_tree_digest(REPO_ROOT):
        raise ValueError("Tracked source changed after claim verification")
    if sitrep.get("claims_manifest_digest") != manifest_digest:
        raise ValueError("Claim evidence does not match CLAIMS.toml")
    if len(ids) != len(set(ids)) or set(ids) != set(declared):
        raise ValueError("Claim evidence is incomplete or contains duplicate claims")
    if sitrep.get("failed_claims") or any(
        not bool(c.get("suite_passed", c.get("verified", False))) for c in claims_list
    ):
        raise ValueError("Cannot publish release evidence with failed claims")
    inv_alignment_errors = sitrep.get("invariant_alignment_errors")
    if inv_alignment_errors:
        raise ValueError(
            "Cannot publish release evidence with invariant alignment errors: "
            + "; ".join(str(err) for err in inv_alignment_errors)
        )
    if isinstance(declared_invariants, dict) and declared_invariants:
        sitrep_invariants = sitrep.get("invariants")
        if not isinstance(sitrep_invariants, list):
            raise ValueError("Invariant evidence is missing from claims_sitrep.json")
        inv_keys = [inv.get("key") for inv in sitrep_invariants if isinstance(inv, dict)]
        if (
            len(inv_keys) != len(sitrep_invariants)
            or len(inv_keys) != len(set(inv_keys))
            or set(inv_keys) != set(declared_invariants)
        ):
            raise ValueError("Invariant evidence is incomplete or contains duplicate invariants")
        if any(not bool(inv.get("gate_aligned", False)) for inv in sitrep_invariants):
            raise ValueError("Cannot publish release evidence with unaligned [invariants.*]")
        release_spec = load_babylon_release_spec()
        _, inv_errors = audit_invariants_alignment(full_manifest, release_spec)
        if inv_errors:
            raise ValueError(
                "Invariant alignment failure between CLAIMS.toml [invariants.*] and babylon.toml: "
                + "; ".join(inv_errors)
            )

    evidence_entries = []
    merkle_leaves = []

    for c in claims_list:
        cid = c["id"]
        status = c["status"]
        stmt = c["statement"]
        component = c.get("component", "UNKNOWN")
        dur = c.get("duration_s", 0.0)
        suite_passed = bool(c.get("suite_passed", c.get("verified", False)))
        verified_flag = bool(c.get("verified", False)) and status == "verified"

        # Digest determinista del claim + estado verificado (sin jitter de reloj duration_s)
        canonical_claim_repr = f"{cid}:{component}:{status}:{suite_passed}:{stmt}"
        leaf_hash = hashlib.sha3_256(canonical_claim_repr.encode("utf-8")).hexdigest()
        merkle_leaves.append(leaf_hash)

        evidence_entries.append(
            {
                "id": cid,
                "component": component,
                "statement": stmt,
                "status": status,
                "verified": verified_flag,
                "suite_passed": suite_passed,
                "duration_s": dur,
                "leaf_hash": leaf_hash,
            }
        )

    if merkle_leaves:
        merkle_root = build_merkle_tree(merkle_leaves)
    else:
        merkle_root = "0" * 64

    failed_count = sum(1 for e in evidence_entries if not e["suite_passed"])
    raw_ts = sitrep.get("timestamp")
    timestamp_iso = (
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(raw_ts)))
        if isinstance(raw_ts, (int, float))
        else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )

    return {
        "timestamp_iso": timestamp_iso,
        "source_commit": sitrep["source_commit"],
        "source_tree_digest": sitrep["source_tree_digest"],
        "claims_manifest_digest": manifest_digest,
        "environment_digest": sitrep["environment_digest"],
        "total_claims": len(claims_list),
        "verified_count": sitrep.get("verified", 0),
        "partial_count": sitrep.get("partial", 0),
        "experimental_count": sitrep.get("experimental", 0),
        "failed_count": failed_count,
        "merkle_evidence_root": f"sha3-256:{merkle_root}",
        "evidence_entries": evidence_entries,
    }


def _load_signing_key() -> ed25519.Ed25519PrivateKey | None:
    """Sign only with an explicitly provisioned key; never derive a public seed."""
    configured = os.environ.get("BABYLON_RELEASE_SIGNING_KEY")
    key_file = Path(configured) if configured else REPO_ROOT / "keys" / "release_ed25519.Seed"
    if not key_file.exists():
        if configured:
            raise FileNotFoundError(key_file)
        return None
    raw_seed = bytes.fromhex(key_file.read_text(encoding="utf-8").strip())
    return ed25519.Ed25519PrivateKey.from_private_bytes(raw_seed)


def _bundle_tree_digest(entries: List[Tuple[str, bytes]]) -> str:
    """Compute the same deterministic SHA-256 tree digest expected by verify_release.sh."""
    digest = hashlib.sha256()
    seen: set[str] = set()
    for relative, payload in sorted(entries, key=lambda item: item[0]):
        if relative in seen:
            continue
        seen.add(relative)
        if is_excluded_from_public_tree(relative):
            continue
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _read_repo_payload(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        if path.is_symlink():
            return str(path.readlink()).encode("utf-8")
        raise
    with os.fdopen(fd, "rb") as stream:
        return stream.read()


def _validate_bundle_relpath(rel_path: str) -> str:
    candidate = Path(rel_path)
    if not rel_path or rel_path.startswith("/") or "\\" in rel_path or ".." in candidate.parts:
        raise ValueError(f"Invalid path in release bundle inventory: {rel_path!r}")
    return rel_path


def _collect_release_bundle_info(version: str, bundle_path: Path | None) -> Dict[str, Any] | None:
    if bundle_path is not None:
        if not bundle_path.exists():
            return None
        bundle_bytes = bundle_path.read_bytes()
        bundle_info: Dict[str, Any] = {
            "name": bundle_path.name,
            "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "size_bytes": len(bundle_bytes),
        }
        if zipfile.is_zipfile(bundle_path):
            entries: List[Tuple[str, bytes]] = []
            with zipfile.ZipFile(bundle_path, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    mode = (info.external_attr >> 16) & 0o170000
                    if stat.S_ISLNK(mode):
                        raise ValueError(f"Symlink entry forbidden in release bundle: {info.filename!r}")
                    rel_path = _validate_bundle_relpath(info.filename)
                    entries.append((rel_path, zf.read(info)))
            bundle_info["tree_digest"] = _bundle_tree_digest(entries)
            bundle_info["source_files"] = sorted({rel for rel, _ in entries})
        return bundle_info

    packager = REPO_ROOT / "scripts" / "package_release.sh"
    if not packager.is_file():
        return None
    listed = subprocess.run(
        ["bash", str(packager), "--list-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    entries = []
    source_files: set[str] = set()
    for raw_line in listed.stdout.splitlines():
        rel_path = _validate_bundle_relpath(raw_line.strip())
        source_files.add(rel_path)
        if not is_excluded_from_public_tree(rel_path):
            entries.append((rel_path, _read_repo_payload(REPO_ROOT / rel_path)))
    return {
        "name": f"Babylon60-v{version}-terminal-mcp.zip",
        "tree_digest": _bundle_tree_digest(entries),
        "source_files": sorted(source_files),
    }


def emit_claims_artifacts(
    evidence: Dict[str, Any],
    bundle_path: Path | None = None,
) -> Tuple[Path, Path, Path]:
    from scripts.generate_sbom import generate_sboms

    release_spec = load_babylon_release_spec()
    claims_toml_path = REPO_ROOT / "CLAIMS.toml"
    if claims_toml_path.is_file():
        claims_doc = tomllib.loads(claims_toml_path.read_text(encoding="utf-8"))
        _, inv_errors = audit_invariants_alignment(claims_doc, release_spec)
        if inv_errors:
            raise ValueError(
                "Invariant alignment failure between CLAIMS.toml [invariants.*] and babylon.toml: "
                + "; ".join(inv_errors)
            )
    version = release_spec.get("version", "5.0.1")
    state = release_spec.get("state", "candidate")
    axiom = release_spec.get("axiom", "AX-0")
    commit = evidence["source_commit"]
    version_sync = collect_version_sync(version)
    prior_release = load_prior_release()
    signing_key = _load_signing_key()
    sbom_summary = generate_sboms(repo_root=REPO_ROOT)

    bundle_info = _collect_release_bundle_info(version, bundle_path)

    # 1. evidence.json
    evidence_json_path = REPO_ROOT / "evidence.json"
    evidence_json_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 2. claims.lock
    lock_data = {
        "format": "babylon60.claims.lock.v1",
        "version": version,
        "commit": commit,
        "source_tree_digest": evidence["source_tree_digest"],
        "timestamp": evidence["timestamp_iso"],
        "claims_manifest_digest": evidence["claims_manifest_digest"],
        "evidence_root": evidence["merkle_evidence_root"],
        "claims_pinned": {
            e["id"]: {
                "status": e["status"],
                "component": e["component"],
                "hash": e["leaf_hash"],
            }
            for e in evidence["evidence_entries"]
        },
    }
    claims_lock_path = REPO_ROOT / "claims.lock"
    claims_lock_path.write_text(
        json.dumps(lock_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 3. RELEASE_MANIFEST.json (signed only when a key is provisioned)
    pubkey_hex = signing_key.public_key().public_bytes_raw().hex() if signing_key else None

    manifest_body: Dict[str, Any] = {
        "manifest_schema": MANIFEST_SCHEMA,
        "release": version,
        "version": version,
        "state": state,
        "commit": commit,
        "source_tree_digest": evidence["source_tree_digest"],
        "axiom_root": axiom,
        "claims_manifest_digest": evidence["claims_manifest_digest"],
        "compiled_at_iso": evidence["timestamp_iso"],
        "prior_release": prior_release,
        "version_sync": version_sync,
        "substrate": dict(release_spec.get("substrate", {})),
        "gate_attestations": dict(release_spec.get("gate_attestations", {})),
        "gate_attestations_basis": (
            "Declared in babylon.toml [release.gate_attestations]; executable evidence is bound only by evidence_root."
        ),
        "artifacts_sha256": collect_artifact_digests(),
        "claims": {
            "verified": evidence["verified_count"],
            "empirical_and_bounded": evidence["partial_count"],
            "experimental": evidence["experimental_count"],
            "failed": evidence.get("failed_count", 0),
            "total": evidence["total_claims"],
        },
        "evidence_root": evidence["merkle_evidence_root"],
        "sbom": {
            "format": sbom_summary["format"],
            "cargo_sbom_sha256": sbom_summary["cargo_sbom_sha256"],
            "cargo_components": sbom_summary["cargo_components"],
            "python_sbom_sha256": sbom_summary["python_sbom_sha256"],
            "python_components": sbom_summary["python_components"],
        },
        "release_bundle": bundle_info,
        "signing_authority": {
            "algorithm": "Ed25519" if signing_key else None,
            "scope": "detached_release_attestation" if signing_key else "unsigned_local_evidence",
            "public_key": pubkey_hex,
        },
    }

    canonical_bytes = json.dumps(manifest_body, sort_keys=True).encode("utf-8")
    signature = signing_key.sign(canonical_bytes).hex() if signing_key else None

    manifest_full = dict(manifest_body)
    manifest_full["signature"] = signature

    release_manifest_path = REPO_ROOT / "RELEASE_MANIFEST.json"
    release_manifest_path.write_text(
        json.dumps(manifest_full, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    sig_path = REPO_ROOT / "RELEASE_MANIFEST.json.sig"
    if signature and pubkey_hex:
        sig_doc = {
            "algorithm": "Ed25519",
            "public_key": pubkey_hex,
            "canonical_body_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
            "signature": signature,
        }
        sig_path.write_text(json.dumps(sig_doc, indent=2) + "\n", encoding="utf-8")
    elif sig_path.exists():
        sig_path.unlink()

    return evidence_json_path, claims_lock_path, release_manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile claims and release manifest")
    parser.add_argument("--fresh", action="store_true", help="Re-run all evidence tests before compiling")
    parser.add_argument(
        "--bundle", type=Path, default=None, help="Optional release archive (.zip/.whl) to bind into manifest"
    )
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("BABYLON-60 · COMPILADOR DE EPISTEMOLOGÍA Y RELEASE MANIFEST (v5.0)")
    print("=" * 80)

    evidence = compile_claims_evidence(run_fresh=args.fresh)
    ev_path, lock_path, rel_path = emit_claims_artifacts(evidence, bundle_path=args.bundle)

    manifest = json.loads(rel_path.read_text(encoding="utf-8"))

    print("\n┌─ [RELEASE MANIFEST COMPILADO]")
    print(f"├▸ Release Version : v{manifest['release']} ({manifest['state']})")
    print(f"├▸ Commit Hash     : {manifest['commit']}")
    print(f"├▸ Axioma Raíz     : {manifest['axiom_root']}")
    print(f"├▸ Evidence Root   : {manifest['evidence_root']}")
    print(
        f"├▸ SBOM CycloneDX  : {manifest['sbom']['cargo_components']} crates / "
        f"{manifest['sbom']['python_components']} paquetes PyPI"
    )
    print(
        f"├▸ Claims Verific. : {manifest['claims']['verified']} rigurosos / "
        f"{manifest['claims']['empirical_and_bounded']} acotados / "
        f"{manifest['claims']['failed']} fallos"
    )
    print(
        f"├▸ Firma Digital   : {'Ed25519 (detached .sig)' if manifest['signature'] else 'UNSIGNED (no provisioned key)'}"
    )
    print("└──────────────────────────────────────────────────────────────")
    print(f"\n[✓] evidence.json   : {ev_path.relative_to(REPO_ROOT)}")
    print(f"[✓] claims.lock     : {lock_path.relative_to(REPO_ROOT)}")
    print(f"[✓] RELEASE_MANIFEST: {rel_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
