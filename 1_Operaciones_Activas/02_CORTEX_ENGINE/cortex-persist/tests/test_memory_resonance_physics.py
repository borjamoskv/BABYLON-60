# [C5-REAL] Exergy-Maximized
import pytest
from typing import Any
from babylon60.memory.engrams import CortexSemanticEngram
from babylon60.memory.resonance import AdaptiveResonanceGate


class DummyVectorStore:
    def __init__(self):
        self.store = {}

    async def upsert(self, engram: CortexSemanticEngram):
        self.store[engram.id] = engram

    async def search_similar(self, embedding, tenant_id, limit):
        return list(self.store.values())


@pytest.mark.asyncio
async def test_adaptive_resonance_gate_collision_blocks_candidate():
    vs = DummyVectorStore()
    gate = AdaptiveResonanceGate(vector_store=vs, rho=0.7)

    # 1. Insertar vecino fuerte en el store
    vecino = CortexSemanticEngram(
        id="strong_neighbor",
        tenant_id="test",
        project_id="test",
        content="El Sol es una estrella",
        embedding=[0.0, 0.0],
        timestamp=1000.0,
        metadata={"confidence_score": 0.9},
        cognitive_layer="semantic",
    )
    await vs.upsert(vecino)

    # 2. Candidato débil que contradice al vecino
    candidato = CortexSemanticEngram(
        id="weak_candidate",
        tenant_id="test",
        project_id="test",
        content="El Sol es un planeta",
        embedding=[0.1, 0.1],
        timestamp=1001.0,
        metadata={"confidence_score": 0.2, "contradicts": "strong_neighbor"},
        cognitive_layer="semantic",
    )

    # Evaluar en el gate
    status, engram = await gate.gate(candidate=candidato)

    # Debe ser bloqueado por la colisión física contra el vecino fuerte
    assert status == "blocked"
    assert engram.id == "weak_candidate"
    assert "weak_candidate" not in vs.store


@pytest.mark.asyncio
async def test_adaptive_resonance_gate_collision_collapses_neighbor():
    vs = DummyVectorStore()
    gate = AdaptiveResonanceGate(vector_store=vs, rho=0.7)

    # 1. Insertar vecino débil en el store
    vecino = CortexSemanticEngram(
        id="weak_neighbor",
        tenant_id="test",
        project_id="test",
        content="El Sol es un planeta",
        embedding=[0.0, 0.0],
        timestamp=1000.0,
        metadata={"confidence_score": 0.2},
        cognitive_layer="semantic",
    )
    await vs.upsert(vecino)

    # 2. Candidato fuerte que contradice al vecino
    candidato = CortexSemanticEngram(
        id="strong_candidate",
        tenant_id="test",
        project_id="test",
        content="El Sol es una estrella",
        embedding=[0.1, 0.1],
        timestamp=1001.0,
        metadata={"confidence_score": 0.9, "contradicts": "weak_neighbor"},
        cognitive_layer="semantic",
    )

    # Evaluar en el gate
    status, engram = await gate.gate(candidate=candidato)

    # Debe ser insertado (reset) porque es fuerte
    assert status == "reset"
    assert engram.id == "strong_candidate"
    assert "strong_candidate" in vs.store

    # El vecino débil en el store debe haber colapsado (energía = 0.0 y estado contradictorio)
    collapsed_neighbor = vs.store["weak_neighbor"]
    assert collapsed_neighbor.energy_level == 0.0
    assert collapsed_neighbor.metadata.get("status") == "contradicted"
