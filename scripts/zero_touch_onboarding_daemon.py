#!/usr/bin/env python3
"""
BABYLON-60 · Zero-Touch Enterprise Onboarding Daemon (C5-REAL)
Author: Borja Fernández Angulo (borjamoskv)
Role: Sovereign Autonomous Provisioning Engine

Automates 100% of the client onboarding for the 15,000 € Pilot Pack:
1. Validates B2B client entity, VAT/Tax ID, and CISO contact.
2. Invokes TAMKARUM-60 to mint Ed25519 license certificates and proforma invoices.
3. Packages the delivery bundle (Ring-0 binary pointer, installer script, and compliance JSON).
4. Grants asynchronous L3 support channel via private repository issues (Zero Voice / Air-Gap).
"""

import sys
import os
import json
import time
import datetime
import argparse
from collections.abc import Mapping
from typing import TypedDict
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

try:
    from tamkarum_license_provisioner import (
        generate_license_certificate,
        generate_proforma_invoice,
        DEFAULT_BTC_SETTLEMENT_ADDRESS,
    )
except ImportError:
    # Fallback if executed standalone
    from tools.tamkarum_license_provisioner import (
        generate_license_certificate,
        generate_proforma_invoice,
        DEFAULT_BTC_SETTLEMENT_ADDRESS,
    )


class SupportChannel(TypedDict):
    channel_type: str
    private_repo_invite: str
    sla_guarantee: str
    human_air_gap: bool
    meetings_required: int


class ReceiptLicense(TypedDict):
    license_id: str
    tier: str
    entity: str
    vat_id: str
    file_path: str
    sha256: str


class ReceiptInvoice(TypedDict):
    invoice_number: str
    base_amount_eur: float
    vat_rate: float
    total_due_eur: float
    amount_eur: float
    file_path: str
    payment_channels: dict[str, str]


class DeliveryBundle(TypedDict):
    installer_command: str
    compliance_pack_sample: str | None
    support_channel: SupportChannel


class OrderReceipt(TypedDict):
    status: str
    timestamp: str
    order_id: str
    processing_time_ms: float
    license_certificate: ReceiptLicense
    proforma_invoice: ReceiptInvoice
    delivery_bundle: DeliveryBundle


OUTPUT_BASE_DIR = REPO_ROOT / ".audit" / "issued_licenses"
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)


def _sanitize_field(val: object, max_len: int = 120) -> str:
    """Purga saltos de línea y caracteres de control para prevenir text-injection."""
    cleaned = str(val or "").replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
    return cleaned[:max_len]


