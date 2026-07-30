# [C5-REAL] Exergy-Maximized
import logging
import math
import zlib

from babylon60.crypto.hash_registry import cortex_hash
from babylon60.engine.flow.causality_models import (
    Claim,
    DecisionTrace,
    EpistemicStatus,
    TruthScore,
    UtilityScore,
)
from babylon60.extensions.security.utils import calculate_lexical_entropy

logger = logging.getLogger("babylon60.engine.causal.epistemic_physics")


class SemanticParticle:
    def __init__(self, claim: Claim):
        self.claim = claim

        # 1. Truth (T): Promedio de evidencias
        truth = 0.5
        if claim.evidence_list:
            truth = sum(e.confidence for e in claim.evidence_list) / len(claim.evidence_list)

        # 2. Shannon Entropy (H): Complejidad léxica
        self.shannon_h = calculate_lexical_entropy(claim.statement)

        # 3. Kolmogorov Complexity proxy (K): Ratio de compresión (gzip)
        raw_bytes = claim.statement.encode("utf-8")
        compressed = zlib.compress(raw_bytes)
        self.kolmogorov_k = len(compressed) / max(1, len(raw_bytes))

        # Modulación termodinámica suave para evitar inflación de masa en cadenas cortas
        h_mod = 1.0 + (self.shannon_h / 10.0)
        k_mod = min(1.2, max(0.5, self.kolmogorov_k))

        # Masa termodinámica: T * H_mod * K_mod
        self.mass = max(0.01, truth * h_mod * k_mod)

        # Determinar posición semántica (embedding). Intentar leer de metadatos o crear dummy bidimensional.
        self.position: list[float] | None = None

        # Buscar en metadatos de las evidencias
        for e in claim.evidence_list:
            if e.metadata and "embedding" in e.metadata and e.metadata["embedding"] is not None:
                self.position = list(e.metadata["embedding"])
                break

        # Si no hay, usar un hash reproducible para asignar coordenadas fijas bidimensionales
        if self.position is None:
            h = hash(claim.id)
            # Normalizar entre -1.0 y 1.0
            x = (h % 1000) / 500.0 - 1.0
            y = ((h // 1000) % 1000) / 500.0 - 1.0
            self.position = [x, y]

        # Garantizar que pyright sepa que position nunca es None a partir de este punto
        assert self.position is not None

        self.velocity: list[float] = [0.0] * len(self.position)
        self.active = True

    def apply_impulse(self, impulse: list[float]):
        assert self.position is not None
        for i in range(len(self.position)):
            self.velocity[i] += impulse[i] / self.mass

    def update(self, dt: float, decay_rate: float):
        if not self.active:
            return
        assert self.position is not None
        for i in range(len(self.position)):
            self.position[i] += self.velocity[i] * dt
            self.velocity[i] *= 1.0 - decay_rate * dt

        # Degradación temporal
        self.mass = max(0.01, self.mass - decay_rate * 0.02 * dt)


class EpistemicPhysicsArbiter:
    """
    Resolvedor de colisiones semánticas basado en la física de impulsos de Newton y Resonancia.
    Trata las contradicciones entre afirmaciones como colisiones físicas (Shannon + K + Resonance).
    """

    def __init__(self, decay_rate: float = 0.05, collision_threshold: float = 0.8):
        self.decay_rate = decay_rate
        self.collision_threshold = collision_threshold

    def _is_contradictory(self, p1: SemanticParticle, p2: SemanticParticle) -> bool:
        for e in p1.claim.evidence_list:
            if e.metadata and e.metadata.get("contradicts") == p2.claim.id:
                return True
        for e in p2.claim.evidence_list:
            if e.metadata and e.metadata.get("contradicts") == p1.claim.id:
                return True
        return False

    def _apply_collision(self, p1: SemanticParticle, p2: SemanticParticle):
        assert p1.position is not None and p2.position is not None
        # Distancia euclidiana en el espacio semántico
        squared_sum = sum((x1 - x2) ** 2 for x1, x2 in zip(p1.position, p2.position, strict=True))
        dist = math.sqrt(squared_sum)

        if dist < self.collision_threshold:
            # 4. Resonance (R): Fuerza inversa a la distancia
            resonance = max(0.0, 1.0 - (dist / self.collision_threshold))

            # Dirección de la colisión
            direction = [x2 - x1 for x1, x2 in zip(p1.position, p2.position, strict=True)]
            norm = math.sqrt(sum(x**2 for x in direction))
            if norm == 0:
                norm = 0.001
                direction = [0.001] * len(direction)
            direction = [x / norm for x in direction]

            # Conservación de momento con masa (T * H * K) proporcional
            total_mass = p1.mass + p2.mass
            mass_ratio = p1.mass / total_mass

            # La fuerza depende directamente de la Resonancia (R)
            force = resonance * self.collision_threshold * 3.0

            impulse_p1 = [-x * force * (1.0 - mass_ratio) for x in direction]
            impulse_p2 = [x * force * mass_ratio for x in direction]

            p1.apply_impulse(impulse_p1)
            p2.apply_impulse(impulse_p2)

            # Reducción de masa (daño por colisión termodinámica)
            p1.mass = max(0.01, p1.mass - force * 0.15 * (1.0 - mass_ratio))
            p2.mass = max(0.01, p2.mass - force * 0.15 * mass_ratio)

            if p1.mass <= 0.1:
                p1.active = False
            if p2.mass <= 0.1:
                p2.active = False

    def _simulate_step(self, particles: list[SemanticParticle], dt: float):
        for i in range(len(particles)):
            for j in range(i + 1, len(particles)):
                p1 = particles[i]
                p2 = particles[j]

                if not (p1.active and p2.active):
                    continue

                if self._is_contradictory(p1, p2):
                    self._apply_collision(p1, p2)

        # Paso de actualización física
        for p in particles:
            p.update(dt, self.decay_rate)

    def _generate_traces(self, particles: list[SemanticParticle]) -> list[DecisionTrace]:
        traces = []
        for p in particles:
            trace_steps = [
                f"INIT: Evaluating claim {p.claim.id} via EpistemicPhysicsArbiter",
                f"PHYS: Shannon Entropy (H) = {p.shannon_h:.4f}",
                f"PHYS: Kolmogorov proxy (K) = {p.kolmogorov_k:.4f}",
                f"PHYS: Final semantic mass (T*H*K) = {p.mass:.4f}",
                f"PHYS: Particle active status = {p.active}",
            ]

            if not p.active:
                verdict = EpistemicStatus.CONTRADICTED
                truth = 0.0
                trace_steps.append("DECISION: Claim collapsed due to thermodynamic collision.")
            else:
                truth = p.mass
                # Escalar umbrales debido al incremento de masa por K y H
                if truth >= 1.2:
                    verdict = EpistemicStatus.VERIFIED
                elif truth >= 0.5:
                    verdict = EpistemicStatus.SUPPORTED
                else:
                    verdict = EpistemicStatus.SPECULATIVE
                trace_steps.append(f"DECISION: Verdict set to {verdict.value}")

            raw_trace = "\n".join(trace_steps)
            trace_hash = cortex_hash(raw_trace.encode("utf-8"))

            traces.append(
                DecisionTrace(
                    verdict=verdict,
                    trace_steps=trace_steps,
                    trace_hash=trace_hash,
                    truth_score=TruthScore(value=truth),
                    utility_score=UtilityScore(value=0.8),
                )
            )
        return traces

    def resolve_collisions(self, claims: list[Claim]) -> list[DecisionTrace]:
        particles = [SemanticParticle(c) for c in claims]

        # Simular 3 pasos de integración de colisiones
        dt = 0.5
        for _ in range(3):
            self._simulate_step(particles, dt)

        # Generar DecisionTrace final
        return self._generate_traces(particles)
