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
from contextlib import contextmanager
import fcntl
import hashlib
import json
import logging
import os
import stat
import signal
import struct
import sys
import uuid
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


class PrivateRotatingHandler(logging.Handler):
    """Bounded logs anchored to a private directory descriptor."""

    def __init__(self, path: Path, max_bytes: int = 1024 * 1024, backups: int = 3):
        super().__init__()
        if max_bytes < 256 or not 1 <= backups <= 10:
            raise ValueError("Invalid rotation bounds")
        self.max_bytes = max_bytes
        self.backups = backups
        self.filename = path.name
        absolute = path.parent.absolute()
        fd = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in absolute.parts[1:]:
                if part == "..":
                    raise ValueError("Parent traversal is not allowed")
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            info = os.fstat(fd)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise PermissionError("Log directory must be private (0700) and user-owned")
            self.directory = fd
            self.stream_fd = self._open()
        except BaseException:
            os.close(fd)
            raise

    def _open(self) -> int:
        fd = os.open(self.filename, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=self.directory)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            os.close(fd)
            raise PermissionError("Log must be a private regular file without hardlinks")
        os.fchmod(fd, 0o600)
        return fd

    def emit(self, record: logging.LogRecord) -> None:
        data = (self.format(record) + "\n").encode("utf-8")[:self.max_bytes]
        if os.fstat(self.stream_fd).st_size + len(data) > self.max_bytes:
            for index in range(self.backups, 0, -1):
                source = self.filename if index == 1 else f"{self.filename}.{index - 1}"
                dest = f"{self.filename}.{index}"
                try:
                    os.rename(source, dest, src_dir_fd=self.directory, dst_dir_fd=self.directory)
                except FileNotFoundError:
                    pass
            os.close(self.stream_fd)
            self.stream_fd = self._open()
        while data:
            written = os.write(self.stream_fd, data)
            data = data[written:]

    def close(self) -> None:
        if getattr(self, "stream_fd", None) is not None:
            os.close(self.stream_fd)
            del self.stream_fd
            os.close(self.directory)
        super().close()


def setup_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """Keep minimized operational logs in a private bounded store."""
    if log_file is None:
        log_file = Path.home() / ".babylon60" / "native_host_logs" / "moskv_native_host.log"
    logger = logging.getLogger("moskv_native_host")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = PrivateRotatingHandler(log_file)
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


DEFAULT_PROMPT = "Dark cyber flamenco ambient with heavy bass, 120bpm"
QUEUE_FILE = Path.home() / ".babylon60" / "native_host_queue" / "prompts.json"


def _private_regular(fd: int) -> None:
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) & 0o077):
        raise PermissionError("Queue files must be private, user-owned regular files without hardlinks")


