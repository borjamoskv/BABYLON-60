# C5-REAL EXERGY CERTIFIED
"""
CAM-5.0 Minimal Instruction Families & Structural Error Model.
Instruction Families: READ, WRITE, CONTROL.
"""

from dataclasses import dataclass, field
import enum
import uuid

class ExecutionError(Exception):
    """Raised when an instruction execution fails due to invalid parameters or runtime stack issues."""

class CapabilityError(Exception):
    """Raised when an agent attempts an instruction requiring an unauthorized algebraic effect."""

class IntegrityError(Exception):
    """Raised when an ASSERT predicate evaluation fails in CONTROL family."""

class ImplementationError(Exception):
    """Raised when an underlying backend storage engine or driver internal fails."""

class InstructionFamily(enum.Enum):
    READ = "READ"
    WRITE = "WRITE"
    CONTROL = "CONTROL"

@dataclass(frozen=True)
class Handle:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
