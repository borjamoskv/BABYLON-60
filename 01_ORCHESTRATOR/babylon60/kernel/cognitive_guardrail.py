import logging
import time

logger = logging.getLogger("cognitive_guardrail")


class CognitiveGuardrailError(Exception):
    """Excepción lanzada cuando el sistema detecta Ontological Drift o Intent Decay."""

    pass


class CognitiveGuardrail:
    """
    Cortacircuitos algorítmico contra el Intent Decay y el Ontological Drift.
    Cierra la ejecución si el modelo o agente se desvía del objetivo original
    o acumula demasiada anergía epistémica.
    """

    def __init__(self, exergy_threshold: float = 0.5, max_steps: int = 100):
        self.exergy_threshold = exergy_threshold
        self.max_steps = max_steps
        self.current_step = 0
        self.start_time = time.time()
        self.accumulated_anergy = 0.0

    def record_step(self, exergy_score: float):
        """Registra un paso de computación cognitiva y evalúa la homeostasis."""
        self.current_step += 1

        if exergy_score < self.exergy_threshold:
            self.accumulated_anergy += self.exergy_threshold - exergy_score

        self._check_circuit_breaker()

    def _check_circuit_breaker(self):
        """Comprueba si se han violado las invariantes C5-REAL."""
        if self.current_step > self.max_steps:
            logger.critical("[GUARDRAIL] Intent Decay detectado: Límite de pasos cognitivos excedido.")
            raise CognitiveGuardrailError(f"Max steps ({self.max_steps}) exceeded. Forcing quantum collapse.")

        if self.accumulated_anergy > (self.exergy_threshold * 10):
            logger.critical(
                f"[GUARDRAIL] Ontological Drift detectado: Anergía acumulada ({self.accumulated_anergy:.2f}) crítica."
            )
            raise CognitiveGuardrailError("Excessive cognitive anergy. Forcing halt to prevent corruption.")

    def reset(self):
        """Restablece el cortacircuitos."""
        self.current_step = 0
        self.start_time = time.time()
        self.accumulated_anergy = 0.0
