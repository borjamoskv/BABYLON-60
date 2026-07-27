import asyncio
import json
import logging
import sys

from babylon60.extensions.skills.autodidact.actuator import autodidact_pipeline

logging.basicConfig(level=logging.INFO)


async def main():
    target_url = sys.argv[1]
    logging.getLogger(__name__).info(f"Executing AUTODIDACT-Ω on {target_url}...")
    try:
        # 'quick_read' intent should trigger the jina/firecrawl pipeline
        result = await autodidact_pipeline(target_url, intent="quick_read", force=True)
        logging.getLogger(__name__).info("\n=== FINAL RESULT ===")
        logging.getLogger(__name__).info(json.dumps(result, indent=2))
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
