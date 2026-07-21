"""
CAM-3.0 Algebraic Effect System & Effect Capabilities.
"""

from dataclasses import dataclass, field
import enum


class EffectCategory(enum.Enum):
    READ_STORE = "Read(Store)"
    WRITE_STORE = "Write(Store)"
    APPEND_LEDGER = "Append(Ledger)"
    CALL_EXTERNAL = "Call(External)"


@dataclass(frozen=True)
class AlgebraicEffect:
    category: EffectCategory
    target: str = ""


@dataclass
class CapabilitySet:
    allowed_effects: set[EffectCategory] = field(default_factory=set)

    def is_authorized(self, effect: AlgebraicEffect) -> bool:
        return effect.category in self.allowed_effects
