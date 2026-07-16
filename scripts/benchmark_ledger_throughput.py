import asyncio
import time
from pathlib import Path
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

async def run_benchmark(iterations: int = 10000):
    db_path = Path("benchmark_temp.db")
    if db_path.exists():
        db_path.unlink()
        
    actor = BFTLedgerActor(db_path)
    await actor.start()
    
    print(f"⚡ [C5-REAL] Ignición de Benchmark: {iterations} transacciones WAL")
    
    start_time = time.perf_counter()
    
    # Pre-generar eventos para medir puramente el IO y el BFT Actor
    events = [
        LedgerEvent(
            stream="benchmark",
            entity_id=str(i),
            event_type="STRESS_TEST",
            payload={"iteration": i, "padding": "x" * 256}, # Payload con entropía controlada
            source_db="bench",
            source_table="load",
            source_pk=str(i),
            cortex_taint=f"benchmark_taint_{i}"
        )
        for i in range(iterations)
    ]
    
    # Encolar todo de golpe
    futures = [actor.append(event) for event in events]
    
    # Esperar resolución
    results = await asyncio.gather(*futures, return_exceptions=True)
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    await actor.stop()
    
    # Limpieza
    if db_path.exists():
        db_path.unlink()
    shm = Path("benchmark_temp.db-shm")
    wal = Path("benchmark_temp.db-wal")
    if shm.exists():
        shm.unlink()
    if wal.exists():
        wal.unlink()
    
    # Métricas
    success = sum(1 for r in results if not isinstance(r, BaseException))
    errors = len(results) - success
    tps = success / total_time
    
    print("\n--- MOSKV-1 APEX METRICS ---")
    print(f"Total Time : {total_time:.3f} s")
    print(f"Throughput : {tps:.2f} tx/s")
    print(f"Successful : {success}")
    print(f"Failed     : {errors}")
    print("----------------------------\n")

if __name__ == "__main__":
    asyncio.run(run_benchmark(1000))
