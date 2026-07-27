# [C5-REAL] Exergy-Maximized
"""
Motor de Física Termodinámica para el modo Ultrathink (P0-Mechanics).
Calcula la exergía cognitiva y el Blast Radius para autorizar bifurcaciones masivas.

AUTODIDACT / Ultrathink Paradigm:
Un agente no "entiende" la petición; el agente extrae la Exergía (ORT-001),
aplica el Colapso (ORT-003) para purgar la Anergía (ORT-005),
preserva el Invariante (ORT-004) y ancla el isomorfismo en el Estado/Ledger (ORT-002).
"""

import logging
import math
import os
from collections import deque
from enum import Enum
from typing import Any

from babylon60.extensions.security.utils import calculate_shannon_entropy

logger = logging.getLogger("babylon60.engine.exergy_physics")

# [C5-REAL] Static Exergy Cache: Eliminates environment variable reading at inference time
_ENV_DOMAINS = os.getenv("CORTEX_CRITICAL_DOMAINS")
_CACHED_CRITICAL_DOMAINS: frozenset[str] = (
    frozenset(d.strip().lower() for d in _ENV_DOMAINS.split(",") if d.strip())
    if _ENV_DOMAINS
    else frozenset(
        [
            "ledger",
            "crypto",
            "auth",
            "db",
            "migration",
            "guard",
            "security",
            "vault",
            "engine",
            "sovereign",
            "audit",
            "pii",
            "trust",
        ]
    )
)


class LegionFormation(str, Enum):
    """Sovereign Swarm Formations (LEGIØN-1 Protocol)"""

    BLITZ = "BLITZ"  # 3-5 agents: Atomic tasks
    PHALANX = "PHALANX"  # 6-10 agents: Audit & coverage
    SIEGE = "SIEGE"  # 8-15 agents: Deep research
    HYDRA = "HYDRA"  # 10-20 agents: Parallel domain mutation
    ORACLE = "ORACLE"  # 3-5 agents: Strategic prediction
    PHOENIX = "PHOENIX"  # 5-8 agents: Self-healing & technical debt
    CHIMERA = "CHIMERA"  # 4-12 agents: Innovation
    LEVIATHAN = "LEVIATHAN"  # 20-50 agents: Total P0 singularity siege
    CENTURIA = "CENTURIA"  # 100 agents: Massive parallel refactor
    MILLENNIUM = "MILLENNIUM"  # 1000 agents: Continental codebase rewrite
    LEGION_10K = "LEGION_10K"  # 10000 agents: Planetary intelligence collapse
    OUROBOROS = "OUROBOROS"  # 3-7 agents: Recursive self-improvement
    SENTINEL = "SENTINEL"  # Security & Infrastructure monitoring
    SPECTRE = "SPECTRE"  # OSINT & Intelligence stealth
    GHOST = "GHOST"  # Single specialized agent
    TESTUDO = "TESTUDO"  # 15 agents: Proactive infrastructure defense
    SANEDRIN = "SANEDRIN"  # 5 agents: Heterogeneous Supreme Quorum


