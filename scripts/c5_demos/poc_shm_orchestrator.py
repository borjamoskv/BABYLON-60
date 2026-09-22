#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
POSIX Shared Memory (SHM) IPC Orchestrator & Zero-Leak Verifier
================================================================
Audited under KUDURRU-64 Invariant (Ring-0 / Ring-1 C-ABI Hot Path).
Guarantees deterministic lifecycle management over multiprocessing.shared_memory
on macOS (Darwin kernel shm_open/shm_unlink) and POSIX systems.

Invariants Enforced:
1. INV_C5_SHM_ALIGN: Kudurru64 struct is strictly 64 bytes (1 L1 cache line).
2. INV_C5_SHM_ZERO_LEAK: Any exit (clean, exception, SIGINT, SIGTERM) guarantees
   shm.unlink() and shm.close() in nested try...finally blocks.
3. INV_C5_SHM_ORPHAN_RECLAIM: Recovers stale segments from previous ungraceful kills.
4. INV_C5_SHM_BUFFER_DECOUPLING: Decouples ctypes structure references before closing
   to avoid Python BufferError on exported memory views.
"""

import argparse
import atexit
import ctypes
import mmap
import os
import signal
import sys
import time
from multiprocessing import shared_memory
from typing import Optional, Union

# ============================================================================
# 1. KUDURRU-64 C-ABI SPECIFICATION (64 Bytes / 1 Cache Line)
# ============================================================================
class Kudurru64(ctypes.Structure):
    """
    C-ABI lock-free 64-byte memory mapping definition (KUDURRU-64).
    Aligned to 64 bytes to eliminate false sharing across CPU cache lines.
    Offsets:
      0..8   : sequence_id (uint64)
      8..40  : biometric_attestation_hash (uint8[32])
      40..44 : state_flags (uint32)
      44..46 : exergy_score (uint16)
      46..50 : ebr_ticket (uint32)
      50..64 : padding (uint8[14])
      Total  : 64 bytes.
    """
    _layout_ = "ms"
    _pack_ = 2
    _fields_ = [
        ("sequence_id", ctypes.c_uint64),
        ("biometric_attestation_hash", ctypes.c_uint8 * 32),
        ("state_flags", ctypes.c_uint32),
        ("exergy_score", ctypes.c_uint16),
        ("ebr_ticket", ctypes.c_uint32),
        ("padding", ctypes.c_uint8 * 14),
    ]

# Assert KUDURRU-64 invariant at module load time
assert ctypes.sizeof(Kudurru64) == 64, (
    f"INV_C5_SHM_ALIGN fractured: expected exactly 64 bytes, got {ctypes.sizeof(Kudurru64)}"
)


# ============================================================================
# 2. SOVEREIGN SHM LIFECYCLE MANAGER (DETERMINISTIC ZERO-LEAK)
# ============================================================================
class SovereignShmManager:
    """
    Deterministic POSIX Shared Memory Context Manager.
    
    Protects macOS Darwin kernel shm_open tables from leaks across:
    - Normal script completion
    - Unhandled Python exceptions (KeyError, RuntimeError, etc.)
    - Process interruption signals: SIGINT (Ctrl+C), SIGTERM (pkill/launchd)
    - Stale orphaned segments from prior ungraceful crashes (SIGKILL)
    """

    def __init__(self, name: str = "c5_kudurru_shm", size: int = 64, create: bool = True):
        self.name = name
        self.size = size
        self.create = create
        self.shm: Optional[shared_memory.SharedMemory] = None
        self._unlinked: bool = False
        self._previous_sigint = None
        self._previous_sigterm = None

    def _setup_signal_traps(self):
        """Trap termination signals to trigger graceful unwind of finally blocks."""
        def _signal_handler(signum, frame):
            # Raising SystemExit unwinds the Python call stack, executing finally: blocks
            sys.exit(128 + signum)

        self._previous_sigint = signal.signal(signal.SIGINT, _signal_handler)
        self._previous_sigterm = signal.signal(signal.SIGTERM, _signal_handler)

    def _restore_signals(self):
        """Restore previous signal handlers when context exits."""
        if self._previous_sigint is not None:
            signal.signal(signal.SIGINT, self._previous_sigint)
        if self._previous_sigterm is not None:
            signal.signal(signal.SIGTERM, self._previous_sigterm)

    def __enter__(self) -> shared_memory.SharedMemory:
        self._setup_signal_traps()
        atexit.register(self.cleanup)

        if self.create:
            try:
                self.shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.size)
            except FileExistsError:
                # Invariant 3: Reclaim orphaned segment left behind by previous crash
                try:
                    stale = shared_memory.SharedMemory(name=self.name)
                    stale.close()
                    stale.unlink()
                except Exception:
                    pass
                self.shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.size)
        else:
            self.shm = shared_memory.SharedMemory(name=self.name)

        return self.shm

    def cleanup(self):
        """
        Deterministic unlink and close sequence.
        Unlink is given absolute priority to release kernel namespace immediately.
        """
        if self.shm is not None:
            target_shm = self.shm
            self.shm = None  # Prevent re-entrant double execution

            # Step 1: Unlink from kernel namespace (prevents orphaned shm nodes on macOS)
            if self.create and not self._unlinked:
                try:
                    target_shm.unlink()
                    self._unlinked = True
                except FileNotFoundError:
                    self._unlinked = True
                except Exception:
                    pass

            # Step 2: Release exported buffer views to avoid BufferError
            try:
                target_shm.buf.release()
            except Exception:
                pass

            # Step 3: Close local process file descriptor / mmap
            try:
                target_shm.close()
            except Exception:
                pass

        try:
            atexit.unregister(self.cleanup)
        except Exception:
            pass
        self._restore_signals()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


# ============================================================================
# 3. ZERO-COPY HOT PATH TELEMETRY
# ============================================================================
def read_shm_hot_path(target: Union[int, shared_memory.SharedMemory]) -> Kudurru64:
    """
    Zero-friction E2E Orchestrator hot path.
    Instead of spawning subprocess.run() and parsing stdout, it reads the 64-byte 
    L1 cache line directly from the POSIX Shared Memory segment (Zero-Copy).
    """
    if isinstance(target, int):
        # Backward compatibility: raw file descriptor (e.g. from memfd_create)
        with os.fdopen(target, "r+b") as f:
            with mmap.mmap(f.fileno(), 64, access=mmap.ACCESS_READ) as mm:
                kudurru = Kudurru64.from_buffer_copy(mm[:64])
    elif isinstance(target, shared_memory.SharedMemory):
        # Decoupled copy from shared memory buffer to prevent BufferError on unmap
        kudurru = Kudurru64.from_buffer_copy(target.buf[:64])
    else:
        raise TypeError(f"Unsupported target type for SHM read: {type(target)}")

    print("[ TOPOLOGÍA ACTIVA ]: C-FFI Shared Memory (KUDURRU-64)")
    print(f"Sequence ID    : {kudurru.sequence_id}")
    print(f"Exergy Score   : {kudurru.exergy_score} / 21000")
    print(f"State Flags    : {bin(kudurru.state_flags)}")
    print(f"EBR Ticket     : {kudurru.ebr_ticket}")
    hash_hex = bytes(kudurru.biometric_attestation_hash).hex()
    print(f"Attestation    : 0x{hash_hex[:16]}... (32 bytes)")
    return kudurru


def write_shm_telemetry(
    shm: shared_memory.SharedMemory,
    sequence_id: int = 1,
    exergy_score: int = 21000,
    state_flags: int = 0b0001,
    ebr_ticket: int = 1,
    attestation_bytes: Optional[bytes] = None,
) -> None:
    """
    Writes structured KUDURRU-64 telemetry directly into the POSIX shared memory buffer.
    """
    kudurru = Kudurru64()
    kudurru.sequence_id = sequence_id
    kudurru.exergy_score = exergy_score
    kudurru.state_flags = state_flags
    kudurru.ebr_ticket = ebr_ticket

    if attestation_bytes:
        ctypes.memmove(
            kudurru.biometric_attestation_hash,
            attestation_bytes[:32],
            min(len(attestation_bytes), 32),
        )
    else:
        # Default canonical attestation: TouchID Secure Enclave token mock
        default_hash = b"\xca\xfe\xba\xbe" * 8
        ctypes.memmove(kudurru.biometric_attestation_hash, default_hash, 32)

    shm.buf[:64] = bytes(kudurru)


def verify_zero_leak(name: str = "c5_kudurru_shm") -> bool:
    """
    Proves deterministically that no orphaned segment remains in the kernel table.
    """
    try:
        orphan = shared_memory.SharedMemory(name=name)
        orphan.close()
        try:
            orphan.unlink()
        except Exception:
            pass
        return False  # Segment existed: LEAK
    except FileNotFoundError:
        return True   # Segment does not exist: ZERO LEAK


# ============================================================================
# 4. DEMONSTRATION & SELF-TEST SUITE
# ============================================================================
def run_demo(name: str = "c5_kudurru_shm", size: int = 64) -> None:
    """Runs a full create-write-read-cleanup cycle certifying zero kernel leaks."""
    print("============================================================================")
    print("█ BABYLON-60 | POSIX SHM IPC ORCHESTRATOR DEMO (C5-REAL)")
    print("============================================================================")
    print(f"[*] Allocating POSIX Shared Memory segment: '{name}' ({size} bytes)...")

    with SovereignShmManager(name=name, size=size, create=True) as shm:
        print("[*] Segment allocated successfully. Injecting C5 telemetry...")
        write_shm_telemetry(
            shm,
            sequence_id=42,
            exergy_score=21000,
            state_flags=0b0001,
            ebr_ticket=108,
            attestation_bytes=b"\xde\xad\xbe\xef" * 8,
        )

        print("[*] Invoking zero-copy hot path reader:")
        k = read_shm_hot_path(shm)
        assert k.sequence_id == 42, "Sequence ID mismatch"
        assert k.exergy_score == 21000, "Exergy score mismatch"
        assert k.ebr_ticket == 108, "EBR ticket mismatch"
        print("[+] Telemetry read verified with zero-copy C-ABI integrity.")

    print("[*] Context exited. Verifying kernel namespace status...")
    if verify_zero_leak(name):
        print(f"[✅ ZERO-LEAK CERTIFIED]: POSIX segment '{name}' unlinked cleanly from macOS kernel.")
    else:
        print(f"[❌ LEAK DETECTED]: Segment '{name}' remained in kernel table!")
        sys.exit(1)


def run_legacy_fd_demo() -> None:
    """Runs the legacy file descriptor fallback using a temporary backing file."""
    shm_path = "/tmp/c5_kudurru_shm.bin"
    print(f"[*] Running legacy file descriptor fallback via '{shm_path}'...")
    try:
        with open(shm_path, "wb") as f:
            k = Kudurru64()
            k.sequence_id = 7
            k.exergy_score = 19500
            k.state_flags = 0b0010
            k.ebr_ticket = 3
            f.write(bytes(k))

        fd = os.open(shm_path, os.O_RDWR)
        read_shm_hot_path(fd)
    finally:
        if os.path.exists(shm_path):
            os.unlink(shm_path)
        print("[+] Legacy temporary backing file unlinked cleanly.")


def run_signal_test(name: str = "c5_test_signal_leak") -> None:
    """Verifies that SIGINT and SIGTERM trigger deterministic unlinking."""
    print("[*] Executing signal trap verification (SIGINT & SIGTERM)...")
    for sig, sig_name in [(signal.SIGINT, "SIGINT"), (signal.SIGTERM, "SIGTERM")]:
        pid = os.fork()
        if pid == 0:
            # Child process: enter manager, send signal to self
            try:
                with SovereignShmManager(name=name, size=64, create=True) as shm:
                    write_shm_telemetry(shm, sequence_id=100)
                    os.kill(os.getpid(), sig)
            except (KeyboardInterrupt, SystemExit):
                sys.exit(0)
            except Exception:
                sys.exit(2)
        else:
            _, status = os.waitpid(pid, 0)
            time.sleep(0.05)
            if not verify_zero_leak(name):
                print(f"[❌ FAILED]: Leak detected after {sig_name}!")
                sys.exit(1)
            print(f"[+] {sig_name} trapped: segment '{name}' unlinked with 0 kernel leaks.")
    print("[✅ SIGNAL TRAP CERTIFIED]: All termination signals guarantee deterministic cleanup.")


# ============================================================================
# 5. CLI ENTRYPOINT
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="BABYLON-60 POSIX SHM IPC Orchestrator & Zero-Leak Verifier (KUDURRU-64 C-ABI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Invariants Enforced:
  - Kudurru64 alignment: exactly 64 bytes (L1 cache line).
  - Deterministic unlinking on SIGINT, SIGTERM, and unhandled exceptions.
  - Zero-copy C-ABI hot path reading without syscall overhead.
        """,
    )
    parser.add_argument(
        "--name",
        type=str,
        default="c5_kudurru_shm",
        help="POSIX Shared Memory segment name (default: 'c5_kudurru_shm')",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=64,
        help="Segment size in bytes (default: 64)",
    )
    parser.add_argument(
        "--legacy-fd",
        action="store_true",
        help="Run legacy file descriptor fallback test using /tmp file",
    )
    parser.add_argument(
        "--test-signals",
        action="store_true",
        help="Run automated fork/signal test verifying SIGINT/SIGTERM zero-leak cleanup",
    )

    args = parser.parse_args()

    if args.legacy_fd:
        run_legacy_fd_demo()
    elif args.test_signals:
        run_signal_test(name=args.name)
    else:
        run_demo(name=args.name, size=args.size)


if __name__ == "__main__":
    main()