def _open_queue_lock(directory: int) -> int:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK
    # Concurrent cold starts on APFS can transiently return ENOENT while a
    # name is being created. Separate exclusive creation from opening an
    # existing lock; never unlink it or retry unsafe-object errors.
    for _ in range(8):
        try:
            return os.open(".queue.lock", flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
        except FileExistsError:
            try:
                return os.open(".queue.lock", flags, dir_fd=directory)
            except FileNotFoundError:
                continue
        except FileNotFoundError:
            continue
    raise RuntimeError("Queue lock could not be opened after bounded creation retries")


@contextmanager
def _queue_store():
    """Serialize callers using a stable lock in a descriptor-anchored private directory."""
    absolute = QUEUE_FILE.parent.absolute()
    directory = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
    lock = None
    try:
        for part in absolute.parts[1:]:
            if part == "..":
                raise ValueError("Parent traversal is not allowed")
            try:
                os.mkdir(part, 0o700, dir_fd=directory)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("Queue directory must be private and user-owned")
        lock = _open_queue_lock(directory)
        _private_regular(lock)
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield directory
    finally:
        if lock is not None:
            os.close(lock)
        os.close(directory)


def _read_queue(directory: int) -> list[str]:
    try:
        fd = os.open(QUEUE_FILE.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError:
        return []
    try:
        _private_regular(fd)
        with os.fdopen(fd, "r", encoding="utf-8", closefd=False) as stream:
            queue = json.load(stream)
        if not isinstance(queue, list) or any(not isinstance(item, str) for item in queue):
            raise ValueError("Invalid queue schema; original content preserved")
        return queue
    finally:
        os.close(fd)


def _write_queue(directory: int, queue: list[str]) -> None:
    temporary = f".queue-{uuid.uuid4().hex}.json"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", closefd=False) as stream:
            json.dump(queue, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(fd)
        os.replace(temporary, QUEUE_FILE.name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(fd)
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def queued_prompts() -> list[str]:
    with _queue_store() as directory:
        return _read_queue(directory)


def clear_prompt_queue() -> None:
    with _queue_store() as directory:
        _read_queue(directory)  # Reject unsafe/corrupt existing objects before changing anything.
        _write_queue(directory, [])


def enqueue_prompt(prompt: str) -> int:
    """Enqueue a prompt for causal synthesis (Action E: TaskQueue)."""
    if not isinstance(prompt, str):
        raise TypeError("Prompt must be a string")
    with _queue_store() as directory:
        queue = _read_queue(directory)
        queue.append(prompt)
        _write_queue(directory, queue)
        return len(queue)


def get_next_prompt() -> str:
    """Pop the next prompt from the FIFO queue, or fallback to default."""
    with _queue_store() as directory:
        queue = _read_queue(directory)
        if not queue:
            return DEFAULT_PROMPT
        prompt = queue.pop(0)
        _write_queue(directory, queue)
        return prompt


def process_extension_event(msg: dict[str, Any], logger: logging.Logger) -> None:
    """Dispatch extension event to Motor Causal handler."""
    status = msg.get("status")
    cmd = msg.get("cmd")
    logger.info("Ingested extension event")

    if cmd == "PING":
        import time
        logger.info("PING received from extension. Emitting PONG...")
        send_message_frame(
            {
                "status": "PONG",
                "timestamp": time.time(),
                "echo": msg.get("payload"),
            }
        )
    elif status == "READY":
        prompt = get_next_prompt()
        logger.info("Extension READY. Emitting GENERATE command [characters=%d]", len(prompt))
        send_message_frame(
            {
                "cmd": "GENERATE",
                "prompt": prompt,
                "exergy_target": 1000.0,
            }
        )
    elif status == "CRYSTALLIZED":
        url = msg.get("url", "unknown")
        logger.info("Domain state crystallized. Artifact received")
        # Invariante de Centralización de Activos Musicales (Directorio Canónico ~/Music)
        if url.startswith("http://") or url.startswith("https://"):
            try:
                import time
                import urllib.request
                dest_dir = Path.home() / "Music" / "MusicFX"
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / f"musicfx_{int(time.time())}.wav"
                logger.info("Downloading crystallized asset to canonical directory %s...", dest_file)
                urllib.request.urlretrieve(url, dest_file)
                logger.info("Asset successfully centralized at %s", dest_file)
                send_message_frame(
                    {
                        "status": "ASSET_STORED",
                        "path": str(dest_file),
                        "url": url,
                    }
                )
            except Exception as e:
                logger.error("Failed to centralize audio asset [%s]", type(e).__name__)
    elif status == "FATAL_ENTROPY":
        error_msg = msg.get("error", "unspecified")
        logger.error("Byzantine Failure reported by extension [characters=%d]", len(str(error_msg)))
    else:
        logger.warning("Unrecognized extension event")


def run_selftest(logger: logging.Logger) -> bool:
    """Execute hermetic in-memory self-test of IPC framing and handlers."""
    import io
    logger.info("Running hermetic self-test...")
    
    # Test 1: Frame Packing and Unpacking
    test_payload = {"cmd": "PING", "payload": "SelfTest_Probe_123"}
    out_buf = io.BytesIO()
    if not send_message_frame(test_payload, stream=out_buf):
        logger.error("SelfTest Failed: send_message_frame returned False")
        return False
    
    out_buf.seek(0)
    unpacked = read_message_frame(stream=out_buf)
    if not unpacked or unpacked.get("cmd") != "PING" or unpacked.get("payload") != "SelfTest_Probe_123":
        logger.error("SelfTest Failed: unpacked frame mismatch: %s", unpacked)
        return False
    
    hash_comm = unpacked.get("_hash_commitment")
    hash_str = str(hash_comm)[:12] if hash_comm is not None else "none"
    logger.info("Frame encode/decode: PASSED (hash_commitment=%s)", hash_str)
    return True


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Native Host Transducer."""
    parser = argparse.ArgumentParser(description="MOSKV Native Host Transducer (Chrome Native Messaging IPC)")
    parser.add_argument("--log-file", type=Path, default=None, help="Path to log file")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_PAYLOAD_BYTES, help="Max IPC payload bound")
    parser.add_argument("--selftest", action="store_true", help="Execute hermetic framing self-test and exit")
    parser.add_argument("--enqueue", type=str, default=None, help="Enqueue a prompt for the next generation task and exit")
    parser.add_argument("--list-queue", action="store_true", help="List currently queued prompts and exit")
    parser.add_argument("--clear-queue", action="store_true", help="Clear all currently queued prompts and exit")
    return parser.parse_args()


def main() -> None:
    """Native Messaging Transducer loop (Turing-Incomplete sentinel halting)."""
    args = parse_args()

    if args.enqueue:
        count = enqueue_prompt(args.enqueue)
        print(f"[✓] Enqueued prompt: '{args.enqueue}'. Total in queue: {count}")
        sys.exit(0)

    if args.list_queue:
        items = queued_prompts()
        if items:
            print(f"Current Moskv Queue ({len(items)} items):")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")
        else:
            print("Moskv Queue is empty.")
        sys.exit(0)

    if args.clear_queue:
        clear_prompt_queue()
        print("[✓] Moskv Queue cleared.")
        sys.exit(0)

    logger = setup_logger(args.log_file)
    logger.info("Initializing Motor Causal Native Host Transducer (max_bytes=%d)...", args.max_bytes)

    if args.selftest:
        success = run_selftest(logger)
        print("SELFTEST_PASSED" if success else "SELFTEST_FAILED")
        sys.exit(0 if success else 1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Bounded sentinel loop: terminates on EOF, None read, or signal halt
    while RUNNING and (msg := read_message_frame(max_bytes=args.max_bytes)) is not None:
        process_extension_event(msg, logger)

    logger.info("Native Host Transducer terminated gracefully.")


if __name__ == "__main__":
    main()
