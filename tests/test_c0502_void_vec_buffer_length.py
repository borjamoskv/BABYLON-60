"""C0502 regression: vectors must match the query by real buffer size, not by len().

A bytes subclass can override __len__ so the Python-level guard passes while the
buffer handed to the C kernel is shorter. The guard must measure the real buffer.
Uses a recording stand-in for the native kernel; no native library is required.
"""

import sys

import pytest

from babylon60.transducers import void_vec


class _LyingBytes(bytes):
    def __len__(self) -> int:  # reports 8 while holding 1 real byte
        return 8


@pytest.fixture
def recording_kernel(monkeypatch):
    calls = []

    def fake(query, flat, results, count, q_len):
        calls.append((len(flat), count, q_len))

    monkeypatch.setattr(void_vec, "_accel_func", fake)
    return calls


def test_lying_length_vector_is_rejected_before_ffi(recording_kernel):
    query = b"\x00" * 8
    with pytest.raises(ValueError):
        void_vec.void_batch_hamming_dist(query, [_LyingBytes(b"\x00")])
    assert recording_kernel == [], "el kernel no debe recibir un búfer más corto que el stride"


def test_lying_length_vector_is_rejected_in_single_path(monkeypatch):
    monkeypatch.setattr(void_vec, "_accel", None)
    with pytest.raises(ValueError):
        void_vec.void_hamming_dist(b"\x00" * 8, _LyingBytes(b"\x00"))


def test_matching_buffers_reach_kernel(recording_kernel):
    void_vec.void_batch_hamming_dist(b"\x00" * 8, [b"\x00" * 8, b"\xff" * 8])
    assert recording_kernel == [(16, 2, 8)]


class _BytesDunderLies(bytes):
    def __bytes__(self) -> bytes:  # 8 real bytes, but bytes(obj) yields 1
        return b"\x00"


class _ShrinkingBuffer:
    """Exports 8 bytes on the first buffer request and 1 byte afterwards."""

    def __init__(self) -> None:
        self.calls = 0

    def __buffer__(self, flags):
        self.calls += 1
        return memoryview(b"\x00" * 8 if self.calls == 1 else b"\x00")


@pytest.mark.parametrize("make_vector", [lambda: _BytesDunderLies(b"\x00" * 8), _ShrinkingBuffer])
def test_kernel_receives_exactly_count_times_stride(recording_kernel, make_vector):
    if make_vector is _ShrinkingBuffer and sys.version_info < (3, 12):
        # Python-level buffer exporters are supported from Python 3.12 (PEP 688).
        with pytest.raises(TypeError):
            void_vec.void_batch_hamming_dist(b"\x00" * 8, [make_vector()])
        assert recording_kernel == []
        return
    void_vec.void_batch_hamming_dist(b"\x00" * 8, [make_vector()])
    assert recording_kernel == [(8, 1, 8)], f"búfer de la FFI distinto del comprobado: {recording_kernel}"
