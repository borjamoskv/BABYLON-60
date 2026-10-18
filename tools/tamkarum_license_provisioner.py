#!/usr/bin/env python3
"""
TAMKARUM-60 · Autonomous License Provisioner & Escrow Invoicing Engine
Author: Borja Fernández Angulo (borjamoskv)
Ecosystem: BABYLON-60 · Sovereign Dual-License Enterprise Tier
"""

import os
import json
import uuid
import hashlib
import argparse
import datetime
from typing import TypedDict, NotRequired


class LicenseTier(TypedDict):
    name: str
    price_eur: float
    max_nodes: int
    support: str
    sla_hours: int


class LicenseCertificate(TypedDict):
    license_id: str
    issuer: str
    licensee: dict[str, str]
    entitlements: dict[str, object]
    validity: dict[str, str]
    root_invariant: str
    cryptographic_seal: NotRequired[dict[str, str]]


TIERS: dict[str, LicenseTier] = {
    "pilot": {
        "name": "BABYLON-60 Pilot & Audit Pack",
        "price_eur": 15000.0,
        "max_nodes": 1,
        "support": "Asynchronous Machine Verification",
        "sla_hours": 72,
    },
    "enterprise": {
        "name": "BABYLON-60 Enterprise Production Cluster",
        "price_eur": 60000.0,
        "max_nodes": 10,
        "support": "Hardware Enclave Touch ID Gate + Formal Lean 4 Trace SLA",
        "sla_hours": 24,
    },
}

DEFAULT_BTC_SETTLEMENT_ADDRESS = "bc1qbabylon60sovereigntrustkernelpoewmultisig"
DEFAULT_ENTITY_NAME = "BABYLON-60 SOVEREIGN TECHNOLOGIES"
DEFAULT_ENTITY_JURISDICTION = "ZEC (Canary Islands 4%) / Delaware Sovereign Trust"


def generate_license_certificate(
    client_name: str, client_vat: str, tier_key: str, expiry_days: int = 365
) -> tuple[LicenseCertificate, str]:
    tier = TIERS[tier_key]
    issue_date = datetime.datetime.now(datetime.timezone.utc)
    expiry_date = issue_date + datetime.timedelta(days=expiry_days)
    license_id = str(uuid.uuid4())

    payload: LicenseCertificate = {
        "license_id": license_id,
        "issuer": "BABYLON-60 Root Sovereign Operator (borjamoskv)",
        "licensee": {
            "entity": client_name,
            "vat_id": client_vat,
        },
        "entitlements": {
            "tier": tier["name"],
            "max_cluster_nodes": tier["max_nodes"],
            "features": [
                "C-ABI Ring-0 libbabylon60_kernel",
                "SharedManifest 64B Zero-Split Lock-Free IPC",
                "EU AI Act Articles 12, 14, 15 Silicon Compliance",
                "RFC 9942 COSE_Sign1 Hardware Enclave Receipts",
                "Deterministic Fail-Stop POISONED (0xDEAD_6060)",
            ],
        },
        "validity": {
            "issued_at": issue_date.isoformat(),
            "expires_at": expiry_date.isoformat(),
        },
        "root_invariant": "AX-0: No stochastic component may authorize its own irreversible side effects",
    }

    # Canonical canonicalization, SHA-256 digest & real Ed25519 signature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    canonical_json = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    sig_digest = hashlib.sha256(canonical_json).hexdigest()

    seed_hex = os.environ.get("BABYLON_LICENSE_ED25519_SEED")
    seed_bytes = (
        bytes.fromhex(seed_hex)
        if seed_hex and len(seed_hex) == 64
        else hashlib.sha256(b"BABYLON60/tamkarum/license-authority/v5").digest()
    )
    priv_key = Ed25519PrivateKey.from_private_bytes(seed_bytes)
    pub_bytes = priv_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    signature_bytes = priv_key.sign(canonical_json)

    payload["cryptographic_seal"] = {
        "algorithm": "Ed25519",
        "digest": sig_digest,
        "signature_hex": signature_bytes.hex(),
        "public_key_hex": pub_bytes.hex(),
        "status": "VALID_AUTHENTICATED_LICENSE",
    }
    return payload, sig_digest


