#!/usr/bin/env bash
# ============================================================================
# BABYLON-60 — Zero-Trust Standalone Release & Evidence Verifier (Fase 2)
# Verifies RELEASE_MANIFEST.json, evidence.json, claims.lock, CycloneDX SBOMs,
# release bundle SHA-256, Merkle root, and detached Ed25519 / OIDC signatures
# WITHOUT importing or executing any code from the babylon60 package.
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -L)"
BUNDLE_PATH=""
EXPECTED_PUBKEY=""
EXPECTED_MANIFEST_SHA256=""
REQUIRE_SIGNATURE=0
VERIFY_OIDC_REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --bundle)
      BUNDLE_PATH="$2"
      shift 2
      ;;
    --pubkey)
      EXPECTED_PUBKEY="$2"
      shift 2
      ;;
    --expected-manifest-sha256)
      EXPECTED_MANIFEST_SHA256="$2"
      shift 2
      ;;
    --require-signature)
      REQUIRE_SIGNATURE=1
      shift
      ;;
    --verify-oidc)
      VERIFY_OIDC_REPO="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

python3 - "$REPO_ROOT" "$BUNDLE_PATH" "$EXPECTED_PUBKEY" "$REQUIRE_SIGNATURE" "$EXPECTED_MANIFEST_SHA256" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo_root = Path(sys.argv[1]).absolute()
bundle_arg = sys.argv[2]
expected_pubkey = sys.argv[3].strip().lower()
require_sig = sys.argv[4] == "1"
expected_manifest_sha256 = sys.argv[5].strip().lower()

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
}

VAULT_ONLY_PREFIXES = (
    ".agents/rules/",
    ".agents/mcp_config.json",
    ".playwright-mcp/",
    "docs/security/evidence/",
    "tools/skill_library/",
    "assets/brand/github-art-brut.svg",
    "assets/AppIcon.icns",
    "assets/babylon60_brutalist_logo_1024.png",
)


def is_excluded_from_public_tree(relative: str) -> bool:
    return relative in GENERATED_EVIDENCE or relative.startswith(VAULT_ONLY_PREFIXES)


