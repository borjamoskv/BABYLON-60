# C5-REAL EXERGY CERTIFIED
"""
Verifies top-level export integrity of CORTEX package.
"""

from cortex import (
    QuadPillarKernel,
    SystemPillar,
    OrchestrationPillar,
    MemoryPillar,
    DeterminismPillar,
    CognitiveStateObserver,
    CertificateCategoryP,
    ThermodynamicEntropyEngine,
    audit_and_align_invariants,
    DeliverabilityValidator,
    UnifiedActiveInferenceEngine,
)

def test_cortex_top_level_exports() -> None:
    assert QuadPillarKernel is not None
    assert SystemPillar is not None
    assert OrchestrationPillar is not None
    assert MemoryPillar is not None
    assert DeterminismPillar is not None
    assert CognitiveStateObserver is not None
    assert CertificateCategoryP is not None
    assert ThermodynamicEntropyEngine is not None
    assert audit_and_align_invariants is not None
    assert DeliverabilityValidator is not None
    assert UnifiedActiveInferenceEngine is not None
