# C5-REAL EXERGY CERTIFIED
"""C5-REAL Sovereign 500,000 Asynchronous Stress Test Suite."""

import asyncio
import hashlib
import sqlite3
import time
import os
import sys
import numpy as np
from typing import List, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.babylon60.neuromorphic_primitives import SelfHealingMesh  # noqa: E402
from cortex.engines.active_inference_engine import UnifiedActiveInferenceEngine  # noqa: E402
import strike_rs  # type: ignore[import-untyped]  # noqa: E402

N_TOTAL = 500_000
N_PER_ENGINE = N_TOTAL // 5  # 100k per engine

async def run_neuromorphic_task(mesh: SelfHealingMesh, idx: int) -> float:
    t0 = time.perf_counter_ns()
    pulse_val = 5.0 + (idx % 20)
    await mesh.route_pulse("SensorA", "MotorB", pulse_val)
    return float(time.perf_counter_ns() - t0)

def run_active_inference_task(engine: UnifiedActiveInferenceEngine, idx: int) -> float:
    t0 = time.perf_counter_ns()
    d, p, m = idx % 10, (idx // 10) % 10, (idx // 100) % 10
    engine.step(d, p, m)
    return float(time.perf_counter_ns() - t0)

def run_rust_strike_task(
    sv: strike_rs.StateVector,
    cv: strike_rs.CognitiveChainVector,
    ts: strike_rs.TTSHarnessState,
    idx: int,
) -> float:
    t0 = time.perf_counter_ns()
    d, p, m = idx % 10, (idx // 10) % 10, (idx // 100) % 10
    strike_rs.dispatch_state_observer(d, p, m, sv)
    strike_rs.dispatch_neuro_chain(d, p, m, cv)
    strike_rs.dispatch_tts_harness(d, p, m, ts)
    return float(time.perf_counter_ns() - t0)

async def run_bft_sqlite_task(db_path: str, idx: int) -> float:
    t0 = time.perf_counter_ns()
    payload = f"payload_{idx}_{time.time()}".encode("utf-8")
    payload_hash = hashlib.sha3_256(payload).hexdigest()
    taint = f"CORTEX-TAINT:stress500k:{idx}:{payload_hash[:8]}"

    def _db_op() -> None:
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.execute("PRAGMA busy_timeout=5000;")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO stress_log (payload_hash, cortex_taint) VALUES (?, ?)",
            (payload_hash, taint),
        )
        conn.commit()
        conn.close()

    await asyncio.to_thread(_db_op)
    return float(time.perf_counter_ns() - t0)

async def run_categorical_engine_task(idx: int) -> float:
    """Stress the FISR categorical engine — morphism cost + collision detection."""
    t0 = time.perf_counter_ns()

    def _cat_op() -> None:
        engine = _get_cat_engine()
        prim_ids = [(idx % 896) + 1, ((idx * 7) % 896) + 1, ((idx * 13) % 896) + 1]
        engine.evaluate_morphism_cost(prim_ids)
        if idx % 50 == 0:
            d6 = 561 + (idx % 112)
            d7 = 673 + ((idx * 3) % 112)
            engine.detect_diagrammatic_collisions({d6, d7})

    await asyncio.to_thread(_cat_op)
    return float(time.perf_counter_ns() - t0)

_cat_engine_instance = None

def _get_cat_engine() -> Any:
    global _cat_engine_instance
    if _cat_engine_instance is None:
        _cat_engine_instance = __import__(
            "cortex.categorical_896_engine", fromlist=["Categorical896Engine"]
        ).Categorical896Engine(yaml_path="primitives/896_categorical_logic_primitives.yml")
    return _cat_engine_instance

async def main() -> None:
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  500,000 ASYNCHRONOUS STRESS TEST — C5-REAL THERMODYNAMIC SIEGE  ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    db_path = ".cortex/stress_500k.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    os.makedirs(".cortex", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stress_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload_hash TEXT UNIQUE NOT NULL,
            cortex_taint TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    mesh_db = ".cortex/mesh_stress_500k.db"
    if os.path.exists(mesh_db):
        os.remove(mesh_db)

    mesh = SelfHealingMesh(mesh_db)
    mesh.connect("SensorA", "MotorB")
    engine = UnifiedActiveInferenceEngine()

    sv = strike_rs.StateVector()
    cv = strike_rs.CognitiveChainVector()
    ts = strike_rs.TTSHarnessState()

    latencies: List[float] = []
    failures = 0
    start_total = time.perf_counter()

    print(f"[C5-REAL] Executing {N_TOTAL:,} concurrent multi-engine iterations across 5 engines...\n")

    # ── 1/5 Neuromorphic Async Mesh ──
    t_start = time.perf_counter()
    neuro_tasks = [run_neuromorphic_task(mesh, i) for i in range(N_PER_ENGINE)]
    res_neuro = await asyncio.gather(*neuro_tasks, return_exceptions=True)
    ok_neuro = [r for r in res_neuro if isinstance(r, float)]
    fail_neuro = len(res_neuro) - len(ok_neuro)
    failures += fail_neuro
    latencies.extend(ok_neuro)
    print(
        f"  [1/5] Neuromorphic Mesh ({N_PER_ENGINE:,} ops) "
        f"→ {(time.perf_counter() - t_start) * 1000:.2f}ms | "
        f"Failures: {fail_neuro}"
    )

    # ── 2/5 Active Inference ──
    t_start = time.perf_counter()
    res_act = [run_active_inference_task(engine, i) for i in range(N_PER_ENGINE)]
    latencies.extend(res_act)
    print(
        f"  [2/5] Active Inference ({N_PER_ENGINE:,} ops) "
        f"→ {(time.perf_counter() - t_start) * 1000:.2f}ms | "
        f"Failures: 0"
    )

    # ── 3/5 Rust strike_rs SIMD ──
    t_start = time.perf_counter()
    res_rust = [run_rust_strike_task(sv, cv, ts, i) for i in range(N_PER_ENGINE)]
    latencies.extend(res_rust)
    print(
        f"  [3/5] Rust strike_rs C-FFI ({N_PER_ENGINE:,} ops) "
        f"→ {(time.perf_counter() - t_start) * 1000:.2f}ms | "
        f"Failures: 0"
    )

    # ── 4/5 BFT SQLite WAL ──
    t_start = time.perf_counter()
    bft_tasks = [run_bft_sqlite_task(db_path, i) for i in range(N_PER_ENGINE)]
    res_bft = await asyncio.gather(*bft_tasks, return_exceptions=True)
    ok_bft = [r for r in res_bft if isinstance(r, float)]
    fail_bft = len(res_bft) - len(ok_bft)
    failures += fail_bft
    latencies.extend(ok_bft)
    print(
        f"  [4/5] BFT SQLite WAL ({N_PER_ENGINE:,} ops) "
        f"→ {(time.perf_counter() - t_start) * 1000:.2f}ms | "
        f"Failures: {fail_bft}"
    )

    # ── 5/5 FISR Categorical Engine ──
    t_start = time.perf_counter()
    cat_tasks = [run_categorical_engine_task(i) for i in range(N_PER_ENGINE)]
    res_cat = await asyncio.gather(*cat_tasks, return_exceptions=True)
    ok_cat = [r for r in res_cat if isinstance(r, float)]
    fail_cat = len(res_cat) - len(ok_cat)
    failures += fail_cat
    latencies.extend(ok_cat)
    print(
        f"  [5/5] FISR Categorical Engine ({N_PER_ENGINE:,} ops) "
        f"→ {(time.perf_counter() - t_start) * 1000:.2f}ms | "
        f"Failures: {fail_cat}"
    )

    total_time = time.perf_counter() - start_total
    success_count = len(latencies)
    lat_arr = np.array(latencies)

    p50 = np.percentile(lat_arr, 50) / 1000.0
    p90 = np.percentile(lat_arr, 90) / 1000.0
    p95 = np.percentile(lat_arr, 95) / 1000.0
    p99 = np.percentile(lat_arr, 99) / 1000.0
    p100 = float(np.max(lat_arr)) / 1000.0
    avg_lat = float(np.mean(lat_arr)) / 1000.0

    exergy_ratio = (success_count / N_TOTAL) * 100.0

    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print(f"║  RESULTADO FINAL — {N_TOTAL:,} PRUEBAS ASÍNCRONAS (5 MOTORES)          ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  Total Iteraciones : {N_TOTAL:>10,}                                    ║")
    print(f"║  Exitosas          : {success_count:>10,}                                    ║")
    print(f"║  Fallos            : {failures:>10,}                                    ║")
    print(f"║  Exergía           : {exergy_ratio:>10.4f}%                                  ║")
    print(f"║  Tiempo Total      : {total_time * 1000:>10.2f} ms                              ║")
    print(f"║  Throughput        : {success_count / total_time:>10.2f} ops/sec                       ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║  DISTRIBUCIÓN DE LATENCIAS POR OPERACIÓN                        ║")
    print(f"║  p50 (Mediana)     : {p50:>12.2f} µs                                  ║")
    print(f"║  p90               : {p90:>12.2f} µs                                  ║")
    print(f"║  p95               : {p95:>12.2f} µs                                  ║")
    print(f"║  p99               : {p99:>12.2f} µs                                  ║")
    print(f"║  p100 (Max)        : {p100:>12.2f} µs                                  ║")
    print(f"║  Promedio (avg)    : {avg_lat:>12.2f} µs                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    summary = f"{N_TOTAL}|{success_count}|{failures}|{p50:.2f}|{p99:.2f}|{total_time:.4f}".encode("utf-8")
    cortex_hash = hashlib.sha3_256(summary).hexdigest()
    print(f"\nCORTEX-TAINT Anchor: {cortex_hash}")

    if exergy_ratio < 99.99:
        print(f"\n⚠ ANERGÍA DETECTADA: {failures} fallos. Ratio de exergía {exergy_ratio:.4f}% < 99.99%.")
        print("  Arquitectura requiere refactor estructural.")
    else:
        print(f"\n✓ EXERGÍA ABSOLUTA: {exergy_ratio:.4f}% — Resiliencia termodinámica confirmada C5-REAL.")

    # Cleanup
    for p in [db_path, mesh_db]:
        if os.path.exists(p):
            os.remove(p)
        for suffix in ["-wal", "-shm"]:
            wal_p = p + suffix
            if os.path.exists(wal_p):
                os.remove(wal_p)

if __name__ == "__main__":
    asyncio.run(main())
