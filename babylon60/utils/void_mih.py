from __future__ import annotations
import struct
from collections.abc import Sequence
__all__ = ['get_mih_shards', 'slice_void_bit']

def slice_void_bit(packed: bytes, shard_count: int=16) -> list[int]:
    required_bytes = shard_count * 8
    if len(packed) < required_bytes:
        padding = required_bytes - len(packed)
        packed = packed + b'\xa5' * padding
    fmt = f'>{shard_count}q'
    return list(struct.unpack(fmt, packed[:required_bytes]))

def get_mih_shards(vector: Sequence[float] | bytes, shard_count: int=16) -> list[int]:
    from babylon60.utils import void_vec
    if isinstance(vector, bytes):
        packed = vector
    else:
        packed = void_vec.pack_void_bit(list(vector))
    return slice_void_bit(packed, shard_count)