def compute_public_tree_digest(cwd: Path) -> str | None:
    if not (cwd / ".git").exists():
        return None
    try:
        files = subprocess.check_output(["git", "ls-files", "-z"], cwd=cwd, stderr=subprocess.DEVNULL).split(b"\0")
    except Exception:
        return None
    digest = hashlib.sha256()
    for raw_path in sorted(path for path in files if path):
        relative = raw_path.decode("utf-8")
        if is_excluded_from_public_tree(relative):
            continue
        path = cwd / relative
        if not path.exists() and not path.is_symlink():
            return None
        payload = str(path.readlink()).encode("utf-8") if path.is_symlink() else path.read_bytes()
        digest.update(raw_path + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def fail(msg: str) -> None:
    print(f"[FAIL-CLOSED] {msg}", file=sys.stderr)
    raise SystemExit(1)


def compute_merkle_root(entry_hashes: list[str]) -> str:
    if not entry_hashes:
        return "0" * 64
    total_leaves = len(entry_hashes)
    layer = [bytes.fromhex(h) for h in entry_hashes]
    level = 0
    while len(layer) > 1:
        if len(layer) % 2 != 0:
            layer.append(layer[-1])
        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            domain_tag = b"\x00" if level == 0 else b"\x01"
            next_layer.append(hashlib.sha3_256(domain_tag + combined).digest())
        layer = next_layer
        level += 1
    root_with_cardinality = b"\x02" + layer[0] + total_leaves.to_bytes(8, "little")
    return hashlib.sha3_256(root_with_cardinality).hexdigest()


manifest_path = repo_root / "RELEASE_MANIFEST.json"
evidence_path = repo_root / "evidence.json"
lock_path = repo_root / "claims.lock"
claims_toml_path = repo_root / "CLAIMS.toml"

for req in (manifest_path, evidence_path, lock_path, claims_toml_path):
    if not req.is_file():
        fail(f"Missing required verification input: {req}")

actual_manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
if expected_manifest_sha256 and actual_manifest_sha256 != expected_manifest_sha256:
    fail(
        f"RELEASE_MANIFEST.json SHA-256 mismatch against --expected-manifest-sha256: "
        f"expected {expected_manifest_sha256}, got {actual_manifest_sha256}"
    )

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
claims_lock = json.loads(lock_path.read_text(encoding="utf-8"))

# 1. Verify CLAIMS.toml digest
actual_claims_digest = hashlib.sha256(claims_toml_path.read_bytes()).hexdigest()
if manifest.get("claims_manifest_digest") != actual_claims_digest:
    fail("CLAIMS.toml SHA-256 mismatch against RELEASE_MANIFEST.json")
if evidence.get("claims_manifest_digest") != actual_claims_digest:
    fail("CLAIMS.toml SHA-256 mismatch against evidence.json")
if claims_lock.get("claims_manifest_digest") != actual_claims_digest:
    fail("CLAIMS.toml SHA-256 mismatch against claims.lock")

sitrep_path = repo_root / "scripts" / "c5_quality_gates" / "claims_sitrep.json"
if sitrep_path.is_file():
    sitrep_doc = json.loads(sitrep_path.read_text(encoding="utf-8"))
    if sitrep_doc.get("claims_manifest_digest") != actual_claims_digest:
        fail("CLAIMS.toml SHA-256 mismatch against claims_sitrep.json")
    if int(sitrep_doc.get("total_claims", 0)) != int(manifest.get("claims", {}).get("total", 0)):
        fail("Mismatch in total claims count between RELEASE_MANIFEST.json and claims_sitrep.json")

# 2. Verify zero failed claims and recompute every leaf hash + Merkle root
claims_summary = manifest.get("claims", {})
if int(claims_summary.get("failed", 1)) != 0 or int(evidence.get("failed_count", 1)) != 0:
    fail("Release manifest or evidence reports failed claims > 0")

entries = evidence.get("evidence_entries", [])
if not entries or len(entries) != int(claims_summary.get("total", 0)):
    fail("Mismatch in total claims count between RELEASE_MANIFEST.json and evidence.json")

recomputed_leaves: list[str] = []
pinned = claims_lock.get("claims_pinned", {})
for entry in entries:
    cid = entry["id"]
    comp = entry["component"]
    status = entry["status"]
    suite_passed = bool(entry.get("suite_passed", entry.get("verified", False)))
    stmt = entry["statement"]
    if not suite_passed:
        fail(f"Claim '{cid}' did not pass its evidence suite in evidence.json")
    canonical = f"{cid}:{comp}:{status}:{suite_passed}:{stmt}"
    leaf = hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()
    if leaf != entry.get("leaf_hash"):
        fail(f"Tampered leaf_hash detected for claim '{cid}'")
    if pinned.get(cid, {}).get("hash") != leaf:
        fail(f"claims.lock hash mismatch for claim '{cid}'")
    recomputed_leaves.append(leaf)

expected_root = f"sha3-256:{compute_merkle_root(recomputed_leaves)}"
if manifest.get("evidence_root") != expected_root:
    fail(f"Merkle root mismatch in RELEASE_MANIFEST.json: expected {expected_root}, got {manifest.get('evidence_root')}")
if evidence.get("merkle_evidence_root") != expected_root:
    fail("Merkle root mismatch in evidence.json")
if claims_lock.get("evidence_root") != expected_root:
    fail("Merkle root mismatch in claims.lock")

# 3. Verify CycloneDX SBOM digests if present in manifest
sbom_meta = manifest.get("sbom")
if sbom_meta:
    for sbom_file, key in (
        ("sbom.cargo.cdx.json", "cargo_sbom_sha256"),
        ("sbom.python.cdx.json", "python_sbom_sha256"),
    ):
        sbom_path = repo_root / sbom_file
        if not sbom_path.is_file():
            fail(f"Missing SBOM file required by manifest: {sbom_file}")
        digest = hashlib.sha256(sbom_path.read_bytes()).hexdigest()
        if digest != sbom_meta.get(key):
            fail(f"SBOM SHA-256 mismatch for {sbom_file}")

# 3b. Verify governance root artifacts and public source_tree_digest
artifacts_meta = manifest.get("artifacts_sha256")
if isinstance(artifacts_meta, dict):
    for rel_artifact, expected_art_digest in artifacts_meta.items():
        art_path = repo_root / rel_artifact
        if not art_path.is_file():
            fail(f"Missing governance artifact required by manifest: {rel_artifact}")
        actual_art_digest = hashlib.sha256(art_path.read_bytes()).hexdigest()
        if actual_art_digest != expected_art_digest:
            fail(
                f"Governance artifact SHA-256 mismatch for {rel_artifact}: "
                f"expected {expected_art_digest}, got {actual_art_digest}"
            )

expected_tree_digest = manifest.get("source_tree_digest")
actual_tree_digest = compute_public_tree_digest(repo_root)
if expected_tree_digest and actual_tree_digest and actual_tree_digest != expected_tree_digest:
    fail(
        f"Public source_tree_digest mismatch against RELEASE_MANIFEST.json: "
        f"expected {expected_tree_digest}, got {actual_tree_digest}"
    )

# 4. Verify packaged release bundle if specified or recorded in manifest
bundle_meta = manifest.get("release_bundle")
if bundle_arg:
    bpath = Path(bundle_arg)
    if not bpath.is_file():
        fail(f"Specified release bundle does not exist: {bpath}")
    bsha = hashlib.sha256(bpath.read_bytes()).hexdigest()
    if bundle_meta and bundle_meta.get("sha256") != bsha:
        fail(f"Release bundle SHA-256 mismatch: manifest={bundle_meta.get('sha256')} actual={bsha}")
elif bundle_meta:
    bpath = repo_root / "dist" / str(bundle_meta.get("name", ""))
    if bpath.is_file():
        bsha = hashlib.sha256(bpath.read_bytes()).hexdigest()
        if bundle_meta.get("sha256") != bsha:
            fail(f"Release bundle SHA-256 mismatch in dist/: {bpath.name}")

# 5. Verify canonical body and detached Ed25519 signature
manifest_body = {k: v for k, v in manifest.items() if k != "signature"}
canonical_bytes = json.dumps(manifest_body, sort_keys=True).encode("utf-8")
sig_hex = manifest.get("signature")
auth = manifest.get("signing_authority") or {}
manifest_pubkey = (auth.get("public_key") or "").strip().lower()

if require_sig and not sig_hex:
    fail("Signature required (--require-signature) but RELEASE_MANIFEST.json is unsigned")

if expected_pubkey and manifest_pubkey != expected_pubkey:
    fail(f"Signing authority public key mismatch: expected {expected_pubkey}, got {manifest_pubkey}")

if sig_hex:
    if not manifest_pubkey:
        fail("Signature present without public_key in signing_authority")
    sig_file = repo_root / "RELEASE_MANIFEST.json.sig"
    if sig_file.is_file():
        sig_doc = json.loads(sig_file.read_text(encoding="utf-8"))
        if sig_doc.get("signature") != sig_hex or sig_doc.get("public_key", "").lower() != manifest_pubkey:
            fail("Detached RELEASE_MANIFEST.json.sig does not match RELEASE_MANIFEST.json")
        if sig_doc.get("canonical_body_sha256") != hashlib.sha256(canonical_bytes).hexdigest():
            fail("Detached RELEASE_MANIFEST.json.sig canonical_body_sha256 mismatch")

    # Verify Ed25519 signature via OpenSSL (ASN.1 SubjectPublicKeyInfo prefix for Ed25519 = 302a300506032b6570032100)
    spki_der = bytes.fromhex("302a300506032b6570032100" + manifest_pubkey)
    sig_bytes = bytes.fromhex(sig_hex)
    with tempfile.TemporaryDirectory(prefix="b60_verify_") as td:
        td_path = Path(td)
        pub_der_file = td_path / "pub.der"
        msg_file = td_path / "msg.bin"
        sig_bin_file = td_path / "sig.bin"
        pub_der_file.write_bytes(spki_der)
        msg_file.write_bytes(canonical_bytes)
        sig_bin_file.write_bytes(sig_bytes)
        res = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(pub_der_file),
                "-keyform",
                "DER",
                "-rawin",
                "-in",
                str(msg_file),
                "-sigfile",
                str(sig_bin_file),
            ],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            fail(f"Ed25519 cryptographic signature verification failed: {res.stderr.strip()}")

print(
    f"[VERIFIED] release=v{manifest.get('release')} commit={manifest.get('commit')[:12]} "
    f"claims={len(entries)} merkle={expected_root[:25]}... "
    f"signed={'yes' if sig_hex else 'no'}"
)
PY

if [[ -n "$VERIFY_OIDC_REPO" && -n "$BUNDLE_PATH" ]]; then
  echo "[OIDC] Verifying GitHub SLSA Build Provenance via gh attestation verify..."
  gh attestation verify "$BUNDLE_PATH" --repo "$VERIFY_OIDC_REPO"
fi
