#!/usr/bin/env python3
"""
import logging
C5-REAL Thermodynamic Stress Test
Bombardeo asíncrono para validar la tolerancia a fallos bizantinos (BFT)
y la resistencia de SQLite WAL ante la concurrencia masiva (Directiva Ω10).
"""

import asyncio
import sys
import time

try:
    import aiohttp
except ImportError:
    logging.getLogger(__name__).info("[C5-REAL] aiohttp no detectado. Ejecuta: uv pip install aiohttp")
    sys.exit(1)

URL = "http://127.0.0.1:8000/api/v1/sanhedrin/judge"
CONCURRENT_REQUESTS = 50


async def fire_request(session, req_id):
    payload = {
        "data": {"test_id": req_id, "entropy": "high_velocity_bombardment"},
        "taint": f"taint:stress:{time.time()}:{req_id}",
        "stripe_token": f"tok_stress_{req_id}",
    }
    start = time.perf_counter()
    try:
        async with session.post(URL, json=payload, timeout=10) as resp:
            status = resp.status
    except Exception:  # noqa: BLE001
        status = 500
    end = time.perf_counter()
    return req_id, status, end - start


async def main():
    logging.getLogger(__name__).info(
        f"\n[\033[91mIGNICIÓN\033[0m] Lanzando test de estrés termodinámico (N={CONCURRENT_REQUESTS})..."
    )
    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        tasks = [fire_request(session, i) for i in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_time
    success = sum(1 for r in results if r[1] == 200)
    failed = CONCURRENT_REQUESTS - success

    logging.getLogger(__name__).info("\n[\033[94mC5-REAL REPORT\033[0m]")
    logging.getLogger(__name__).info(f"-> Tiempo total de colapso: {total_time:.2f}s")
    logging.getLogger(__name__).info(f"-> Transacciones Exitosas:  {success}/{CONCURRENT_REQUESTS}")
    logging.getLogger(__name__).info(f"-> Fallos (Deadlocks/OOM):  {failed}/{CONCURRENT_REQUESTS}")

    if failed > 0:
        logging.getLogger(__name__).info(
            "\n[\033[93mALERTA\033[0m] Anergía detectada. El motor BFT o SQLite WAL fallaron bajo concurrencia."
        )
    else:
        logging.getLogger(__name__).info(
            "\n[\033[92mEXERGÍA ABSOLUTA\033[0m] Cero deadlocks. La arquitectura resiste el bombardeo asíncrono."
        )


if __name__ == "__main__":
    asyncio.run(main())
