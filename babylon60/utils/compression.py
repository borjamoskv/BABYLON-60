from __future__ import annotations

import logging
import struct

__all__ = ['compression_ratio', 'dequantize_int8', 'quantize_int8']
logger = logging.getLogger('babylon60.embeddings.compression')
try:
    import numpy as np
    _NP_AVAILABLE = True
except ImportError:
    _NP_AVAILABLE = False
    logger.debug('numpy not available - embedding compression disabled')

def quantize_int8(embedding: list[float]) -> bytes:
    if not _NP_AVAILABLE:
        raise RuntimeError('numpy required for embedding compression')
    arr = np.array(embedding, dtype=np.float32)
    abs_max = max(abs(arr.max()), abs(arr.min()))
    scale = abs_max if abs_max > 0 else 1.0
    quantized = np.clip(np.round(arr / scale * 127), -128, 127).astype(np.int8)
    return struct.pack('f', scale) + quantized.tobytes()

def dequantize_int8(data: bytes) -> list[float]:
    if not _NP_AVAILABLE:
        raise RuntimeError('numpy required for embedding decompression')
    scale = struct.unpack('f', data[:4])[0]
    quantized = np.frombuffer(data[4:], dtype=np.int8)
    return (quantized.astype(np.float32) * scale / 127.0).tolist()

def compression_ratio(dim: int=384) -> dict:
    original_float32 = dim * 4
    original_json = dim * 7
    compressed = 4 + dim
    return {'dim': dim, 'float32_bytes': original_float32, 'json_approx_bytes': original_json, 'int8_bytes': compressed, 'ratio_vs_float32': round(original_float32 / compressed, 1), 'ratio_vs_json': round(original_json / compressed, 1)}