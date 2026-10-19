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
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(REPO_ROOT / "01_KISH_ENGINE"))

from babylon60.bft.cortex_crypto_kernel import build_merkle_tree  # noqa: E402

sys.path.insert(0, str(REPO_ROOT))
from scripts.c5_quality_gates.verify_claims import source_tree_digest  # noqa: E402

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
    declared = tomllib.loads(manifest_path.read_text(encoding="utf-8"))["claim"]
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
    if sitrep.get("failed_claims") or any(not c.get("verified") for c in claims_list):
        raise ValueError("Cannot publish release evidence with failed claims")

    evidence_entries = []
    merkle_leaves = []

    for c in claims_list:
        cid = c["id"]
        status = c["status"]
        stmt = c["statement"]
        component = c.get("component", "UNKNOWN")
        dur = c.get("duration_s", 0.0)
        verified_flag = bool(c.get("verified", False))

        # Digest determinista del claim + estado verificado (sin jitter de reloj duration_s)
        canonical_claim_repr = f"{cid}:{component}:{status}:{verified_flag}:{stmt}"
        leaf_hash = hashlib.sha3_256(canonical_claim_repr.encode("utf-8")).hexdigest()
        merkle_leaves.append(leaf_hash)

        evidence_entries.append(
            {
                "id": cid,
                "component": component,
                "statement": stmt,
                "status": status,
                "verified": verified_flag,
                "duration_s": dur,
                "leaf_hash": leaf_hash,
            }
        )

    if merkle_leaves:
        merkle_root = build_merkle_tree(merkle_leaves)
    else:
        merkle_root = "0" * 64

    failed_count = sum(1 for e in evidence_entries if not e["verified"])

    return {
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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


def emit_claims_artifacts(
    evidence: Dict[str, Any],
    bundle_path: Path | None = None,
) -> Tuple[Path, Path, Path]:
    from scripts.generate_sbom import generate_sboms

    release_spec = load_babylon_release_spec()
    version = release_spec.get("version", "5.0.0")
    state = release_spec.get("state", "candidate")
    axiom = release_spec.get("axiom", "AX-0")
    commit = evidence["source_commit"]
    signing_key = _load_signing_key()
    sbom_summary = generate_sboms(repo_root=REPO_ROOT)

    bundle_info: Dict[str, Any] | None = None
    if bundle_path is not None and bundle_path.exists():
        bundle_bytes = bundle_path.read_bytes()
        bundle_info = {
            "name": bundle_path.name,
            "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "size_bytes": len(bundle_bytes),
        }

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
        "release": version,
        "state": state,
        "commit": commit,
        "source_tree_digest": evidence["source_tree_digest"],
        "axiom_root": axiom,
        "claims_manifest_digest": evidence["claims_manifest_digest"],
        "compiled_at_iso": evidence["timestamp_iso"],
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
