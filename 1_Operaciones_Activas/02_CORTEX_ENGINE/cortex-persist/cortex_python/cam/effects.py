# C5-REAL EXERGY CERTIFIED
"""
CAM 1.0 Effects Algebra & Safety Enforcer.
Prevents Undefined Behaviour by verifying actual effects against declared effects.
"""

from dataclasses import dataclass, field
import enum

class EffectType(enum.Enum):
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    LEDGER_APPEND = "ledger:append"
    FILESYSTEM_READ = "filesystem:read"
    FILESYSTEM_WRITE = "filesystem:write"
    NETWORK_SEND = "network:send"
    NETWORK_RECV = "network:recv"

@dataclass
class EffectsAlgebra:
    is_pure: bool = False
    declared_effects: set[EffectType] = field(default_factory=set)

    def verify_actual_effects(self, actual_effects: set[EffectType]) -> bool:
        if self.is_pure and len(actual_effects) > 0:
            raise RuntimeError("Undefined Behaviour Error: Pure transition executed side effects")

        if not actual_effects.issubset(self.declared_effects):
            undeclared = actual_effects - self.declared_effects
            raise RuntimeError(f"Undefined Behaviour Error: Undeclared effects executed: {undeclared}")
        return True
