import hashlib
import cbor2
from typing import Any, Dict


def canonicalize_cbor(data: Dict[str, Any]) -> bytes:
    """
    Serialización canónica determinista usando CBOR.
    Las claves del diccionario se ordenan lexicográficamente para asegurar BFT.
    """
    return cbor2.dumps(data, canonical=True)


def hash_sha3_256(data: bytes) -> str:
    """
    Genera un hash SHA3-256 (no SHA-256) garantizando resistencia a ataques de extensión de longitud.
    """
    return hashlib.sha3_256(data).hexdigest()


class Ed25519Signer:
    """
    Firma criptográfica usando Ed25519.
    """

    def sign(self, payload_hash: str) -> str:
        # Placeholder for physical signature implementation
        return "ed25519:mock_signature_for_" + payload_hash[:8]
