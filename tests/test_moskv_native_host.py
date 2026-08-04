"""
Unit tests for Native Messaging Transducer (scripts/moskv_native_host.py).
Tests IPC frame reading, 32-bit LE packing, payload commitment, size limits, and event dispatch.
"""

import io
import json
import logging
import struct
from scripts.moskv_native_host import (
    calculate_payload_commitment,
    process_extension_event,
    read_message_frame,
    send_message_frame,
)


def test_payload_commitment():
    raw = b'{"status": "READY"}'
    hash_hex = calculate_payload_commitment(raw)
    assert len(hash_hex) == 64
    assert hash_hex == "867e0cd435381bb56251908fc2cf891b652c72d233a5f3a2fe5582a98cfde5e0"


def test_read_send_message_frame_roundtrip():
    payload = {"status": "READY", "exergy": 500.0}

    # Test send_message_frame to in-memory buffer
    buf = io.BytesIO()
    success = send_message_frame(payload, stream=buf)
    assert success is True

    # Inspect binary stream layout
    buf.seek(0)
    data = buf.read()
    length_prefix = struct.unpack("<I", data[:4])[0]
    encoded_json = data[4:].decode("utf-8")
    assert length_prefix == len(encoded_json)
    assert json.loads(encoded_json) == payload

    # Test read_message_frame from in-memory buffer
    buf.seek(0)
    read_result = read_message_frame(stream=buf)
    assert read_result is not None
    assert read_result["status"] == "READY"
    assert read_result["exergy"] == 500.0
    assert "_sha256_commitment" in read_result


def test_read_message_frame_exceeds_max_bytes(caplog):
    caplog.set_level(logging.ERROR)
    raw_payload = json.dumps({"data": "x" * 1000}).encode("utf-8")
    buf = io.BytesIO(struct.pack("<I", len(raw_payload)) + raw_payload)

    # Set max_bytes lower than payload length
    result = read_message_frame(stream=buf, max_bytes=100)
    assert result is None
    assert "Payload length" in caplog.text


def test_read_message_frame_truncated_stream(caplog):
    caplog.set_level(logging.ERROR)
    buf = io.BytesIO(struct.pack("<I", 100) + b"short")
    result = read_message_frame(stream=buf)
    assert result is None
    assert "Truncated binary payload stream" in caplog.text


def test_process_extension_event_dispatch(caplog):
    caplog.set_level(logging.INFO)
    logger = logging.getLogger("moskv_native_host")

    # Dispatch READY status
    process_extension_event({"status": "READY"}, logger)
    assert "READY" in caplog.text

    # Dispatch CRYSTALLIZED status
    process_extension_event({"status": "CRYSTALLIZED", "url": "https://example.com/b60"}, logger)
    assert "Crystallized" in caplog.text

    # Dispatch FATAL_ENTROPY status
    process_extension_event({"status": "FATAL_ENTROPY", "error": "BFT Failure"}, logger)
    assert "Byzantine Failure" in caplog.text
