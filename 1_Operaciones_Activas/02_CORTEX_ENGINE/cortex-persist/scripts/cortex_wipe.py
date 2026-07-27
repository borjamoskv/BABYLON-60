# [C5-REAL] Exergy-Maximized
"""
cat_id: cortex-wipe
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


import logging


import argparse
import json
import os
import subprocess
import sys


def get_device_info(device_path):
    """
    Queries sysfs to check if the target disk is rotational or solid-state.
    """
    device_name = os.path.basename(device_path)
    # Target path in sysfs for rotational status
    sys_path = f"/sys/class/block/{device_name}/queue/rotational"
    if not os.path.exists(sys_path):
        # Check if parent device path works
        parent_name = "".join([c for c in device_name if not c.isdigit()])
        sys_path = f"/sys/class/block/{parent_name}/queue/rotational"
        if not os.path.exists(sys_path):
            raise FileNotFoundError(f"Cannot determine physical properties for: {device_path}")

    with open(sys_path) as f:
        is_rotational = f.read().strip() == "1"

    return {
        "device": device_path,
        "rotational": is_rotational,
        "type": "HDD (Rotational)" if is_rotational else "SSD (Solid-State/NAND)",
    }


def execute_command(cmd, dry_run=True):
    logging.getLogger(__name__).info(f"Executing: {' '.join(cmd)}")
    if dry_run:
        logging.getLogger(__name__).info("[DRY-RUN] Command simulated successfully.")
        return 0

    try:
        res = subprocess.run(cmd, check=True, capture_output=True)
        logging.getLogger(__name__).info(res.stdout.decode())
        return res.returncode
    except subprocess.CalledProcessError as e:
        logging.getLogger(__name__).info(f"Error during execution: {e.stderr.decode()}", file=sys.stderr)
        return e.returncode


def main():
    parser = argparse.ArgumentParser(description="cortex_wipe.py: Hardware-Aware Sanitization Tool")
    parser.add_argument("device", help="Target block device (e.g., /dev/sdb or /dev/nvme0n1)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate commands without writing (default: True)",
    )
    parser.add_argument(
        "--force-execute",
        action="store_false",
        dest="dry_run",
        help="Disable dry-run and commit changes to disk",
    )

    args = parser.parse_args()

    if os.geteuid() != 0:
        logging.getLogger(__name__).info("CRITICAL: Root permissions required.", file=sys.stderr)
        sys.exit(1)

    try:
        info = get_device_info(args.device)
        logging.getLogger(__name__).info(json.dumps(info, indent=2))
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info(f"Error reading device parameters: {e}", file=sys.stderr)
        sys.exit(1)

    logging.getLogger(__name__).info("\n--- SANITIZATION STRATEGY ---")
    if not info["rotational"]:
        logging.getLogger(__name__).info(
            "Device is SSD. Traditional multi-pass logical wipe is forbidden (Write Amplification / Ineffective FTL bypass)."
        )
        if "nvme" in args.device:
            logging.getLogger(__name__).info("Selected: NVMe Cryptographic/Format Erase")
            # Format NVMe with user-data erase (ses=1: User Data Erase, ses=2: Cryptographic Erase)
            cmd = ["nvme", "format", args.device, "--namespace-id=1", "--ses=1"]
        else:
            logging.getLogger(__name__).info("Selected: ATA Secure Erase via hdparm")
            logging.getLogger(__name__).info("Ensure device is not FROZEN. (Check: hdparm -I /dev/device)")
            cmd = ["hdparm", "--user-master", "u", "--security-erase", "NULL", args.device]
    else:
        logging.getLogger(__name__).info("Device is HDD. Executing zeroing with random pass fallback.")
        cmd = [
            "dd",
            "if=/dev/urandom",
            f"of={args.device}",
            "bs=4M",
            "status=progress",
            "conv=fdatasync",
        ]

    logging.getLogger(__name__).info("")
    execute_command(cmd, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
