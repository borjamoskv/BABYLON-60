# C5-REAL EXERGY CERTIFIED
"""
CAM-5.0 (C5 Abstract Effect Observation Machine) Package.
"""

from cortex.aem.isa import Handle, InstructionFamily, ExecutionError, CapabilityError, IntegrityError, ImplementationError
from cortex.aem.effects import AlgebraicEffect, EffectProgram, CapabilitySet
from cortex.aem.space import ObjectSpace
from cortex.aem.machine import AbstractEffectMachine

__all__ = [
    "Handle",
    "InstructionFamily",
    "ExecutionError",
    "CapabilityError",
    "IntegrityError",
    "ImplementationError",
    "AlgebraicEffect",
    "EffectProgram",
    "CapabilitySet",
    "ObjectSpace",
    "AbstractEffectMachine",
]
