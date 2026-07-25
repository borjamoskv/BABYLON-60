import argparse
import base64
import hashlib
import json
import sys
from typing import Any

try:
    from nacl.exceptions import BadSignatureError
    from nacl.signing import VerifyKey

    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False


def jcs_canonicalize(data: dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")


def hash_sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def hash_sha3_256(data: bytes) -> str:
    return f"sha3-256:{hashlib.sha3_256(data).hexdigest()}"


_HEX_CHARS = set("0123456789abcdef")


def _recompute_declared(declared_hash: str, canonical_payload: bytes) -> tuple[str | None, str]:
    if declared_hash.startswith("sha3-256:"):
        return (hash_sha3_256(canonical_payload), "sha3-256")
    if declared_hash.startswith("sha256:"):
        return (hash_sha256(canonical_payload), "sha256-legacy")
    if len(declared_hash) == 64 and set(declared_hash) <= _HEX_CHARS:
        return (hashlib.sha3_256(canonical_payload).hexdigest(), "sha3-256-bare")
    return (None, "unknown")


def verify_ed25519(public_key_b64: str, signature_b64: str, message: bytes) -> bool:
    if not NACL_AVAILABLE:
        print("ERROR: PyNaCl not installed. Cannot verify Ed25519 signatures.")
        return False
    try:
        pub_key_bytes = base64.urlsafe_b64decode(public_key_b64 + "=" * (-len(public_key_b64) % 4))
        sig_bytes = base64.urlsafe_b64decode(signature_b64.replace("base64url:", "") + "=" * (-len(signature_b64) % 4))
        vk = VerifyKey(pub_key_bytes)
        vk.verify(message, sig_bytes)
        return True
    except BadSignatureError:
        return False
    except RuntimeError as e:
        print(f"Signature decoding error: {e}")
        return False


def verify_merkle_leaf(payload_hash: str) -> str:
    clean_hash = payload_hash.replace("sha256:", "")
    leaf_bytes = b"\x00" + bytes.fromhex(clean_hash)
    return hashlib.sha256(leaf_bytes).hexdigest()


def verify_merkle_node(left_hex: str, right_hex: str) -> str:
    node_bytes = b"\x01" + bytes.fromhex(left_hex) + bytes.fromhex(right_hex)
    return hashlib.sha256(node_bytes).hexdigest()


def verify_merkle_proof(leaf_hash: str, proof: list[str], root: str, index: int) -> bool:
    if root is None or index is None:
        return False
    if not proof and leaf_hash != root:
        return False
    current = leaf_hash
    for i, sibling in enumerate(proof):
        is_left = not bool(index >> i & 1)
        if is_left:
            current = verify_merkle_node(current, sibling)
        else:
            current = verify_merkle_node(sibling, current)
    return current == root


def verify_receipt(receipt_path: str) -> dict[str, Any]:
    with open(receipt_path) as f:
        receipt = json.load(f)
    if "payload" not in receipt or "payload_hash" not in receipt or "signature" not in receipt:
        print("ERROR: Receipt does not conform to v0.2 structure (payload, payload_hash, signature).")
        sys.exit(1)
    payload = receipt["payload"]
    declared_hash = receipt["payload_hash"]
    sig_block = receipt["signature"]
    canonical_payload = jcs_canonicalize(payload)
    calculated_hash, hash_primitive = _recompute_declared(declared_hash, canonical_payload)
    hash_valid = calculated_hash is not None and calculated_hash == declared_hash
    sig_valid = False
    if sig_block.get("algorithm") == "Ed25519":
        sig_valid = verify_ed25519(
            sig_block.get("key_id", "").replace("did:key:", ""),
            sig_block.get("value", ""),
            declared_hash.encode("utf-8"),
        )
    else:
        print(f"ERROR: Algorithm {sig_block.get('algorithm')} is not implemented. Failing closed.")
        sig_valid = False
    report = {
        "receipt_id": receipt.get("receipt_id", "unknown"),
        "schema": receipt.get("schema", "unknown"),
        "payload_hash_valid": hash_valid,
        "hash_primitive": hash_primitive,
        "signature_valid": sig_valid,
        "status": "verified" if hash_valid and sig_valid else "invalid",
    }
    if "request_commitment" in payload:
        report["prompt_verification"] = "unverifiable_without_secret"
    print(json.dumps(report, indent=2))
    if not hash_valid or not sig_valid:
        sys.exit(1)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Proof-of-Route v0.2 Receipts")
    parser.add_argument("receipt_file", help="Path to the JSON receipt")
    args = parser.parse_args()
    verify_receipt(args.receipt_file)


if __name__ == "__main__":
    main()
