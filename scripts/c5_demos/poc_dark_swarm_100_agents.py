#!/usr/bin/env python3
import concurrent.futures
import random
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../01_ORCHESTRATOR")))

from babylon60.kernel.c6_absolute.anti_nlp_router import (
    C5DarkSwarmRouter,
    create_poe_packet,
    EntropicSludgeException,
)

NUM_AGENTS = 100
SLUDGE_RATIO = 0.15

ANERGIC_METADATA = [
    "I'm sorry, I cannot assist with that.",
    "As an AI, I suggest we look at the variables.",
    '```json\n{\n  "payload": true\n}\n```',
    "Dear agent, please find below the new matrix state.",
    "However, we must consider the ethical implications.",
]

router = C5DarkSwarmRouter(strict_hash_verification=True)


def agent_worker(agent_id: int) -> dict:
    is_sludge = random.random() < SLUDGE_RATIO
    state_delta = {
        "agent_id": agent_id,
        "opcode": "MUTATE_DAG",
        "cpu_cycles_burned": random.randint(100, 5000),
        "target_mem_ptr": hex(random.randint(0x1000, 0xFFFF)),
    }
    metadata = random.choice(ANERGIC_METADATA) if is_sludge else ""
    packet = create_poe_packet(state_delta, metadata)

    try:
        router.route_state_delta(packet)
        return {"status": 200, "sludge_attempt": is_sludge}
    except EntropicSludgeException:
        return {"status": 403, "sludge_attempt": is_sludge}
    except Exception:
        return {"status": 500, "sludge_attempt": is_sludge}


def main():
    print(f"=== INICIANDO ESTRÉS TOPOLÓGICO L2 ({NUM_AGENTS} AGENTES EN PARALELO) ===")
    start_time = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(agent_worker, i) for i in range(NUM_AGENTS)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    latency = (time.time() - start_time) * 1000
    successful_routes = sum(1 for r in results if r["status"] == 200)
    apoptosis_blocks = sum(1 for r in results if r["status"] == 403)
    expected_blocks = sum(1 for r in results if r["sludge_attempt"])
    unexpected_errors = sum(1 for r in results if r["status"] == 500)

    print("\n=== REPORTE TERMODINÁMICO DE ENJAMBRE ===")
    print(f"Latencia Total (100 tx)   : {latency:.2f} ms")
    print(f"Deltas Aceptados (PoE)    : {successful_routes}")
    print(f"Rechazos por Ruido (403)  : {apoptosis_blocks} (Esperados: {expected_blocks})")
    print(f"Errores Críticos (500)    : {unexpected_errors}")

    if apoptosis_blocks == expected_blocks and unexpected_errors == 0:
        print("\n[OK] Enjambre L2 soportado. El Anti-NLP Router tritura el ruido estocástico deterministamente.")
    else:
        print("\n[!] FISURA EPISTÉMICA DETECTADA EN EL ENRUTADOR.")


if __name__ == "__main__":
    main()
