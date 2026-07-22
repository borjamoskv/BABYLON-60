#!/usr/bin/env python3
"""
Experiment: tercer_experimento_c5
STDP Memristor SQLite WAL Concurrency Stress Test.
"""

import os
import sys
import time
import json
import sqlite3
from typing import Any
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.append(PROJECT_ROOT)

from cortex.babylon60.neuromorphic_primitives import STDPMemristor  # noqa: E402

DB_PATH = "memristor_stress_test.db"


def run_single_thread(thread_id: int, db_path: str, pre: str, post: str) -> dict[str, Any]:
    mem = STDPMemristor(db_path, pre, post)
    success = 0
    failures = 0
    errors = []

    for i in range(20):
        try:
            mem.register_pre_spike()
            time.sleep(0.01)
            mem.register_post_spike()
            success += 2
        except sqlite3.OperationalError as e:
            failures += 2
            errors.append(str(e))
        except Exception as e:
            failures += 2
            errors.append(f"Unexpected: {str(e)}")

    return {
        "thread_id": thread_id,
        "success": success,
        "failures": failures,
        "errors": errors,
    }


def execute() -> None:
    print("[C5-REAL] Iniciando estrés de concurrencia en STDPMemristor (50 hilos)...")

    # Limpiar base de datos previa
    for suffix in ["", "-wal", "-shm"]:
        p = f"{DB_PATH}{suffix}"
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass  # Clean-up fallback

    # Inicializar memristores primarios
    STDPMemristor(DB_PATH, "SensorA", "MotorB")

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(
                run_single_thread, idx, DB_PATH, f"Sensor_{idx}", f"Motor_{idx}"
            )
            for idx in range(50)
        ]
        for fut in futures:
            results.append(fut.result())

    elapsed = time.time() - start_time

    total_success = sum(r["success"] for r in results)
    total_failures = sum(r["failures"] for r in results)

    all_errors = []
    for r in results:
        if r["errors"]:
            all_errors.extend(r["errors"])

    report = {
        "timestamp": int(time.time()),
        "threads": 50,
        "total_operations": total_success + total_failures,
        "success_ops": total_success,
        "failed_ops": total_failures,
        "exergy_ratio": round(
            total_success / max(1, total_success + total_failures), 4
        ),
        "elapsed_seconds": round(elapsed, 4),
        "errors": all_errors[:10],  # first 10 errors
    }

    # Persistir resultado localmente
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "synth_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    # Limpieza final
    for suffix in ["", "-wal", "-shm"]:
        p = f"{DB_PATH}{suffix}"
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass  # Clean-up fallback

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    execute()
