#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
MOSKV-1 APEX: Native Messaging Transducer (INV_C5_18 / INV_C5_THERMO_VALVE)
Bridge between WebExtension IPC (Chrome/Firefox Native Messaging) and Motor Causal Core.

Protocol Specifications:
- 32-bit unsigned little-endian integer length prefix (<I)
- Max payload bound: 1 MiB (1,048,576 bytes)
- Bounded sentinel-halting read loop (INV_C5_TURING_CASTRATION)
- SHA-256 Cryptographic Payload Commitments (INV_C5_15)
"""

import argparse
import hashlib
import json
import logging
import signal
import struct
import sys
from pathlib import Path
from typing import Any, BinaryIO, Optional

DEFAULT_MAX_PAYLOAD_BYTES = 1024 * 1024  # 1 MiB Chrome Native Messaging ceiling
RUNNING = True


def signal_handler(signum: int, _frame: Any) -> None:
    """Handle termination signals gracefully (INV_C5_TURING_CASTRATION)."""
    global RUNNING
    RUNNING = False
    logger = logging.getLogger("moskv_native_host")
    logger.info("Signal %d received. Halting Native Host Transducer...", signum)


def setup_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """Initialize file logger (stdout is strictly reserved for binary IPC)."""
    if log_file is None:
        import os
        babylon_home = os.environ.get("BABYLON_HOME")
        if babylon_home:
            log_dir = Path(babylon_home) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
        else:
            log_dir = Path("/tmp")
        log_file = log_dir / "moskv_native_host.log"

    logger = logging.getLogger("moskv_native_host")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
    return logger


def calculate_payload_commitment(raw_bytes: bytes) -> str:
    """Compute 256-bit SHA3-256 cryptographic payload hash (INV_C5_15)."""
    return hashlib.sha3_256(raw_bytes).hexdigest()


def read_message_frame(
    stream: Optional[BinaryIO] = None,
    max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
) -> Optional[dict[str, Any]]:
    """Read a single binary framed message from stdin using Chrome Native IPC protocol."""
    if stream is None:
        stream = sys.stdin.buffer

    try:
        header = stream.read(4)
        if len(header) < 4:
            return None

        (payload_length,) = struct.unpack("<I", header)
        if payload_length > max_bytes:
            raise ValueError(f"Payload length {payload_length} exceeds max bound {max_bytes}")

        raw_payload = stream.read(payload_length)
        if len(raw_payload) < payload_length:
            raise EOFError("Truncated binary payload stream")

        commitment = calculate_payload_commitment(raw_payload)
        loaded = json.loads(raw_payload.decode("utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("Payload must be a JSON object")
        payload: dict[str, Any] = loaded
        payload["_hash_commitment"] = commitment
        return payload
    except (struct.error, json.JSONDecodeError, ValueError, EOFError) as exc:
        logger = logging.getLogger("moskv_native_host")
        logger.error("IPC Frame Unpacking Error: %s", exc)
        return None


def send_message_frame(payload: dict[str, Any], stream: Optional[BinaryIO] = None) -> bool:
    """Send a framed binary message to stdout using 32-bit LE length prefix."""
    if stream is None:
        stream = sys.stdout.buffer

    try:
        # Exclude internal commitment from outgoing wire format if present
        wire_payload = {k: v for k, v in payload.items() if not k.startswith("_")}
        encoded = json.dumps(wire_payload).encode("utf-8")
        length_prefix = struct.pack("<I", len(encoded))
        stream.write(length_prefix)
        stream.write(encoded)
        stream.flush()
        return True
    except (OSError, TypeError, ValueError) as exc:
        logger = logging.getLogger("moskv_native_host")
        logger.error("IPC Frame Packing Error: %s", exc)
        return False


def process_extension_event(msg: dict[str, Any], logger: logging.Logger) -> None:
    """Dispatch extension event to Motor Causal handler."""
    status = msg.get("status")
    commitment = msg.get("_hash_commitment", "unknown")[:12]
    logger.info("Ingested Extension Event [status=%s, hash=%s]", status, commitment)

    if status == "READY":
        logger.info("Extension operational state READY. Emitting GENERATE command...")
        send_message_frame(
            {
                "cmd": "GENERATE",
                "prompt": "Synthwave dark ambient with heavy bass, 120bpm",
                "exergy_target": 1000.0,
            }
        )
    elif status == "CRYSTALLIZED":
        url = msg.get("url", "unknown")
        logger.info("Thermodynamic Success: Domain state crystallized. Artifact URL: %s", url)
    elif status == "FATAL_ENTROPY":
        error_msg = msg.get("error", "unspecified")
        logger.error("Byzantine Failure reported by extension: %s", error_msg)
    else:
        logger.warning("Unrecognized event payload status: %s", status)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Native Host Transducer."""
    parser = argparse.ArgumentParser(description="MOSKV Native Host Transducer (Chrome Native Messaging IPC)")
    parser.add_argument("--log-file", type=Path, default=None, help="Path to log file")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_PAYLOAD_BYTES, help="Max IPC payload bound")
    return parser.parse_args()


def main() -> None:
    """Native Messaging Transducer loop (Turing-Incomplete sentinel halting)."""
    args = parse_args()
    logger = setup_logger(args.log_file)
    logger.info("Initializing Motor Causal Native Host Transducer (max_bytes=%d)...", args.max_bytes)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Bounded sentinel loop: terminates on EOF, None read, or signal halt
    while RUNNING and (msg := read_message_frame(max_bytes=args.max_bytes)) is not None:
        process_extension_event(msg, logger)

    logger.info("Native Host Transducer terminated gracefully.")


if __name__ == "__main__":
    main()
