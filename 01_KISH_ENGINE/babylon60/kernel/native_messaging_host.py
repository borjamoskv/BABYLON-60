#!/usr/bin/env python3
"""
Native Messaging Host para CORTEX / BABYLON-60
Aislado, 0 anergía, comunicación por Stdin/Stdout binario.
"""

import sys
import struct
import json
import logging
import os
import io
import math
import stat
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

# Toda traza o log DEBE ir a stderr o archivo, nunca a stdout, ya que arruina el túnel IPC
LOG_FILE = os.path.join(os.path.dirname(__file__), "native_host.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


MAX_MESSAGE_BYTES = 1024 * 1024


FRAME_TIMEOUT_SECONDS = 5.0


@contextmanager
def _frame_reader() -> Iterator[Callable[[int], bytes]]:
    """Own stdin reads exclusively; never create a background reader thread.

    Nonblocking pipes are supported by POSIX and modern Python on Windows.
    Unsupported transports fail closed, rather than falling back to blocking IO.
    BytesIO is accepted for finite, in-memory input.
    """
    stream = sys.stdin.buffer
    if isinstance(stream, io.BytesIO):
        yield stream.read
        return
    fd = stream.fileno()
    mode = os.fstat(fd).st_mode
    if not (stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)):
        raise OSError("Native messaging requires a nonblocking pipe or socket")
    blocking = os.get_blocking(fd)
    os.set_blocking(fd, False)
    try:
        yield lambda size: os.read(fd, size)
    finally:
        os.set_blocking(fd, blocking)


def _read_before_deadline(read: Callable[[int], bytes], count: int, deadline: float | None) -> bytes:
    result = bytearray()
    while len(result) < count:
        remaining = deadline - time.monotonic() if deadline is not None else None
        if remaining is not None and remaining <= 0:
            raise TimeoutError("Native messaging frame deadline exceeded")
        try:
            chunk = read(min(count - len(result), 65536))
        except BlockingIOError:
            time.sleep(min(0.005, remaining) if remaining is not None else 0.005)
            continue
        except InterruptedError:
            continue
        if not chunk:
            break
        result.extend(chunk)
    return bytes(result)


def get_message(
    *,
    max_message_bytes: int = MAX_MESSAGE_BYTES,
    timeout_seconds: float = FRAME_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """Bound a started frame; keep idle browser connections open until data or EOF."""
    if max_message_bytes < 1:
        raise ValueError("max_message_bytes must be positive")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    with _frame_reader() as read:
        first_byte = _read_before_deadline(read, 1, None)
        if not first_byte:
            return None
        deadline = time.monotonic() + timeout_seconds
        raw_length = first_byte + _read_before_deadline(read, 3, deadline)
        if len(raw_length) != 4:
            raise EOFError("Incomplete native messaging header")
        message_length: int = struct.unpack("@I", raw_length)[0]
        if message_length > max_message_bytes:
            raise ValueError("Native messaging frame exceeds byte limit")
        body = _read_before_deadline(read, message_length, deadline)
        if len(body) != message_length:
            raise EOFError("Incomplete native messaging body")
    message = body.decode("utf-8")
    data = json.loads(message)
    if isinstance(data, dict):
        return data
    return None


def send_message(message_dict: dict[str, Any]) -> None:
    message = json.dumps(message_dict)
    encoded_message = message.encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded_message)))
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()


def main() -> None:
    logging.info("=======================================")
    logging.info("BABYLON-60 NATIVE HOST ACTIVE (Ring-0)")
    logging.info("=======================================")

    while True:
        try:
            msg = get_message()
            if msg is None:
                logging.info("EOF: Chrome cerró el túnel IPC.")
                break

            logging.info(f"Mensaje entrante de Extensión: {msg}")

            # PoC Causal Echo
            cmd = msg.get("cmd")
            if cmd == "PING":
                reply = {"status": "POC_SUCCESS", "kernel": "MOSKV-1", "echo": msg.get("payload", "")}
                send_message(reply)
                logging.info(f"Respuesta enviada: {reply}")
            elif cmd == "GENERATE":
                # FSM Integration
                reply = {"status": "QUEUED", "message": "FSM Signal Acknowledged by Python Kernel"}
                send_message(reply)
                logging.info("Comando GENERATE interceptado.")
            else:
                send_message({"status": "UNKNOWN_CMD", "cmd": cmd})

        except Exception as e:
            logging.error(f"Error termodinámico fatal en IPC: {e}")
            break


if __name__ == "__main__":
    main()
