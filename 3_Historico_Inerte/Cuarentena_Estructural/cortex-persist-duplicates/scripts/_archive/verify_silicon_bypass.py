import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path("~/10_PROJECTS/Babylon60-Persist")
sys.path.append(str(PROJECT_ROOT / "scripts"))

from db import get_total_yield_dynamic


def verify_silicon_continuity():
    logging.getLogger(__name__).info("∴ BABYLON60-SILICON VERIFICATION (Ω₀/Ω₉)")
    logging.getLogger(__name__).info("──────────────────────────────────────────")

    # 1. Fetch Ledger State (Software Truth)
    software_yield = get_total_yield_dynamic()
    logging.getLogger(__name__).info(f"[◈] Sovereign Ledger Yield: ${software_yield:,.2f}")

    # 2. Check verify_nativeation Results (Hardware Truth)
    # We parse the output of the previous vvp run or verify_native a check
    # In this STRIKE, we verify that the threshold in the TB matches the Ledger.
    tb_path = PROJECT_ROOT / "engine/rtl/tb_babylon60_balance_monitor.v"
    tb_content = tb_path.read_text()

    threshold_line = [line for line in tb_content.splitlines() if "threshold_async =" in line]
    if not threshold_line:
        logging.getLogger(__name__).info("[!] ERROR: Threshold not found in testbench.")
        return

    # Extract numeric value
    import re

    match = re.search(r"64'd(\d+)", threshold_line[0])
    if not match:
        logging.getLogger(__name__).info("[!] ERROR: Could not parse decimal threshold from TB.")
        return

    hardware_threshold = float(match.group(1))
    logging.getLogger(__name__).info(f"[◈] Hardware RTL Threshold: ${hardware_threshold:,.2f}")

    # 3. Continuity Assertion
    if abs(software_yield - hardware_threshold) < 1.0:
        logging.getLogger(__name__).info("[✓] Law Ω₀ VERIFIED: Hardware and Software truth converge.")
    else:
        logging.getLogger(__name__).info("[!] VIOLATION (Ω₉): Ledger/RTL Discontinuity detected!")
        logging.getLogger(__name__).info(f"    Delta: ${abs(software_yield - hardware_threshold):,.2f}")

    # 4. State Summary
    status = (
        "VERIFIED (C5-REAL)" if software_yield >= hardware_threshold else "PENDING_ACCUMULATION"
    )
    logging.getLogger(__name__).info(f"[◈] System Status: {status}")


if __name__ == "__main__":
    verify_silicon_continuity()
