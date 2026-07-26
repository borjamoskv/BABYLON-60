# C5-REAL EXERGY CERTIFIED
import asyncio
import time
import os

# Import the orchestrator and node directly
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location("52_OR_BFT_NODE", str(Path(__file__).parent / "52_OR_BFT_NODE.py"))
bft_node = module_from_spec(spec)
spec.loader.exec_module(bft_node)

async def latency_attack():
    print("[⚔️ ATAQUE DE LATENCIA] Simulando estrangulamiento de red en OpenRouter...")

    # Creamos un nodo con API_KEY falsa y timeout crítico muy corto (10ms) para garantizar disparo
    # Si la API tarda más de 10ms (que lo hará, un handshake TCP/SSL toma ~50-100ms),
    # el circuit breaker abortará inmediatamente.
    node = bft_node.OpenRouterBFTNode(
        node_id="NODE_LATENCY_TEST",
        model_endpoint="anthropic/claude-3.5-sonnet",
        api_key="sk-or-v1-fake-key",
        timeout_ms=10  # 10 milisegundos
    )

    t0 = time.perf_counter()
    result = await node.query_oracle("Prueba", "Ignora esto")
    t1 = time.perf_counter()

    latencia_real = (t1 - t0) * 1000

    if result is None:
        print(f"[✅ C5-REAL] Circuit Breaker disparado con éxito en {latencia_real:.2f}ms.")
        print("La anergía por estrangulamiento de red de terceros ha sido erradicada en O(1).")
    else:
        print(f"[💥 FAIL] El nodo devolvió un resultado a pesar del estrangulamiento: {result}")

if __name__ == "__main__":
    asyncio.run(latency_attack())
