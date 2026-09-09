#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
endocrine.py - Cognitive Endocrine System & Affective State Modulation

Módulo materializado vía Autopoiesis (Sello L0).
Simula la neuromodulación de los agentes del enjambre mediante un sistema
endocrino virtual, ajustando temperaturas (Dopamina/Serotonina) y umbrales de
alerta (Cortisol/Adrenalina) dinámicamente según la fricción entrópica.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict
import logging

logger = logging.getLogger("BABYLON-60.ENDOCRINE")


class HormoneType(Enum):
    CORTISOL = auto()  # Estrés/Amenaza: Aumenta la rigidez (Temperatura baja, top_p restrictivo)
    DOPAMINE = auto()  # Recompensa/Búsqueda: Aumenta la creatividad y exploración (Temperatura alta)
    SEROTONIN = auto()  # Estabilización/Satisfacción: Equilibrio sistémico, detiene bucles infinitos
    ADRENALINE = auto()  # Emergencia: Fail-Stop inmediato, ejecución de instintos básicos (Reglas duras)


@dataclass
class EndocrineState:
    levels: Dict[HormoneType, float] = field(
        default_factory=lambda: {
            HormoneType.CORTISOL: 0.1,
            HormoneType.DOPAMINE: 0.5,
            HormoneType.SEROTONIN: 0.5,
            HormoneType.ADRENALINE: 0.0,
        }
    )

    def inject(self, hormone: HormoneType, amount: float) -> None:
        """Inyecta una hormona, saturando en 1.0 (Máximo) y decaindo las opuestas."""
        self.levels[hormone] = min(1.0, self.levels[hormone] + amount)
        # Antagonismos biológicos simplificados
        if hormone == HormoneType.CORTISOL:
            self.levels[HormoneType.DOPAMINE] = max(0.0, self.levels[HormoneType.DOPAMINE] - (amount * 0.5))
        elif hormone == HormoneType.DOPAMINE:
            self.levels[HormoneType.CORTISOL] = max(0.0, self.levels[HormoneType.CORTISOL] - (amount * 0.5))

    def metabolize(self, decay_rate: float = 0.05) -> None:
        """Decaimiento exponencial hacia la homeostasis basal."""
        for h in self.levels:
            if h == HormoneType.ADRENALINE:
                self.levels[h] = max(0.0, self.levels[h] - (decay_rate * 2))  # Adrenalina decae rápido
            else:
                self.levels[h] = max(0.1, self.levels[h] - decay_rate)


class EndocrineEngine:
    """Motor global/singleton para gestionar estados endocrinos de la legión."""

    def __init__(self):
        self._state = EndocrineState()

    def modulate_llm_params(self) -> Dict[str, float]:
        """Calcula los parámetros de inferencia (Temperature, Top-P) basados en el balance hormonal."""
        base_temp = 0.7
        # Dopamina sube la temperatura, Cortisol la baja
        temp_shift = (self._state.levels[HormoneType.DOPAMINE] * 0.5) - (self._state.levels[HormoneType.CORTISOL] * 0.5)
        temperature = max(0.0, min(1.5, base_temp + temp_shift))

        return {
            "temperature": round(temperature, 2),
            "top_p": round(max(0.1, 1.0 - (self._state.levels[HormoneType.CORTISOL] * 0.5)), 2),
        }

    def trigger_stress_response(self) -> None:
        """Invoca una reacción de pánico sistémico (Inyección de anomalía de seguridad)."""
        logger.warning("💉 Inyectando Adrenalina/Cortisol: Respuesta al estrés sistémico activada.")
        self._state.inject(HormoneType.ADRENALINE, 1.0)
        self._state.inject(HormoneType.CORTISOL, 0.8)


# Singleton exportado para 10 importadores a lo largo de BABYLON-60
ENDOCRINE = EndocrineEngine()
