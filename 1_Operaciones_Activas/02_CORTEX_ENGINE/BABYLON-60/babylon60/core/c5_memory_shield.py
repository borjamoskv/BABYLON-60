# C5-REAL EXERGY CERTIFIED
"""C5-REAL OPSEC Memory Shield — Process Isolation Layer.

Prevents coredump exfiltration and debugger attachment on Darwin (macOS).
Must be imported as the FIRST module in any cryptographic or BFT entry point.

CORTEX-TAINT:borjamoskv:opsec_memory_shield:2026-07-18T00:13:25+02:00
"""

from __future__ import annotations

import ctypes
import os
import resource
import signal
import sys


def _kill_self() -> None:
    """Immediate process termination. No cleanup, no handler, no trace."""
    os.kill(os.getpid(), signal.SIGKILL)


def enforce_no_coredump() -> None:
    """Set RLIMIT_CORE to zero. Prevents RAM dumps on crash."""
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except ValueError as exc:
        # If the kernel rejects the limit, the process is compromised.
        print(f"[OPSEC] RLIMIT_CORE rejection: {exc}", file=sys.stderr)
        _kill_self()


def enforce_anti_debug() -> None:
    """Invoke ptrace(PT_DENY_ATTACH) on macOS to block debugger injection.

    PT_DENY_ATTACH = 31. If a debugger is already attached, ptrace returns
    nonzero and we SIGKILL immediately (Fail-Fast).
    """
    if sys.platform != "darwin":
        return

    try:
        libc = ctypes.CDLL("libc.dylib")
        result: int = libc.ptrace(31, 0, None, 0)
        if result != 0:
            print("[OPSEC] Debugger detected — SIGKILL.", file=sys.stderr)
            _kill_self()
    except OSError as exc:
        print(f"[OPSEC] ptrace syscall failed: {exc}", file=sys.stderr)
        _kill_self()


def arm() -> dict[str, bool | str]:
    """Execute full OPSEC Memory Shield sequence.

    Returns a status dict for audit logging.
    Must be called BEFORE any key decoding or payload import.
    """
    coredump_ok = False
    antidebug_ok = False

    enforce_no_coredump()
    coredump_ok = True

    enforce_anti_debug()
    antidebug_ok = True

    return {
        "coredump_disabled": coredump_ok,
        "antidebug_armed": antidebug_ok,
        "platform": sys.platform,
    }
