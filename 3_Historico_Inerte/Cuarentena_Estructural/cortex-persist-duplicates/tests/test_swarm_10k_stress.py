# [C5-REAL] Exergy-Maximized
import logging
import asyncio
import shutil
import time
from pathlib import Path

from babylon60.swarm.swarm_10k import SwarmCommander


async def run_10k_stress():
    """Execute 10k agents stress test with parallel dispatch."""
    logging.getLogger(__name__).info("🚀 INITIALIZING LEGION-10k STRESS TEST (Zero-Noise Mandate)")

    # Path for test shards
    test_bus_dir = Path("/tmp/cortex_10k_stress")
    if test_bus_dir.exists():
        shutil.rmtree(test_bus_dir)
    test_bus_dir.mkdir()

    commander = SwarmCommander(bus_path=test_bus_dir)
    import sys

    logging.getLogger(__name__).info(f"DEBUG: SwarmCommander module: {sys.modules['babylon60.swarm.swarm_10k'].__file__}")
    logging.getLogger(__name__).info(f"DEBUG: SwarmCommander class: {SwarmCommander}")
    await commander.initialize()

    logging.getLogger(__name__).info(f"📡 Bus initialized with {commander.bus.num_shards} shards.")

    tasks = []
    # Create 10,000 tasks across 10 regions (Legions)
    for i in range(10000):
        domain = f"domain_{i % 10}"
        tasks.append({"id": i, "domain": domain, "payload": "stress_test_v6"})

    logging.getLogger(__name__).info("🌪️ Dispatching 10,000 tasks in parallel...")

    start_time = time.perf_counter()
    await commander.execute_global_dispatch(tasks, parallel=True)
    total_time = time.perf_counter() - start_time

    logging.getLogger(__name__).info(f"✅ Dispatch complete in {total_time:.4f}s")
    logging.getLogger(__name__).info(f"📊 Average dispatch latency: {(total_time / 10000) * 1000:.4f}ms per agent")

    report = await commander.get_density_report()
    logging.getLogger(__name__).info(f"📈 Density Report: {report}")

    # Verify 10,000 agents
    if report["agents"] != 10000:
        logging.getLogger(__name__).info(f"❌ ERROR: Expected 10,000 agents, found {report['agents']}")
    else:
        logging.getLogger(__name__).info("💎 GRAVITY-WELL STABILITY CONFIRMED: 10k agents crystallized.")

    logging.getLogger(__name__).info(f"Legions at teardown: {len(commander.legions)}")
    await commander.consolidate_and_annihilate()
    if test_bus_dir.exists():
        shutil.rmtree(test_bus_dir)


if __name__ == "__main__":
    try:
        asyncio.run(run_10k_stress())
    except Exception as e:  # noqa: BLE001
        import traceback

        logging.getLogger(__name__).info(f"❌ CRITICAL EXCEPTION IN MAIN: {e}")
        traceback.print_exc()
