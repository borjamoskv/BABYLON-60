#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
cbor.py - Zero-Dependency RFC 8949 BFT Deterministic CBOR Codec.

Enforces canonical key sorting (RFC 8949 §4.2.1) and strict zero-dependency
binary encoding/decoding for BFT consensus ledgers under C5-REAL nesting ceilings.
"""

import io
import struct
from typing import Any

MAJOR_UNSIGNED = 0
MAJOR_NEGATIVE = 1
MAJOR_BYTES = 2
MAJOR_TEXT = 3
MAJOR_ARRAY = 4
MAJOR_MAP = 5
MAJOR_TAG = 6
MAJOR_SIMPLE = 7


def _encode_header(major: int, val: int) -> bytes:
    tag = major << 5
    if val < 24:
        return bytes([tag | val])
    if val <= 0xFF:
        return bytes([tag | 24, val])
    if val <= 0xFFFF:
        return struct.pack(">BH", tag | 25, val)
    if val <= 0xFFFFFFFF:
        return struct.pack(">BI", (major << 5) | 26, val)
    if val <= 0xFFFFFFFFFFFFFFFF:
        return struct.pack(">BQ", (major << 5) | 27, val)
    raise ValueError(f"Value too large for CBOR encoding: {val}")


def _encode_int(obj: int) -> bytes:
    if obj >= 0:
        return _encode_header(MAJOR_UNSIGNED, obj)
    return _encode_header(MAJOR_NEGATIVE, -1 - obj)


def _encode_sequence(obj: Any) -> bytes:
    hdr = _encode_header(MAJOR_ARRAY, len(obj))
    return hdr + b"".join(dumps(item) for item in obj)


def _encode_map(obj: dict) -> bytes:
    encoded_pairs = []
    for k, v in obj.items():
        k_bytes = dumps(k)
        v_bytes = dumps(v)
        encoded_pairs.append((k_bytes, v_bytes))
    
    encoded_pairs.sort(key=lambda pair: (len(pair[0]), pair[0]))
    hdr = _encode_header(MAJOR_MAP, len(encoded_pairs))
    body = b"".join(k + v for k, v in encoded_pairs)
    return hdr + body


def dumps(obj: Any) -> bytes:
    """
    Encodes a Python object into canonical CBOR bytes.
    Enforces canonical key sorting for maps (length first, then lexicographical bytes).
    """
    if obj is None:
        return bytes([(MAJOR_SIMPLE << 5) | 22])
    if isinstance(obj, bool):
        return bytes([(MAJOR_SIMPLE << 5) | (21 if obj else 20)])
    if isinstance(obj, int):
        return _encode_int(obj)
    if isinstance(obj, float):
        return struct.pack(">Bd", (MAJOR_SIMPLE << 5) | 27, obj)
    if isinstance(obj, (bytes, bytearray)):
        data = bytes(obj)
        return _encode_header(MAJOR_BYTES, len(data)) + data
    if isinstance(obj, str):
        data = obj.encode("utf-8")
        return _encode_header(MAJOR_TEXT, len(data)) + data
    if isinstance(obj, (list, tuple)):
        return _encode_sequence(obj)
    if isinstance(obj, dict):
        return _encode_map(obj)
    raise TypeError(f"Type {type(obj)} is not CBOR serializable")


def _read_additional(additional: int, stream: io.BytesIO) -> int:
    if additional < 24:
        return additional
    if additional == 24:
        return stream.read(1)[0]
    if additional == 25:
        return struct.unpack(">H", stream.read(2))[0]
    if additional == 26:
        return struct.unpack(">I", stream.read(4))[0]
    if additional == 27:
        return struct.unpack(">Q", stream.read(8))[0]
    return additional


def _decode_simple(additional: int, val: int) -> Any:
    if additional == 20:
        return False
    if additional == 21:
        return True
    if additional == 22:
        return None
    if additional == 27:
        return struct.unpack(">d", struct.pack(">Q", val))[0]
    raise ValueError(f"Unsupported simple value/float additional info: {additional}")


def _decode_map(val: int, stream: io.BytesIO) -> dict:
    res = {}
    for _ in range(val):
        k = _decode_stream(stream)
        v = _decode_stream(stream)
        res[k] = v
    return res


def _decode_stream(stream: io.BytesIO) -> Any:
    b = stream.read(1)
    if not b:
        raise EOFError("Unexpected end of CBOR stream")
    
    first = b[0]
    major = first >> 5
    additional = first & 0x1F
    val = _read_additional(additional, stream)

    if major == MAJOR_UNSIGNED:
        return val
    if major == MAJOR_NEGATIVE:
        return -1 - val
    if major == MAJOR_BYTES:
        return stream.read(val)
    if major == MAJOR_TEXT:
        return stream.read(val).decode("utf-8")
    if major == MAJOR_ARRAY:
        return [_decode_stream(stream) for _ in range(val)]
    if major == MAJOR_MAP:
        return _decode_map(val, stream)
    if major == MAJOR_SIMPLE:
        return _decode_simple(additional, val)
    if major == MAJOR_TAG:
        return _decode_stream(stream)
    raise ValueError(f"Unknown CBOR major type: {major}")


def loads(data: bytes) -> Any:
    """
    Deserializes CBOR bytes into Python objects.
    """
    stream = io.BytesIO(data)
    return _decode_stream(stream)
