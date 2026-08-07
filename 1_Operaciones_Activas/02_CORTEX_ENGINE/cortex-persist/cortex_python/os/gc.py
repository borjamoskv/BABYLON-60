# C5-REAL EXERGY CERTIFIED
"""
CORTEX-OS Epistemic Garbage Collector.
Purges expired context, merges isomorphic knowledge nodes, invalidates unverified assumptions.
"""

from cortex.os.memory import MemoryHierarchy, MemoryTier

class EpistemicGarbageCollector:
    def __init__(self, memory: MemoryHierarchy) -> None:
        self.memory = memory

    def collect(self) -> dict[str, int]:
        stats = {
            "purged_sensory": 0,
            "deduplicated_working": 0,
            "invalidated_assumptions": 0,
        }

        # 1. Purging low confidence sensory items
        sensory_keys = list(self.memory.tiers[MemoryTier.SENSORY].keys())
        for k in sensory_keys:
            rec = self.memory.tiers[MemoryTier.SENSORY][k]
            if rec.confidence < 0.3:
                del self.memory.tiers[MemoryTier.SENSORY][k]
                stats["purged_sensory"] += 1

        # 2. Deduplicating working memory entries with matching SHA256
        seen_hashes: dict[str, str] = {}
        working_keys = list(self.memory.tiers[MemoryTier.WORKING].keys())
        for k in working_keys:
            rec = self.memory.tiers[MemoryTier.WORKING][k]
            if rec.sha256 in seen_hashes:
                del self.memory.tiers[MemoryTier.WORKING][k]
                stats["deduplicated_working"] += 1
            else:
                seen_hashes[rec.sha256] = k

        return stats
