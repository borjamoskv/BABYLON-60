#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
cbor.py - Zero-Dependency RFC 8949 BFT Deterministic CBOR Codec.

Enforces canonical key sorting (RFC 8949 §4.2.1) and strict zero-dependency
binary encoding/decoding for BFT consensus ledgers.
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
    if val < 24:
        return bytes([(major << 5) | val])
    elif val <= 0xFF:
        return bytes([(major << 5) | 24, val])
    elif val <= 0xFFFF:
        return struct.pack(">BH", (major << 5) | 25, val)
    elif val <= 0xFFFFFFFF:
        return struct.pack(">BI", (major << 5) | 26, val)
    elif val <= 0xFFFFFFFFFFFFFFFF:
        return struct.pack(">BQ", (major << 5) | 27, val)
    else:
        raise ValueError(f"Value too large for CBOR encoding: {val}")


def dumps(obj: Any) -> bytes:
    """
    Encodes a Python object into canonical CBOR bytes.
    Enforces canonical key sorting for maps (length first, then lexicographical bytes).
    """
    if obj is None:
        return bytes([(MAJOR_SIMPLE << 5) | 22])
    elif isinstance(obj, bool):
        return bytes([(MAJOR_SIMPLE << 5) | (21 if obj else 20)])
    elif isinstance(obj, int):
        if obj >= 0:
            return _encode_header(MAJOR_UNSIGNED, obj)
        else:
            return _encode_header(MAJOR_NEGATIVE, -1 - obj)
    elif isinstance(obj, float):
        # 64-bit IEEE 754 float
        return struct.pack(">BD", (MAJOR_SIMPLE << 5) | 27, obj)
    elif isinstance(obj, (bytes, bytearray)):
        data = bytes(obj)
        return _encode_header(MAJOR_BYTES, len(data)) + data
    elif isinstance(obj, str):
        data = obj.encode("utf-8")
        return _encode_header(MAJOR_TEXT, len(data)) + data
    elif isinstance(obj, (list, tuple)):
        hdr = _encode_header(MAJOR_ARRAY, len(obj))
        return hdr + b"".join(dumps(item) for item in obj)
    elif isinstance(obj, dict):
        # BFT Canonical encoding: encode key-value pairs, sort by encoded key bytes
        encoded_pairs = []
        for k, v in obj.items():
            k_bytes = dumps(k)
            v_bytes = dumps(v)
            encoded_pairs.append((k_bytes, v_bytes))
        
        # Sort by key bytes: length first, then lexicographical order (RFC 8949 Canonical CBOR)
        encoded_pairs.sort(key=lambda pair: (len(pair[0]), pair[0]))
        
        hdr = _encode_header(MAJOR_MAP, len(encoded_pairs))
        body = b"".join(k + v for k, v in encoded_pairs)
        return hdr + body
    else:
        raise TypeError(f"Type {type(obj)} is not CBOR serializable")


def _decode_stream(stream: io.BytesIO) -> Any:
    b = stream.read(1)
    if not b:
        raise EOFError("Unexpected end of CBOR stream")
    
    first = b[0]
    major = first >> 5
    additional = first & 0x1F

    if additional < 24:
        val = additional
    elif additional == 24:
        val = stream.read(1)[0]
    elif additional == 25:
        val = struct.unpack(">H", stream.read(2))[0]
    elif additional == 26:
        val = struct.unpack(">I", stream.read(4))[0]
    elif additional == 27:
        val = struct.unpack(">Q", stream.read(8))[0]
    else:
        val = additional

    if major == MAJOR_UNSIGNED:
        return val
    elif major == MAJOR_NEGATIVE:
        return -1 - val
    elif major == MAJOR_BYTES:
        return stream.read(val)
    elif major == MAJOR_TEXT:
        return stream.read(val).decode("utf-8")
    elif major == MAJOR_ARRAY:
        return [_decode_stream(stream) for _ in range(val)]
    elif major == MAJOR_MAP:
        res = {}
        for _ in range(val):
            k = _decode_stream(stream)
            v = _decode_stream(stream)
            res[k] = v
        return res
    elif major == MAJOR_SIMPLE:
        if additional == 20:
            return False
        elif additional == 21:
            return True
        elif additional == 22:
            return None
        elif additional == 27:
            return struct.unpack(">d", stream.read(8))[0]
        else:
            raise ValueError(f"Unsupported simple value/float additional info: {additional}")
    elif major == MAJOR_TAG:
        return _decode_stream(stream)
    else:
        raise ValueError(f"Unknown CBOR major type: {major}")


def loads(data: bytes) -> Any:
    """
    Deserializes CBOR bytes into Python objects.
    """
    stream = io.BytesIO(data)
    res = _decode_stream(stream)
    return res
