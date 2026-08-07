# C5-REAL EXERGY CERTIFIED
"""
CAM-5.0 Effect Programs & Family Capabilities.
"""

from dataclasses import dataclass, field
from typing import Any
from cortex.aem.isa import InstructionFamily

@dataclass(frozen=True)
class AlgebraicEffect:
    family: InstructionFamily
    target: str = ""

@dataclass
class CapabilitySet:
    allowed_families: set[InstructionFamily] = field(default_factory=set)

    def is_authorized(self, effect: AlgebraicEffect) -> bool:
        return effect.family in self.allowed_families

@dataclass
class EffectProgram:
    operations: list[tuple[InstructionFamily, dict[str, Any]]] = field(default_factory=list)
