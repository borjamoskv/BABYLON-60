"""
BABYLON-60 Enterprise License Management CLI (cortex-license)
Generates and verifies HMAC-SHA256 authenticated commercial license keys for BABYLON-60.
"""

import sys
import os
import argparse
import time
from babylon60.guards.license_sovereign_validator import (
    generate_license_key,
    verify_license_key,
    LicenseStatus
)


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Enterprise License Manager")
    subparsers = parser.add_subparsers(dest="command", help="Comandos de licencia")

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Generar una clave BABYLON60_LICENSE_KEY")
    gen_parser.add_argument("--owner", required=True, help="Nombre del cliente o entidad propietaria")
    gen_parser.add_argument("--tier", default="enterprise", choices=["pro", "enterprise"], help="Nivel de licencia")
    gen_parser.add_argument("--days", type=int, default=365, help="Días de validez")
    gen_parser.add_argument("--salt", help="Secret salt HMAC (o via env BABYLON60_LICENSE_SALT)")

    # Command: verify
    ver_parser = subparsers.add_parser("verify", help="Verificar una clave BABYLON60_LICENSE_KEY")
    ver_parser.add_argument("--key", help="Clave de licencia a verificar (o via env BABYLON60_LICENSE_KEY / BABYLON60_LICENSE_KEY)")
    ver_parser.add_argument("--salt", help="Secret salt HMAC (o via env BABYLON60_LICENSE_SALT)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.salt:
        os.environ["BABYLON60_LICENSE_SALT"] = args.salt
    elif "BABYLON60_LICENSE_SALT" not in os.environ:
        os.environ["BABYLON60_LICENSE_SALT"] = "default_sovereign_hardened_salt_2026"

    if args.command == "generate":
        expires_at = int(time.time()) + (args.days * 86400)
        key = generate_license_key(owner=args.owner, tier=args.tier, expires_at=expires_at)
        print("==================================================")
        print("BABYLON60_LICENSE_KEY GENERATED SUCCESSFULLY")
        print("==================================================")
        print(f"Owner:      {args.owner}")
        print(f"Tier:       {args.tier.upper()}")
        print(f"Expires At: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(expires_at))}")
        print("--------------------------------------------------")
        print(f"KEY: {key}")
        print("==================================================")

    elif args.command == "verify":
        key_to_check = args.key or os.getenv("BABYLON60_LICENSE_KEY") or os.getenv("BABYLON_LICENSE_KEY") or os.getenv("BABYLON60_LICENSE_KEY")
        status: LicenseStatus = verify_license_key(key=key_to_check)
        
        print("==================================================")
        print(f"LICENSE STATUS: {'VALID' if status.is_valid else 'INVALID'}")
        print("==================================================")
        print(f"Tier:     {status.tier}")
        print(f"Owner:    {status.owner}")
        print(f"Message:  {status.message}")
        if status.expires_at > 0:
            print(f"Expires:  {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(status.expires_at))}")
        print("==================================================")
        
        sys.exit(0 if status.is_valid else 1)


if __name__ == "__main__":
    main()
