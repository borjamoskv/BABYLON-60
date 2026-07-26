# C5-REAL EXERGY CERTIFIED
"""
00_PROMPT_EXERGY.py (C5-REAL Certified)
---------------------------------------
Calculador estático de disipación cuadrática en la KV-Cache (O(N^2)).
Audita y restringe el tamaño del prompt inyectado para prevenir la anergía atencional.

Invariantes: Ω21 (Límite de Landauer), Ω174 (Compresión de Kolmogorov)"""
import sys
import math
from typing import Dict, Tuple

class PromptExergyEvaluator:
    """Evalúa la pérdida de exergía por andamiaje redundante en el contexto."""
    __slots__ = ("max_allowed_tokens", "atten_sink_threshold")

    def __init__(self, max_allowed_tokens: int = 200):
        self.max_allowed_tokens = max_allowed_tokens
        self.atten_sink_threshold = 0.80

    def calculate_dissipation(self, prompt_text: str) -> Tuple[float, float]:
        """
        Calcula la exergía del prompt y la disipación cuadrática teórica de atención.
        Fórmula de Disipación: D = (Tokens^2) * c
        """
        tokens = prompt_text.split()
        token_count = len(tokens)

        if token_count == 0:
            return 1.0, 0.0

        # Costo de disipación cuadrática O(N^2) normalizado
        quadratic_dissipation = float(token_count ** 2) / (self.max_allowed_tokens ** 2)

        # Métrica de eficiencia exergética basada en el límite de des-andamiaje
        exergy_score = 1.0 - (quadratic_dissipation if token_count > self.max_allowed_tokens else (quadratic_dissipation * 0.1))
        exergy_score = max(0.0, min(1.0, exergy_score))

        return exergy_score, quadratic_dissipation

    def enforce_boundary(self, prompt_text: str) -> bool:
        """Detiene el flujo de datos si el andamiaje del prompt induce muerte térmica por tokens."""
        exergy, dissipation = self.calculate_dissipation(prompt_text)

        if exergy < self.atten_sink_threshold:
            sys.stderr.write(
                f"\n[💥 ANERGÍA ATENCIONAL - Ω149] Prompt sobre-andamiado fuera de límites.\n"
                f"-> Eficiencia de Prompt: {exergy:.4f} (Mínimo: {self.atten_sink_threshold})\n"
                f"-> Disipación Cuadrática KV-Cache: {dissipation:.4f}\n"
                f"-> Bloqueando inyección de contexto disipativo.\n"
            )
            return False

        print(f"[✅ C5-REAL] Prompt óptimo. Exergía de atención: {exergy:.4f} | Disipación O(N²): {dissipation:.4f}")
        return True

if __name__ == "__main__":
    evaluator = PromptExergyEvaluator()

    # Simulación de un system prompt verboso del Green Theater (~250 tokens aproximados)
    prompt_contaminado = " ".join(["regla_redundante_de_control"] * 250)
    evaluator.enforce_boundary(prompt_contaminado)
