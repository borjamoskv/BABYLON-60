"""C0502 regression: vectors must match the query by real buffer size, not by len().

A bytes subclass can override __len__ so the Python-level guard passes while the
buffer handed to the C kernel is shorter. The guard must measure the real buffer.
Uses a recording stand-in for the native kernel; no native library is required.
"""

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
