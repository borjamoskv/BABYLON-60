import asyncio
import logging

from babylon60.extensions.hypervisor.belief_object import BeliefConfidence, BeliefObject
from babylon60.extensions.llm.cognitive_handoff import CognitiveHandoff

# Silenciar logs genéricos para claridad en el POC
logging.getLogger("cortex.extensions.llm.cognitive_handoff").setLevel(logging.WARNING)


class MockRouter:
    async def route(self, prompt, provider_hint=None):
        intent = prompt.intent.value if prompt.intent else "N/A"
        mode = prompt.reasoning_mode.value if prompt.reasoning_mode else "N/A"

        logging.getLogger(__name__).info(f"\n[MockRouter] 🔹 Nodo Invocado | Intent: {intent}")
        logging.getLogger(__name__).info(f"[MockRouter] ⚙️ Reasoning Mode: {mode}")
        logging.getLogger(__name__).info(f"[MockRouter] 🚀 Provider Físico Asignado: {provider_hint}")

        class MockResult:
            def __init__(self, tokens):
                self.tokens_used = tokens

        # Simulamos comportamiento de los LLMs
        if intent == "episodic_processing":
            logging.getLogger(__name__).info("[MockRouter] ↳ Resultado: Prescreen completado. Relevancia alta.")
            return MockResult(12)

        elif intent == "belief_audit":
            if provider_hint == "z_ai":  # Auditor Económico (GLM-5.2)
                logging.getLogger(__name__).info(
                    "[MockRouter] ↳ Auditor Económico dictamina: UNCERTAIN (Forzando escalada P0)"
                )
                return MockResult(150)
            elif provider_hint == "anthropic":  # Auditor Premium (Opus 4.8)
                logging.getLogger(__name__).info(
                    "[MockRouter] ↳ Auditor Premium dictamina: CERTAIN sin contradicciones (Axioma preservado)"
                )
                return MockResult(600)

        return MockResult(10)


async def main():
    logging.getLogger(__name__).info("==========================================================")
    logging.getLogger(__name__).info(" 💠 POC: CORTEX COGNITIVE HANDOFF (SOTA 2026-06) 💠")
    logging.getLogger(__name__).info("==========================================================")

    # Instanciar el orquestador modificado
    handoff = CognitiveHandoff(router=MockRouter())

    # Generar un Belief (Conjetura generativa a evaluar)
    belief = BeliefObject(
        content="La red neural de Autodidact debe rutear la carga estructural a arquitecturas MIT para optimización termodinámica.",
        project="cortex-core",
        tenant_id="poc",
        confidence=BeliefConfidence.C3_PROBABLE,
    )

    logging.getLogger(__name__).info(f"\n[+] Ingiriendo Fact: '{belief.content}'")

    # Ejecutar la cascada
    verdict = await handoff.process_belief(belief)

    logging.getLogger(__name__).info("\n==========================================================")
    logging.getLogger(__name__).info(" 🏁 COLAPSO CAUSAL COMPLETADO")
    logging.getLogger(__name__).info("==========================================================")
    logging.getLogger(__name__).info(f" Acción Final:   {verdict.action.value}")
    logging.getLogger(__name__).info(f" Consumo (Tks):  {verdict.cost_tokens}")
    logging.getLogger(__name__).info(f" Razón:          {verdict.reason}")
    logging.getLogger(__name__).info("==========================================================")


if __name__ == "__main__":
    asyncio.run(main())
