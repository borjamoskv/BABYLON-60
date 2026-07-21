import dataclasses
import hashlib
import math
import os
from typing import Dict, List, Tuple

DOMAINS = {
    0: "DAIMON_CORE",
    1: "KAOS_EXEC",
    2: "KOSONG_LLM",
    3: "ACP_ADAPTER",
    4: "OPENCLAW_SHIM",
    5: "GATEWAY_API",
    6: "WEBBRIDGE_DESK",
    7: "MEMORY_LANCEDB",
    8: "PYTHON_RUN",
    9: "OBS_DIAGNOSTICS",
}
PRIMITIVES = {
    0: "INIT_RUNTIME",
    1: "EXEC_SHELL",
    2: "RESOLVE_SKILL",
    3: "STATE_MUTATE",
    4: "COMPOSE_PROMPT",
    5: "QUERY_VECTOR",
    6: "STREAM_GATEWAY",
    7: "SECURE_TAINT",
    8: "SYNCHRONIZE_UV",
    9: "PURGE_ARCHIVE",
}
MODIFIERS = {
    0: "RAW",
    1: "SECURE",
    2: "BYPASS",
    3: "ATOMIC",
    4: "EPHEMERAL",
    5: "MANAGED",
    6: "OBFUSCATED",
    7: "BFT_CONSENSUS",
    8: "CACHED",
    9: "ASYNC_WAL",
}


class KimiStateVector:
    def __init__(self) -> None:
        self.daimon_latency: List[float] = [0.0] * 64
        self.taint_score: List[float] = [0.0] * 64
        self.prompt_size: List[float] = [0.0] * 64
        self.cache_hits: List[float] = [0.0] * 64
        self.bft_validation_count: List[int] = [0] * 64
        self.execution_count: int = 0


def resolve_kimi_identity(d: int, p: int, m: int) -> Tuple[int, str]:
    if not (0 <= d <= 9 and 0 <= p <= 9 and 0 <= m <= 9):
        raise ValueError("Index out of range [0-9]")
    code = d * 100 + p * 10 + m
    name = f"KIMI-{DOMAINS[d]}-{PRIMITIVES[p]}-{MODIFIERS[m]}"
    return code, name


def dispatch_kimi(
    d: int, p: int, m: int, vec: KimiStateVector
) -> Tuple[int, str, List[float]]:
    code, name = resolve_kimi_identity(d, p, m)
    vec.execution_count += 1
    for i in range(64):
        vec.daimon_latency[i] = max(
            0.001, vec.daimon_latency[i] * 0.95 + 0.05 * abs(math.sin(code + i))
        )
        vec.taint_score[i] = max(
            0.0, min(100.0, vec.taint_score[i] + math.cos(code + i) * 5.0)
        )
        vec.prompt_size[i] = max(0.0, vec.prompt_size[i] + ((code + i) % 50) - 25.0)
        vec.cache_hits[i] = vec.cache_hits[i] * 0.99 + 0.01 * ((code + i) % 2)
        vec.bft_validation_count[i] += (code + i) % 5
    return code, name, vec.daimon_latency


@dataclasses.dataclass(frozen=True)
class KimiK3TrajectoryResult:
    trajectory_id: str
    code_hash: str
    reward: float
    shannon_entropy: float
    cortex_taint: str


class KimiK3TrajectoryEvaluator:
    """Evaluates agent execution trajectories under Kimi K3 ground-truth RLAF paradigm."""

    def evaluate_trajectory(self, payload: str) -> KimiK3TrajectoryResult:
        if not payload:
            raise ValueError("Payload cannot be empty")

        code_hash = hashlib.sha3_256(payload.encode("utf-8")).hexdigest()

        char_counts: Dict[str, int] = {}
        for char in payload:
            char_counts[char] = char_counts.get(char, 0) + 1

        total_len = len(payload)
        entropy = 0.0
        for count in char_counts.values():
            p = count / total_len
            if p > 0:
                entropy -= p * math.log(p)

        pid = os.getpid()
        taint_raw = f"KIMI_K3:{pid}:{code_hash[:16]}"
        cortex_taint = f"CORTEX-TAINT:kimik3:{hashlib.sha3_256(taint_raw.encode()).hexdigest()[:16]}"

        reward = max(0.0, min(1.0, 1.0 - (entropy / 10.0)))
        trajectory_id = f"K3-TRAJ-{code_hash[:8]}"

        return KimiK3TrajectoryResult(
            trajectory_id=trajectory_id,
            code_hash=code_hash,
            reward=reward,
            shannon_entropy=entropy,
            cortex_taint=cortex_taint,
        )

