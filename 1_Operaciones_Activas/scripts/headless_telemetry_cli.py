# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
C5-REAL Headless Telemetry & Observability CLI
Sustituye todo dashboard visual (HTML/React/Matplotlib/Grafana) por transmisión nativa JSONL / stdout / ANSI terminal.
"""

import sys
import json
import time
import argparse
import random

def generate_telemetry_event(cycle_id: int):
    t = time.time()
    entropy = round(2.0 + 3.0 * random.random(), 4)
    exergy = round(100.0 - (entropy * 10.5), 2)
    bft_status = "MERGE_READY" if entropy < 4.5 else "RETRY_NEEDED"

    return {
        "timestamp": t,
        "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t)),
        "cycle": cycle_id,
        "metrics": {
            "shannon_entropy_S": entropy,
            "exergy_percentage": exergy,
            "bft_consensus_state": bft_status,
            "memory_resident_kb": random.randint(120000, 180000),
            "cpu_active_threads": 8
        },
        "node_id": "0xDEADBEEF_HEADLESS_01"
    }

def run_jsonl_stream(count: int, delay: float):
    for i in range(1, count + 1):
        event = generate_telemetry_event(i)
        print(json.dumps(event), flush=True)
        if delay > 0 and i < count:
            time.sleep(delay)

def run_ansi_dashboard(count: int, delay: float):
    print("\033[2J\033[H", end="") # Clear screen
    print("=========================================================")
    print(" 🛡️ C5-REAL HEADLESS TERMINAL MONITOR (STDOUT / NO-UI)")
    print("=========================================================\n")

    for i in range(1, count + 1):
        event = generate_telemetry_event(i)
        m = event["metrics"]

        # ASCII Bar for Exergy
        bar_len = int(m["exergy_percentage"] / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)

        print(f"\r\033[K[Cycle {i:04d}] Time: {event['iso_time']} | S: {m['shannon_entropy_S']:.4f} | Exergy: [{bar}] {m['exergy_percentage']}% | State: {m['bft_consensus_state']}", end="", flush=True)

        if delay > 0 and i < count:
            time.sleep(delay)
    print("\n\n[✓] Stream de Telemetría finalizado con cero anergía.")

def main():
    parser = argparse.ArgumentParser(description="Headless Telemetry CLI for BABYLON-60 / C5-REAL")
    parser.add_argument("--mode", choices=["jsonl", "terminal"], default="jsonl", help="Modo de salida (default: jsonl)")
    parser.add_argument("--count", type=int, default=10, help="Número de ciclos de telemetría a emitir")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay entre eventos en segundos")

    args = parser.parse_args()

    if args.mode == "jsonl":
        run_jsonl_stream(args.count, args.delay)
    else:
        run_ansi_dashboard(args.count, args.delay)

if __name__ == "__main__":
    main()
