"""
CAM-3.0 Micro-ISA & Structural Error Model.
"""

from dataclasses import dataclass, field
import enum
import uuid


class ExecutionError(Exception):
    """Raised when an instruction execution fails due to invalid parameters or runtime stack issues."""


class CapabilityError(Exception):
    """Raised when an agent attempts an instruction requiring an unauthorized algebraic effect."""


class IntegrityError(Exception):
    """Raised when an ASSERT predicate evaluation fails or hash chain integrity is violated."""


class ImplementationError(Exception):
    """Raised when an underlying backend storage engine or driver internal fails."""


class InstructionType(enum.Enum):
    ALLOC = "ALLOC"
    LOAD = "LOAD"
    STORE = "STORE"
    LINK = "LINK"
    UNLINK = "UNLINK"
    CALL = "CALL"
    ASSERT = "ASSERT"
    COMMIT = "COMMIT"
    ABORT = "ABORT"


@dataclass(frozen=True)
class Handle:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
