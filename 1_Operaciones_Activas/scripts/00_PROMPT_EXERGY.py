# C5-REAL EXERGY CERTIFIED
"""
00_PROMPT_EXERGY.py (C5-REAL Certified)
---------------------------------------
Calculador estático de disipación cuadrática en la KV-Cache (O(N^2)).
Audita y restringe el tamaño del prompt inyectado para prevenir la anergía atencional.

Invariantes: Ω21 (Límite de Landauer), Ω174 (Compresión de Kolmogorov)"""
import sys
import math
import zlib
from typing import Dict, Tuple

class PromptExergyEvaluator:
    """Evalúa la pérdida de exergía por andamiaje redundante en el contexto."""
    __slots__ = ("max_allowed_tokens", "atten_sink_threshold")

    def __init__(self, max_allowed_tokens: int = 200):
        self.max_allowed_tokens = max_allowed_tokens
        self.atten_sink_threshold = 0.80

    def calculate_dissipation(self, prompt_text: str) -> Tuple[float, float, float]:
        """
        Calcula la exergía del prompt usando Compresión de Kolmogorov (zlib).
        Penaliza severamente el boilerplate redundante (Green Theater) y calcula
        la disipación cuadrática en base a los tokens equivalentes puros.
        """
        raw_bytes = prompt_text.encode('utf-8')
        raw_len = len(raw_bytes)

        if raw_len == 0:
            return 1.0, 0.0, 1.0

        compressed_len = len(zlib.compress(raw_bytes))
        kolmogorov_ratio = compressed_len / float(raw_len)  # ~1.0 = alta entropía (bueno), ~0.1 = boilerplate redundante (malo)

        # Aproximación de tokens físicos
        token_count = raw_len / 4.0

        # Penalización de Anergía: los tokens redundantes cuestan más cuadráticamente
        effective_tokens = token_count * (1.0 + (1.0 - kolmogorov_ratio))

        # Costo de disipación cuadrática O(N^2) normalizado
        quadratic_dissipation = (effective_tokens ** 2) / (self.max_allowed_tokens ** 2)

        # Métrica de eficiencia exergética
        exergy_score = 1.0 - (quadratic_dissipation if effective_tokens > self.max_allowed_tokens else (quadratic_dissipation * 0.1))
        exergy_score = max(0.0, min(1.0, exergy_score))

        return exergy_score, quadratic_dissipation, kolmogorov_ratio

    def enforce_boundary(self, prompt_text: str) -> bool:
        """Detiene el flujo de datos si el andamiaje del prompt induce muerte térmica por tokens."""
        exergy, dissipation, k_ratio = self.calculate_dissipation(prompt_text)

        if exergy < self.atten_sink_threshold:
            sys.stderr.write(
                f"\n[💥 ANERGÍA ATENCIONAL - Ω149/Ω174] Prompt sobre-andamiado fuera de límites.\n"
                f"-> Eficiencia de Prompt: {exergy:.4f} (Mínimo: {self.atten_sink_threshold})\n"
                f"-> Ratio Kolmogorov (Compresión): {k_ratio:.4f} (Alta redundancia penalizada)\n"
                f"-> Disipación Cuadrática KV-Cache: {dissipation:.4f}\n"
                f"-> Bloqueando inyección de contexto disipativo.\n"
            )
            return False

        print(f"[✅ C5-REAL] Prompt óptimo. Exergía: {exergy:.4f} | Disipación O(N²): {dissipation:.4f} | Kolmogorov Ratio: {k_ratio:.4f}")
        return True

if __name__ == "__main__":
    evaluator = PromptExergyEvaluator()

    # Simulación de un system prompt verboso del Green Theater (~250 tokens aproximados)
    prompt_contaminado = " ".join(["regla_redundante_de_control"] * 250)
    evaluator.enforce_boundary(prompt_contaminado)
