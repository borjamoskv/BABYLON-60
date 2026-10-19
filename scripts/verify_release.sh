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

python3 - "$REPO_ROOT" "$BUNDLE_PATH" "$EXPECTED_PUBKEY" "$REQUIRE_SIGNATURE" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

repo_root = Path(sys.argv[1]).absolute()
bundle_arg = sys.argv[2]
expected_pubkey = sys.argv[3].strip().lower()
require_sig = sys.argv[4] == "1"

GENERATED_EVIDENCE = {
    "evidence.json",
    "claims.lock",
    "RELEASE_MANIFEST.json",
    "RELEASE_MANIFEST.json.sig",
    "sbom.cargo.cdx.json",
    "sbom.python.cdx.json",
    "scripts/c5_quality_gates/claims_sitrep.json",
}


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
    verified = bool(entry["verified"])
    stmt = entry["statement"]
    if not verified:
        fail(f"Claim '{cid}' is not marked verified in evidence.json")
    canonical = f"{cid}:{comp}:{status}:{verified}:{stmt}"
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
