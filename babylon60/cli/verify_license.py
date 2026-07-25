"""
BABYLON-60 OFFLINE LICENSE VERIFIER SCRIPT (C5-REAL)
===================================================
Embeddable zero-dependency CLI script for validating B60 license keys inside Docker containers and CI runners.
"""

import sys
from babylon60.core.license_gate import SovereignLicenseGate

def verify_offline_key(key_str: str) -> bool:
    """Verify license key authenticity offline without network overhead."""
    gate = SovereignLicenseGate()
    verified = gate.verify_license_key(key_str)
    if verified:
        print(f"[+] VALID LICENSE: Owner='{verified['owner']}', Tier='{verified['tier']}', Expires={verified['expires_at']}")
        return True
    else:
        print("[-] INVALID LICENSE: Signature tampered, key corrupted, or expired.")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m babylon60.cli.verify_license <SOVEREIGN_LICENSE_KEY>")
        sys.exit(1)
    
    key_str = sys.argv[1]
    is_valid = verify_offline_key(key_str)
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
