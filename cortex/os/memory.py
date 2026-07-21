"""
CORTEX-OS Epistemic Memory Hierarchy.
5-Tier Memory Architecture: Sensory -> Working -> Verified -> Institutional -> ImmutableLedger.
"""

from dataclasses import dataclass, field
import enum
import hashlib
import time


class MemoryTier(enum.Enum):
    SENSORY = "SENSORY"
    WORKING = "WORKING"
    VERIFIED = "VERIFIED"
    INSTITUTIONAL = "INSTITUTIONAL"
    IMMUTABLE_LEDGER = "IMMUTABLE_LEDGER"


@dataclass
class MemoryRecord:
    key: str
    content: str
    tier: MemoryTier
    confidence: float
    timestamp: float = field(default_factory=time.time)
    sha256: str = ""

    def __post_init__(self) -> None:
        if not self.sha256:
            self.sha256 = hashlib.sha256(self.content.encode("utf-8")).hexdigest()


class MemoryHierarchy:
    def __init__(self) -> None:
        self.tiers: dict[MemoryTier, dict[str, MemoryRecord]] = {
            tier: {} for tier in MemoryTier
        }

    def store(
        self,
        key: str,
        content: str,
        tier: MemoryTier = MemoryTier.SENSORY,
        confidence: float = 0.5,
    ) -> MemoryRecord:
        record = MemoryRecord(
            key=key, content=content, tier=tier, confidence=confidence
        )
        self.tiers[tier][key] = record
        return record

    def promote(self, key: str, from_tier: MemoryTier, to_tier: MemoryTier) -> MemoryRecord:
        if key not in self.tiers[from_tier]:
            raise KeyError(f"Key '{key}' not found in tier {from_tier.value}")
        record = self.tiers[from_tier].pop(key)
        record.tier = to_tier
        self.tiers[to_tier][key] = record
        return record

    def get(self, key: str) -> MemoryRecord | None:
        for tier in reversed(list(MemoryTier)):
            if key in self.tiers[tier]:
                return self.tiers[tier][key]
        return None
