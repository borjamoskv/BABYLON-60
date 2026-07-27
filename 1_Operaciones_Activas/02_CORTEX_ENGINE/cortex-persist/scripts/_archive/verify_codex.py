import logging
import argparse
import asyncio
import os
import sys
import time

import httpx
from dotenv import load_dotenv

# Ensure we can import from local babylon60
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from babylon60.async_client import AsyncBabylon60Client

load_dotenv()

# --- Aesthetic Tokens ---
COLOR_ACCENT = "\033[38;2;0;220;180m"  # Cyber Lime/Teal
COLOR_DIM = "\033[38;2;100;100;100m"
COLOR_ERR = "\033[38;2;255;50;50m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


async def verify_codex(host: str, port: int, limit: int):
    api_key = os.environ.get("BABYLON60_API_KEY")
    base_url = f"http://{host}:{port}"

    logging.getLogger(__name__).info(
        f"{COLOR_DIM}┌─{COLOR_RESET} {COLOR_BOLD}CODEX VERIFICATION PROTOCOL{COLOR_RESET} {COLOR_DIM}─────────────────────────{COLOR_RESET}"
    )
    logging.getLogger(__name__).info(f"{COLOR_DIM}│{COLOR_RESET} TARGET : {COLOR_ACCENT}{base_url}{COLOR_RESET}")
    logging.getLogger(__name__).info(f"{COLOR_DIM}│{COLOR_RESET} LIMIT  : {limit} facts")
    logging.getLogger(__name__).info(f"{COLOR_DIM}└──────────────────────────────────────────────────────{COLOR_RESET}")

    start_time = time.perf_counter()
    client = AsyncBabylon60Client(api_token=api_key, base_url=base_url)

    try:
        # Check status
        status_start = time.perf_counter()
        status = await client.status()
        status_ms = (time.perf_counter() - status_start) * 1000
        logging.getLogger(__name__).info(
            f" {COLOR_ACCENT}✦{COLOR_RESET} Neural Link Active (v{status.get('version', 'unknown')}) {COLOR_DIM}[{status_ms:.2f}ms]{COLOR_RESET}"
        )

        # Recall recent facts to verify storage
        logging.getLogger(__name__).info(f" {COLOR_DIM}▸{COLOR_RESET} Scanning memory banks...")
        fetch_start = time.perf_counter()
        results = await client.recall(project="babylon60", limit=limit)
        fetch_ms = (time.perf_counter() - fetch_start) * 1000

        logging.getLogger(__name__).info(
            f" {COLOR_ACCENT}✦{COLOR_RESET} Found {len(results)} active facts {COLOR_DIM}[{fetch_ms:.2f}ms]{COLOR_RESET}"
        )

        for res in results:
            content_preview = res.content[:80].replace("\n", " ").strip()
            logging.getLogger(__name__).info(
                f"   {COLOR_DIM}├─{COLOR_RESET} [{res.fact_type.upper():<10}] {COLOR_DIM}ID:{res.id:<4}{COLOR_RESET} {content_preview}..."
            )

        total_time = (time.perf_counter() - start_time) * 1000
        logging.getLogger(__name__).info(
            f"\n{COLOR_ACCENT}VERIFICATION COMPLETE{COLOR_RESET} {COLOR_DIM}:: Total Latency: {total_time:.2f}ms{COLOR_RESET}"
        )

    except httpx.ConnectError:
        logging.getLogger(__name__).info(
            f"\n{COLOR_ERR}CRITICAL FAILURE{COLOR_RESET}: Could not connect to BABYLON60 daemon at {base_url}"
        )
        logging.getLogger(__name__).info(f"{COLOR_DIM}Ensure the daemon is running (`babylon60 daemon start`).{COLOR_RESET}")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info(f"\n{COLOR_ERR}VERIFICATION FAILED{COLOR_RESET}: {e}")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify BABYLON60 CODEX integrity.")
    parser.add_argument("--host", default="127.0.0.1", help="BABYLON60 daemon host")
    parser.add_argument("--port", type=int, default=8000, help="BABYLON60 daemon port")
    parser.add_argument("--limit", type=int, default=10, help="Number of facts to recall")

    args = parser.parse_args()

    try:
        asyncio.run(verify_codex(host=args.host, port=args.port, limit=args.limit))
    except KeyboardInterrupt:
        logging.getLogger(__name__).info(f"\n{COLOR_DIM}Verification aborted by user.{COLOR_RESET}")
        sys.exit(0)
