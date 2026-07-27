# [C5-REAL] Exergy-Maximized
from babylon60.engine.flow.causality_models import Claim, Evidence, EpistemicStatus
from babylon60.engine.causal.epistemic_physics import EpistemicPhysicsArbiter


def test_epistemic_physics_collision_collapse():
    # Inicializar resolvedor
    arbiter = EpistemicPhysicsArbiter(decay_rate=0.01, collision_threshold=1.5)

    # Evidencia A (Fuerte)
    ev_a = Evidence(source="oracle", confidence=0.9, metadata={"embedding": [0.0, 0.0]})
    claim_a = Claim(id="claim_strong", statement="Sun is a star", evidence_list=[ev_a])

    # Evidencia B (Débil y contradictoria)
    ev_b = Evidence(
        source="unverified",
        confidence=0.3,
        metadata={"embedding": [0.2, 0.2], "contradicts": "claim_strong"},
    )
    claim_b = Claim(id="claim_weak", statement="Sun is a planet", evidence_list=[ev_b])

    # Ejecutar resolución física
    traces = arbiter.resolve_collisions([claim_a, claim_b])

    # Encontrar traces correspondientes
    trace_a = next(t for t in traces if "claim_strong" in t.trace_steps[0])
    trace_b = next(t for t in traces if "claim_weak" in t.trace_steps[0])

    # El claim A fuerte debe sobrevivir
    assert trace_a.verdict in [EpistemicStatus.VERIFIED, EpistemicStatus.SUPPORTED]
    assert trace_a.truth_score.value > 0.5

    # El claim B débil debe colapsar debido a la colisión de fuerza desigual
    assert trace_b.verdict == EpistemicStatus.CONTRADICTED
    assert trace_b.truth_score.value == 0.0
