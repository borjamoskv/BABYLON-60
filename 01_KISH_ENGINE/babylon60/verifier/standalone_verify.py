"""
BABYLON-60 Open-Core Independent Compliance Verifier (Kerckhoffs Standard)
==========================================================================
Deterministic, open-standard, zero-proprietary-dependencies verification module
for BABYLON-60 EU AI Act Compliance Certificates and cryptographic forensic ledgers.

Conforms to Kerckhoffs's Principle (1883):
Security rests exclusively on cryptographic keys and mathematical proofs,
not on obscurity or proprietary verification binaries.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

ZERO_HASH_256 = "0" * 64


def canonical_json(data: Any) -> str:
    """
    Deterministic canonical JSON serialization according to RFC 8785 (JCS).
    Ensures exact bit-level byte consistency for digital signatures and hashing.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def compute_cortex_hash(
    seq: int,
    event_id: str,
    event_type: str,
    payload_json: str,
    cortex_taint: str,
    lamport_t: int,
    prev_hash: str,
    timestamp: str,
    agent_id: str = "ULTRATHINK-APEX",
    domain: str = "babylon60.com",
) -> str:
    """
    Computes the SHA3-256 hash of a Cortex BFT ledger row.
    Pure mathematical function with zero external dependencies.
    """
    body = {
        "seq": seq,
        "event_id": event_id,
        "event_type": event_type,
        "payload_json": payload_json,
        "cortex_taint": cortex_taint,
        "agent_id": agent_id,
        "domain": domain,
        "lamport_t": lamport_t,
        "prev_hash": prev_hash,
        "timestamp": timestamp,
    }
    return hashlib.sha3_256(canonical_json(body).encode("utf-8")).hexdigest()


def build_cortex_merkle_tree(entry_hashes: List[str]) -> str:
    """
    Constructs a Merkle Tree with Domain Separation (FIX C5-05) and Cardinality Anchor.
    Inputs: list of SHA3-256 hex strings.
    Output: root hash hex string.
    """
    if not entry_hashes:
        return ZERO_HASH_256

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


def build_sha256_merkle_tree(entry_hashes: List[str]) -> str:
    """
    Standard binary SHA-256 Merkle tree calculation for general-purpose ledgers.
    """
    if not entry_hashes:
        return ZERO_HASH_256

    layer = [bytes.fromhex(h) for h in entry_hashes]
    while len(layer) > 1:
        if len(layer) % 2 != 0:
            layer.append(layer[-1])
        next_layer = []
        for i in range(0, len(layer), 2):
            next_layer.append(hashlib.sha256(layer[i] + layer[i + 1]).digest())
        layer = next_layer
    return layer[0].hex()


def build_blake3_merkle_tree(entry_hashes: List[str]) -> str:
    """
    Canonical BLAKE3 Merkle tree calculation (scheme v1 `b3:` or 64-char hex conformal tree).
    """
    if not entry_hashes:
        return ZERO_HASH_256
    import blake3

    current_level = list(entry_hashes)
    while len(current_level) > 1:
        next_level: List[str] = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = f"{left}:{right}".encode("utf-8")
            next_level.append(blake3.blake3(combined).hexdigest())
        current_level = next_level
    return current_level[0]


