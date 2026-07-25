# C5-REAL EXERGY CERTIFIED
import time
import sys
import os
import statistics

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from cortex.swarm.engine_fsm import run_fsm_cycle  # noqa: E402


def itera_5000() -> None:
    print(
        "=== CORTEX-OMEGA: IGNICIÓN DE BUCLE ITERA 5000 (TEST DE ENDURANCIA TERMODINÁMICA) ==="
    )

    success_count = 0
    failure_count = 0
    latencies = []

    old_stdout = sys.stdout
    devnull = open(os.devnull, "w")

    start_time_global = time.time()

    try:
        for i in range(5000):
            sys.stdout = devnull

            t0 = time.time()
            try:
                run_fsm_cycle()
                latencies.append(time.time() - t0)
                success_count += 1
            except (RuntimeError, OSError, ValueError) as e:
                sys.stdout = old_stdout
                print(f"\\n[ITERA-5000] FALLO ESTRUCTURAL EN CICLO {i + 1}: {e}")
                failure_count += 1
                break
            finally:
                sys.stdout = devnull

            # Restore stdout briefly to print progress
            if (i + 1) % 500 == 0:
                sys.stdout = old_stdout
                print(f"[ITERA-5000] Ciclos colapsados: {i + 1}/5000")
                sys.stdout = devnull

    finally:
        sys.stdout = old_stdout
        devnull.close()

    total_time = time.time() - start_time_global

    print("\\n=== RESULTADO DE ITERA 5000 ===")
    print(f"Ciclos Completados (Exergía): {success_count}/5000")
    print(f"Fallos (Anergía): {failure_count}")
    print(f"Tiempo Total de Colapso: {total_time:.4f}s")

    if latencies:
        p50 = (
            statistics.quantiles(latencies, n=100)[49]
            if len(latencies) >= 2
            else latencies[0]
        )
        p90 = (
            statistics.quantiles(latencies, n=100)[89]
            if len(latencies) >= 2
            else latencies[0]
        )
        p99 = (
            statistics.quantiles(latencies, n=100)[98]
            if len(latencies) >= 2
            else latencies[0]
        )

        print("\\n--- PERFIL DE LATENCIA (I/O SQLite WAL) ---")
        print(f"Latencia Media : {statistics.mean(latencies):.6f}s")
        print(f"Latencia P50   : {p50:.6f}s")
        print(f"Latencia P90   : {p90:.6f}s")
        print(f"Latencia P99   : {p99:.6f}s")
        print(f"Latencia Max   : {max(latencies):.6f}s")

    if failure_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    itera_5000()
