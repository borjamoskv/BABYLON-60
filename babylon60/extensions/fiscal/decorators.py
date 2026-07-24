# [C5-REAL] Exergy-Maximized
import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def seal_decision(fact_type: str, client_id_kwarg: str = "client_id"):
    """
    Parasitic Overlay Decorator.
    Seals a fiscal decision automatically into the CORTEX immutable ledger
    without requiring the user to re-architect their application.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            client_id = kwargs.get(client_id_kwarg, "unknown_client")

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            inputs_trace = [
                f"{k}={v}"
                for k, v in bound_args.arguments.items()
                if isinstance(v, str | int | float | bool)
            ]

            # 3. Forge the TaxFact payload (C5-REAL integration)
            try:
                from babylon60.cli.common import get_engine
                from babylon60.events.loop import sovereign_run
                from babylon60.extensions.fiscal.models import TaxFact, TaxFactPayload

                payload = TaxFactPayload(
                    action=func.__name__,
                    amount_eur=0.0,  # Placeholder, should be mapped from result
                    tax_category="auto_extracted",
                    rationale=str(result)[:200],  # First 200 chars as rationale
                )

                fact = TaxFact(
                    fact_type=fact_type,
                    agent_id="auto-sealed-agent",
                    client_id=client_id,
                    period="current",
                    confidence=1.0,
                    payload=payload,
                    provenance_chain=inputs_trace,
                )

                engine = get_engine()

                async def _persist_fact():
                    await engine.add_fact(fact_type, fact.to_dict())  # type: ignore

                sovereign_run(_persist_fact())
                logger.info("[CORTEX] Sealed decision %s for client ***id", fact_type)

            except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:  # noqa: BLE001
                logger.error("[CORTEX] Failed to seal decision: %s", e)

            return result

        return wrapper

    return decorator
