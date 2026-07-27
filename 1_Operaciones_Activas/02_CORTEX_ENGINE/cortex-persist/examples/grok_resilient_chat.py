# [C5-REAL] Exergy-Maximized
# This file is part of CORTEX. Apache-2.0.

"""Demo script showing ResilientGrokClient usage.

import logging
Demonstrates:
1. Resilient error handling (connection issues, rate limits).
2. Structured outputs using Pydantic.
3. Conversation history with context pruning.
"""

from __future__ import annotations

import os
import sys
import time

from pydantic import BaseModel, Field

# Ensure we can import from babylon60
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.extensions.llm.grok_client import ConversationHistory, ResilientGrokClient

# ─── 1. Define Pydantic Models for Structured JSON Outputs ────────────


class BottleneckAnalysis(BaseModel):
    """Pydantic model representing structured audit findings for KV-Cache."""

    component: str = Field(description="The component analyzed (e.g., KV-Cache, Attention, etc.)")
    physical_cause: str = Field(
        description="The physical/computational reason for the bottleneck (e.g., IO-bound, memory bandwidth)"
    )
    memory_scaling_complexity: str = Field(
        description="Complexity formula explaining memory usage scaling (e.g., O(B * L * H * D))"
    )
    mitigation_strategies: list[str] = Field(
        description="List of modern mitigations (e.g., FlashAttention, GQA, MQA, PageAttention)"
    )
    energy_exergy_impact: str = Field(
        description="Exergy degradation or thermodynamic cost description"
    )


# ─── 2. Main Demo Execution ──────────────────────────────────────────


