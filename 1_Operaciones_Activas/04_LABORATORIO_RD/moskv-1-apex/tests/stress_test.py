# [C5-REAL] Exergy-Maximized
import asyncio
import time
from moskv_1.event_bus import EventBus, CortexEvent
from moskv_1.memory import MemoryStore
from moskv_1.immunity import ImmuneState

async def run_c5_python_stress_test(num_iterations: int = 500):
    print(f"[STRESS-TEST] Starting Python Core Stress Test: {num_iterations} concurrent iterations...")
    store = MemoryStore()
    bus = EventBus()
    await store.connect()
    await bus.connect()
    
    start_time = time.time()
    
    # Generate high and low entropy events
    events = []
    for i in range(num_iterations):
        if i % 2 == 0:
            # High entropy random text simulation
            content = f"C5-REAL System event metrics iteration {i} containing unique alphanumeric markers: {time.time()}."
        else:
            # Low entropy redundant text
            content = "a" * (50 + (i % 5))
            
        events.append(CortexEvent(
            hash=f"stress_hash_{i}",
            prevHash="prev",
            timestamp=time.time(),
            payload={
                "sourceRegion": f"StressUnit_{i % 5}",
                "content": content
            }
        ))
        
    # Concurrently crystallize all events in the MemoryStore
    print(f"[STRESS-TEST] Injecting {num_iterations} events concurrently into MemoryStore...")
    tasks = [store.crystallize(evt) for evt in events]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    total_nodes = len(store._nodes)
    
    quarantined_nodes = sum(1 for n in store._nodes.values() if n.get("is_quarantined") is True)
    passed_nodes = sum(1 for n in store._nodes.values() if n.get("is_quarantined") is False)
    
    print("\n[STRESS-TEST] Python Core stress test complete.")
    print(f"[STRESS-TEST] Elapsed time: {elapsed:.4f}s")
    print(f"[STRESS-TEST] Total Crystallized Nodes: {total_nodes}")
    print(f"[STRESS-TEST] Quarantined (Low-Entropy/Necrotic): {quarantined_nodes}")
    print(f"[STRESS-TEST] Passed (High-Entropy/Promotable): {passed_nodes}")
    print(f"[STRESS-TEST] Throughput: {num_iterations / elapsed:.2f} ops/sec")
    
    await store.close()
    await bus.close()

if __name__ == "__main__":
    asyncio.run(run_c5_python_stress_test())
