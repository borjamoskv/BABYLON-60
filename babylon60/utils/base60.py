from __future__ import annotations

# [C5-REAL] Exergy-Maximized
"""Base-60 (Sexagesimal) Encoder and Decoder.

Provides deterministic representation of transaction hashes and identifier bytes.
Maintains sexagesimal divisibility and ledger compatibility (BABYLON-60 identity).
Residual visual ambiguity (0/o, 1/I) is acknowledged. Mitigation is strictly
forensic via Base60Check (Detection > Prevention), as removing 4 chars would
force a drop to Base-58, breaking the sexagesimal ontology.

Detection is probabilistic, not deterministic: a corrupted string passes the
2-byte double-SHA256 checksum with P(escape) = 2**-16 (~0.0015%).
"""


import hashlib  # noqa: E402 — docstring extendido del módulo precede a los imports por legibilidad
import math  # noqa: E402

__all__ = [
    "BASE60_ALPHABET",
    "base60_check_to_bytes",
    "base60_to_bytes",
    "bytes_to_base60",
    "bytes_to_base60_check",
    "decode_base60",
    "encode_base60",
    "encoded_length",
]

BASE60_ALPHABET = "0123456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ"
BASE60_MAP = {char: idx for idx, char in enumerate(BASE60_ALPHABET)}

_LOG2_60 = 5.906890595608519

_CHECKSUM_LEN = 2

_CHUNK_BASE = 60**8  # 167_961_600_000_000
_PAIR_BASE = 60 * 60
_DIGIT_PAIRS = tuple(hi + lo for hi in BASE60_ALPHABET for lo in BASE60_ALPHABET)


def _encode_positive(num: int) -> str:
    """Minimal (unpadded) Base-60 string for num > 0. Internal helper."""
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
    return "".join(parts).lstrip("0")


def encoded_length(num_bytes: int) -> int:
    """Canonical Base-60 string width for a payload of ``num_bytes``.

    Fast paths for standard payload sizes (UUID=16 -> 22 chars,
    SHA-256=32 -> 44 chars; with the Base60Check checksum appended:
    18 -> 25, 34 -> 47).

    Args:
        num_bytes: Payload size in bytes.

    Returns:
        Number of Base-60 characters in the canonical encoding.
    """
    if num_bytes == 32:
        return 44
    if num_bytes == 16:
        return 22
    if num_bytes <= 0:
        return 0
    return math.ceil((num_bytes * 8) / _LOG2_60)


def encode_base60(num: int) -> str:
    """Encode a non-negative integer into a Base-60 string.

    Args:
        num: Non-negative integer.

    Returns:
        Base-60 representation string.

    Raises:
        ValueError: If num is negative.
    """
    if num < 0:
        raise ValueError("Cannot encode negative integers in Base-60.")
    if num == 0:
        return BASE60_ALPHABET[0]
    return _encode_positive(num)


def decode_base60(s: str) -> int:
    """Decode a Base-60 string back to an integer.

    Args:
        s: Base-60 string.

    Returns:
        Decoded integer value.

    Raises:
        ValueError: If string is empty or contains characters not in alphabet.
    """
    if not s:
        raise ValueError("Cannot decode empty string.")

    val = 0
    base60_map = BASE60_MAP
    char = ""
    try:
        for char in s:
            val = val * 60 + base60_map[char]
    except KeyError as err:
        raise ValueError(f"Character {repr(char)} is not in the Base-60 alphabet.") from err
    return val


def bytes_to_base60(data: bytes) -> str:
    """Encode arbitrary bytes to a Base-60 string with length-based padding.

    Left-pads the result with '0' to the canonical width (see encoded_length)
    so that leading zero bytes are preserved.

    Args:
        data: Raw bytes to encode.

    Returns:
        Padded Base-60 string of canonical width.
    """
    if not data:
        return ""

    num = int.from_bytes(data, byteorder="big")
    char_len = encoded_length(len(data))

    if num == 0:
        return BASE60_ALPHABET[0] * char_len

    encoded = _encode_positive(num)
    if len(encoded) >= char_len:
        return encoded
    return encoded.rjust(char_len, BASE60_ALPHABET[0])


def base60_to_bytes(s: str, expected_len: int) -> bytes:
    """Decode a Base-60 string back to bytes of expected length.

    Permissive on width (accepts non-canonical leading '0's) for legacy
    compatibility; Base60Check enforces strict canonical width instead.

    Args:
        s: Base-60 encoded string.
        expected_len: The expected length of the decoded bytes.

    Returns:
        Decoded byte array.

    Raises:
        ValueError: If string is empty, contains invalid characters, or decoded
            value exceeds the capacity of the expected byte length.
    """
    if not s:
        if expected_len == 0:
            return b""
        raise ValueError("Cannot decode empty string to non-empty bytes.")

    val = 0
    base60_map = BASE60_MAP
    char = ""
    try:
        for char in s:
            val = val * 60 + base60_map[char]
    except KeyError as err:
        raise ValueError(f"Character {repr(char)} is not in the Base-60 alphabet.") from err

    try:
        return val.to_bytes(expected_len, byteorder="big")
    except OverflowError as err:
        raise ValueError(f"Decoded Base-60 value exceeds capacity of {expected_len} bytes.") from err


def _checksum(data: bytes) -> bytes:
    """Compute a double SHA-256 checksum, truncating to 2 bytes."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()[:_CHECKSUM_LEN]


def bytes_to_base60_check(data: bytes) -> str:
    """Encode arbitrary bytes to a Base-60 string with a 2-byte checksum.

    Provides Base60Check to detect human transcription errors due to residual
    visual ambiguity (0/o, 1/I). Detection is probabilistic: a corrupted
    string escapes verification with P = 2**-16 (~0.0015%).

    Args:
        data: Raw bytes to encode.

    Returns:
        Base-60 string of canonical width with checksum appended
        (e.g., 47 chars for a 32-byte hash).
    """
    if not data:
        return ""
    chk = _checksum(data)
    return bytes_to_base60(data + chk)


def base60_check_to_bytes(s: str, expected_data_len: int) -> bytes:
    """Decode a Base-60 string, validating its 2-byte checksum.

    Enforces strict canonical width: strings with missing or extra characters
    (including dropped leading '0's) are rejected before any arithmetic.

    Args:
        s: Base-60 encoded string containing the checksum.
        expected_data_len: Expected length of the ORIGINAL data bytes (excluding checksum).

    Returns:
        Decoded byte array (original data without checksum).

    Raises:
        ValueError: If string is empty, has non-canonical width, contains
            invalid chars, or the checksum does not match.
    """
    if not s:
        if expected_data_len == 0:
            return b""
        raise ValueError("Cannot decode empty string to non-empty bytes.")

    total_len = expected_data_len + _CHECKSUM_LEN
    expected_chars = encoded_length(total_len)
    if len(s) != expected_chars:
        raise ValueError(
            f"Base60Check failed: expected {expected_chars} chars for a {expected_data_len}-byte payload, got {len(s)}."
        )

    decoded = base60_to_bytes(s, total_len)
    data, chk = decoded[:-_CHECKSUM_LEN], decoded[-_CHECKSUM_LEN:]

    if _checksum(data) != chk:
        raise ValueError(f"Base60Check failed: Checksum mismatch for data length {expected_data_len}.")

    return data
