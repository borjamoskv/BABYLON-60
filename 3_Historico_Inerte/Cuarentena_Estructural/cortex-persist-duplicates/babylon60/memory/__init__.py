# [C5-REAL] Exergy-Maximized
"""
Cognitive Memory Module.

Tripartite Memory Architecture (KETER-∞ Frontera 2):
    L1: WorkingMemoryL1  - Token-budgeted sliding window
    L2: VectorStoreL2    - Qdrant-backed semantic recall
    L3: EventLedgerL3    - SQLite WAL immutable event log

Orchestrator: CortexMemoryManager wires L1 → L2 → L3.

Uses __getattr__ lazy loading to avoid pulling in 18 submodules
eagerly on package import (PEP 562).

Usage::

    from babylon60.memory import CortexMemoryManager, WorkingMemoryL1

"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babylon60.memory.consolidation import SilentEngram, SystemsConsolidator
    from babylon60.memory.drift import DriftMonitor, DriftSignature
    from babylon60.memory.encoder import AsyncEncoder
    from babylon60.memory.engrams import CortexSemanticEngram
    from babylon60.memory.frequency import (
        BIFTRouter,
        ContinuousMemorySystem,
        MemoryFrequency,
        RetrievalBand,
    )
    from babylon60.memory.homeostasis import DynamicSynapseUpdate, EntropyPruner
    from babylon60.memory.ledger import EventLedgerL3
    from babylon60.memory.manager import CortexMemoryManager
    from babylon60.memory.metamemory import (
        MemoryCard,
        MetacognitiveJudge,
        MetaJudgment,
        MetamemoryIndex,
        MetamemoryMonitor,
        MetamemoryStats,
        RetrievalOutcome,
        Verdict,
        build_memory_card,
    )
    from babylon60.memory.models import EpisodicSnapshot, MemoryEntry, MemoryEvent
    from babylon60.memory.navigator import (
        ClusterInfo,
        KnowledgeMap,
        NavigationState,
        SemanticNavigator,
        SemanticPath,
    )
    from babylon60.memory.pipeline import NeuromorphicPipeline, QueryResult, StoreResult
    from babylon60.memory.resonance import AdaptiveResonanceGate
    from babylon60.memory.sleep import SleepCycleReport, SleepOrchestrator
    from babylon60.memory.sparse import MushroomBodyEncoder
    from babylon60.memory.sqlite_vec_store import SovereignVectorStoreL2 as VectorStoreL2
    from babylon60.memory.temporal_health import (
        HealthReport,
        SchedulerConfig,
        TemporalHealthScheduler,
    )
    from babylon60.memory.void_detector import (
        EpistemicAnalysis,
        EpistemicState,
        EpistemicVoidDetector,
    )
    from babylon60.memory.working import WorkingMemoryL1

__all__ = [  # type: ignore[reportUnsupportedDunderAll]
    "AdaptiveResonanceGate",
    "AsyncEncoder",
    "BIFTRouter",
    "ClusterInfo",
    "ContinuousMemorySystem",
    "CortexMemoryManager",
    "CortexSemanticEngram",
    "DriftMonitor",
    "DriftSignature",
    "DynamicSynapseUpdate",
    "EntropyPruner",
    "EpisodicSnapshot",
    "EpistemicAnalysis",
    "EpistemicState",
    "EpistemicVoidDetector",
    "EventLedgerL3",
    "HealthReport",
    "KnowledgeMap",
    "MemoryCard",
    "MemoryEntry",
    "MemoryEvent",
    "MemoryFrequency",
    "MetaJudgment",
    "MetacognitiveJudge",
    "MetamemoryIndex",
    "MetamemoryMonitor",
    "MetamemoryStats",
    "MushroomBodyEncoder",
    "NavigationState",
    "NeuromorphicPipeline",
    "QueryResult",
    "RetrievalBand",
    "RetrievalOutcome",
    "SchedulerConfig",
    "SemanticNavigator",
    "SemanticPath",
    "SilentEngram",
    "SleepCycleReport",
    "SleepOrchestrator",
    "StoreResult",
    "SystemsConsolidator",
    "TemporalHealthScheduler",
    "VectorStoreL2",
    "Verdict",
    "WorkingMemoryL1",
    "build_memory_card",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # consolidation
    "SilentEngram": ("babylon60.memory.consolidation", "SilentEngram"),
    "SystemsConsolidator": ("babylon60.memory.consolidation", "SystemsConsolidator"),
    # drift
    "DriftMonitor": ("babylon60.memory.drift", "DriftMonitor"),
    "DriftSignature": ("babylon60.memory.drift", "DriftSignature"),
    # encoder
    "AsyncEncoder": ("babylon60.memory.encoder", "AsyncEncoder"),
    # engrams
    "CortexSemanticEngram": ("babylon60.memory.engrams", "CortexSemanticEngram"),
    # frequency
    "BIFTRouter": ("babylon60.memory.frequency", "BIFTRouter"),
    "ContinuousMemorySystem": ("babylon60.memory.frequency", "ContinuousMemorySystem"),
    "MemoryFrequency": ("babylon60.memory.frequency", "MemoryFrequency"),
    "RetrievalBand": ("babylon60.memory.frequency", "RetrievalBand"),
    # homeostasis
    "DynamicSynapseUpdate": ("babylon60.memory.homeostasis", "DynamicSynapseUpdate"),
    "EntropyPruner": ("babylon60.memory.homeostasis", "EntropyPruner"),
    # ledger
    "EventLedgerL3": ("babylon60.memory.ledger", "EventLedgerL3"),
    # manager
    "CortexMemoryManager": ("babylon60.memory.manager", "CortexMemoryManager"),
    # metamemory
    "MemoryCard": ("babylon60.memory.metamemory", "MemoryCard"),
    "MetacognitiveJudge": ("babylon60.memory.metamemory", "MetacognitiveJudge"),
    "MetaJudgment": ("babylon60.memory.metamemory", "MetaJudgment"),
    "MetamemoryIndex": ("babylon60.memory.metamemory", "MetamemoryIndex"),
    "MetamemoryMonitor": ("babylon60.memory.metamemory", "MetamemoryMonitor"),
    "MetamemoryStats": ("babylon60.memory.metamemory", "MetamemoryStats"),
    "RetrievalOutcome": ("babylon60.memory.metamemory", "RetrievalOutcome"),
    "Verdict": ("babylon60.memory.metamemory", "Verdict"),
    "build_memory_card": ("babylon60.memory.metamemory", "build_memory_card"),
    # models
    "EpisodicSnapshot": ("babylon60.memory.models", "EpisodicSnapshot"),
    "MemoryEntry": ("babylon60.memory.models", "MemoryEntry"),
    "MemoryEvent": ("babylon60.memory.models", "MemoryEvent"),
    # navigator
    "ClusterInfo": ("babylon60.memory.navigator", "ClusterInfo"),
    "KnowledgeMap": ("babylon60.memory.navigator", "KnowledgeMap"),
    "NavigationState": ("babylon60.memory.navigator", "NavigationState"),
    "SemanticNavigator": ("babylon60.memory.navigator", "SemanticNavigator"),
    "SemanticPath": ("babylon60.memory.navigator", "SemanticPath"),
    # pipeline
    "NeuromorphicPipeline": ("babylon60.memory.pipeline", "NeuromorphicPipeline"),
    "QueryResult": ("babylon60.memory.pipeline", "QueryResult"),
    "StoreResult": ("babylon60.memory.pipeline", "StoreResult"),
    # resonance
    "AdaptiveResonanceGate": ("babylon60.memory.resonance", "AdaptiveResonanceGate"),
    # sleep
    "SleepCycleReport": ("babylon60.memory.sleep", "SleepCycleReport"),
    "SleepOrchestrator": ("babylon60.memory.sleep", "SleepOrchestrator"),
    # sparse
    "MushroomBodyEncoder": ("babylon60.memory.sparse", "MushroomBodyEncoder"),
    # temporal_health
    "HealthReport": ("babylon60.memory.temporal_health", "HealthReport"),
    "SchedulerConfig": ("babylon60.memory.temporal_health", "SchedulerConfig"),
    "TemporalHealthScheduler": ("babylon60.memory.temporal_health", "TemporalHealthScheduler"),
    # void_detector
    "EpistemicAnalysis": ("babylon60.memory.void_detector", "EpistemicAnalysis"),
    "EpistemicState": ("babylon60.memory.void_detector", "EpistemicState"),
    "EpistemicVoidDetector": ("babylon60.memory.void_detector", "EpistemicVoidDetector"),
    # working
    "WorkingMemoryL1": ("babylon60.memory.working", "WorkingMemoryL1"),
}


def __getattr__(name: str) -> object:
    """Lazy-load memory symbols on first access (PEP 562)."""
    if name == "VectorStoreL2":
        # Special case: VectorStoreL2 has a fallback chain
        try:
            from babylon60.memory.sqlite_vec_store import SovereignVectorStoreL2

            val = SovereignVectorStoreL2
        except ImportError:
            # cortex.memory.vector_store was removed; no further fallback
            val = None  # type: ignore[assignment]
        globals()["VectorStoreL2"] = val
        return val

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'cortex.memory' has no attribute {name!r}")