class UltrathinkPhysicsEngine:
    """
    Controlador matemático para la Inferencia P0.
    Aplica la fórmula de Exergía Cognitiva.
    """

    # Constante de Singularidad (Singularity Exergy Limit)
    SINGULARITY_CONSTANT: float = 100.0

    # Critical subsystems for trust scaling (frozenset for O(1) ops where applicable)
    CRITICAL_DOMAINS: frozenset[str] = frozenset(
        [
            "ledger",
            "crypto",
            "auth",
            "db",
            "migration",
            "guard",
            "security",
            "vault",
            "engine",
            "sovereign",
            "audit",
            "pii",
            "trust",
        ]
    )

    # Constante teórica de Landauer (J/bit a 300K)
    BASE_LANDAUER_LIMIT_J: float = 2.75e-21

    @classmethod
    def get_thermal_penalty(cls) -> float:
        """
        Calcula empíricamente (o estáticamente por SO) la fricción térmica.
        M-Series (Darwin) sufre asimetría en Memoria Unificada bajo carga NPU/GPU.
        """
        import platform
        if platform.system() == "Darwin":
            return 1.15  # Asimetría Apple Silicon (Thermal throttling de bus unificado)
        return 1.05

    @classmethod
    def _resolve_risk(cls, epicenter_node: str = "default_node") -> tuple[float, bool]:
        """Calcula el multiplicador de riesgo termodinámico en O(K). Cero tolerancia a Nones (K1)."""
        node_lower = epicenter_node.lower()
        if any(domain in node_lower for domain in _CACHED_CRITICAL_DOMAINS):
            return 1.5, True
        return 1.0, False

    @classmethod
    def calculate_exergy_yield(
        cls, stochastic_entropy: float, deterministic_output: float, execution_time: float
    ) -> float:
        """
        Calcula la exergía (Ξ) producida en un ciclo de razonamiento (Landauer Principle).
        Ξ = ((S_out[Determinista] - S_in[Estocástico]) / ΔT) / (Penalización Térmica ^ ΔT)
        """
        # [C5-REAL] Precondición matemática estricta: NaN/Inf son anomalías
        if not (
            math.isfinite(stochastic_entropy)
            and math.isfinite(deterministic_output)
            and math.isfinite(execution_time)
        ):
            return 0.0

        # CORTEX Optimization: Capping minimal execution time to 1ms to prevent mathematical noise
        execution_time = max(execution_time, 0.001)

        raw_exergy = (deterministic_output - stochastic_entropy) / execution_time
        try:
            thermal_dissipation = cls.get_thermal_penalty() ** execution_time
            exergy = raw_exergy / thermal_dissipation
        except OverflowError:
            exergy = 0.0
        return max(0.0, exergy)

    @classmethod
    def measure_blast_metrics(
        cls, dependency_graph: dict[str, Any], epicenter_node: str
    ) -> dict[str, int]:
        """
        Calcula métricas detalladas del radio de explosión (volumen y profundidad máxima).
        Retorna {"volume": int, "depth": int}. Asume validación tipográfica fuerte (K1).
        """
        visited = {epicenter_node}
        queue = deque([(epicenter_node, 0)])  # (node, depth)
        max_depth = 0

        while queue:
            current, depth = queue.popleft()
            if depth > max_depth:
                max_depth = depth

            # [K1] Eliminada la programación defensiva de tipos. Crasheará si el grafo es termodinámicamente inválido.
            neighbors = dependency_graph.get(current, [])
            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    queue.append((n, depth + 1))

        return {"volume": len(visited), "depth": max_depth}

    @classmethod
    def measure_blast_radius(cls, dependency_graph: dict[str, Any], epicenter_node: str) -> int:
        """
        Calcula el 'Blast Radius' topológico de una corrupción P0 para el aislamiento térmico.
        Devuelve el número de nodos afectados.
        """
        if not isinstance(dependency_graph, dict):
            return 1
        metrics = cls.measure_blast_metrics(dependency_graph, epicenter_node)
        radius = metrics["volume"]
        logger.debug(
            "Blast Radius measure for %s: %d (Depth: %d)", epicenter_node, radius, metrics["depth"]
        )
        return radius

    @classmethod
    def calculate_legion_formation(
        cls, epicenter_radius: int, exergy_yield: float, epicenter_node: str = "default_node"
    ) -> LegionFormation:
        """
        Collapses thermodynamic requirements into a specific LEGIØN-1 Swarm Formation.
        Includes critical path amplification.
        """
        risk_multiplier, _ = cls._resolve_risk(epicenter_node)
        effective_radius = math.ceil(epicenter_radius * risk_multiplier)

        if effective_radius >= 10 and exergy_yield > (cls.SINGULARITY_CONSTANT * 0.5):
            return LegionFormation.LEVIATHAN
        if effective_radius >= 7:
            return LegionFormation.HYDRA
        if effective_radius >= 5:
            return LegionFormation.TESTUDO
        if exergy_yield > (cls.SINGULARITY_CONSTANT * 0.3):
            return LegionFormation.OUROBOROS
        return LegionFormation.PHOENIX

    @classmethod
    def authorize_ultrathink(
        cls,
        stochastic_entropy: float,
        deterministic_output: float,
        execution_time: float,
        epicenter_radius: int,
        epicenter_node: str = "default_node",
    ) -> tuple[bool, str, LegionFormation | None]:
        """
        El colapso a 'Ultrathink' exige un rendimiento exergético masivo
        y un radio de explosión demostrable. Amplifica la sensibilidad ante nodos críticos.
        """
        # [C5-REAL] Precondición matemática estricta: NaN/Inf son anomalías
        if not math.isfinite(epicenter_radius):
            return (
                False,
                "Invalid epicenter radius provided (NaN/Inf or non-numeric).",
                None,
            )

        if not (
            math.isfinite(stochastic_entropy)
            and math.isfinite(deterministic_output)
            and math.isfinite(execution_time)
        ):
            return (
                False,
                "Invalid parameters (NaN or Inf detected).",
                None,
            )

        epicenter_radius = int(epicenter_radius)
        exergy = cls.calculate_exergy_yield(
            stochastic_entropy, deterministic_output, execution_time
        )

        risk_multiplier, is_critical = cls._resolve_risk(epicenter_node)
        effective_radius = math.ceil(epicenter_radius * risk_multiplier)

        required_exergy_ratio = 0.05 if is_critical else 0.1

        if effective_radius < 3:
            return (
                False,
                f"[THK-P-095] ULTRATHINK P0 Horizon restricted to epicenter_radius >= 3 (effective radius too small). (Current: {effective_radius})",
                None,
            )

        required_exergy = cls.SINGULARITY_CONSTANT * required_exergy_ratio
        if exergy < required_exergy:
            return (
                False,
                f"Insufficient Exergy Yield ({exergy:.2f}) for JIT structural collapse (Required: {required_exergy:.2f}).",
                None,
            )

        formation = cls.calculate_legion_formation(epicenter_radius, exergy, epicenter_node)
        return (
            True,
            f"Ultrathink P0 Singularity Horizon Authorized. Swarm: {formation.value}",
            formation,
        )

    @staticmethod
    def estimate_shannon_entropy(text: str) -> float:
        """
        Estimates the Shannon Entropy of raw text output.
        S = -sum(p(x) * log2(p(x)))
        """
        return calculate_shannon_entropy(text)