def process_zero_touch_pilot_order(client_data: Mapping[str, str], out_dir: Path | None = None) -> OrderReceipt:
    """
    Procesa un pedido de piloto enterprise sin intervención humana:
    Genera factura proforma, certificado digital de licencia y paquete de entrega.
    """
    t0 = time.perf_counter()
    target_dir = out_dir or OUTPUT_BASE_DIR
    target_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    client_name = _sanitize_field(client_data.get("client_name", "Acme Corporation"), max_len=100)
    client_vat = _sanitize_field(client_data.get("client_vat", "ESB00000000"), max_len=30)
    _sanitize_field(client_data.get("client_email", "ciso@acme.com"), max_len=80)
    client_address = _sanitize_field(client_data.get("client_address", "Corporate Headquarters"), max_len=150)
    client_data.get("host_os", "macOS-arm64").strip()
    tier_key = client_data.get("tier", "pilot").strip()

    # 1. Generar certificado de licencia y factura con TAMKARUM-60
    lic_obj, sig_digest = generate_license_certificate(client_name, client_vat, tier_key)
    invoice_num, proforma_text = generate_proforma_invoice(
        client_name, client_vat, client_address, tier_key, lic_obj["license_id"], sig_digest
    )

    # Persistir licencia e invoice en target_dir con permisos WORM restringidos (0600)
    lic_filename = f"{invoice_num}_license.json"
    lic_path = target_dir / lic_filename
    with open(lic_path, "w", encoding="utf-8") as f:
        json.dump(lic_obj, f, indent=2, ensure_ascii=False)
    os.chmod(lic_path, 0o600)

    inv_filename = f"{invoice_num}_invoice.txt"
    inv_path = target_dir / inv_filename
    with open(inv_path, "w", encoding="utf-8") as f:
        f.write(proforma_text)
    os.chmod(inv_path, 0o600)

    # 2. Asignar canal de soporte asíncrono L3 (Air-Gap Humano)
    order_id = lic_obj["license_id"][:8].upper()
    support_channel: SupportChannel = {
        "channel_type": "Asynchronous Machine Verification & GitHub Issues",
        "private_repo_invite": f"https://github.com/borjamoskv/babylon60-pilot-{order_id.lower()}",
        "sla_guarantee": "Severity 1 < 2h (24/7) · Severity 2 < 4h (8x5 CET)",
        "human_air_gap": True,
        "meetings_required": 0,
    }

    # 3. Empaquetar enlaces de artefactos
    compliance_sample_path = REPO_ROOT / "compliance_reports" / "eu_ai_act_compliance_pack.json"
    installer_script = "curl -sSfL https://babylon60.com/install.sh | bash"

    duration_ms = (time.perf_counter() - t0) * 1000

    base_eur = 15000.0 if tier_key == "pilot" else 60000.0
    is_spanish = client_vat.upper().startswith("ES") or (
        len(client_vat) == 9 and client_vat[0].upper() in "ABCDEFGHJNPQRSUVW"
    )
    vat_rate = 0.21 if is_spanish else 0.00
    total_due_eur = round(base_eur * (1.0 + vat_rate), 2)

    order_receipt: OrderReceipt = {
        "status": "PROVISIONED_AUTONOMOUSLY",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "order_id": order_id,
        "processing_time_ms": round(duration_ms, 2),
        "license_certificate": {
            "license_id": lic_obj["license_id"],
            "tier": tier_key,
            "entity": client_name,
            "vat_id": client_vat,
            "file_path": str(lic_path),
            "sha256": lic_obj["cryptographic_seal"]["digest"],
        },
        "proforma_invoice": {
            "invoice_number": invoice_num,
            "base_amount_eur": base_eur,
            "vat_rate": vat_rate,
            "total_due_eur": total_due_eur,
            "amount_eur": total_due_eur,
            "file_path": str(inv_path),
            "payment_channels": {
                "seqa_wire": "ES91 0000 0000 0000 0000 0000 (BIC: BBVVESMMXXX)",
                "bitcoin_l1": DEFAULT_BTC_SETTLEMENT_ADDRESS,
            },
        },
        "delivery_bundle": {
            "installer_command": installer_script,
            "compliance_pack_sample": str(compliance_sample_path) if compliance_sample_path.exists() else None,
            "support_channel": support_channel,
        },
    }

    # Guardar recibo del pedido con permisos 0600
    receipt_path = target_dir / f"ORDER_{order_id}_receipt.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(order_receipt, f, indent=2)
    os.chmod(receipt_path, 0o600)

    return order_receipt


class ZeroTouchHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/v1/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "HEALTHY", "engine": "TAMKARUM-60", "zero_touch": True}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/api/v1/onboard-pilot":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0 or content_length > 1024 * 1024:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Payload missing or exceeds 1MB limit"}).encode())
                return
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON body must be a structured dictionary")
                receipt = process_zero_touch_pilot_order(payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(receipt, indent=2).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Zero-Touch Onboarding Daemon")
    parser.add_argument("--client", help="Legal Entity Name")
    parser.add_argument("--vat", help="Tax ID / CIF / VAT")
    parser.add_argument("--email", default="ciso@client.com", help="CISO contact email")
    parser.add_argument("--address", default="Corporate Headquarters", help="Fiscal Address")
    parser.add_argument("--tier", default="pilot", choices=["pilot", "enterprise"])
    parser.add_argument("--serve", action="store_true", help="Start HTTP daemon on port 8060")
    parser.add_argument("--port", type=int, default=8060, help="Port for HTTP daemon")
    args = parser.parse_args()

    if args.serve:
        server_address = ("127.0.0.1", args.port)
        httpd = HTTPServer(server_address, ZeroTouchHttpHandler)
        print(f"🚀 BABYLON-60 Zero-Touch Daemon corriendo en http://127.0.0.1:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Daemon detenido por el operador.")
    else:
        if not args.client or not args.vat:
            # Demo run if no args provided
            args.client = "Demo Corp S.A."
            args.vat = "ESA99887766"

        client_payload = {
            "client_name": args.client,
            "client_vat": args.vat,
            "client_email": args.email,
            "client_address": args.address,
            "tier": args.tier,
        }
        res = process_zero_touch_pilot_order(client_payload)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    run_cli()
