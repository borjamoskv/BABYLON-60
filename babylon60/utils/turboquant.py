from __future__ import annotations

import logging
from collections.abc import Sequence

from babylon60.compat.optional import np
from babylon60.utils import void_vec

logger = logging.getLogger('babylon60.utils.turboquant')
_ROTATION_CACHE: dict[int, np.ndarray] = {}

def _get_rotation_matrix(dim: int) -> np.ndarray:
    if dim not in _ROTATION_CACHE:
        rng = np.random.RandomState(dim)
        R = rng.randn(dim, dim)
        q, _ = np.linalg.qr(R)
        _ROTATION_CACHE[dim] = q
    return _ROTATION_CACHE[dim]

def optimize_vector_qjl(vector: Sequence[float] | Sequence[int], bits: float=3.5, layer_depth_ratio: float=0.0) -> list[float] | bytes:
    try:
        effective_bits = max(1.0, bits * (1.0 - layer_depth_ratio * 0.7))
        arr = np.array(vector, dtype=np.float32)
        is_2d = len(arr.shape) > 1
        if not is_2d:
            arr = arr[np.newaxis, :]
        dim = arr.shape[1]
        try:
            from scipy.fft import fwht
            rotated = fwht(arr, norm='ortho')
        except ImportError:
            q = _get_rotation_matrix(dim)
            rotated = np.matmul(arr, q.T)
        if effective_bits <= 1.0:
            v_bits = void_vec.pack_void_bit(rotated[0] if not is_2d else rotated)
            return v_bits
        levels = int(2 ** effective_bits)
        min_val = np.min(rotated, axis=1, keepdims=True)
        max_val = np.max(rotated, axis=1, keepdims=True)
        step = np.where(max_val == min_val, 1e-09, (max_val - min_val) / levels)
        quantized_mse = np.round((rotated - min_val) / step) * step + min_val
        residual = rotated - quantized_mse
        qjl_1bit_residual = np.sign(residual) * np.mean(np.abs(residual), axis=1, keepdims=True)
        turboquant_encoded = quantized_mse + qjl_1bit_residual
        min_enc = np.min(turboquant_encoded, axis=1, keepdims=True)
        max_enc = np.max(turboquant_encoded, axis=1, keepdims=True)
        range_enc = np.where(max_enc == min_enc, 1.0, max_enc - min_enc)
        normalized = (turboquant_encoded - min_enc) / range_enc
        int8_scaled = np.clip(np.round(normalized * 255.0) - 128.0, -128, 127).astype(np.int8)
        if not is_2d:
            return [float(x) for x in int8_scaled[0]]
        return int8_scaled.tolist()
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
        logger.error('TurboQuant failure (Exergy Shield bypassed): %s', e)
        return [0.0] * len(vector)

def encode_query_qjl(vector: list[float]) -> list[float]:
    try:
        arr = np.array(vector, dtype=np.float32)
        is_2d = len(arr.shape) > 1
        if not is_2d:
            arr = arr[np.newaxis, :]
        dim = arr.shape[1]
        try:
            from scipy.fft import fwht
            rotated = fwht(arr, norm='ortho')
        except ImportError:
            q = _get_rotation_matrix(dim)
            rotated = np.matmul(arr, q.T)
        if not is_2d:
            return [float(x) for x in rotated[0]]
        return rotated.tolist()
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
        logger.error('TurboQuant query encoding failure: %s', e)
        return vector