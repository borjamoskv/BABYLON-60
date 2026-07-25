import asyncio
import time
from pathlib import Path
from typing import Any
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

async def run_benchmark(iterations: int=10000) -> None:
    db_path: Path = Path('benchmark_temp.db')
    if db_path.exists():
        db_path.unlink()
    actor: BFTLedgerActor = BFTLedgerActor(db_path)
    await actor.start()
    print(f'⚡ [C5-REAL] Ignición de Benchmark: {iterations} transacciones WAL')
    start_time: float = time.perf_counter()
    events: list[LedgerEvent] = [LedgerEvent(stream='benchmark', entity_id=str(i), event_type='STRESS_TEST', payload={'iteration': i, 'padding': 'x' * 256}, source_db='bench', source_table='load', source_pk=str(i), cortex_taint=f'benchmark_taint_{i}') for i in range(iterations)]
    futures: list[asyncio.Future[dict[str, Any]]] = [actor.append(event) for event in events]
    results: list[dict[str, Any] | BaseException] = await asyncio.gather(*futures, return_exceptions=True)
    end_time: float = time.perf_counter()
    total_time: float = end_time - start_time
    await actor.stop()
    if db_path.exists():
        db_path.unlink()
    shm: Path = Path('benchmark_temp.db-shm')
    wal: Path = Path('benchmark_temp.db-wal')
    if shm.exists():
        shm.unlink()
    if wal.exists():
        wal.unlink()
    success: int = sum((1 for r in results if not isinstance(r, BaseException)))
    errors: int = len(results) - success
    tps: float = success / total_time
    print('\n--- MOSKV-1 APEX METRICS ---')
    print(f'Total Time : {total_time:.3f} s')
    print(f'Throughput : {tps:.2f} tx/s')
    print(f'Successful : {success}')
    print(f'Failed     : {errors}')
    print('----------------------------\n')

def main() -> None:
    asyncio.run(run_benchmark(1000))
if __name__ == '__main__':
    main()