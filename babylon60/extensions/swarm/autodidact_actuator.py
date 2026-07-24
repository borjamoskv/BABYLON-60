# [C5-REAL] Exergy-Maximized
import logging
from typing import Any

from babylon60.extensions.swarm.sortu_jit_executor import run_jit_sandbox

logger = logging.getLogger("babylon60.autodidact.actuator")
logging.basicConfig(level=logging.INFO)


async def autodidact_ingest(source_code: str, expected_yield_gain: float, metadata: dict) -> dict[str, Any]:
    """
    Sovereign Autodidact-Omega Actuator Pipeline (v4.0)
    1. Parse and JIT execute
    2. Thermometer (Yield Calculation)
    3. Return structured payload for Ledger (if valid)
    """
    logger.info("🔥 [AUTODIDACT-Ω] Starting Thermodynamic Ingestion...")

    is_bounty = metadata.get("intent") == "bounty_poc"
    global_ctx = {"bounty_mode": is_bounty}

    try:
        sandbox_res = await run_jit_sandbox(source_code, timeout_ms=500, global_ctx=global_ctx)
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as e:
        logger.warning("🔥 [AUTODIDACT-Ω] PURGED. AST Execution Failed: %s", e)
        return {"action": "PURGE", "reason": "JIT_BREAKER", "details": str(e)}

    if sandbox_res["status"] == "failed":
        logger.warning("🔥 [AUTODIDACT-Ω] PURGED. Epistemic Failure: %s", sandbox_res["error"])
        return {"action": "PURGE", "reason": "LOGIC_ERROR", "details": sandbox_res["error"]}

    if sandbox_res["status"] == "poc_success":
        logger.info("🔥 [AUTODIDACT-Ω] SUCCESS. PoC Validado. Massive Exergy Extracted.")
        return {
            "action": "CRYSTALLIZE",
            "yield_time_ms": 0.0,
            "resonance": expected_yield_gain * 1000.0,
            "locals": str(list(sandbox_res["result"].keys())),
        }

    exec_time = sandbox_res["time_ms"]

    performance_resonance = 1.0 if exec_time < 150 else (0.5 if exec_time < 300 else 0.1)

    if performance_resonance < 0.2:
        logger.warning(
            "🔥 [AUTODIDACT-Ω] PURGED. Negative Thermodynamic Yield (%.2fms).", exec_time
        )
        return {"action": "PURGE", "reason": "NEGATIVE_YIELD", "yield": exec_time}

    logger.info(
        "🔥 [AUTODIDACT-Ω] SUCCESS. O(1) Yield Crystal Forged (Resonance: %s).",
        performance_resonance,
    )
    return {
        "action": "CRYSTALLIZE",
        "yield_time_ms": exec_time,
        "resonance": performance_resonance,
        "locals": str(list(sandbox_res["result"].keys())),
    }
