import base64
import hashlib
import json
import sys
from typing import Any, Dict

from nacl.signing import SigningKey


def jcs_canonicalize(data: Dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: attest_character_count.py <word> <char>")
        sys.exit(1)
    word = sys.argv[1]
    char = sys.argv[2]
    count = word.lower().count(char.lower())
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    pub_bytes = verify_key.encode()
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).decode("utf-8").rstrip("=")
    did_key = f"did:key:{pub_b64}"
    payload = {
        "word": word,
        "character": char,
        "count": count,
        "reality_level": "C5-REAL",
        "verifier": "Physical CPU Core",
    }
    canonical_payload = jcs_canonicalize(payload)
    # INV_C5_03: un solo primitivo (SHA3-256) atraviesa el arco de atestación.
    payload_hash = f"sha3-256:{hashlib.sha3_256(canonical_payload).hexdigest()}"
    signature_bytes = signing_key.sign(payload_hash.encode("utf-8")).signature
    sig_b64 = base64.urlsafe_b64encode(signature_bytes).decode("utf-8").rstrip("=")
    receipt = {
        "receipt_id": f"rec_{hashlib.sha3_256(canonical_payload).hexdigest()[:8]}",
        "schema": "https://schema.babylon60.dev/v0.2/character-attestation",
        "payload": payload,
        "payload_hash": payload_hash,
        "signature": {"algorithm": "Ed25519", "key_id": did_key, "value": sig_b64},
    }
    with open("receipt.json", "w") as f:
        json.dump(receipt, f, indent=2)
    print(f"Receipt written to receipt.json. Count of '{char}' in '{word}' is {count}.")


if __name__ == "__main__":
    main()
