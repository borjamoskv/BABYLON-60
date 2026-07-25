import asyncio
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path.home() / ".babylon60/exergy_agent_ledger.db"


@dataclass
class SwarmMetrics:
    successes: int = 0
    failures: int = 0
    deadlocks: int = 0


def _write_swarm_node_record(agent_id: int) -> str:
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        timestamp = int(time.time() * 1000)
        commit_hash = f"swarm_mitosis_{agent_id:03d}"
        exergy_score = 1000.0
        verdict_yaml = f"Agent {agent_id} achieved convergence."
        prov_hash = str(uuid.uuid5(uuid.NAMESPACE_OID, f"agent_{agent_id}_{time.time()}"))
        cursor.execute(
            "\n            INSERT INTO ledger (timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml, prov_hash)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ",
            (
                timestamp,
                commit_hash,
                exergy_score,
                "Swarm Gradient",
                "Zero Entropy",
                "Max Leverage",
                "AutoLoop 100",
                "None",
                verdict_yaml,
                prov_hash,
            ),
        )
        conn.commit()
        conn.close()
        return "SUCCESS"
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower() or "busy" in str(e).lower():
            return f"DEADLOCK: {e}"
        return f"FAILED: {e}"
    except (OSError, RuntimeError, ValueError) as e:
        return f"FATAL: {e}"


async def bft_agent_task(agent_id: int, metrics: SwarmMetrics) -> None:
    await asyncio.sleep(0.01 * (agent_id % 10))
    res = await asyncio.to_thread(_write_swarm_node_record, agent_id)
    if res == "SUCCESS":
        metrics.successes += 1
    elif res.startswith("DEADLOCK"):
        metrics.deadlocks += 1
    else:
        metrics.failures += 1


async def main() -> None:
    print("🔋 Igniting BFT Swarm Mitosis: 100 Concurrent Agents...")
    if not DB_PATH.exists():
        print("❌ Ledger DB does not exist. Run exergy optimizer first.")
        return
    metrics = SwarmMetrics()
    tasks = []
    for i in range(1, 101):
        tasks.append(asyncio.create_task(bft_agent_task(i, metrics)))
    await asyncio.gather(*tasks)
    print("\n# SWARM COLLAPSE METRICS")
    print("Total Agents : 100")
    print(f"Successes    : {metrics.successes}")
    print(f"Deadlocks    : {metrics.deadlocks} (SQLite WAL contention)")
    print(f"Other Errors : {metrics.failures}")
    if metrics.successes == 100:
        print("\n✅ INV_BFT_02 VERIFIED: SQLite WAL busy_timeout survived 100 concurrent writers.")
        exit(0)
    else:
        print("\n❌ SWARM FAILED: Thermodynamical necrosis detected.")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
