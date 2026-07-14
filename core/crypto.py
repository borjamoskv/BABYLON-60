import json
import hashlib

def jcs_canonicalize(data: dict) -> bytes:
    return json.dumps(data, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode('utf-8')

def hash_sha256(data: bytes) -> str:
    return f'sha256:{hashlib.sha256(data).hexdigest()}'

class Ed25519Signer:

    def sign(self, payload_hash: str) -> str:
        return 'base64url:mock_signature'