# [C5-REAL] Exergy-Maximized
import hashlib
import uuid
import pytest
from hypothesis import given, strategies as st
from babylon60.utils.base60 import (
    BASE60_ALPHABET,
    encode_base60,
    decode_base60,
    bytes_to_base60,
    base60_to_bytes,
    bytes_to_base60_check,
    base60_check_to_bytes,
    encoded_length,
)


def test_encode_decode_integers():
    # Test base cases
    assert encode_base60(0) == BASE60_ALPHABET[0]
    assert decode_base60(BASE60_ALPHABET[0]) == 0

    assert encode_base60(1) == BASE60_ALPHABET[1]
    assert decode_base60(BASE60_ALPHABET[1]) == 1

    assert encode_base60(59) == BASE60_ALPHABET[59]
    assert decode_base60(BASE60_ALPHABET[59]) == 59

    # Test multiples
    assert encode_base60(60) == f"{BASE60_ALPHABET[1]}{BASE60_ALPHABET[0]}"
    assert decode_base60(f"{BASE60_ALPHABET[1]}{BASE60_ALPHABET[0]}") == 60

    assert encode_base60(3600) == f"{BASE60_ALPHABET[1]}{BASE60_ALPHABET[0]}{BASE60_ALPHABET[0]}"
    assert decode_base60(f"{BASE60_ALPHABET[1]}{BASE60_ALPHABET[0]}{BASE60_ALPHABET[0]}") == 3600

    # Large integer roundtrip
    large_num = 123456789012345678901234567890
    encoded = encode_base60(large_num)
    assert decode_base60(encoded) == large_num


def test_encode_negative_raises():
    with pytest.raises(ValueError, match="Cannot encode negative integers"):
        encode_base60(-1)


def test_decode_invalid_raises():
    with pytest.raises(ValueError, match="Cannot decode empty string"):
        decode_base60("")

    # 'l' (lowercase L) and 'O' (uppercase O) are excluded
    with pytest.raises(ValueError, match="is not in the Base-60 alphabet"):
        decode_base60("l")

    with pytest.raises(ValueError, match="is not in the Base-60 alphabet"):
        decode_base60("O")

    with pytest.raises(ValueError, match="is not in the Base-60 alphabet"):
        decode_base60("some_invalid_string!")


def test_bytes_base60_roundtrip():
    # Empty bytes
    assert bytes_to_base60(b"") == ""
    assert base60_to_bytes("", 0) == b""

    # Single byte
    data = b"\xff"
    encoded = bytes_to_base60(data)
    assert len(encoded) == 2  # math.ceil(8 / 5.906) = 2
    assert base60_to_bytes(encoded, 1) == data

    # 16-byte UUID
    u = uuid.uuid4()
    encoded_uuid = bytes_to_base60(u.bytes)
    assert len(encoded_uuid) == 22  # math.ceil(128 / 5.906) = 22
    assert base60_to_bytes(encoded_uuid, 16) == u.bytes

    # 32-byte hash
    h = hashlib.sha256(b"cortex-persist").digest()
    encoded_hash = bytes_to_base60(h)
    assert len(encoded_hash) == 44  # math.ceil(256 / 5.906) = 44
    assert base60_to_bytes(encoded_hash, 32) == h


def test_bytes_leading_zeros():
    # Preserves leading zeros correctly via padding
    data = b"\x00\x00\x00\xff"
    encoded = bytes_to_base60(data)
    assert len(encoded) == 6  # math.ceil(32 / 5.906) = 6
    assert encoded.startswith("000")  # Padded with '0'
    assert base60_to_bytes(encoded, 4) == data

    data_all_zeros = b"\x00\x00\x00\x00"
    encoded_zeros = bytes_to_base60(data_all_zeros)
    assert encoded_zeros == "0" * 6
    assert base60_to_bytes(encoded_zeros, 4) == data_all_zeros


def test_overflow_and_invalid_bytes():
    # If the base60 string decodes to a value larger than fits in expected_len
    # 60^4 = 12960000, which exceeds 2 bytes limit (65535)
    s = "ZZZZ"
    with pytest.raises(ValueError, match="exceeds capacity of"):
        base60_to_bytes(s, 2)


# --- Property-Based Testing (Hypothesis) ---


@given(st.integers(min_value=0, max_value=2**256 - 1))
def test_hypothesis_integer_roundtrip(num):
    encoded = encode_base60(num)
    assert decode_base60(encoded) == num


@given(st.binary(min_size=0, max_size=128))
def test_hypothesis_bytes_roundtrip(data):
    encoded = bytes_to_base60(data)
    decoded = base60_to_bytes(encoded, len(data))
    assert decoded == data


def test_base60_check_roundtrip():
    data = b"cortex-persist-test-data"
    encoded = bytes_to_base60_check(data)

    # Must decode back to the exact original bytes
    decoded = base60_check_to_bytes(encoded, len(data))
    assert decoded == data


def test_base60_check_detects_ambiguity():
    # Simulate transcription error (0 -> o, 1 -> I)
    data = b"some-important-hash"
    encoded = bytes_to_base60_check(data)

    if "0" in encoded:
        corrupted = encoded.replace("0", "o", 1)
        with pytest.raises(ValueError, match="Base60Check failed"):
            base60_check_to_bytes(corrupted, len(data))

    if "1" in encoded:
        corrupted = encoded.replace("1", "I", 1)
        with pytest.raises(ValueError, match="Base60Check failed"):
            base60_check_to_bytes(corrupted, len(data))


@given(st.binary(min_size=0, max_size=128))
def test_hypothesis_base60_check_roundtrip(data):
    encoded = bytes_to_base60_check(data)
    decoded = base60_check_to_bytes(encoded, len(data))
    assert decoded == data


def test_encoded_length_canonical_widths():
    assert encoded_length(32) == 44  # SHA-256
    assert encoded_length(16) == 22  # UUID
    assert encoded_length(34) == 47  # SHA-256 + Base60Check
    assert encoded_length(18) == 25  # UUID + Base60Check
    assert encoded_length(1) == 2
    assert encoded_length(4) == 6
    assert encoded_length(0) == 0
    assert encoded_length(-5) == 0


@given(st.binary(min_size=0, max_size=128))
def test_hypothesis_width_matches_encoded_length(data):
    assert len(bytes_to_base60(data)) == encoded_length(len(data))
    if data:
        assert len(bytes_to_base60_check(data)) == encoded_length(len(data) + 2)


def test_base60_check_canonical_widths():
    assert len(bytes_to_base60_check(hashlib.sha256(b"w").digest())) == 47
    assert len(bytes_to_base60_check(uuid.uuid4().bytes)) == 25


def test_base60_check_strict_width():
    # Length mutations must be rejected BEFORE checksum arithmetic. A dropped
    # leading '0' preserves the integer value, so only strict canonical width
    # can detect it (the checksum alone would pass).
    data = b"\x00\x00" + hashlib.sha256(b"strict").digest()[2:]
    encoded = bytes_to_base60_check(data)
    assert len(encoded) == 47
    assert encoded[0] == BASE60_ALPHABET[0]  # guaranteed leading '0'

    for corrupted in (encoded[1:], "0" + encoded, encoded[:-1], encoded + "7"):
        with pytest.raises(ValueError, match="Base60Check failed"):
            base60_check_to_bytes(corrupted, len(data))