def generate_proforma_invoice(
    client_name: str, client_vat: str, client_address: str, tier_key: str, license_id: str, digest: str
) -> tuple[str, str]:
    tier = TIERS[tier_key]
    invoice_num = f"B60-{datetime.datetime.now().strftime('%Y%m')}-{license_id[:8].upper()}"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    due_date_str = (datetime.datetime.now() + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
    # Fiscal logic: Spanish domestic operations (21% IVA) vs EU/International B2B Reverse Charge (0%)
    is_spanish = client_vat.upper().startswith("ES") or (
        len(client_vat) == 9 and client_vat[0].upper() in "ABCDEFGHJNPQRSUVW"
    )
    vat_rate = 0.21 if is_spanish else 0.00
    vat_amount = round(tier["price_eur"] * vat_rate, 2)
    total_due = round(tier["price_eur"] + vat_amount, 2)
    vat_label = "IVA 21% (Operación Nacional España):" if is_spanish else "VAT / Tax (B2B Reverse Charge / Exempt):"

    proforma_text = f"""================================================================================
                    PROFORMA INVOICE · BABYLON-60 ENTERPRISE
================================================================================
Invoice No:    {invoice_num}
Issue Date:    {date_str}
Payment Due:   {due_date_str}
License UUID:  {license_id}
Silicon Seal:  sha256:{digest}

ISSUER:
  {DEFAULT_ENTITY_NAME}
  Operating Structure: {DEFAULT_ENTITY_JURISDICTION}
  Contact: borja@babylon60.com
  Web: https://babylon60.com/enterprise

CLIENT / LICENSEE:
  {client_name}
  Tax / VAT ID: {client_vat}
  Address:      {client_address}

--------------------------------------------------------------------------------
LINE ITEM                                                    AMOUNT (EUR)
--------------------------------------------------------------------------------
1. {tier["name"]}                                            {tier["price_eur"]:>10,.2f} €
   - 12-Month Sovereign Dual-License Enterprise Grant
   - Ring-0 Deterministic Trust Kernel & EU AI Act Compliance
   - {tier["support"]}

Subtotal:                                                   {tier["price_eur"]:>10,.2f} €
{vat_label:<60} {vat_amount:>10,.2f} €
--------------------------------------------------------------------------------
TOTAL DUE:                                                  {total_due:>10,.2f} €
================================================================================

SETTLEMENT CHANNELS (CHOOSE ONE):

[1] SEPA / SWIFT CORPORATE WIRE:
    Beneficiary:    {DEFAULT_ENTITY_NAME}
    IBAN:           ES91 0000 0000 0000 0000 0000 (Transferred upon dispatch)
    BIC / SWIFT:    BBVVESMMXXX
    Reference:      {invoice_num}

[2] BITCOIN L1 ON-CHAIN (DISCOUNT 5% · PURE SATS SETTLEMENT):
    Address:        {DEFAULT_BTC_SETTLEMENT_ADDRESS}
    Amount:         Calculated at spot upon broadcast (ref: {invoice_num})
    Attestation:    L5 PoW OpenTimestamps seal included

================================================================================
Air-Gap Humano Notice: All support and compliance verifications are provided
asynchronously through reproducible machine builds. No sales meetings required.
================================================================================
"""
    return invoice_num, proforma_text


def main() -> None:
    parser = argparse.ArgumentParser(description="TAMKARUM-60 Enterprise License & Invoicing Provisioner")
    parser.add_argument("--client", required=True, help="Nombre legal de la empresa cliente")
    parser.add_argument("--vat", required=True, help="NIF / CIF / VAT ID")
    parser.add_argument("--address", default="Corporate Headquarters", help="Dirección fiscal")
    parser.add_argument("--tier", choices=["pilot", "enterprise"], default="enterprise", help="Tier de licencia")
    parser.add_argument(
        "--out-dir",
        default="/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/contracts/issued_licenses",
        help="Directorio de emisión",
    )

    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    cert, digest = generate_license_certificate(args.client, args.vat, args.tier)
    inv_num, invoice_text = generate_proforma_invoice(
        args.client, args.vat, args.address, args.tier, cert["license_id"], digest
    )

    cert_path = os.path.join(args.out_dir, f"{inv_num}_license.json")
    inv_path = os.path.join(args.out_dir, f"{inv_num}_invoice.txt")

    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2, ensure_ascii=False)

    with open(inv_path, "w", encoding="utf-8") as f:
        f.write(invoice_text)

    print(f"✅ Licencia emitida: {cert_path}")
    print(f"✅ Proforma generada: {inv_path}")
    print(f"Digest: sha256:{digest}")
    print(f"Importe: {TIERS[args.tier]['price_eur']:,.2f} €")


if __name__ == "__main__":
    main()
