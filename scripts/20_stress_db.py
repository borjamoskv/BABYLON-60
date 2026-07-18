import concurrent.futures
import time
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from cortex.swarm.memory_store import AgentMemory  # noqa: E402


def worker(worker_id: int):
    try:
        memory = AgentMemory()
        start = time.perf_counter()
        _ = memory.log(
            issue_id=worker_id, agent_role="STRESS_TESTER", action="FIRE", result="OK"
        )
        elapsed = time.perf_counter() - start
        return ("OK", worker_id, elapsed)
    except Exception as e:
        return ("ERROR", worker_id, str(e))


def run_stress_test(num_requests=1000, max_workers=100):
    print(
        f"Iniciando asedio C5-REAL SQLite WAL BFT | Requests: {num_requests} | Concurrency: {max_workers}"
    )

    start_time = time.time()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, i) for i in range(num_requests)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    end_time = time.time()
    total_time = end_time - start_time

    success = sum(1 for r in results if r[0] == "OK")
    errors = sum(1 for r in results if r[0] == "ERROR")
    error_types = {}
    for r in results:
        if r[0] == "ERROR":
            error_types[r[2]] = error_types.get(r[2], 0) + 1

    print("\n=== RESULTADOS DEL ASEDIO ===")
    print(f"Tiempo Total: {total_time:.4f}s")
    print(f"Exitos (Exergía): {success}")
    print(f"Errores (Anergía): {errors}")

    if errors > 0:
        print("\n=== TOPOLOGÍA DEL COLAPSO ===")
        for e_msg, count in error_types.items():
            print(f"- {count} ocurrencias: {e_msg}")
        sys.exit(1)
    else:
        print("\nResiliencia Topológica Confirmada (C5-REAL).")
        sys.exit(0)


if __name__ == "__main__":
    run_stress_test(num_requests=1000, max_workers=100)
