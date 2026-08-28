# C5-REAL EXERGY CERTIFIED
"""
CORTEX-OS Syscall Interface & Handlers.
Defines system calls: Observe, Measure, Verify, Persist, Search, Compile, Execute, Rollback, Audit, Learn.
"""

from dataclasses import dataclass
import enum
from typing import Any

class SyscallType(enum.Enum):
    OBSERVE = "OBSERVE"
    MEASURE = "MEASURE"
    VERIFY = "VERIFY"
    PERSIST = "PERSIST"
    SEARCH = "SEARCH"
    COMPILE = "COMPILE"
    EXECUTE = "EXECUTE"
    ROLLBACK = "ROLLBACK"
    AUDIT = "AUDIT"
    LEARN = "LEARN"

@dataclass
class SyscallRequest:
    syscall: SyscallType
    caller_pid: int
    payload: dict[str, Any]

@dataclass
class SyscallResponse:
    success: bool
    data: dict[str, Any]
    error: str = ""