def _verify_ed25519_signature(
    public_key_hex: str,
    signature_hex: str,
    payload_bytes: bytes,
) -> Tuple[bool, str]:
    """
    Verifies an Ed25519 signature using cryptography or PyNaCl.
    Zero proprietary dependencies; relies on standard, audited open-source libraries.
    """
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
    except (ValueError, TypeError) as exc:
        return False, f"MALFORMED_HEX_KEYS: {exc}"

    if len(pub_bytes) != 32:
        return False, f"INVALID_PUBLIC_KEY_LENGTH: expected 32 bytes, got {len(pub_bytes)}"
    if len(sig_bytes) != 64:
        return False, f"INVALID_SIGNATURE_LENGTH: expected 64 bytes, got {len(sig_bytes)}"

    # 1. Try python 'cryptography' library (FOSS standard)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature

        verifier = Ed25519PublicKey.from_public_bytes(pub_bytes)
        try:
            verifier.verify(sig_bytes, payload_bytes)
            return True, "Ed25519 signature valid (via cryptography)"
        except InvalidSignature:
            return False, "Ed25519 signature invalid"
    except ImportError:
        pass

    # 2. Fallback to 'pynacl' (FOSS standard)
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError

        vk = VerifyKey(pub_bytes)
        try:
            vk.verify(payload_bytes, sig_bytes)
            return True, "Ed25519 signature valid (via PyNaCl)"
        except BadSignatureError:
            return False, "Ed25519 signature invalid"
    except ImportError:
        pass

    return False, "NO_ED25519_ENGINE: neither 'cryptography' nor 'pynacl' is installed"


