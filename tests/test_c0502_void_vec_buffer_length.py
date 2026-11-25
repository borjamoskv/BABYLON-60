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


@pytest.mark.parametrize(
    "make_vector",
    [
        lambda: _BytesDunderLies(b"\x00" * 8),
        pytest.param(
            _ShrinkingBuffer,
            marks=pytest.mark.skipif(
                sys.version_info < (3, 12),
                reason="PEP 688 __buffer__ requires Python 3.12+",
            ),
        ),
    ],
)
def test_kernel_receives_exactly_count_times_stride(recording_kernel, make_vector):
    if make_vector is _ShrinkingBuffer and sys.version_info < (3, 12):
        # Python-level buffer exporters are supported from Python 3.12 (PEP 688).
        with pytest.raises(TypeError):
            void_vec.void_batch_hamming_dist(b"\x00" * 8, [make_vector()])
        assert recording_kernel == []
        return
    void_vec.void_batch_hamming_dist(b"\x00" * 8, [make_vector()])
    assert recording_kernel == [(8, 1, 8)], f"búfer de la FFI distinto del comprobado: {recording_kernel}"


class _ConvertingBytes(bytes):
    def __bytes__(self) -> bytes:
        return b""


class _ConvertingBytearray(bytearray):
    def __bytes__(self) -> bytes:
        return b""


@pytest.fixture
def recording_kernel_payloads(monkeypatch):
    calls = []

    def fake(query, flat, results, count, q_len):
        calls.append((query, flat, count, q_len))

    monkeypatch.setattr(void_vec, "_accel_func", fake)
    return calls


@pytest.mark.parametrize("buffer_type", [_ConvertingBytes, _ConvertingBytearray])
def test_bytes_override_cannot_shorten_native_vector_buffer(recording_kernel_payloads, buffer_type):
    query = b"\x0f" * 32
    vector = b"\xf0" * 32

    void_vec.void_batch_hamming_dist(query, [buffer_type(vector)])

    assert recording_kernel_payloads == [(query, vector, 1, 32)]


@pytest.mark.parametrize("buffer_type", [_ConvertingBytes, _ConvertingBytearray])
def test_query_is_normalized_before_native_call(recording_kernel_payloads, buffer_type):
    query = b"\x0f" * 32
    vector = b"\xf0" * 32

    void_vec.void_batch_hamming_dist(buffer_type(query), [vector])

    assert recording_kernel_payloads == [(query, vector, 1, 32)]
    assert type(recording_kernel_payloads[0][0]) is bytes


@pytest.mark.parametrize("buffer_type", [_ConvertingBytes, _ConvertingBytearray])
def test_bytes_override_cannot_change_scalar_distance(monkeypatch, buffer_type):
    monkeypatch.setattr(void_vec, "_accel", None)
    monkeypatch.setattr(void_vec, "_accel_func", None)
    query = buffer_type(b"\x0f" * 32)
    vector = buffer_type(b"\xf0" * 32)

    assert void_vec.void_hamming_dist(query, vector) == 256
    assert void_vec.void_batch_hamming_dist(query, [vector]) == [256]


@pytest.mark.parametrize("buffer_type", [bytes, bytearray, memoryview])
def test_native_call_uses_the_validated_buffer_snapshots(recording_kernel_payloads, buffer_type):
    query = b"\x0f" * 32
    vector = b"\xf0" * 32

    void_vec.void_batch_hamming_dist(buffer_type(query), [buffer_type(vector)])

    assert recording_kernel_payloads == [(query, vector, 1, 32)]
    assert type(recording_kernel_payloads[0][0]) is bytes
    assert type(recording_kernel_payloads[0][1]) is bytes


@pytest.mark.parametrize("reported_count", [0, 1, 7])
def test_native_count_matches_snapshotted_elements(recording_kernel_payloads, reported_count):
    class LyingBatch(list[bytes]):
        def __len__(self) -> int:
            return int(reported_count)

    query = b"\x0f" * 8
    vector = b"\xf0" * 8

    void_vec.void_batch_hamming_dist(query, LyingBatch([vector, vector]))

    assert recording_kernel_payloads == [(query, vector * 2, 2, 8)]


def test_native_call_uses_the_elements_from_the_validated_iteration(recording_kernel_payloads):
    class ChangingBatch(list[bytes]):
        iterations = 0

        def __iter__(self):
            self.iterations += 1
            return iter([b"\xf0" * 8] if self.iterations == 1 else [b"\x00"])

    query = b"\x0f" * 8
    batch = ChangingBatch([b"\x11" * 8, b"\x22" * 8])

    void_vec.void_batch_hamming_dist(query, batch)

    assert recording_kernel_payloads == [(query, b"\xf0" * 8, 1, 8)]


@pytest.mark.parametrize("view_kind", ["multidimensional", "strided", "reversed"])
def test_complex_views_use_logical_bytes_in_native_and_scalar_paths(recording_kernel_payloads, monkeypatch, view_kind):
    query = bytes(range(32))
    vector = bytes(255 - value for value in range(32))
    if view_kind == "multidimensional":
        query_view = memoryview(query).cast("B", shape=[4, 8])
        vector_view = memoryview(vector).cast("B", shape=[8, 4])
        expected_query, expected_vector = query, vector
    elif view_kind == "strided":
        query_view, vector_view = memoryview(query)[::2], memoryview(vector)[::2]
        expected_query, expected_vector = query[::2], vector[::2]
    else:
        query_view, vector_view = memoryview(query)[::-1], memoryview(vector)[::-1]
        expected_query, expected_vector = query[::-1], vector[::-1]

    void_vec.void_batch_hamming_dist(query_view, [vector_view])

    assert recording_kernel_payloads == [(expected_query, expected_vector, 1, len(expected_query))]
    assert type(recording_kernel_payloads[0][0]) is bytes
    monkeypatch.setattr(void_vec, "_accel", None)
    monkeypatch.setattr(void_vec, "_accel_func", None)
    expected_distance = len(expected_query) * 8
    assert void_vec.void_hamming_dist(query_view, vector_view) == expected_distance
    assert void_vec.void_batch_hamming_dist(query_view, [vector_view]) == [expected_distance]


@pytest.mark.parametrize("accelerated", [True, False])
def test_iteration_cannot_resize_query_or_previous_vector_snapshot(recording_kernel_payloads, monkeypatch, accelerated):
    query = bytearray(b"\x0f" * 32)
    first = bytearray(b"\xf0" * 32)
    second = bytearray(b"\xf0" * 32)

    class MutatingBatch(list[bytearray]):
        def __iter__(self):
            yield self[0]
            query.clear()
            first.clear()
            yield self[1]

    if not accelerated:
        monkeypatch.setattr(void_vec, "_accel", None)
        monkeypatch.setattr(void_vec, "_accel_func", None)

    result = void_vec.void_batch_hamming_dist(query, MutatingBatch([first, second]))

    assert query == first == bytearray()
    if accelerated:
        assert recording_kernel_payloads == [(b"\x0f" * 32, b"\xf0" * 64, 2, 32)]
    else:
        assert result == [256, 256]


def test_resized_later_vector_is_rejected_before_native_call(recording_kernel_payloads):
    later = bytearray(b"\xf0" * 32)

    class MutatingBatch(list[bytes | bytearray]):
        def __iter__(self):
            yield self[0]
            later.clear()
            yield self[1]

    with pytest.raises(ValueError):
        void_vec.void_batch_hamming_dist(b"\x0f" * 32, MutatingBatch([b"\xf0" * 32, later]))

    assert recording_kernel_payloads == []
