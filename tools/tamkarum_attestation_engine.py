#!/usr/bin/env python3
"""Local JSON evidence manifests and Ed25519 verification.

Schema tamkarum-evidence/v2 authenticates the complete header and payload using
the domain BABYLON60:TAMKARUM:ATTESTATION:v2 followed by a NUL byte and UTF-8 JSON
(sorted keys, compact separators, ensure_ascii=False, finite numbers only).
The signature field is excluded. This is not COSE, registered SCITT or hardware
attestation. --emit creates an explicitly unsigned manifest; an authorized
external signer must set header.algorithm=Ed25519 and sign that body.
"""

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

BASE_DIR = Path(__file__).absolute().parent.parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"
OUTREACH_MANIFEST = CAMPAIGNS_DIR / "outreach_manifest_consolidated.json"
SOCIAL_CALENDAR = CAMPAIGNS_DIR / "social_30day_calendar.json"
COMPLIANCE_PACK = BASE_DIR / "reports" / "eu_ai_act_compliance_pack.json"
ATTESTATION_STATEMENT_PATH = CAMPAIGNS_DIR / "SCITT_ATTESTATION_STATEMENT.json"
SCHEMA = "tamkarum-evidence/v2"
SIGNING_DOMAIN = b"BABYLON60:TAMKARUM:ATTESTATION:v2\0"
PAYLOAD_DOMAIN = b"BABYLON60:TAMKARUM:PAYLOAD:v2\0"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _read_json(data: bytes) -> Any:
    return json.loads(data, object_pairs_hook=_unique_pairs)


def _valid_hex(value: Any, lengths: tuple[int, ...]) -> bool:
    return (type(value) is str and len(value) in lengths
            and re.fullmatch(r"[0-9a-f]+", value) is not None
            and value != "0" * len(value))


def get_git_head_commit() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR),
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""  # No invented zero-hash state.


def compute_topology_sha256() -> str:
    """Hash named roster lists with unambiguous boundaries."""
    root = str(BASE_DIR / "02_EDIN_SWARMS")
    if root not in sys.path:
        sys.path.insert(0, root)
    from agents_archi import DistributionDesignTeam, SocialMediaTeam

    topology = {
        "distribution": [a.canonical_name for a in DistributionDesignTeam.list_team()],
        "social": [a.canonical_name for a in SocialMediaTeam.list_team()],
    }
    return hashlib.sha256(_canonical(topology)).hexdigest()


