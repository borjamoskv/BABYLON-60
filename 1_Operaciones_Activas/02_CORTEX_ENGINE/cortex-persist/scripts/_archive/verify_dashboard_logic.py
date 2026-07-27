import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path("~/10_PROJECTS/Babylon60-Persist")
sys.path.append(str(PROJECT_ROOT / "scripts"))

from db import get_total_yield_dynamic, query_bridge_responses


def verify_logic():
    logging.getLogger(__name__).info("∴ BABYLON60-DASHBOARD VERIFICATION")
    logging.getLogger(__name__).info("──────────────────────────────────────────")

    # 1. Verify Yield Aggregation
    total = get_total_yield_dynamic()
    logging.getLogger(__name__).info(f"[◈] Dynamic Total Yield: ${total:,.2f}")

    # We expect: 1,000,000 (baseline) + 510,000 (Stellar) + Stargate (if recorded)
    if total >= 1510000.0:
        logging.getLogger(__name__).info("[✓] Yield correctly includes Stellar strike.")
    else:
        logging.getLogger(__name__).info("[!] Warning: Yield aggregation might be missing ledger entries.")

    # 2. Verify Bridge Events
    bridge_events = query_bridge_responses(limit=5)
    logging.getLogger(__name__).info(f"[◈] Bridge Events Found: {len(bridge_events)}")
    for evt in bridge_events:
        logging.getLogger(__name__).info(f"  - {evt['category']} | {evt['content']}")

    if bridge_events:
        logging.getLogger(__name__).info("[✓] Bridge responses synthesized successfully.")
    else:
        logging.getLogger(__name__).info("[!] No bridge responses found. Check directory path.")


if __name__ == "__main__":
    verify_logic()
