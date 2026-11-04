"""Resource-limit regressions using in-memory frames, without browser startup."""

import asyncio
import io
import json
import os
import struct
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from babylon60.kernel.browser_cdp_engine import CDPPage
from babylon60.kernel import native_messaging_host as host


def test_cdp_history_retains_recent_bounded_fields():
    page = CDPPage("test", "unused", max_network_logs=3, max_network_field_chars=8)

    async def events():
        for index in range(20):
            yield json.dumps(
                {
                    "method": "Network.responseReceived",
                    "params": {"response": {"url": "x" * 200, "status": index, "mimeType": "text/" + "y" * 100}},
                }
            )

    page.ws = events()
    asyncio.run(page._listen_loop())
    assert isinstance(page.network_logs, list)
    assert [record["status"] for record in page.network_logs] == [17, 18, 19]
    assert page.network_logs_dropped == 17
    assert all(len(record["url"]) == 8 and len(record["mimeType"]) == 8 for record in page.network_logs)


def test_cdp_history_can_be_disabled():
    page = CDPPage("test", "unused", max_network_logs=0)

    async def events():
        yield json.dumps({"method": "Network.responseReceived", "params": {"response": {}}})

    page.ws = events()
    asyncio.run(page._listen_loop())
    assert page.network_logs == []
    assert page.network_logs_dropped == 1


def test_native_rejects_large_frame_without_reading_body(monkeypatch):
    stream = io.BytesIO(struct.pack("@I", 0xFFFFFFFF) + b"body must remain unread")
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
    with pytest.raises(ValueError, match="byte limit"):
        host.get_message()
    assert stream.tell() == 4


def test_native_accepts_exact_limit_and_clean_eof(monkeypatch):
    body = b'{"cmd":"PING"}'
    stream = io.BytesIO(struct.pack("@I", len(body)) + body)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
    assert host.get_message(max_message_bytes=len(body)) == {"cmd": "PING"}
    assert host.get_message() is None


@pytest.mark.parametrize("frame", [b"\x01", struct.pack("@I", 5) + b"{}"])
def test_native_rejects_truncated_frames(monkeypatch, frame):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(frame)))
    with pytest.raises(EOFError, match="Incomplete"):
        host.get_message()


def test_native_configured_limit_rejected_before_body(monkeypatch):
    stream = io.BytesIO(struct.pack("@I", 3) + b"{} ")
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
    with pytest.raises(ValueError, match="byte limit"):
        host.get_message(max_message_bytes=2)
    assert stream.tell() == 4


@pytest.mark.parametrize("kwargs", [{"max_network_logs": -1}, {"max_network_field_chars": 0}])
def test_cdp_rejects_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        CDPPage("test", "unused", **kwargs)


@pytest.mark.parametrize("partial", [b"\x01", struct.pack("@I", 20) + b"{"])
def test_native_partial_pipe_times_out_and_restores_descriptor(monkeypatch, partial):
    read_fd, write_fd = os.pipe()
    with os.fdopen(read_fd, "rb", buffering=0) as stream:
        try:
            os.write(write_fd, partial)
            monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
            started = time.monotonic()
            with pytest.raises(TimeoutError, match="deadline"):
                host.get_message(timeout_seconds=0.05)
            assert 0.04 <= time.monotonic() - started < 1.0
            assert os.get_blocking(read_fd)
        finally:
            os.close(write_fd)


def test_native_pipe_valid_frames_do_not_overread(monkeypatch):
    read_fd, write_fd = os.pipe()
    with os.fdopen(read_fd, "rb", buffering=0) as stream:
        try:
            body = b'{"cmd":"PING"}'
            frame = struct.pack("@I", len(body)) + body
            os.write(write_fd, frame * 2)
            monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
            assert host.get_message(timeout_seconds=0.5) == {"cmd": "PING"}
            assert host.get_message(timeout_seconds=0.5) == {"cmd": "PING"}
            assert os.get_blocking(read_fd)
        finally:
            os.close(write_fd)


def test_native_idle_pipe_keeps_connection_until_first_frame(monkeypatch):
    read_fd, write_fd = os.pipe()
    body = b'{"cmd":"PING"}'
    frame = struct.pack("@I", len(body)) + body
    release = threading.Event()

    def delayed_frame():
        # An idle connection is valid even after a whole frame deadline.
        release.wait(0.15)
        try:
            os.write(write_fd, frame)
        except BrokenPipeError:
            pass
        finally:
            os.close(write_fd)

    writer = threading.Thread(target=delayed_frame)
    with os.fdopen(read_fd, "rb", buffering=0) as stream:
        monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
        writer.start()
        try:
            assert host.get_message(timeout_seconds=0.05) == {"cmd": "PING"}
            assert os.get_blocking(read_fd)
        finally:
            release.set()
            writer.join(timeout=1)


def test_native_pipe_bounded_repeated_frames_after_warmup(monkeypatch: pytest.MonkeyPatch) -> None:
    read_fd, write_fd = os.pipe()
    body = b'{"cmd":"PING"}'
    frame = struct.pack("@I", len(body)) + body
    with os.fdopen(read_fd, "rb", buffering=0) as stream:
        try:
            monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))
            for count in (16, 128):
                for _ in range(count):
                    assert os.write(write_fd, frame) == len(frame)
                    assert host.get_message(timeout_seconds=0.5) == {"cmd": "PING"}
                    assert os.get_blocking(read_fd)
        finally:
            os.close(write_fd)


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_native_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="finite and positive"):
        host.get_message(timeout_seconds=timeout)


def test_native_nonblocking_unavailable_fails_before_read(monkeypatch):
    read_fd, write_fd = os.pipe()
    with os.fdopen(read_fd, "rb", buffering=0) as stream:
        try:
            monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=stream))

            def unsupported(fd, blocking):
                raise OSError("nonblocking unavailable")

            monkeypatch.setattr(os, "set_blocking", unsupported)
            with pytest.raises(OSError, match="nonblocking unavailable"):
                host.get_message(timeout_seconds=0.05)
        finally:
            os.close(write_fd)
