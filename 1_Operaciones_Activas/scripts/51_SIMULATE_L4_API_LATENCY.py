# C5-REAL EXERGY CERTIFIED
import asyncio
import time
import statistics

async def mock_api_call(node_id: int) -> float:
    """Simula el jitter de red de la API REST."""
    t0 = time.perf_counter()
    # Latencia base ~ 800ms, jitter +- 200ms
    jitter = 0.8 + (node_id % 3) * 0.1
    await asyncio.sleep(jitter)
    return time.perf_counter() - t0

async def simulate_swarm_latency(n_nodes: int = 10, batch_size: int = 50):
    print(f"[🛡️] SIMULANDO ENJAMBRE L4 BFT ({n_nodes} NODOS ESCLAVOS API)")
    print(f"Lanzando batch de {batch_size} auditorías concurrentes...\n")

    start_global = time.perf_counter()

    tasks = []
    for i in range(batch_size):
        # Escoger un nodo aleatorio o rotar
        node = i % n_nodes
        tasks.append(asyncio.create_task(mock_api_call(node)))

    results = await asyncio.gather(*tasks)
    end_global = time.perf_counter()

    avg_latency = statistics.mean(results)

    # Cálculo manual de percentil si statistics.quantiles no está disponible
    sorted_results = sorted(results)
    p95_idx = int(len(sorted_results) * 0.95)
    p95_latency = sorted_results[p95_idx]

    print("[📊] RESULTADOS DEL COLAPSO (Exergía de Red):")
    print(f"  - Tiempo total de ejecución (Batch completo): {end_global - start_global:.2f}s")
    print(f"  - Latencia media por nodo: {avg_latency:.2f}s")
    print(f"  - Latencia P95: {p95_latency:.2f}s")
    print("\n[⚠️ DIAGNÓSTICO C5-REAL]:")
    if avg_latency > 1.0:
        print("  La inyección del oráculo externo destruye el tiempo O(1) del consenso L4.")
        print("  Recomendación: Mover la inferencia pesada a un plano asíncrono (L2 Off-Chain) y")
        print("  mantener el BFT L4 exclusivamente con validaciones criptográficas locales SHA3-256.")
    else:
        print("  El enjambre asimila la latencia externa de manera exergética.")

if __name__ == "__main__":
    asyncio.run(simulate_swarm_latency())
