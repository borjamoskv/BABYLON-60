import abc
import hashlib
import hmac
import os
from enum import Enum

from babylon60.crypto.hash_registry import cortex_hash, cortex_hmac, get_active_algorithm
from babylon60.utils.base60 import bytes_to_base60


class SignatureAlgorithm(Enum):
    ED25519 = "ed25519"
    ML_DSA_65 = "ml_dsa_65"
    SLH_DSA_256S = "slh_dsa_256s"


class KMSProvider(abc.ABC):
    @abc.abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        pass

    @abc.abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        pass


class AWSKMSProvider(KMSProvider):
    def __init__(self, key_id: str):
        self.key_id = key_id

    def encrypt(self, plaintext: bytes) -> bytes:
        raise NotImplementedError("AWS KMS encrypt not yet implemented")

    def decrypt(self, ciphertext: bytes) -> bytes:
        raise NotImplementedError("AWS KMS decrypt not yet implemented")


class VaultKMSProvider(KMSProvider):
    def __init__(self, vault_url: str, token: str, key_name: str):
        self.vault_url = vault_url
        self.token = token
        self.key_name = key_name

    def encrypt(self, plaintext: bytes) -> bytes:
        raise NotImplementedError("Vault KMS encrypt not yet implemented")

    def decrypt(self, ciphertext: bytes) -> bytes:
        raise NotImplementedError("Vault KMS decrypt not yet implemented")


class HashProvider:
    @staticmethod
    def sha256(data: bytes | str) -> str:
        return cortex_hash(data)

    @staticmethod
    def sha512(data: bytes | str) -> str:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return bytes_to_base60(hashlib.sha512(data).digest())


class SignatureProvider:
    @staticmethod
    def sign_hmac(key: bytes | str, data: bytes | str) -> str:
        return cortex_hmac(key, data)

    @staticmethod
    def sign_hmac_sha256(key: bytes | str, data: bytes | str) -> str:
        return cortex_hmac(key, data)

    @staticmethod
    def verify_hmac_sha256(key: bytes | str, data: bytes | str, signature: str) -> bool:
        expected = SignatureProvider.sign_hmac_sha256(key, data)
        return hmac.compare_digest(expected, signature)


class KDFProvider:
    @staticmethod
    def pbkdf2_hmac_sha256(secret: bytes | str, salt: bytes, iterations: int = 100000) -> bytes:
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        algo = get_active_algorithm().value
        return hashlib.pbkdf2_hmac(algo, secret, salt, iterations)


class RandomProvider:
    @staticmethod
    def generate_bytes(num_bytes: int = 32) -> bytes:
        return os.urandom(num_bytes)
