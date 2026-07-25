from __future__ import annotations

import hashlib
from enum import Enum

from babylon60.utils.base60 import bytes_to_base60


class HashAlgorithm(Enum):
    SHA256 = 'sha256'
    SHA3_256 = 'sha3_256'
    SHA512 = 'sha512'
    SHA3_512 = 'sha3_512'
_active_algorithm: HashAlgorithm = HashAlgorithm.SHA256

def configure(algorithm: HashAlgorithm) -> None:
    global _active_algorithm
    _active_algorithm = algorithm

def get_active_algorithm() -> HashAlgorithm:
    return _active_algorithm

def cortex_hash(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return bytes_to_base60(hashlib.new(_active_algorithm.value, data).digest())

def cortex_hash_b60(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return bytes_to_base60(hashlib.new(_active_algorithm.value, data).digest())

def cortex_hash_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.new(_active_algorithm.value, data).hexdigest()

def cortex_hash_truncated(data: bytes | str, length: int=16) -> str:
    return cortex_hash(data)[:length]

def cortex_hmac(key: bytes | str, data: bytes | str) -> str:
    import hmac as _hmac
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(data, str):
        data = data.encode('utf-8')
    return _hmac.new(key, data, hashlib.new(_active_algorithm.value).__class__).hexdigest()

def cortex_hmac_b60(key: bytes | str, data: bytes | str) -> str:
    import hmac as _hmac
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(data, str):
        data = data.encode('utf-8')
    return bytes_to_base60(_hmac.new(key, data, hashlib.new(_active_algorithm.value).__class__).digest())

def cortex_hash_raw(data: bytes | str) -> bytes:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.new(_active_algorithm.value, data).digest()
hash_sha256 = cortex_hash