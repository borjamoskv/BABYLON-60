"""
CAM-3.0 (C5 Abstract Effect Machine) Package.
"""

from cortex.aem.isa import Handle, InstructionType, ExecutionError, CapabilityError, IntegrityError, ImplementationError
from cortex.aem.effects import AlgebraicEffect, EffectCategory
from cortex.aem.space import ObjectSpace
from cortex.aem.machine import AbstractEffectMachine

__all__ = [
    "Handle",
    "InstructionType",
    "ExecutionError",
    "CapabilityError",
    "IntegrityError",
    "ImplementationError",
    "AlgebraicEffect",
    "EffectCategory",
    "ObjectSpace",
    "AbstractEffectMachine",
]
