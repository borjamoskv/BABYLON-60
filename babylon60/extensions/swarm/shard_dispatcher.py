# [C5-REAL] Exergy-Maximized
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger("babylon60_extensions.swarm.shard_dispatcher")


@dataclass(frozen=True)
class InvariantShard:
    """Representa un Shard de reglas invariantes."""
    name: str
    rules: List[str]


class SwarmThreadDispatcher:
    """
    Ω38 · INVARIANT SHARDING (CONTEXT EXERGY MAXIMIZATION)
    Segmenta las reglas masivas en shards funcionales para evitar atenuación atencional.
    El subagente solo recibe el Core y el Shard relevante.
    """

    def __init__(self) -> None:
        self._core_invariants: List[str] = [
            "Φ1 · MEJORALO: Forzar el colapso del AST.",
            "Φ2 · SIN THEATER: Silencio por defecto.",
            "Ω3 · BUCLE BFT_STATE_LOOP: Mutación atómica y verificación.",
        ]
        self._shards: Dict[str, InvariantShard] = {
            "L2/Database": InvariantShard(
                name="L2/Database",
                rules=["Ω1 · MOTOR CAUSAL BASE 60", "Ω13 · SERIALIZACIÓN DE ESCRITURA"]
            ),
            "L3/Hardware": InvariantShard(
                name="L3/Hardware",
                rules=["Ω31 · PHYSICAL SIMULATION ENTROPY MAPPING"]
            ),
            "L15/Diamond": InvariantShard(
                name="L15/Diamond",
                rules=["Ω15 · IDEMPOTENCY LOCK"]
            ),
            "Frontend/Cinematic": InvariantShard(
                name="Frontend/Cinematic",
                rules=["Ω11 · Compatibilidad de Sintaxis AST"]
            ),
        }

    def dispatch_prompt(self, target_domain: Optional[str]) -> str:
        """
        Construye el system prompt maximizando exergía por token.
        Combina Core Invariants con el shard del dominio específico.
        """
        prompt_lines = ["--- CORE INVARIANTS ---"]
        prompt_lines.extend(f"- {rule}" for rule in self._core_invariants)

        if target_domain and target_domain in self._shards:
            shard = self._shards[target_domain]
            logger.info("🔪 [SHARD DISPATCHER] Inyectando Shard: %s", shard.name)
            prompt_lines.append(f"--- SHARD: {shard.name} ---")
            prompt_lines.extend(f"- {rule}" for rule in shard.rules)
        else:
            logger.info("🔪 [SHARD DISPATCHER] Sin dominio objetivo válido. Solo inyectando Core.")

        return "\n".join(prompt_lines)
