#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - MCP SERVER STRESS TEST
# file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/06_apps/mcp_c5_abi_bridge/stress_test_mcp.py

import subprocess
import json
import time

def run_mcp_stress_test(num_requests=5000):
    print(f"=== STRESS TEST: MCP SERVER STDIO ({num_requests} REQS) ===")
    proc = subprocess.Popen(
        ["python3", "src/06_apps/mcp_c5_abi_bridge/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Initialize
    init_req = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()

    start_time = time.perf_counter()

    success_count = 0
    for i in range(1, num_requests + 1):
        req = {
            "jsonrpc": "2.0",
            "id": i,
            "method": "tools/call",
            "params": {
                "name": "c5_abi_execute",
                "arguments": {
                    "command_id": f"CMD_STRESS_{i}",
                    "payload": f"PAQUETE_ESTRÉS_{i}: Verificando estado muy rápido y excelente"
                }
            }
        }
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if line:
            resp = json.loads(line)
            if "result" in resp:
                success_count += 1

    elapsed = time.perf_counter() - start_time
    reqs_per_sec = success_count / elapsed
    avg_latency_us = (elapsed / success_count) * 1_000_000

    print(f"Peticiones Procesadas: {success_count}/{num_requests}")
    print(f"Tiempo Total: {elapsed:.3f} segundos")
    print(f"Rendimiento (Throughput): {reqs_per_sec:.2f} req/sec")
    print(f"Latencia Media por Petición: {avg_latency_us:.2f} μs")

    proc.terminate()

if __name__ == "__main__":
    run_mcp_stress_test(5000)
