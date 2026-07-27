import logging
import uuid
import math
from typing import List, Dict

class BeliefParticle:
    def __init__(self, key: str, confidence: float, coordinates: List[float], discard_keys: List[str]):
        self.id = str(uuid.uuid4())
        self.key = key
        # La masa es proporcional a la confianza epistémica
        self.mass = max(0.01, confidence)
        self.position = list(coordinates)
        self.velocity = [0.0] * len(coordinates)
        self.discard_keys = discard_keys
        self.active = True

    def apply_impulse(self, impulse: List[float]):
        # F = m * a => delta_v = impulse / mass
        for i in range(len(self.position)):
            self.velocity[i] += impulse[i] / self.mass

    def update(self, dt: float, decay_rate: float):
        if not self.active:
            return
        # Actualización de posición
        for i in range(len(self.position)):
            self.position[i] += self.velocity[i] * dt
            # Fricción del espacio semántico (fading/decay)
            self.velocity[i] *= (1.0 - decay_rate * dt)

        # El decaimiento natural reduce la masa (confianza)
        self.mass = max(0.01, self.mass - decay_rate * 0.05 * dt)

def compute_semantic_distance(p1: BeliefParticle, p2: BeliefParticle) -> float:
    squared_sum = sum((x1 - x2) ** 2 for x1, x2 in zip(p1.position, p2.position))
    return math.sqrt(squared_sum)

class BeliefPhysicsEngine:
    def __init__(self, decay_rate: float = 0.1):
        self.particles: Dict[str, BeliefParticle] = {}
        self.decay_rate = decay_rate

    def add_particle(self, particle: BeliefParticle):
        self.particles[particle.key] = particle

    def step(self, dt: float):
        keys = list(self.particles.keys())
        # Resolver colisiones (contradicciones directas)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                p1 = self.particles[keys[i]]
                p2 = self.particles[keys[j]]

                if not (p1.active and p2.active):
                    continue

                # Si una descarta a la otra o son mutuamente contradictorias
                if p2.key in p1.discard_keys or p1.key in p2.discard_keys:
                    dist = compute_semantic_distance(p1, p2)
                    # Umbral de colisión semántica (física de impacto)
                    collision_threshold = 1.0
                    if dist < collision_threshold:
                        # Colisión detectada
                        # Dirección del impacto (vector de p1 a p2)
                        direction = [x2 - x1 for x1, x2 in zip(p1.position, p2.position)]
                        norm = math.sqrt(sum(x ** 2 for x in direction))
                        if norm == 0:
                            norm = 0.001
                            direction = [0.001] * len(direction)
                        direction = [x / norm for x in direction]

                        # Calcular impulso relativo de impacto (física de colisión)
                        # Aquí, el conflicto semántico reduce la masa (confianza) del nodo más débil
                        mass_ratio = p1.mass / (p1.mass + p2.mass)

                        # Impulso de repulsión semántica
                        force_magnitude = (collision_threshold - dist) * 2.0
                        impulse_p1 = [-x * force_magnitude * (1.0 - mass_ratio) for x in direction]
                        impulse_p2 = [x * force_magnitude * mass_ratio for x in direction]

                        p1.apply_impulse(impulse_p1)
                        p2.apply_impulse(impulse_p2)

                        # Reducción de confianza (daño de colisión)
                        damage = force_magnitude * 0.1
                        p1.mass = max(0.01, p1.mass - damage * (1.0 - mass_ratio))
                        p2.mass = max(0.01, p2.mass - damage * mass_ratio)

                        # Si la confianza (masa) cae por debajo de un umbral, la creencia colapsa
                        if p1.mass <= 0.05:
                            p1.active = False
                        if p2.mass <= 0.05:
                            p2.active = False

        # Actualizar posiciones y velocidades
        for p in self.particles.values():
            p.update(dt, self.decay_rate)

if __name__ == "__main__":
    engine = BeliefPhysicsEngine()

    # Creencia A: "El Sol es una estrella" (Confianza alta, coordenadas [0.0, 0.0])
    p1 = BeliefParticle("SunIsStar", 0.9, [0.0, 0.0], ["SunIsPlanet"])
    # Creencia B: "El Sol es un planeta" (Confianza media, moviéndose hacia A)
    p2 = BeliefParticle("SunIsPlanet", 0.4, [0.5, 0.5], ["SunIsStar"])
    # Añadir velocidad inicial que fuerce la colisión
    p2.velocity = [-0.1, -0.1]

    engine.add_particle(p1)
    engine.add_particle(p2)

    logging.getLogger(__name__).info("--- INICIO DE SIMULACIÓN DE FÍSICA DE CREENCIAS ---")
    for step_idx in range(5):
        engine.step(0.5)
        logging.getLogger(__name__).info(f"Paso {step_idx + 1}:")
        logging.getLogger(__name__).info(f"  SunIsStar -> Posición: {p1.position}, Masa (Confianza): {p1.mass:.4f}, Activa: {p1.active}")
        logging.getLogger(__name__).info(f"  SunIsPlanet -> Posición: {p2.position}, Masa (Confianza): {p2.mass:.4f}, Activa: {p2.active}")
