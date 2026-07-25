from __future__ import annotations
import ctypes
import math
import os
from babylon60.compat.optional import np
__all__ = ['cosine_similarity', 'pack_void_bit', 'unpack_void_bit', 'void_hamming_dist', 'void_similarity']

def cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum((x * y for x, y in zip(a, b, strict=False)))
    norm_a = math.sqrt(sum((x * x for x in a)))
    norm_b = math.sqrt(sum((x * x for x in b)))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return dot / (norm_a * norm_b)
_ACCEL_PATH = os.path.join(os.path.dirname(__file__), 'void_accel.so')
_accel = None
_accel_func = None
if os.path.exists(_ACCEL_PATH):
    try:
        _accel = ctypes.CDLL(_ACCEL_PATH)
        if hasattr(_accel, 'void_batch_hamming_dist_avx512'):
            _accel_func = _accel.void_batch_hamming_dist_avx512
        elif hasattr(_accel, 'void_batch_hamming_dist_neon'):
            _accel_func = _accel.void_batch_hamming_dist_neon
        if _accel_func:
            _accel_func.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t]
            _accel_func.restype = None
    except (ValueError, TypeError, OSError, KeyError):
        _accel = None
        _accel_func = None

def void_batch_hamming_dist(query: bytes, batch: list[bytes]) -> list[int]:
    count = len(batch)
    if _accel_func and count > 0:
        q_len = len(query)
        flat_batch = b''.join(batch)
        results = (ctypes.c_uint64 * count)()
        _accel_func(query, flat_batch, results, count, q_len)
        return list(results)
    return [void_hamming_dist(query, b) for b in batch]

def pack_void_bit(vector: list[float] | np.ndarray) -> bytes:
    arr = np.array(vector, dtype=np.float32)
    binary = (arr > 0).astype(np.uint8)
    dim = len(binary)
    if dim % 8 != 0:
        padding = 8 - dim % 8
        binary = np.pad(binary, (0, padding), 'constant')
    packed = np.packbits(binary)
    return packed.tobytes()

def void_hamming_dist(a: bytes, b: bytes) -> int:
    if _accel:
        return void_batch_hamming_dist(a, [b])[0]
    int_a = int.from_bytes(a, byteorder='big')
    int_b = int.from_bytes(b, byteorder='big')
    return (int_a ^ int_b).bit_count()

def void_similarity(a: bytes, b: bytes, total_dim: int) -> float:
    dist = void_hamming_dist(a, b)
    return 1.0 - dist / total_dim

def unpack_void_bit(packed: bytes, dim: int) -> np.ndarray:
    binary = np.unpackbits(np.frombuffer(packed, dtype=np.uint8))
    binary = binary[:dim]
    return binary.astype(np.float32) * 2.0 - 1.0