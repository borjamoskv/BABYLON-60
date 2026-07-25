from __future__ import annotations

import hashlib
import math

__all__ = ['BASE60_ALPHABET', 'base60_check_to_bytes', 'base60_to_bytes', 'bytes_to_base60', 'bytes_to_base60_check', 'decode_base60', 'encode_base60', 'encoded_length']
BASE60_ALPHABET = '0123456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ'
BASE60_MAP = {char: idx for idx, char in enumerate(BASE60_ALPHABET)}
_LOG2_60 = 5.906890595608519
_CHECKSUM_LEN = 2
_CHUNK_BASE = 60 ** 8
_PAIR_BASE = 60 * 60
_DIGIT_PAIRS = tuple(hi + lo for hi in BASE60_ALPHABET for lo in BASE60_ALPHABET)

def _encode_positive(num: int) -> str:
    parts: list[str] = []
    pairs = _DIGIT_PAIRS
    while num:
        num, block = divmod(num, _CHUNK_BASE)
        block, p0 = divmod(block, _PAIR_BASE)
        block, p1 = divmod(block, _PAIR_BASE)
        block, p2 = divmod(block, _PAIR_BASE)
        parts.append(pairs[p0])
        parts.append(pairs[p1])
        parts.append(pairs[p2])
        parts.append(pairs[block])
    parts.reverse()
    return ''.join(parts).lstrip('0')

def encoded_length(num_bytes: int) -> int:
    if num_bytes == 32:
        return 44
    if num_bytes == 16:
        return 22
    if num_bytes <= 0:
        return 0
    return math.ceil(num_bytes * 8 / _LOG2_60)

def encode_base60(num: int) -> str:
    if num < 0:
        raise ValueError('Cannot encode negative integers in Base-60.')
    if num == 0:
        return BASE60_ALPHABET[0]
    return _encode_positive(num)

def decode_base60(s: str) -> int:
    if not s:
        raise ValueError('Cannot decode empty string.')
    val = 0
    base60_map = BASE60_MAP
    char = ''
    try:
        for char in s:
            val = val * 60 + base60_map[char]
    except KeyError as err:
        raise ValueError(f'Character {repr(char)} is not in the Base-60 alphabet.') from err
    return val

def bytes_to_base60(data: bytes) -> str:
    if not data:
        return ''
    num = int.from_bytes(data, byteorder='big')
    char_len = encoded_length(len(data))
    if num == 0:
        return BASE60_ALPHABET[0] * char_len
    encoded = _encode_positive(num)
    if len(encoded) >= char_len:
        return encoded
    return encoded.rjust(char_len, BASE60_ALPHABET[0])

def base60_to_bytes(s: str, expected_len: int) -> bytes:
    if not s:
        if expected_len == 0:
            return b''
        raise ValueError('Cannot decode empty string to non-empty bytes.')
    val = 0
    base60_map = BASE60_MAP
    char = ''
    try:
        for char in s:
            val = val * 60 + base60_map[char]
    except KeyError as err:
        raise ValueError(f'Character {repr(char)} is not in the Base-60 alphabet.') from err
    try:
        return val.to_bytes(expected_len, byteorder='big')
    except OverflowError as err:
        raise ValueError(f'Decoded Base-60 value exceeds capacity of {expected_len} bytes.') from err

def _checksum(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()[:_CHECKSUM_LEN]

def bytes_to_base60_check(data: bytes) -> str:
    if not data:
        return ''
    chk = _checksum(data)
    return bytes_to_base60(data + chk)

def base60_check_to_bytes(s: str, expected_data_len: int) -> bytes:
    if not s:
        if expected_data_len == 0:
            return b''
        raise ValueError('Cannot decode empty string to non-empty bytes.')
    total_len = expected_data_len + _CHECKSUM_LEN
    expected_chars = encoded_length(total_len)
    if len(s) != expected_chars:
        raise ValueError(f'Base60Check failed: expected {expected_chars} chars for a {expected_data_len}-byte payload, got {len(s)}.')
    decoded = base60_to_bytes(s, total_len)
    data, chk = (decoded[:-_CHECKSUM_LEN], decoded[-_CHECKSUM_LEN:])
    if _checksum(data) != chk:
        raise ValueError(f'Base60Check failed: Checksum mismatch for data length {expected_data_len}.')
    return data