def compute_file_sha256(path: Path) -> str:
    """Missing/unreadable files are errors, never successful zero digests."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _default_paths() -> dict[str, Path]:
    return {"outreach_manifest": OUTREACH_MANIFEST,
            "social_calendar": SOCIAL_CALENDAR, "compliance_pack": COMPLIANCE_PACK}


def _read_evidence(paths: Mapping[str, Path]) -> tuple[dict[str, str], str]:
    if set(paths) != set(_default_paths()):
        raise ValueError("Exactly three externally selected evidence references are required")
    contents = {name: Path(path).read_bytes() for name, path in paths.items()}
    manifest = _read_json(contents["outreach_manifest"])
    if type(manifest) is not dict or not _valid_hex(manifest.get("global_consolidated_merkle_root"), (64,)):
        raise ValueError("Outreach manifest needs a valid declared root")
    return ({name: hashlib.sha256(data).hexdigest() for name, data in contents.items()},
            manifest["global_consolidated_merkle_root"])


def _compound(payload: dict[str, Any]) -> str:
    return hashlib.sha256(PAYLOAD_DOMAIN + _canonical(payload)).hexdigest()


def generate_attestation_statement() -> dict[str, Any]:
    """Write an unsigned snapshot, without asserting audit or compliance results."""
    commit = get_git_head_commit()
    topology = compute_topology_sha256()
    digests, root = _read_evidence(_default_paths())
    if not _valid_hex(commit, (40, 64)) or not _valid_hex(topology, (64,)):
        raise ValueError("Current commit/topology unavailable")
    payload = {"git_commit": commit, "topology_sha256": topology,
               "outreach_root": root, "evidence_sha256": digests}
    payload["compound_attestation_hash"] = _compound(payload)
    statement = {"header": {"schema": SCHEMA, "algorithm": "UNSIGNED"}, "payload": payload}
    ATTESTATION_STATEMENT_PATH.write_text(json.dumps(statement, indent=2, ensure_ascii=False), encoding="utf-8")
    print("UNSIGNED: snapshot written; provenance is NO_VERIFICADO")
    return statement


def verify_attestation(
    statement_path: Optional[Path] = None, *, trusted_public_key: Optional[bytes] = None,
    evidence_paths: Optional[Mapping[str, Path]] = None, expected_commit: Optional[str] = None,
    expected_topology_sha256: Optional[str] = None,
) -> bool:
    """Verify signed bytes and correspondence to explicit current references.

    Trust comes exclusively from the caller's raw Ed25519 public key. Evidence
    paths and optional offline commit/topology expectations are also caller
    inputs; no document-supplied path or key is used. This does not prove the
    truth of a campaign claim, hardware attestation, key freshness or revocation.
    """
    try:
        if type(trusted_public_key) is not bytes or len(trusted_public_key) != 32:
            raise ValueError("External trusted raw Ed25519 key required")
        document = _read_json(Path(statement_path or ATTESTATION_STATEMENT_PATH).read_bytes())
        if type(document) is not dict or set(document) != {"header", "payload", "signature"}:
            raise ValueError("Signed v2 document required")
        header, payload, signature = document["header"], document["payload"], document["signature"]
        if header != {"schema": SCHEMA, "algorithm": "Ed25519"}:
            raise ValueError("Unsupported signed schema")
        if (type(signature) is not dict or set(signature) != {"algorithm", "value"}
                or signature["algorithm"] != "Ed25519" or type(signature["value"]) is not str):
            raise ValueError("Invalid signature envelope")
        signed_body = {"header": header, "payload": payload}
        Ed25519PublicKey.from_public_bytes(trusted_public_key).verify(
            base64.b64decode(signature["value"], validate=True), SIGNING_DOMAIN + _canonical(signed_body))
        if type(payload) is not dict or set(payload) != {
            "git_commit", "topology_sha256", "outreach_root", "evidence_sha256", "compound_attestation_hash",
        }:
            raise ValueError("Invalid payload schema")
        fields = {k: v for k, v in payload.items() if k != "compound_attestation_hash"}
        if not _valid_hex(payload["compound_attestation_hash"], (64,)) or _compound(fields) != payload["compound_attestation_hash"]:
            raise ValueError("Invalid compound digest")
        commit = get_git_head_commit() if expected_commit is None else expected_commit
        topology = compute_topology_sha256() if expected_topology_sha256 is None else expected_topology_sha256
        if (not _valid_hex(commit, (40, 64)) or not _valid_hex(topology, (64,))
                or payload["git_commit"] != commit or payload["topology_sha256"] != topology):
            raise ValueError("Current commit/topology mismatch")
        digests, root = _read_evidence(_default_paths() if evidence_paths is None else evidence_paths)
        if payload["evidence_sha256"] != digests or payload["outreach_root"] != root:
            raise ValueError("Current evidence mismatch")
    except (OSError, ValueError, TypeError, KeyError, RecursionError, InvalidSignature, UnsupportedAlgorithm):
        print("NO_VERIFICADO: trusted signature, schema or current evidence rejected")
        return False
    print("VERIFICADO: Ed25519 body and correspondence to outreach_manifest, social_calendar, compliance_pack")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Local JSON evidence verification (tamkarum-evidence/v2)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", action="store_true", help="Write an UNSIGNED snapshot")
    mode.add_argument("--verify", action="store_true", help="Verify a signed snapshot and current evidence")
    parser.add_argument("--statement", type=Path)
    parser.add_argument("--trusted-key", type=Path, help="Externally authorized raw 32-byte Ed25519 public key")
    parser.add_argument("--expected-commit", help="Explicit trusted offline commit expectation; default current HEAD")
    parser.add_argument("--expected-topology-sha256", help="Explicit trusted offline topology; default current roster")
    parser.add_argument("--outreach-manifest", type=Path)
    parser.add_argument("--social-calendar", type=Path)
    parser.add_argument("--compliance-pack", type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            key = args.trusted_key.read_bytes() if args.trusted_key else None
            return 0 if verify_attestation(
                args.statement, trusted_public_key=key,
                evidence_paths={"outreach_manifest": args.outreach_manifest or OUTREACH_MANIFEST,
                                "social_calendar": args.social_calendar or SOCIAL_CALENDAR,
                                "compliance_pack": args.compliance_pack or COMPLIANCE_PACK},
                expected_commit=args.expected_commit, expected_topology_sha256=args.expected_topology_sha256,
            ) else 1
        if any(value is not None for value in (
            args.statement, args.trusted_key, args.outreach_manifest, args.social_calendar,
            args.compliance_pack, args.expected_commit, args.expected_topology_sha256,
        )):
            parser.error("Evidence paths, trusted key and expectations apply only to --verify")
        generate_attestation_statement()
        return 0
    except (OSError, ValueError, UnsupportedAlgorithm):
        print("NO_VERIFICADO: evidence input or output unavailable")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
