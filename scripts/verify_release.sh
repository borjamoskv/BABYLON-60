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
    "tests/test_skill_intent_routing.py",
    "tests/test_skill_library_convergence.py",
    "tests/test_skill_maintenance.py",
    "assets/brand/github-art-brut.svg",
    "assets/AppIcon.icns",
    "assets/babylon60_brutalist_logo_1024.png",
)


def is_excluded_from_public_tree(relative: str) -> bool:
    return relative in GENERATED_EVIDENCE or relative.startswith(VAULT_ONLY_PREFIXES)


def compute_public_tree_digest(cwd: Path, manifest_doc: dict) -> tuple[str | None, str, str]:
    raw_paths: list[bytes] = []
    expected_digest = str(manifest_doc.get("source_tree_digest") or "").strip()
    if (cwd / ".git").exists():
        try:
            out = subprocess.check_output(["git", "ls-files", "-z"], cwd=cwd, stderr=subprocess.DEVNULL)
            raw_paths = [p for p in out.split(b"\0") if p]
        except Exception as exc:
            return None, expected_digest, f"git ls-files failed: {exc}"
        if not raw_paths:
            return None, expected_digest, "git ls-files returned an empty tracked file index"
    else:
        source_files = manifest_doc.get("source_files")
        bundle_doc = manifest_doc.get("release_bundle")
        if isinstance(source_files, list) and source_files:
            for item in source_files:
                if not isinstance(item, str) or not item or item.startswith("/") or ".." in Path(item).parts:
                    return None, expected_digest, f"Invalid path in manifest source_files inventory: {item!r}"
                raw_paths.append(item.encode("utf-8"))
        elif (
            isinstance(bundle_doc, dict)
            and isinstance(bundle_doc.get("source_files"), list)
            and bundle_doc.get("source_files")
            and str(bundle_doc.get("tree_digest") or "").strip()
        ):
            expected_digest = str(bundle_doc.get("tree_digest") or "").strip()
            for item in bundle_doc["source_files"]:
                if not isinstance(item, str) or not item or item.startswith("/") or ".." in Path(item).parts:
                    return None, expected_digest, f"Invalid path in release_bundle.source_files inventory: {item!r}"
                raw_paths.append(item.encode("utf-8"))
        else:
            return (
                None,
                expected_digest,
                ".git metadata is absent and RELEASE_MANIFEST.json contains no authenticated source_files inventory",
            )

    digest = hashlib.sha256()
    for raw_path in sorted(set(raw_paths)):
        relative = raw_path.decode("utf-8")
        if is_excluded_from_public_tree(relative):
            continue
        path = cwd / relative
        if not path.exists() and not path.is_symlink():
            return None, expected_digest, f"Tracked source file missing from working tree: {relative}"
        payload = str(path.readlink()).encode("utf-8") if path.is_symlink() else path.read_bytes()
        digest.update(raw_path + b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest(), expected_digest, "verified"


checks: list[tuple[str, str, bool, str]] = []


def record_check(name: str, status: str, required: bool, detail: str = "") -> None:
    if status not in {"PASS", "FAIL", "NOT_CHECKED"}:
        raise ValueError(f"Invalid check status: {status}")
    checks.append((name, status, required, detail))


def emit_checks(stream) -> None:
    for name, status, required, detail in checks:
        req_label = "required" if required else "optional"
        suffix = f" ({detail})" if detail else ""
        print(f"[CHECK] {name}: {status} [{req_label}]{suffix}", file=stream)


def fail(msg: str, *, check_name: str = "verification_gate", status: str = "FAIL", required: bool = True) -> None:
    record_check(check_name, status, required, msg)
    emit_checks(sys.stderr)
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
        fail(f"Missing required verification input: {req}", check_name="manifest_integrity")

actual_manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
if expected_manifest_sha256 and actual_manifest_sha256 != expected_manifest_sha256:
    fail(
        f"RELEASE_MANIFEST.json SHA-256 mismatch against --expected-manifest-sha256: "
        f"expected {expected_manifest_sha256}, got {actual_manifest_sha256}",
        check_name="manifest_integrity",
    )
record_check("manifest_integrity", "PASS", True, f"sha256={actual_manifest_sha256[:16]}...")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
claims_lock = json.loads(lock_path.read_text(encoding="utf-8"))

# 1. Verify CLAIMS.toml digest
actual_claims_digest = hashlib.sha256(claims_toml_path.read_bytes()).hexdigest()
if manifest.get("claims_manifest_digest") != actual_claims_digest:
    fail("CLAIMS.toml SHA-256 mismatch against RELEASE_MANIFEST.json", check_name="claims_manifest_digest")
if evidence.get("claims_manifest_digest") != actual_claims_digest:
    fail("CLAIMS.toml SHA-256 mismatch against evidence.json", check_name="claims_manifest_digest")
if claims_lock.get("claims_manifest_digest") != actual_claims_digest:
    fail("CLAIMS.toml SHA-256 mismatch against claims.lock", check_name="claims_manifest_digest")

sitrep_path = repo_root / "scripts" / "c5_quality_gates" / "claims_sitrep.json"
if sitrep_path.is_file():
    sitrep_doc = json.loads(sitrep_path.read_text(encoding="utf-8"))
    if sitrep_doc.get("claims_manifest_digest") != actual_claims_digest:
        fail("CLAIMS.toml SHA-256 mismatch against claims_sitrep.json", check_name="claims_manifest_digest")
    if int(sitrep_doc.get("total_claims", 0)) != int(manifest.get("claims", {}).get("total", 0)):
        fail(
            "Mismatch in total claims count between RELEASE_MANIFEST.json and claims_sitrep.json",
            check_name="claims_manifest_digest",
        )
record_check("claims_manifest_digest", "PASS", True, f"sha256={actual_claims_digest[:16]}...")

# 1b. Verify provenance concordance across RELEASE_MANIFEST.json, evidence.json, and claims.lock
manifest_commit = str(manifest.get("commit") or "").strip()
evidence_commit = str(evidence.get("source_commit") or "").strip()
lock_commit = str(claims_lock.get("commit") or "").strip()
if not manifest_commit or not evidence_commit or manifest_commit != evidence_commit:
    fail(
        f"Provenance commit mismatch between RELEASE_MANIFEST.json ({manifest_commit}) "
        f"and evidence.json ({evidence_commit})",
        check_name="provenance_alignment",
    )
if lock_commit and lock_commit != manifest_commit:
    fail(
        f"Provenance commit mismatch between RELEASE_MANIFEST.json ({manifest_commit}) "
        f"and claims.lock ({lock_commit})",
        check_name="provenance_alignment",
    )

manifest_tree_digest = str(manifest.get("source_tree_digest") or "").strip()
evidence_tree_digest = str(evidence.get("source_tree_digest") or "").strip()
lock_tree_digest = str(claims_lock.get("source_tree_digest") or "").strip()
if not manifest_tree_digest or not evidence_tree_digest or manifest_tree_digest != evidence_tree_digest:
    fail(
        f"Provenance source_tree_digest mismatch between RELEASE_MANIFEST.json ({manifest_tree_digest}) "
        f"and evidence.json ({evidence_tree_digest})",
        check_name="provenance_alignment",
    )
if lock_tree_digest and lock_tree_digest != manifest_tree_digest:
    fail(
        f"Provenance source_tree_digest mismatch between RELEASE_MANIFEST.json ({manifest_tree_digest}) "
        f"and claims.lock ({lock_tree_digest})",
        check_name="provenance_alignment",
    )

env_digest = str(evidence.get("environment_digest") or "").strip()
if not env_digest:
    fail("Missing execution subject environment_digest in evidence.json", check_name="provenance_alignment")
record_check("provenance_alignment", "PASS", True, f"commit={manifest_commit[:12]}")

# 2. Verify zero failed claims and recompute every leaf hash + Merkle root
claims_summary = manifest.get("claims", {})
if int(claims_summary.get("failed", 1)) != 0 or int(evidence.get("failed_count", 1)) != 0:
    fail("Release manifest or evidence reports failed claims > 0", check_name="merkle_evidence_tree")

entries = evidence.get("evidence_entries", [])
if not entries or len(entries) != int(claims_summary.get("total", 0)):
    fail(
        "Mismatch in total claims count between RELEASE_MANIFEST.json and evidence.json",
        check_name="merkle_evidence_tree",
    )

recomputed_total = len(entries)
recomputed_verified = 0
recomputed_bounded = 0
recomputed_experimental = 0
recomputed_failed = 0
recomputed_leaves: list[str] = []
pinned = claims_lock.get("claims_pinned", {})

for entry in entries:
    cid = entry.get("id")
    if not cid or not isinstance(cid, str):
        fail("Missing or invalid claim 'id' in evidence entry", check_name="merkle_evidence_tree")
    comp = entry.get("component", "")
    status = entry.get("status", "")

    # 1. Strict boolean type verification (anti-coercion gate: rejects string 'false', int 0/1, etc.)
    raw_passed = entry.get("suite_passed")
    if raw_passed is None:
        raw_passed = entry.get("verified")
    if not isinstance(raw_passed, bool):
        fail(
            f"Type violation in claim '{cid}': suite_passed must be boolean True/False, got {type(raw_passed).__name__} ({raw_passed!r})",
            check_name="merkle_evidence_tree",
        )
    if not raw_passed:
        recomputed_failed += 1
        fail(f"Claim '{cid}' did not pass its evidence suite in evidence.json", check_name="merkle_evidence_tree")
    suite_passed = raw_passed

    raw_verified = entry.get("verified")
    if raw_verified is not None and not isinstance(raw_verified, bool):
        fail(
            f"Type violation in claim '{cid}': verified must be boolean True/False, got {type(raw_verified).__name__} ({raw_verified!r})",
            check_name="merkle_evidence_tree",
        )

    # Inductive classification of verification tier
    if raw_verified is True:
        if status != "verified":
            fail(
                f"Contradictory state in claim '{cid}': verified=True but status='{status}' (expected 'verified')",
                check_name="merkle_evidence_tree",
            )
        recomputed_verified += 1
    else:
        if status == "verified":
            fail(
                f"Contradictory state in claim '{cid}': verified=False but status='verified'",
                check_name="merkle_evidence_tree",
            )
        if status == "experimental":
            recomputed_experimental += 1
        else:
            recomputed_bounded += 1

    stmt = entry.get("statement", "")
    canonical = f"{cid}:{comp}:{status}:{suite_passed}:{stmt}"
    leaf = hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()
    if leaf != entry.get("leaf_hash"):
        fail(f"Tampered leaf_hash detected for claim '{cid}'", check_name="merkle_evidence_tree")
    if pinned.get(cid, {}).get("hash") != leaf:
        fail(f"claims.lock hash mismatch for claim '{cid}'", check_name="merkle_evidence_tree")
    recomputed_leaves.append(leaf)

# 2b. Inductive reconstruction check: recomputed counts must match manifest claims summary
manifest_verified = int(claims_summary.get("verified", -1))
manifest_bounded = int(claims_summary.get("empirical_and_bounded", -1))
manifest_experimental = int(claims_summary.get("experimental", -1))
manifest_failed = int(claims_summary.get("failed", -1))
manifest_total = int(claims_summary.get("total", -1))

if recomputed_total != manifest_total:
    fail(
        f"Claims count mismatch: reconstructed total={recomputed_total} from entries, but manifest claims.total={manifest_total}",
        check_name="merkle_evidence_tree",
    )
if recomputed_verified != manifest_verified:
    fail(
        f"Claims count mismatch: reconstructed verified={recomputed_verified} from entries, but manifest claims.verified={manifest_verified}",
        check_name="merkle_evidence_tree",
    )
if recomputed_bounded != manifest_bounded:
    fail(
        f"Claims count mismatch: reconstructed empirical_and_bounded={recomputed_bounded} from entries, but manifest claims.empirical_and_bounded={manifest_bounded}",
        check_name="merkle_evidence_tree",
    )
if recomputed_experimental != manifest_experimental:
    fail(
        f"Claims count mismatch: reconstructed experimental={recomputed_experimental} from entries, but manifest claims.experimental={manifest_experimental}",
        check_name="merkle_evidence_tree",
    )
if recomputed_failed != manifest_failed:
    fail(
        f"Claims count mismatch: reconstructed failed={recomputed_failed} from entries, but manifest claims.failed={manifest_failed}",
        check_name="merkle_evidence_tree",
    )

# 2c. Inductive reconstruction check: recomputed counts must match evidence.json top-level summary
ev_total = int(evidence.get("total_claims", -1))
ev_verified = int(evidence.get("verified_count", -1))
ev_partial = int(evidence.get("partial_count", -1))
ev_experimental = int(evidence.get("experimental_count", -1))
ev_failed = int(evidence.get("failed_count", -1))

if recomputed_total != ev_total:
    fail(
        f"Claims count mismatch: reconstructed total={recomputed_total} from entries, but evidence.json total_claims={ev_total}",
        check_name="merkle_evidence_tree",
    )
if recomputed_verified != ev_verified:
    fail(
        f"Claims count mismatch: reconstructed verified={recomputed_verified} from entries, but evidence.json verified_count={ev_verified}",
        check_name="merkle_evidence_tree",
    )
if recomputed_bounded != ev_partial:
    fail(
        f"Claims count mismatch: reconstructed partial={recomputed_bounded} from entries, but evidence.json partial_count={ev_partial}",
        check_name="merkle_evidence_tree",
    )
if recomputed_experimental != ev_experimental:
    fail(
        f"Claims count mismatch: reconstructed experimental={recomputed_experimental} from entries, but evidence.json experimental_count={ev_experimental}",
        check_name="merkle_evidence_tree",
    )
if recomputed_failed != ev_failed:
    fail(
        f"Claims count mismatch: reconstructed failed={recomputed_failed} from entries, but evidence.json failed_count={ev_failed}",
        check_name="merkle_evidence_tree",
    )

expected_root = f"sha3-256:{compute_merkle_root(recomputed_leaves)}"
if manifest.get("evidence_root") != expected_root:
    fail(
        f"Merkle root mismatch in RELEASE_MANIFEST.json: expected {expected_root}, got {manifest.get('evidence_root')}",
        check_name="merkle_evidence_tree",
    )
if evidence.get("merkle_evidence_root") != expected_root:
    fail("Merkle root mismatch in evidence.json", check_name="merkle_evidence_tree")
if claims_lock.get("evidence_root") != expected_root:
    fail("Merkle root mismatch in claims.lock", check_name="merkle_evidence_tree")
record_check("merkle_evidence_tree", "PASS", True, f"leaves={len(recomputed_leaves)} verified={recomputed_verified} bounded={recomputed_bounded}")

# 3. Verify CycloneDX SBOM digests if present in manifest
sbom_meta = manifest.get("sbom")
if sbom_meta:
    for sbom_file, key in (
        ("sbom.cargo.cdx.json", "cargo_sbom_sha256"),
        ("sbom.python.cdx.json", "python_sbom_sha256"),
    ):
        sbom_path = repo_root / sbom_file
        if not sbom_path.is_file():
            fail(f"Missing SBOM file required by manifest: {sbom_file}", check_name="cyclonedx_sbom")
        digest = hashlib.sha256(sbom_path.read_bytes()).hexdigest()
        if digest != sbom_meta.get(key):
            fail(f"SBOM SHA-256 mismatch for {sbom_file}", check_name="cyclonedx_sbom")
    record_check("cyclonedx_sbom", "PASS", True, "cargo+python")
else:
    record_check("cyclonedx_sbom", "NOT_CHECKED", False, "not declared in manifest")

# 3b. Verify governance root artifacts and public source_tree_digest
artifacts_meta = manifest.get("artifacts_sha256")
if isinstance(artifacts_meta, dict) and artifacts_meta:
    for rel_artifact, expected_art_digest in artifacts_meta.items():
        art_path = repo_root / rel_artifact
        if not art_path.is_file():
            fail(f"Missing governance artifact required by manifest: {rel_artifact}", check_name="governance_artifacts")
        actual_art_digest = hashlib.sha256(art_path.read_bytes()).hexdigest()
        if actual_art_digest != expected_art_digest:
            fail(
                f"Governance artifact SHA-256 mismatch for {rel_artifact}: "
                f"expected {expected_art_digest}, got {actual_art_digest}",
                check_name="governance_artifacts",
            )
    record_check("governance_artifacts", "PASS", True, f"files={len(artifacts_meta)}")
else:
    record_check("governance_artifacts", "NOT_CHECKED", False, "not declared in manifest")

if not str(manifest.get("source_tree_digest") or "").strip():
    fail("Missing required source_tree_digest in RELEASE_MANIFEST.json", check_name="source_tree_digest")
actual_tree_digest, expected_tree_digest, tree_reason = compute_public_tree_digest(repo_root, manifest)
if actual_tree_digest is None:
    fail(
        f"Mandatory check source_tree_digest is NOT_CHECKED: {tree_reason}",
        check_name="source_tree_digest",
        status="NOT_CHECKED",
        required=True,
    )
if actual_tree_digest != expected_tree_digest:
    fail(
        f"Public source_tree_digest mismatch against RELEASE_MANIFEST.json: "
        f"expected {expected_tree_digest}, got {actual_tree_digest}",
        check_name="source_tree_digest",
    )
record_check("source_tree_digest", "PASS", True, f"sha256={actual_tree_digest[:16]}...")

# 4. Verify packaged release bundle if specified or recorded in manifest
bundle_meta = manifest.get("release_bundle")
if bundle_arg:
    bpath = Path(bundle_arg)
    if not bpath.is_file():
        fail(f"Specified release bundle does not exist: {bpath}", check_name="release_bundle")
    if not isinstance(bundle_meta, dict) or not bundle_meta.get("sha256"):
        fail(
            "Mandatory check release_bundle is NOT_CHECKED: --bundle was specified "
            "but RELEASE_MANIFEST.json has no verifiable release_bundle.sha256 reference",
            check_name="release_bundle",
            status="NOT_CHECKED",
            required=True,
        )
    bsha = hashlib.sha256(bpath.read_bytes()).hexdigest()
    if bundle_meta.get("sha256") != bsha:
        fail(
            f"Release bundle SHA-256 mismatch: manifest={bundle_meta.get('sha256')} actual={bsha}",
            check_name="release_bundle",
        )
    record_check("release_bundle", "PASS", True, f"sha256={bsha[:16]}...")
elif isinstance(bundle_meta, dict) and bundle_meta.get("sha256"):
    bpath = repo_root / "dist" / str(bundle_meta.get("name", ""))
    if bpath.is_file():
        bsha = hashlib.sha256(bpath.read_bytes()).hexdigest()
        if bundle_meta.get("sha256") != bsha:
            fail(f"Release bundle SHA-256 mismatch in dist/: {bpath.name}", check_name="release_bundle")
        record_check("release_bundle", "PASS", True, f"dist/{bpath.name}")
    else:
        record_check("release_bundle", "NOT_CHECKED", False, f"dist/{bpath.name} not present locally")
else:
    record_check("release_bundle", "NOT_CHECKED", False, "no bundle requested")

# 5. Verify canonical body and detached Ed25519 signature
manifest_body = {k: v for k, v in manifest.items() if k != "signature"}
canonical_bytes = json.dumps(manifest_body, sort_keys=True).encode("utf-8")
sig_hex = manifest.get("signature")
auth = manifest.get("signing_authority") or {}
manifest_pubkey = (auth.get("public_key") or "").strip().lower()

if require_sig and not sig_hex:
    fail(
        "Signature required (--require-signature) but RELEASE_MANIFEST.json is unsigned",
        check_name="cryptographic_signature",
        status="NOT_CHECKED",
        required=True,
    )

if expected_pubkey and manifest_pubkey != expected_pubkey:
    fail(
        f"Signing authority public key mismatch: expected {expected_pubkey}, got {manifest_pubkey}",
        check_name="cryptographic_signature",
    )

if sig_hex:
    if not manifest_pubkey:
        fail("Signature present without public_key in signing_authority", check_name="cryptographic_signature")
    sig_file = repo_root / "RELEASE_MANIFEST.json.sig"
    if sig_file.is_file():
        sig_doc = json.loads(sig_file.read_text(encoding="utf-8"))
        if sig_doc.get("signature") != sig_hex or sig_doc.get("public_key", "").lower() != manifest_pubkey:
            fail(
                "Detached RELEASE_MANIFEST.json.sig does not match RELEASE_MANIFEST.json",
                check_name="cryptographic_signature",
            )
        if sig_doc.get("canonical_body_sha256") != hashlib.sha256(canonical_bytes).hexdigest():
            fail(
                "Detached RELEASE_MANIFEST.json.sig canonical_body_sha256 mismatch",
                check_name="cryptographic_signature",
            )

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
            fail(
                f"Ed25519 cryptographic signature verification failed: {res.stderr.strip()}",
                check_name="cryptographic_signature",
            )
    record_check("cryptographic_signature", "PASS", True, "Ed25519")
else:
    record_check("cryptographic_signature", "NOT_CHECKED", False, "unsigned manifest")

# Final fail-closed invariant gate: any FAIL or any required check in NOT_CHECKED blocks [VERIFIED]
for check_name, check_status, is_req, detail in checks:
    if check_status == "FAIL" or (is_req and check_status != "PASS"):
        emit_checks(sys.stderr)
        print(
            f"[FAIL-CLOSED] Verification gate blocked by {check_name}={check_status} (required={is_req}): {detail}",
            file=sys.stderr,
        )
        raise SystemExit(1)

emit_checks(sys.stdout)
pass_count = sum(1 for _, st, _, _ in checks if st == "PASS")
not_checked_count = sum(1 for _, st, _, _ in checks if st == "NOT_CHECKED")
print(
    f"[VERIFIED] release=v{manifest.get('release')} commit={manifest.get('commit')[:12]} "
    f"claims={len(entries)} merkle={expected_root[:25]}... "
    f"signed={'yes' if sig_hex else 'no'} "
    f"checks_pass={pass_count} checks_not_checked={not_checked_count}"
)
PY

if [[ -n "$VERIFY_OIDC_REPO" && -n "$BUNDLE_PATH" ]]; then
  echo "[OIDC] Verifying GitHub SLSA Build Provenance via gh attestation verify..."
  gh attestation verify "$BUNDLE_PATH" --repo "$VERIFY_OIDC_REPO"
fi
