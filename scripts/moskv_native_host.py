#!/usr/bin/env python3
"""
MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE)
Bridge between WebExtension IPC (Chrome/Firefox Native Messaging) and Motor Causal Core.

Protocol Specifications:
- 32-bit unsigned little-endian integer length prefix (<I)
- Max payload bound: 1 MiB (1,048,576 bytes)
- Bounded sentinel-halting read loop (INV_C5_TURING_CASTRATION)
"""

import json
import logging
import struct
import sys
from pathlib import Path
from typing import Any, Optional

MAX_PAYLOAD_BYTES = 1024 * 1024  # 1 MiB Chrome Native Messaging ceiling


def setup_logger() -> logging.Logger:
    """Initialize file logger (stdout is strictly reserved for binary IPC)."""
    log_dir = Path.home() / "80_LOGS"
    if not log_dir.exists():
        log_dir = Path("/tmp")
    log_path = log_dir / "moskv_native_host.log"

    logger = logging.getLogger("moskv_native_host")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
    return logger


def read_message_frame() -> Optional[dict[str, Any]]:
    """Read a single binary framed message from stdin using Chrome Native IPC protocol."""
    try:
        header = sys.stdin.buffer.read(4)
        if len(header) < 4:
            return None

        (payload_length,) = struct.unpack("<I", header)
        if payload_length > MAX_PAYLOAD_BYTES:
            raise ValueError(f"Payload length {payload_length} exceeds max bound {MAX_PAYLOAD_BYTES}")

        raw_payload = sys.stdin.buffer.read(payload_length)
        if len(raw_payload) < payload_length:
            raise EOFError("Truncated binary payload stream")

        return json.loads(raw_payload.decode("utf-8"))
    except (struct.error, json.JSONDecodeError, ValueError, EOFError) as exc:
        logger = logging.getLogger("moskv_native_host")
        logger.error("IPC Frame Unpacking Error: %s", exc)
        return None


def send_message_frame(payload: dict[str, Any]) -> bool:
    """Send a framed binary message to stdout using 32-bit LE length prefix."""
    try:
        encoded = json.dumps(payload).encode("utf-8")
        length_prefix = struct.pack("<I", len(encoded))
        sys.stdout.buffer.write(length_prefix)
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
        return True
    except Exception as exc:
        logger = logging.getLogger("moskv_native_host")
        logger.error("IPC Frame Packing Error: %s", exc)
        return False


def process_extension_event(msg: dict[str, Any], logger: logging.Logger) -> None:
    """Dispatch extension event to Motor Causal handler."""
    status = msg.get("status")
    logger.info("Ingested Extension Event [status=%s]", status)

    if status == "READY":
        logger.info("Extension operational state READY. Emitting GENERATE command...")
        send_message_frame({
            "cmd": "GENERATE",
            "prompt": "Synthwave dark ambient with heavy bass, 120bpm",
            "exergy_target": 1000.0,
        })
    elif status == "CRYSTALLIZED":
        url = msg.get("url", "unknown")
        logger.info("Thermodynamic Success: Domain state crystallized. Artifact URL: %s", url)
    elif status == "FATAL_ENTROPY":
        error_msg = msg.get("error", "unspecified")
        logger.error("Byzantine Failure reported by extension: %s", error_msg)
    else:
        logger.warning("Unrecognized event payload status: %s", status)


def main() -> None:
    """Native Messaging Transducer loop (Turing-Incomplete sentinel halting)."""
    logger = setup_logger()
    logger.info("Initializing Motor Causal Native Host Transducer...")

    # Bounded sentinel loop: terminates when stdin closes or framed read returns None
    while (msg := read_message_frame()) is not None:
        process_extension_event(msg, logger)

    logger.info("Native Host Transducer terminated gracefully (EOF received).")


if __name__ == "__main__":
    main()
