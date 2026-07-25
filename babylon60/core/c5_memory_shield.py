from __future__ import annotations

import ctypes
import resource
import sys


def _kill_self() -> None:
    sys.exit(1)

def enforce_no_coredump() -> None:
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except ValueError as exc:
        print(f'[OPSEC] RLIMIT_CORE rejection: {exc}', file=sys.stderr)
        _kill_self()

def enforce_anti_debug() -> None:
    if sys.platform != 'darwin':
        return
    try:
        libc = ctypes.CDLL('libc.dylib')
        result: int = libc.ptrace(31, 0, None, 0)
        if result != 0:
            print('[OPSEC] Debugger detected — SIGKILL.', file=sys.stderr)
            _kill_self()
    except OSError as exc:
        print(f'[OPSEC] ptrace syscall failed: {exc}', file=sys.stderr)
        _kill_self()

def arm() -> dict[str, bool | str]:
    coredump_ok = False
    antidebug_ok = False
    enforce_no_coredump()
    coredump_ok = True
    enforce_anti_debug()
    antidebug_ok = True
    return {'coredump_disabled': coredump_ok, 'antidebug_armed': antidebug_ok, 'platform': sys.platform}