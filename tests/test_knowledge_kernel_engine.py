# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Test Suite for Knowledge Kernel Engine (Omega 1 - Omega 12).
"""
import pytest
from cortex.engines.knowledge_kernel_engine import (
    KnowledgeKernelEngine,
    CompressionPyramid,
)


def test_knowledge_kernel_event_sourcing():
    engine = KnowledgeKernelEngine()
    evt = engine.append_event(
        actor="Paul Graham",
        action="published",
        object_id="Essay:LLM_Memory",
        confidence=0.95,
        source="https://paulgraham.com/llm_memory.html",
    )
    assert evt.event_id is not None
    assert len(evt.event_id) == 64  # SHA3-256 length
    assert evt.actor == "Paul Graham"
    assert evt.confidence == 0.95


def test_knowledge_kernel_graph_and_claims():
    engine = KnowledgeKernelEngine()
    n1 = engine.register_node("node:pg", "Person", [0.1, 0.2, 0.3], {"name": "Paul Graham"})
    n2 = engine.register_node("node:llm", "Concept", [0.4, 0.5, 0.6], {"name": "LLM Memory"})

    edge = engine.add_edge(n1.id, n2.id, "mentions", 0.9)
    assert edge.source == "node:pg"
    assert edge.target == "node:llm"

    claim = engine.register_claim(
        proposition="Persistent memory is required for autonomous agentic convergence",
        source="arXiv:2026.12345",
        evidence=["paper:1", "repo:2"],
        counter_evidence=["blog:3"],
    )
    assert claim.claim_id is not None
    assert claim.confidence == pytest.approx(2.0 / 3.0)


def test_compression_pyramid():
    pyramid = CompressionPyramid.compute_exergy_density(100000)
    assert pyramid["articles"] == 100000
    assert pyramid["ideas"] == 20000
    assert pyramid["concepts"] == 4000
    assert pyramid["patterns"] == 900
    assert pyramid["paradigms"] == 120
    assert pyramid["structural_shifts"] == 12
    assert pyramid["meta_trends"] == 3
    assert pyramid["signal"] == 1


def test_counterfactual_simulation():
    engine = KnowledgeKernelEngine()
    n1 = engine.register_node("node:a", "Company", [0.1], {})
    n2 = engine.register_node("node:b", "Model", [0.2], {})
    engine.add_edge("node:a", "node:b", "releases", 0.99)

    sim = engine.simulate_counterfactual("node:a", {"status": "released_model_x"})
    assert sim["target"] == "node:a"
    assert sim["impacted_edges_count"] == 1
    assert "node:b" in sim["affected_neighbors"]