def main() -> None:
    logging.getLogger(__name__).info("======================================================================")
    logging.getLogger(__name__).info("🤖 xAI Grok Multi-Agent Resilient Client Demonstration (C5-REAL)")
    logging.getLogger(__name__).info("======================================================================\n")

    # API key check
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not api_key:
        logging.getLogger(__name__).info("⚠️  Warning: XAI_API_KEY or GROK_API_KEY environment variables not found.")
        logging.getLogger(__name__).info("👉 Running in simulation / fallback demo mode using mock client.\n")
        # We will use a mock/fake API key to initialize client, but since we will mock the responses
        # for verification purposes, let's configure client to use a dummy key if none exists.
        client = ResilientGrokClient(api_key="mock_key", base_url="http://localhost:8080/v1")
    else:
        logging.getLogger(__name__).info("✅ API Key detected.")
        client = ResilientGrokClient(api_key=api_key)

    # ─── Demo 1: Conversation History & Continuous Chat ────────────────────
    logging.getLogger(__name__).info("─── Part 1: Conversation History & Continuous Chat ───")
    history = ConversationHistory(
        system_prompt="Eres un auditor de sistemas experto en termodinámica de la información.",
        max_messages=6,
    )

    # Round 1
    user_msg_1 = "Analiza brevemente el cuello de botella físico del KV-Cache en Transformers."
    history.add_message("user", user_msg_1)
    logging.getLogger(__name__).info(f"\nUser 👤: {user_msg_1}")

    if api_key:
        logging.getLogger(__name__).info("Assistant 🤖 (Streaming...): ", end="", flush=True)
        try:
            full_response = ""
            for chunk in client.chat_stream(
                "grok-4.20-multi-agent-beta-0309", history.get_messages()
            ):
                logging.getLogger(__name__).info(chunk, end="", flush=True)
                full_response += chunk
            logging.getLogger(__name__).info()
            history.add_message("assistant", full_response)
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).info(f"\n❌ Error during execution: {e}")
            # Fallback/simulation
            mock_resp = "El KV-Cache consume memoria de forma cuadrática respecto a la longitud de secuencia, causando un cuello de botella de ancho de banda de memoria (IO-bound) durante la fase de generación autoregresiva."
            logging.getLogger(__name__).info(f"Assistant 🤖 (Mocked): {mock_resp}")
            history.add_message("assistant", mock_resp)
    else:
        # Simulation mode
        mock_resp = "El KV-Cache introduce un cuello de botella de I/O en la fase de generación (decode) de los Transformers debido a la necesidad de leer y escribir matrices gigantescas de Key-Value en memoria SRAM/HBM en cada token."
        time.sleep(1)
        logging.getLogger(__name__).info(f"Assistant 🤖 (Simulado): {mock_resp}")
        history.add_message("assistant", mock_resp)

    # Round 2 (Context continues)
    user_msg_2 = "Explica por qué MQA o GQA mitiga este problema de la memoria."
    history.add_message("user", user_msg_2)
    logging.getLogger(__name__).info(f"\nUser 👤: {user_msg_2}")

    if api_key:
        logging.getLogger(__name__).info("Assistant 🤖 (Streaming...): ", end="", flush=True)
        try:
            full_response = ""
            for chunk in client.chat_stream(
                "grok-4.20-multi-agent-beta-0309", history.get_messages()
            ):
                logging.getLogger(__name__).info(chunk, end="", flush=True)
                full_response += chunk
            logging.getLogger(__name__).info()
            history.add_message("assistant", full_response)
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).info(f"\n❌ Error during execution: {e}")
            mock_resp_2 = "MQA y GQA reducen el número de cabezas de clave y valor (KV), disminuyendo drásticamente el tamaño del KV-cache en memoria."
            logging.getLogger(__name__).info(f"Assistant 🤖 (Mocked): {mock_resp_2}")
            history.add_message("assistant", mock_resp_2)
    else:
        mock_resp_2 = "Multi-Query Attention (MQA) reduce las cabezas de KV a 1, mientras que Grouped-Query Attention (GQA) las agrupa (ej. 8 cabezas). Esto reduce la cantidad de datos que deben transferirse del HBM a los registros de la GPU en una proporción de hasta 8x."
        time.sleep(1)
        logging.getLogger(__name__).info(f"Assistant 🤖 (Simulado): {mock_resp_2}")
        history.add_message("assistant", mock_resp_2)

    # Inspect history structure (verifying max_messages sliding window)
    logging.getLogger(__name__).info("\n🔍 Estado del historial en memoria (Sliding Window):")
    for idx, msg in enumerate(history.get_messages()):
        logging.getLogger(__name__).info(f"  [{idx}] {msg['role'].upper()}: {msg['content'][:60]}...")

    # ─── Demo 2: Structured Outputs ──────────────────────────────────────
    logging.getLogger(__name__).info("\n─── Part 2: Structured JSON Outputs using Pydantic ───")
    struct_history = ConversationHistory(
        system_prompt="Eres un analista de hardware y microarquitectura. Responde estrictamente usando la estructura JSON solicitada."
    )
    struct_history.add_message("user", "Audita el KV-Cache en Transformers modernos.")

    logging.getLogger(__name__).info("🤖 Solicitando salida JSON estructurada y parseando con Pydantic...")

    if api_key:
        try:
            analysis: BottleneckAnalysis = client.chat_structured(
                model="grok-4.20-multi-agent-beta-0309",
                messages=struct_history.get_messages(),
                response_model=BottleneckAnalysis,
                temperature=0.1,
            )
            logging.getLogger(__name__).info("\n✅ Datos parseados con éxito en objeto Pydantic:")
            logging.getLogger(__name__).info(f"  • Componente: {analysis.component}")
            logging.getLogger(__name__).info(f"  • Causa Física: {analysis.physical_cause}")
            logging.getLogger(__name__).info(f"  • Complejidad: {analysis.memory_scaling_complexity}")
            logging.getLogger(__name__).info(f"  • Estrategias de Mitigación: {', '.join(analysis.mitigation_strategies)}")
            logging.getLogger(__name__).info(f"  • Impacto de Exergía: {analysis.energy_exergy_impact}")
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).info(f"❌ Error in structured parsing: {e}")
    else:
        # Simulating Pydantic parsing
        simulated_analysis = BottleneckAnalysis(
            component="KV-Cache en la fase de generación (Decode)",
            physical_cause="Ancho de banda de memoria DRAM/HBM limitado (Memory Bandwidth Bound)",
            memory_scaling_complexity="O(2 * BatchSize * SeqLen * NumLayers * NumHeads * HeadDim)",
            mitigation_strategies=[
                "Grouped-Query Attention (GQA)",
                "PagedAttention (vLLM)",
                "FlashDecoding",
                "Quantization (FP8/INT4 KV)",
            ],
            energy_exergy_impact="El movimiento masivo de datos entre memoria HBM y SRAM SRAM degrada la eficiencia térmica de los Tensor Cores, reduciendo el rendimiento efectivo de cómputo (FLOPs/watt).",
        )
        logging.getLogger(__name__).info("\n✅ Datos parseados con éxito en objeto Pydantic (Simulado):")
        logging.getLogger(__name__).info(f"  • Componente: {simulated_analysis.component}")
        logging.getLogger(__name__).info(f"  • Causa Física: {simulated_analysis.physical_cause}")
        logging.getLogger(__name__).info(f"  • Complejidad: {simulated_analysis.memory_scaling_complexity}")
        logging.getLogger(__name__).info(
            f"  • Estrategias de Mitigación: {', '.join(simulated_analysis.mitigation_strategies)}"
        )
        logging.getLogger(__name__).info(f"  • Impacto de Exergía: {simulated_analysis.energy_exergy_impact}")

    # ─── Demo 3: Connection & Rate Limits Error Handling ─────────────────
    logging.getLogger(__name__).info("\n─── Part 3: Connection Error & Rate Limit Handling ───")
    logging.getLogger(__name__).info("Este módulo utiliza políticas de reintento exponencial backoff con Jitter.")
    logging.getLogger(__name__).info("Si ocurre un error transitorio de red (RateLimitError, TimeoutError, etc.),")
    logging.getLogger(__name__).info("el cliente reintentará automáticamente hasta 5 veces.")

    # We can inspect the tenacity decorators on ResilientGrokClient.chat
    logging.getLogger(__name__).info("Resilience metadata:")
    retry_settings = client.chat.retry.statistics
    logging.getLogger(__name__).info(
        f"  • Intentos realizados (estadística actual del proceso): {retry_settings.get('attempts_count', 0)}"
    )
    logging.getLogger(__name__).info("\n🎉 ¡Demostración de resiliencia finalizada!")


if __name__ == "__main__":
    main()
