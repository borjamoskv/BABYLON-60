# [C5-REAL] Exergy-Maximized
"""
cat_id: legion-strike
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


import logging


import asyncio
import os
import sys
from argparse import ArgumentParser

# Ensure CWD is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.extensions.llm.provider import LLMProvider
from babylon60.extensions.llm.router import CortexLLMRouter
from babylon60.extensions.swarm.centauro_engine import CentauroEngine, Formation


def emit(msg: str, level: str = "INFO"):
    logging.getLogger(__name__).info(f"[{level}] [C5-REAL] {msg}")


async def run_strike(mission: str, formation_name: str, tolerance: float, sim: bool):
    emit("Orchestrating Sovereign Swarm CentauroEngine...", "BOOT")
    emit(
        f"Mission Parameters:\n  - Focus: {mission}\n  - Formation: {formation_name}\n  - Consensus Threshold: {tolerance}",
        "INFO",
    )

    router = None
    if not sim:
        # Detect if any key is set to attempt C5-REAL execution
        has_gemini = "GEMINI_API_KEY" in os.environ
        has_anthropic = "ANTHROPIC_API_KEY" in os.environ
        has_openai = "OPENAI_API_KEY" in os.environ

        if has_gemini or has_anthropic or has_openai:
            try:
                emit("Initializing CortexLLMRouter for C5-REAL execution...", "INFO")
                # Forzar bypass termodinámico para que el Swarm pueda operar si Ollama está caído
                os.environ["CORTEX_ALLOW_EXTERNAL_SWARM"] = "1"
                prov = "gemini" if has_gemini else ("anthropic" if has_anthropic else "openai")
                primary_provider = LLMProvider(provider=prov)

                fallbacks = []
                if has_gemini and prov != "gemini":
                    fallbacks.append(LLMProvider(provider="gemini"))
                if has_anthropic and prov != "anthropic":
                    fallbacks.append(LLMProvider(provider="anthropic"))
                if has_openai and prov != "openai":
                    fallbacks.append(LLMProvider(provider="openai"))

                router = CortexLLMRouter(primary=primary_provider, fallbacks=fallbacks)
            except Exception as e:  # noqa: BLE001
                emit(f"Failed to instantiate C5-REAL Router: {e}. Degrading to C4-SIM.", "WARNING")
        else:
            emit("No remote API keys detected in environment. Operating in C4-SIM mode.", "WARNING")
    else:
        emit("Dry run requested (--sim). Forcing C4-SIM mode.", "INFO")

    # Instantiate Centauro
    engine = CentauroEngine(tolerance=tolerance, router=router)

    # Run mission
    start_time = asyncio.get_event_loop().time()
    try:
        result = await engine.engage(mission=mission, formation=formation_name)
        elapsed = asyncio.get_event_loop().time() - start_time

        status = result.get("status", "unknown").upper()
        solution = result.get("solution", "N/A")
        agents_used = result.get("agents_used", 0)
        actual_formation = result.get("formation", formation_name)

        emit("Consensus Sweep Completed.", "SUCCESS")
        logging.getLogger(__name__).info("\n" + "=" * 60)
        logging.getLogger(__name__).info(f" 🔱 MISSION RESULT: {status}")
        logging.getLogger(__name__).info(f"  - Agents Activated: {agents_used} ({actual_formation})")
        logging.getLogger(__name__).info(f"  - Elapsed Time: {elapsed:.2f}s")
        logging.getLogger(__name__).info(f"  - Consensus Resolution:\n{solution}")
        logging.getLogger(__name__).info("=" * 60 + "\n")

    except Exception as e:  # noqa: BLE001
        emit(f"Swarm compromised. Apoptosis triggered: {e}", "CRITICAL")
        sys.exit(1)


if __name__ == "__main__":
    parser = ArgumentParser(description="LEGIØN-1 Sovereign Swarm Protocol Strike Interface")
    parser.add_argument(
        "--mission", type=str, required=True, help="Task or objective for the swarm"
    )
    parser.add_argument("--formation", type=str, default="BLITZ", help="Swarm formation layout")
    parser.add_argument(
        "--tolerance", type=float, default=0.67, help="Byzantine consensus threshold"
    )
    parser.add_argument("--sim", action="store_true", help="Force C4-SIM test mock execution")

    args = parser.parse_args()

    # Normalize formation name against catalog
    formation_upper = args.formation.upper()
    valid_formations = [
        getattr(Formation, name) for name in dir(Formation) if not name.startswith("_")
    ]
    if formation_upper not in valid_formations:
        emit(f"Invalid formation: {args.formation}. Fallback to BLITZ.", "WARNING")
        formation_upper = "BLITZ"

    asyncio.run(run_strike(args.mission, formation_upper, args.tolerance, args.sim))
