#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
PoC Termodinámico: Swarm Research API
Demuestra la inyección de una intención a través de la pasarela y la restricción Hysteresis.
"""
import urllib.request
import json
import time

def fire_intent(topic: str, max_workers: int, reasoning: str):
    url = "http://127.0.0.1:8000/api/swarm/research"
    payload = {
        "topic": topic,
        "max_workers": max_workers,
        "enable_cloud_transduction": True,
        "reasoning_effort": reasoning,
        "cortex_taint": "[CORTEX-TAINT:poc_swarm_test]"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    print(f"\n--- Disparando Swarm Intent (Workers: {max_workers} | Effort: {reasoning}) ---")
    try:
        t0 = time.time()
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            latency = time.time() - t0
            print(f"HTTP {response.status} (Latencia: {latency:.3f}s)")
            print(json.dumps(json.loads(res_body), indent=2))
    except urllib.error.HTTPError as e:
        latency = time.time() - t0
        print(f"HTTP ERROR {e.code}: {e.read().decode('utf-8')} (Latencia: {latency:.3f}s)")

if __name__ == "__main__":
    # Prueba 1: Intent normal (Low effort, 2 workers)
    fire_intent("Teorema de Robinson", 2, "low")

    # Prueba 2: Violación de Hysteresis Gating (Topic Masivo > 10KB)
    print("\n[!] Disparando Carga Termica Hostil (Swarm DoS)")
    fire_intent("x" * 15000, 4, "max")
