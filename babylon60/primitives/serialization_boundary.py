"""
BABYLON-60 v4.0 Serialization Boundary & Tensor Checksum Verifier
Safely converts F60 sexagesimal rational values to GPU tensor format (bf16 / f32)
with strict bounds checking and SHA-256 checksum verification (Vector 3 Mitigation).
"""

import hashlib
import struct
from typing import List, Tuple, Dict, Any


class SerializationBoundaryError(ValueError):
    """Raised when F60 to GPU tensor conversion violates bounds or fails checksum verification."""

    pass


class SerializationBoundary:
    """
    Enforces strict bounds checking and checksum verification during
    F60 -> bf16/f32 conversions at the CPU/GPU interface.
    """

    # Bounds: F60 values must fit within valid finite float ranges [-1e30, 1e30]
    MIN_BOUND = -1e30
    MAX_BOUND = 1e30

    @classmethod
    def convert_f60_to_float_buffer(cls, f60_values: List[Tuple[int, int]]) -> Tuple[bytes, str]:
        """
        Converts a list of F60 tuples (numerator, scale_base60) to a packed f32 binary buffer.
        Validates bounds and returns (packed_bytes, sha256_checksum).

        Args:
            f60_values: List of (numerator, scale) tuples representing F60 rationals.

        Returns:
            Tuple of (binary_buffer, sha256_hex_checksum).

        Raises:
            SerializationBoundaryError: If any value is out-of-bounds or non-finite.
        """
        floats = []
        for num, scale in f60_values:
            denom = 60**scale if scale > 0 else 1
            val = float(num) / float(denom)

            if val < cls.MIN_BOUND or val > cls.MAX_BOUND:
                raise SerializationBoundaryError(
                    f"Serialization Boundary Violation: F60 value {val} out of bounds [{cls.MIN_BOUND}, {cls.MAX_BOUND}]"
                )
            floats.append(val)

        # Pack into float32 little-endian binary buffer
        packed_buffer = struct.pack(f"<{len(floats)}f", *floats)
        checksum = hashlib.sha256(packed_buffer).hexdigest()

        return packed_buffer, checksum

    @classmethod
    def validate_tensor_checksum(cls, buffer: bytes, expected_checksum: str) -> bool:
        """Verifies that the GPU tensor buffer hash matches the expected CPU commitment hash."""
        computed = hashlib.sha256(buffer).hexdigest()
        if computed != expected_checksum:
            raise SerializationBoundaryError(
                f"Tensor Checksum Mismatch! Computed {computed} != Expected {expected_checksum}"
            )
        return True