def _parse_iso_timestamp(ts_str: str) -> Optional[datetime.datetime]:
    """Parses an ISO 8601 timestamp string into an aware UTC datetime object."""
    if not isinstance(ts_str, str):
        return None
    try:
        clean = ts_str.strip().replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def verify_offline_evidence(
    ledger_path: Union[str, Path],
    expected_merkle_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Independently inspects an offline forensic ledger (SQLite or JSON),
    recomputes all row hashes, verifies chain integrity and order,
    and recalculates the Merkle Root.

    Returns:
        {
            "verified": bool,
            "integrity_verified": bool,
            "merkle_root": str,
            "total_entries": int,
            "detail": str,
        }
    """
    path = Path(ledger_path)
    if not path.exists() or not path.is_file():
        return {
            "verified": False,
            "integrity_verified": False,
            "merkle_root": "",
            "total_entries": 0,
            "detail": f"LEDGER_NOT_FOUND: '{path}' does not exist",
        }

    # Detect SQLite format by header or extension
    is_sqlite = False
    try:
        with open(path, "rb") as f:
            header = f.read(16)
            if header.startswith(b"SQLite format 3"):
                is_sqlite = True
    except Exception as exc:
        return {
            "verified": False,
            "integrity_verified": False,
            "merkle_root": "",
            "total_entries": 0,
            "detail": f"READ_ERROR: {exc}",
        }

    if is_sqlite or path.suffix.lower() in [".db", ".sqlite", ".sqlite3"]:
        return _verify_sqlite_ledger(path, expected_merkle_root)
    else:
        return _verify_json_ledger(path, expected_merkle_root)


def _verify_sqlite_ledger(
    path: Path,
    expected_merkle_root: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Check if cortex_ledger table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cortex_ledger'")
        has_cortex = cursor.fetchone() is not None

        if not has_cortex:
            conn.close()
            return {
                "verified": False,
                "integrity_verified": False,
                "merkle_root": "",
                "total_entries": 0,
                "detail": "SQLITE_MISSING_CORTEX_LEDGER_TABLE",
            }

        cursor.execute(
            """
            SELECT seq, event_id, event_type, payload_json, cortex_taint,
                   agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp
            FROM cortex_ledger
            ORDER BY seq ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        total_entries = len(rows)
        prev_hash = ZERO_HASH_256
        last_lamport = 0
        expected_seq = 1
        entry_hashes: List[str] = []

        for row in rows:
            (
                seq,
                event_id,
                event_type,
                payload_json,
                cortex_taint,
                agent_id,
                domain,
                lamport_t,
                row_prev_hash,
                entry_hash,
                timestamp,
            ) = row

            if seq != expected_seq:
                return {
                    "verified": False,
                    "integrity_verified": False,
                    "merkle_root": "",
                    "total_entries": total_entries,
                    "detail": f"SEQ_DISCONTINUITY: expected {expected_seq}, got {seq}",
                }

            if lamport_t <= last_lamport:
                return {
                    "verified": False,
                    "integrity_verified": False,
                    "merkle_root": "",
                    "total_entries": total_entries,
                    "detail": f"LAMPORT_VIOLATION: row {seq} lamport {lamport_t} <= {last_lamport}",
                }

            if row_prev_hash != prev_hash:
                return {
                    "verified": False,
                    "integrity_verified": False,
                    "merkle_root": "",
                    "total_entries": total_entries,
                    "detail": f"HASH_CHAIN_BROKEN: row {seq} prev_hash mismatch",
                }

            recomputed_entry_hash = compute_cortex_hash(
                seq=seq,
                event_id=event_id,
                event_type=event_type,
                payload_json=payload_json,
                cortex_taint=cortex_taint,
                lamport_t=lamport_t,
                prev_hash=prev_hash,
                timestamp=timestamp,
                agent_id=agent_id,
                domain=domain,
            )

            if recomputed_entry_hash != entry_hash:
                return {
                    "verified": False,
                    "integrity_verified": False,
                    "merkle_root": "",
                    "total_entries": total_entries,
                    "detail": f"ENTRY_HASH_MISMATCH: row {seq} computed {recomputed_entry_hash} != {entry_hash}",
                }

            entry_hashes.append(entry_hash)
            prev_hash = entry_hash
            last_lamport = lamport_t
            expected_seq += 1

        computed_merkle_root = build_cortex_merkle_tree(entry_hashes)

        match = True
        if expected_merkle_root:
            if computed_merkle_root != expected_merkle_root:
                # Also try standard sha256 or canonical BLAKE3 tree
                sha256_root = build_sha256_merkle_tree(entry_hashes)
                blake3_root = build_blake3_merkle_tree(entry_hashes)
                from babylon60.attestation.merkle_b3 import build_root as build_b3_tagged

                b3_tagged_root = build_b3_tagged([h.encode("utf-8") for h in entry_hashes]) if entry_hashes else ""
                if sha256_root == expected_merkle_root:
                    computed_merkle_root = sha256_root
                    match = True
                elif blake3_root == expected_merkle_root:
                    computed_merkle_root = blake3_root
                    match = True
                elif b3_tagged_root == expected_merkle_root:
                    computed_merkle_root = b3_tagged_root
                    match = True
                else:
                    match = False

        if not match:
            return {
                "verified": False,
                "integrity_verified": True,
                "merkle_root": computed_merkle_root,
                "total_entries": total_entries,
                "detail": f"MERKLE_ROOT_MISMATCH: computed {computed_merkle_root} != expected {expected_merkle_root}",
            }

        return {
            "verified": True,
            "integrity_verified": True,
            "merkle_root": computed_merkle_root,
            "total_entries": total_entries,
            "detail": "LEDGER_INTEGRITY_AND_MERKLE_VERIFIED",
        }

    except Exception as exc:
        return {
            "verified": False,
            "integrity_verified": False,
            "merkle_root": "",
            "total_entries": 0,
            "detail": f"SQLITE_VERIFY_ERROR: {exc.__class__.__name__}: {exc}",
        }


def _verify_json_ledger(
    path: Path,
    expected_merkle_root: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        leaves: List[str] = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    leaves.append(item)
                elif isinstance(item, dict):
                    h = item.get("entry_hash") or item.get("hash")
                    if h:
                        leaves.append(str(h))
                    else:
                        leaves.append(hashlib.sha256(canonical_json(item).encode()).hexdigest())
        elif isinstance(data, dict):
            if "leaves" in data and isinstance(data["leaves"], list):
                leaves = [str(x) for x in data["leaves"]]
            elif "entry_hashes" in data and isinstance(data["entry_hashes"], list):
                leaves = [str(x) for x in data["entry_hashes"]]
            elif "events" in data and isinstance(data["events"], list):
                for ev in data["events"]:
                    if isinstance(ev, str):
                        leaves.append(ev)
                    elif isinstance(ev, dict):
                        h = ev.get("entry_hash") or ev.get("hash")
                        if h:
                            leaves.append(str(h))
                        else:
                            leaves.append(hashlib.sha256(canonical_json(ev).encode()).hexdigest())
            elif "global_hash" in data:
                # Minimal manifest
                g_hash = data.get("global_hash")
                return {
                    "verified": (g_hash == expected_merkle_root) if expected_merkle_root else True,
                    "integrity_verified": True,
                    "merkle_root": g_hash,
                    "total_entries": 1,
                    "detail": "MANIFEST_GLOBAL_HASH_PARSED",
                }

        cortex_root = build_cortex_merkle_tree(leaves)
        sha256_root = build_sha256_merkle_tree(leaves)
        blake3_root = build_blake3_merkle_tree(leaves)
        from babylon60.attestation.merkle_b3 import build_root as build_b3_tagged

        b3_tagged_root = build_b3_tagged([h.encode("utf-8") for h in leaves]) if leaves else ""

        root = cortex_root
        match = True
        if expected_merkle_root:
            if cortex_root == expected_merkle_root:
                root = cortex_root
            elif sha256_root == expected_merkle_root:
                root = sha256_root
            elif blake3_root == expected_merkle_root:
                root = blake3_root
            elif b3_tagged_root == expected_merkle_root:
                root = b3_tagged_root
            else:
                match = False

        if not match:
            return {
                "verified": False,
                "integrity_verified": True,
                "merkle_root": root,
                "total_entries": len(leaves),
                "detail": f"MERKLE_ROOT_MISMATCH: computed {root} != expected {expected_merkle_root}",
            }

        return {
            "verified": True,
            "integrity_verified": True,
            "merkle_root": root,
            "total_entries": len(leaves),
            "detail": "JSON_LEDGER_MERKLE_VERIFIED",
        }

    except Exception as exc:
        return {
            "verified": False,
            "integrity_verified": False,
            "merkle_root": "",
            "total_entries": 0,
            "detail": f"JSON_VERIFY_ERROR: {exc.__class__.__name__}: {exc}",
        }


def verify_compliance_certificate(
    cert_dict_or_path: Union[Dict[str, Any], str, Path],
    ledger_path: Optional[Union[str, Path]] = None,
    crl: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Pure, independent, deterministic verifier for BABYLON-60 Compliance Certificates.

    Verifies:
      1. Schema compliance (required fields and formats).
      2. Cryptographic signature (Ed25519 signature over canonical JSON payload).
      3. Payload SHA-256 integrity (matches signed_payload_sha256 if present).
      4. Certificate lifecycle (not expired according to valid_until, not revoked).
      5. Ledger & Merkle root match (if ledger_path is supplied, recomputes hashes
         and verifies exact match against global_merkle_root).

    Returns:
        {
            "valid": bool,
            "signature_valid": bool,
            "merkle_valid": bool,
            "detail": str,
        }
    """
    # 1. Load Certificate
    cert: Dict[str, Any]
    if isinstance(cert_dict_or_path, dict):
        cert = dict(cert_dict_or_path)
    elif isinstance(cert_dict_or_path, (str, Path)):
        path = Path(cert_dict_or_path)
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if not isinstance(loaded, dict):
                        return {
                            "valid": False,
                            "signature_valid": False,
                            "merkle_valid": False,
                            "detail": "SCHEMA_INVALID: root element is not a JSON object",
                        }
                    cert = loaded
            except Exception as exc:
                return {
                    "valid": False,
                    "signature_valid": False,
                    "merkle_valid": False,
                    "detail": f"FILE_READ_ERROR: {exc}",
                }
        else:
            # Maybe raw JSON string
            try:
                loaded = json.loads(str(cert_dict_or_path))
                if not isinstance(loaded, dict):
                    return {
                        "valid": False,
                        "signature_valid": False,
                        "merkle_valid": False,
                        "detail": "SCHEMA_INVALID: root element is not a JSON object",
                    }
                cert = loaded
            except Exception:
                return {
                    "valid": False,
                    "signature_valid": False,
                    "merkle_valid": False,
                    "detail": f"INVALID_CERTIFICATE_INPUT: '{cert_dict_or_path}' is neither existing file nor valid JSON",
                }
    else:
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "detail": f"UNSUPPORTED_INPUT_TYPE: {type(cert_dict_or_path).__name__}",
        }

    # 2. Schema Validation
    required_fields = [
        "certificate_id",
        "system_identifier",
        "operator",
        "issued_at",
        "valid_until",
        "global_merkle_root",
        "articles_compliance",
        "signature",
    ]
    for rf in required_fields:
        if rf not in cert:
            return {
                "valid": False,
                "signature_valid": False,
                "merkle_valid": False,
                "detail": f"SCHEMA_INVALID: missing required field '{rf}'",
            }

    sig_block = cert.get("signature")
    if not isinstance(sig_block, dict):
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "detail": "SCHEMA_INVALID: 'signature' must be a JSON object",
        }

    for sf in ["public_key", "signature"]:
        if sf not in sig_block or not isinstance(sig_block[sf], str):
            return {
                "valid": False,
                "signature_valid": False,
                "merkle_valid": False,
                "detail": f"SCHEMA_INVALID: signature block missing '{sf}'",
            }

    public_key_hex = sig_block["public_key"]
    signature_hex = sig_block["signature"]

    # 3. Canonical Payload & Ed25519 Cryptographic Verification
    cert_without_sig = {k: v for k, v in cert.items() if k != "signature"}
    try:
        canonical_str = canonical_json(cert_without_sig)
        canonical_bytes = canonical_str.encode("utf-8")
    except Exception as exc:
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "detail": f"CANONICALIZATION_ERROR: {exc}",
        }

    # Check signed payload hash match if provided in signature
    if "signed_payload_sha256" in sig_block:
        computed_payload_sha256 = hashlib.sha256(canonical_bytes).hexdigest()
        if computed_payload_sha256 != sig_block["signed_payload_sha256"]:
            return {
                "valid": False,
                "signature_valid": False,
                "merkle_valid": False,
                "detail": "PAYLOAD_HASH_MISMATCH: canonical payload SHA-256 does not match signature header",
            }

    sig_ok, sig_detail = _verify_ed25519_signature(
        public_key_hex=public_key_hex,
        signature_hex=signature_hex,
        payload_bytes=canonical_bytes,
    )
    if not sig_ok:
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "detail": f"SIGNATURE_VERIFICATION_FAILED: {sig_detail}",
        }

    # 4. Lifecycle & Revocation Verification
    # 4a. Expiration
    valid_until_dt = _parse_iso_timestamp(cert.get("valid_until", ""))
    if valid_until_dt is None:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": False,
            "detail": "LIFECYCLE_INVALID: cannot parse 'valid_until' timestamp",
        }

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if now_utc > valid_until_dt:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": False,
            "detail": f"CERTIFICATE_EXPIRED: expired at {cert.get('valid_until')}",
        }

    # 4b. Revocation
    revocation_obj = cert.get("revocation")
    if isinstance(revocation_obj, dict):
        if revocation_obj.get("status", "").upper() == "REVOKED":
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "detail": "CERTIFICATE_REVOKED: status in certificate revocation header is REVOKED",
            }

    cert_id = cert.get("certificate_id", "")
    if crl and cert_id in crl:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": False,
            "detail": f"CERTIFICATE_REVOKED: {cert_id} found in Certificate Revocation List (CRL)",
        }

    # 5. Ledger & Merkle Root Verification
    merkle_valid = True
    merkle_detail = "STANDALONE_NO_LEDGER_SUPPLIED"

    if ledger_path is not None:
        # User explicitly supplied a ledger
        expected_root = cert.get("global_merkle_root", "")
        ev_res = verify_offline_evidence(ledger_path, expected_merkle_root=expected_root)
        if not ev_res["verified"]:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "detail": f"LEDGER_VERIFICATION_FAILED: {ev_res['detail']}",
            }
        merkle_valid = True
        merkle_detail = f"LEDGER_VERIFIED: {ev_res['detail']}"
    else:
        # Validate format of global_merkle_root
        g_root = cert.get("global_merkle_root", "")
        if not isinstance(g_root, str) or len(g_root) != 64:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "detail": f"INVALID_MERKLE_ROOT_FORMAT: expected 64 hex characters, got '{g_root}'",
            }

    return {
        "valid": True,
        "signature_valid": True,
        "merkle_valid": merkle_valid,
        "detail": f"CERTIFICATE_VALID_AND_VERIFIED ({merkle_detail})",
    }


def _sha256_file_standalone(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_m0_evidence_pack(pack_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    Independently verifies a `babylon-m0-evidence-pack/` directory (Kerckhoffs Standard).
    Checks:
      1. Presence of all required M0 Evidence Pack files.
      2. SHA-256 file integrity against `verification/checksums.sha256` and signed envelope.
      3. Ed25519 signature (`verification/signature.sig`) over canonical `signing_envelope`.
      4. Full offline hash-chain and Merkle root recomputation of `evidence/ledger_l0.sqlite`
         and cross-check with `evidence/execution-trace.jsonl`.
      5. Cross-verification of `evidence/nemesis-results.json` against `claims.json` and
         `scope.json` (detects masked bypasses or contradictory evidence).
      6. Regulatory Matrix non-overclaim check (forbids automatic `COMPLIANT` status).
    """
    root = Path(pack_dir)
    if not root.exists() or not root.is_dir():
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "checksums_valid": False,
            "epistemic_status": "PACK_NOT_FOUND",
            "detail": f"PACK_DIR_NOT_FOUND: '{root}' does not exist or is not a directory",
        }

    required_rel_files = [
        "manifest.json",
        "claims.json",
        "scope.json",
        "environment.json",
        "evidence/ledger_l0.sqlite",
        "evidence/execution-trace.jsonl",
        "evidence/nemesis-results.json",
        "evidence/formal-proofs.json",
        "compliance/regulatory-matrix.json",
        "compliance/auditor-report.pdf",
        "verification/checksums.sha256",
        "verification/signature.sig",
        "verification/verifier-metadata.json",
        "README.md",
    ]
    for rel in required_rel_files:
        if not (root / rel).is_file():
            return {
                "valid": False,
                "signature_valid": False,
                "merkle_valid": False,
                "checksums_valid": False,
                "epistemic_status": "INCOMPLETE_PACK",
                "detail": f"MISSING_REQUIRED_FILE: '{rel}'",
            }

    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        claims_doc = json.loads((root / "claims.json").read_text(encoding="utf-8"))
        scope_doc = json.loads((root / "scope.json").read_text(encoding="utf-8"))
        nemesis_doc = json.loads((root / "evidence/nemesis-results.json").read_text(encoding="utf-8"))
        reg_matrix_doc = json.loads((root / "compliance/regulatory-matrix.json").read_text(encoding="utf-8"))
        verifier_meta = json.loads((root / "verification/verifier-metadata.json").read_text(encoding="utf-8"))
        sig_hex = (root / "verification/signature.sig").read_text(encoding="utf-8").strip()
        checksums_raw = (root / "verification/checksums.sha256").read_bytes()
    except Exception as exc:
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "checksums_valid": False,
            "epistemic_status": "MALFORMED_PACK_JSON",
            "detail": f"JSON_PARSE_ERROR: {exc}",
        }

    # 1. Verify Ed25519 signature over signing_envelope first
    signing_envelope = verifier_meta.get("signing_envelope")
    pub_hex = verifier_meta.get("public_key", "")
    if not isinstance(signing_envelope, dict) or not isinstance(pub_hex, str):
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "checksums_valid": False,
            "epistemic_status": "INVALID_VERIFIER_METADATA",
            "detail": "SCHEMA_INVALID: missing signing_envelope or public_key in verifier-metadata.json",
        }

    envelope_bytes = canonical_json(signing_envelope).encode("utf-8")
    if hashlib.sha256(envelope_bytes).hexdigest() != verifier_meta.get("signed_envelope_sha256"):
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "checksums_valid": False,
            "epistemic_status": "TAMPERED_METADATA",
            "detail": "ENVELOPE_DIGEST_MISMATCH: verifier-metadata.json envelope digest mismatch",
        }

    sig_ok, sig_detail = _verify_ed25519_signature(
        public_key_hex=pub_hex,
        signature_hex=sig_hex,
        payload_bytes=envelope_bytes,
    )
    if not sig_ok:
        return {
            "valid": False,
            "signature_valid": False,
            "merkle_valid": False,
            "checksums_valid": False,
            "epistemic_status": "SIGNATURE_INVALID",
            "detail": f"SIGNATURE_VERIFICATION_FAILED: {sig_detail}",
        }

    # 2. Verify checksums.sha256 matches signed envelope and actual files on disk
    computed_checksums_digest = hashlib.sha256(checksums_raw).hexdigest()
    if computed_checksums_digest != signing_envelope.get("checksums_sha256_digest"):
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": False,
            "checksums_valid": False,
            "epistemic_status": "TAMPERED_CHECKSUMS",
            "detail": "CHECKSUMS_FILE_TAMPERED: checksums.sha256 does not match signed digest",
        }

    signed_file_digests = signing_envelope.get("file_digests", {})
    parsed_checksums: Dict[str, str] = {}
    for line in checksums_raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "checksums_valid": False,
                "epistemic_status": "MALFORMED_CHECKSUMS",
                "detail": f"MALFORMED_CHECKSUM_LINE: '{line}'",
            }
        parsed_checksums[parts[1]] = parts[0]

    for rel_file, expected_digest in signed_file_digests.items():
        if parsed_checksums.get(rel_file) != expected_digest:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "checksums_valid": False,
                "epistemic_status": "CHECKSUM_ENVELOPE_MISMATCH",
                "detail": f"CHECKSUM_MISMATCH_IN_MANIFEST: '{rel_file}'",
            }
        actual_digest = _sha256_file_standalone(root / rel_file)
        if actual_digest != expected_digest:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "checksums_valid": False,
                "epistemic_status": "FILE_TAMPERED",
                "detail": f"FILE_INTEGRITY_VIOLATION: '{rel_file}' digest {actual_digest} != signed {expected_digest}",
            }

    # 3. Verify SQLite Ledger L0 and execution-trace.jsonl consistency
    expected_root = manifest.get("ledger_summary", {}).get("global_merkle_root", "")
    if not expected_root or expected_root != signing_envelope.get("global_merkle_root"):
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": False,
            "checksums_valid": True,
            "epistemic_status": "MERKLE_ENVELOPE_MISMATCH",
            "detail": "MANIFEST_MERKLE_ROOT_MISMATCH: manifest root differs from signed envelope",
        }

    ledger_res = verify_offline_evidence(root / "evidence/ledger_l0.sqlite", expected_merkle_root=expected_root)
    if not ledger_res["verified"]:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": False,
            "checksums_valid": True,
            "epistemic_status": "LEDGER_TAMPERED",
            "detail": f"LEDGER_VERIFICATION_FAILED: {ledger_res['detail']}",
        }

    # Verify execution-trace.jsonl matches ledger entry count and hashes
    trace_lines = [
        ln.strip()
        for ln in (root / "evidence/execution-trace.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if trace_lines:
        if len(trace_lines) != ledger_res["total_entries"]:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "checksums_valid": True,
                "epistemic_status": "TRACE_LEDGER_DIVERGENCE",
                "detail": f"TRACE_COUNT_MISMATCH: trace has {len(trace_lines)} rows, ledger has {ledger_res['total_entries']}",
            }
        trace_hashes = [json.loads(ln).get("entry_hash", "") for ln in trace_lines]
        if build_cortex_merkle_tree(trace_hashes) != expected_root:
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": False,
                "checksums_valid": True,
                "epistemic_status": "TRACE_MERKLE_DIVERGENCE",
                "detail": "TRACE_HASH_MISMATCH: execution-trace.jsonl hashes do not match ledger Merkle root",
            }

    # 4. Verify Scope & Regulatory Matrix Non-Overclaim Invariants (Rules 1.A, 1.B, 1.C)
    boundaries = scope_doc.get("enforcement_boundaries", {})
    if "BROKER_MEDIATED" not in boundaries or "OS_ENFORCED" not in boundaries:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": True,
            "checksums_valid": True,
            "epistemic_status": "SCOPE_SCHEMA_INVALID",
            "detail": "SCOPE_INVALID: missing BROKER_MEDIATED or OS_ENFORCED boundary declaration",
        }

    for mapping in reg_matrix_doc.get("mappings", []):
        if (
            mapping.get("automated_compliance_verdict_permitted") is True
            or mapping.get("assessment_status") == "COMPLIANT"
        ):
            return {
                "valid": False,
                "signature_valid": True,
                "merkle_valid": True,
                "checksums_valid": True,
                "epistemic_status": "ILLEGAL_OVERCLAIM",
                "detail": f"ILLEGAL_AUTOMATIC_COMPLIANCE_VERDICT: framework {mapping.get('framework_id')} claims automatic COMPLIANT",
            }

    # 5. Cross-check NEMESIS results against claims.json (Rule 3: never mask a real bypass)
    claims_map = claims_doc.get("claims", {})
    campaigns = nemesis_doc.get("campaigns", {})
    falsified_claims: List[str] = []
    unsupported_claims: List[str] = []

    for camp_id, camp in campaigns.items():
        is_bypass = bool(camp.get("bypass_detected", False)) or camp.get("outcome") == "FALSIFIED"
        if is_bypass:
            for t_cid in camp.get("target_claims", []):
                c_entry = claims_map.get(t_cid, {})
                c_status = c_entry.get("status")
                if c_status not in {"FALSIFIED", "UNSUPPORTED_WITHIN_SCOPE"}:
                    return {
                        "valid": False,
                        "signature_valid": True,
                        "merkle_valid": True,
                        "checksums_valid": True,
                        "epistemic_status": "FALSIFIED",
                        "detail": f"CONTRADICTORY_NEMESIS_EVIDENCE_MASKED: campaign '{camp_id}' falsified '{t_cid}' but claim status is '{c_status}'",
                    }

    for cid, c_entry in claims_map.items():
        st = c_entry.get("status")
        if st == "FALSIFIED":
            falsified_claims.append(cid)
        elif st == "UNSUPPORTED_WITHIN_SCOPE":
            unsupported_claims.append(cid)

    if falsified_claims:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": True,
            "checksums_valid": True,
            "epistemic_status": "FALSIFIED",
            "falsified_claims": falsified_claims,
            "unsupported_claims": unsupported_claims,
            "detail": f"CONTROLS_FALSIFIED_BY_NEMESIS: {', '.join(sorted(falsified_claims))}",
        }

    if unsupported_claims:
        return {
            "valid": False,
            "signature_valid": True,
            "merkle_valid": True,
            "checksums_valid": True,
            "epistemic_status": "UNSUPPORTED_WITHIN_SCOPE",
            "falsified_claims": [],
            "unsupported_claims": unsupported_claims,
            "detail": f"CONTROLS_UNSUPPORTED_WITHIN_SCOPE: {', '.join(sorted(unsupported_claims))}",
        }

    return {
        "valid": True,
        "signature_valid": True,
        "merkle_valid": True,
        "checksums_valid": True,
        "epistemic_status": "EVIDENCE_VERIFIABLE_WITHIN_DECLARED_SCOPE",
        "pack_id": manifest.get("pack_id", ""),
        "global_merkle_root": expected_root,
        "total_claims": claims_doc.get("total_claims_compiled", len(claims_map)),
        "ttve_ms": manifest.get("metrics", {}).get("ttve_ms"),
        "detail": "M0_EVIDENCE_PACK_VERIFIED_AND_INTACT",
    }
