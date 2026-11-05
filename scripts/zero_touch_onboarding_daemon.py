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

HTTP mode requires BABYLON_ONBOARDING_SESSION_TOKEN (32 random bytes, hex).
GET /api/v1/health supplies the public session_id. Clients use
order_request_headers(token, session_id, host, body) to authenticate the exact
POST bytes. Each MAC expires after 60 seconds and its nonce is consumed once.
The token authenticates the caller; it is not hardware biometric attestation.
"""

import sys
import os
import json
import time
import datetime
import argparse
import re
import secrets
import threading
from collections.abc import Mapping
from http.client import HTTPMessage
from typing import TypedDict
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

from blake3 import blake3

REPO_ROOT = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

try:
    from tamkarum_license_provisioner import (
        generate_license_certificate,
        generate_proforma_invoice,
        DEFAULT_SETTLEMENT_IBAN,
        DEFAULT_SETTLEMENT_BIC,
    )
except ImportError:
    # Fallback if executed standalone
    from tools.tamkarum_license_provisioner import (
        generate_license_certificate,
        generate_proforma_invoice,
        DEFAULT_SETTLEMENT_IBAN,
        DEFAULT_SETTLEMENT_BIC,
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
ORDER_PATH = "/api/v1/onboard-pilot"
REQUEST_TTL_SECONDS = 60
MAX_BODY_BYTES = 1024 * 1024


def _session_key(token: str) -> bytes:
    if not re.fullmatch(r"[0-9a-fA-F]{64}", token) or token == "00" * 32:
        raise ValueError("BABYLON_ONBOARDING_SESSION_TOKEN must contain 32 random bytes encoded as hex")
    return bytes.fromhex(token)


def _order_mac(key: bytes, session: str, host: str, timestamp: str, nonce: str, body: bytes) -> str:
    context = json.dumps(
        ["babylon60-onboarding-v1", "POST", ORDER_PATH, host, session, timestamp, nonce],
        separators=(",", ":"),
    ).encode("utf-8")
    return blake3(context + b"\x00" + body, key=key).hexdigest()


def order_request_headers(
    token: str, session_id: str, host: str, body: bytes, *, timestamp: int | None = None, nonce: str | None = None
) -> dict[str, str]:
    """Client helper: sign the exact UTF-8 JSON bytes; never transmit the token."""
    stamp = str(int(time.time()) if timestamp is None else timestamp)
    request_nonce = secrets.token_hex(16) if nonce is None else nonce
    mac = _order_mac(_session_key(token), session_id, host, stamp, request_nonce, body)
    return {
        "Host": host,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "X-Babylon-Session": session_id,
        "X-Babylon-Timestamp": stamp,
        "X-Babylon-Nonce": request_nonce,
        "Authorization": f"BLAKE3 {mac}",
    }


def _one_header(headers: HTTPMessage, name: str) -> str:
    values = headers.get_all(name, [])
    if len(values) != 1:
        raise ValueError("Missing or repeated request header")
    return values[0]


class OnboardingSession:
    """Per-process request authority; a new public session invalidates old MACs."""

    def __init__(self, key: bytes) -> None:
        if len(key) != 32 or key == bytes(32):
            raise ValueError("Invalid onboarding session key")
        self._key = key
        self.session_id = secrets.token_hex(16)
        self._consumed: dict[str, int] = {}
        self._lock = threading.Lock()

    def consume(self, headers: HTTPMessage, host: str, body: bytes) -> None:
        session = _one_header(headers, "X-Babylon-Session")
        stamp = _one_header(headers, "X-Babylon-Timestamp")
        nonce = _one_header(headers, "X-Babylon-Nonce")
        authorization = _one_header(headers, "Authorization")
        if not re.fullmatch(r"BLAKE3 [0-9a-f]{64}", authorization):
            raise ValueError("Invalid request authorization")
        if session != self.session_id or not re.fullmatch(r"[0-9a-f]{32}", nonce):
            raise ValueError("Invalid request authorization")
        if not re.fullmatch(r"[0-9]{1,12}", stamp):
            raise ValueError("Invalid request authorization")
        now = int(time.time())
        issued_at = int(stamp)
        if not 0 <= now - issued_at <= REQUEST_TTL_SECONDS:
            raise ValueError("Expired request authorization")
        expected = "BLAKE3 " + _order_mac(self._key, session, host, stamp, nonce, body)
        if not secrets.compare_digest(expected, authorization):
            raise ValueError("Invalid request authorization")
        with self._lock:
            self._consumed = {value: expiry for value, expiry in self._consumed.items() if expiry >= now}
            if nonce in self._consumed or len(self._consumed) >= 4096:
                raise ValueError("Request authorization already consumed or capacity reached")
            # Consume before provisioning. Failed/unknown effects cannot be replayed.
            self._consumed[nonce] = issued_at + REQUEST_TTL_SECONDS


class OnboardingHTTPServer(HTTPServer):
    def __init__(self, port: int, key: bytes) -> None:
        self.authorization = OnboardingSession(key)
        super().__init__(("127.0.0.1", port), ZeroTouchHttpHandler)
        self.expected_host = f"127.0.0.1:{self.server_address[1]}"


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
                "sepa_swift_wire": f"{DEFAULT_SETTLEMENT_IBAN} (BIC: {DEFAULT_SETTLEMENT_BIC})",
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
    def setup(self) -> None:
        self.request.settimeout(5)
        super().setup()

    def _json_response(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _request_context(self) -> tuple[OnboardingSession, str]:
        authority = getattr(self.server, "authorization", None)
        host = getattr(self.server, "expected_host", None)
        if not isinstance(authority, OnboardingSession) or not isinstance(host, str):
            raise ValueError("Onboarding service has no request authority")
        if _one_header(self.headers, "Host") != host:
            raise ValueError("Invalid request host")
        origins = self.headers.get_all("Origin", [])
        if origins and origins != [f"http://{host}"]:
            raise ValueError("Invalid request origin")
        if self.headers.get_all("Transfer-Encoding", []):
            raise ValueError("Unsupported request transfer encoding")
        return authority, host

    def do_GET(self) -> None:
        try:
            authority, _ = self._request_context()
        except ValueError:
            self._json_response(403, {"error": "Request rejected"})
            return
        if self.path == "/api/v1/health":
            self._json_response(200, {
                "status": "HEALTHY", "engine": "TAMKARUM-60", "session_id": authority.session_id,
                "request_ttl_seconds": REQUEST_TTL_SECONDS,
            })
        else:
            self._json_response(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != ORDER_PATH:
            self._json_response(404, {"error": "Not found"})
            return
        try:
            authority, host = self._request_context()
            if _one_header(self.headers, "Content-Type").lower() not in {
                "application/json", "application/json; charset=utf-8",
            }:
                raise ValueError("Unsupported content type")
            length_text = _one_header(self.headers, "Content-Length")
            if not re.fullmatch(r"[0-9]{1,7}", length_text):
                raise ValueError("Invalid request length")
            content_length = int(length_text)
            if not 0 < content_length <= MAX_BODY_BYTES:
                raise ValueError("Invalid request length")
            post_data = self.rfile.read(content_length)
            if len(post_data) != content_length:
                raise ValueError("Incomplete request body")
            authority.consume(self.headers, host, post_data)
            payload = json.loads(post_data.decode("utf-8"))
            allowed_fields = {"client_name", "client_vat", "client_email", "client_address", "host_os", "tier"}
            if (
                not isinstance(payload, dict)
                or set(payload) - allowed_fields
                or any(not isinstance(value, str) for value in payload.values())
                or not payload.get("client_name", "").strip()
                or not payload.get("client_vat", "").strip()
                or payload.get("tier", "pilot") not in {"pilot", "enterprise"}
            ):
                raise ValueError("Invalid order schema")
        except (ValueError, UnicodeDecodeError, TimeoutError, OSError):
            self._json_response(403, {"error": "Request rejected"})
            return
        try:
            receipt = process_zero_touch_pilot_order(payload)
        except Exception:
            self._json_response(500, {"error": "Provisioning failed; request authorization consumed"})
            return
        self._json_response(200, receipt)


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Zero-Touch Onboarding Daemon")
    parser.add_argument("--client", help="Legal Entity Name")
    parser.add_argument("--vat", help="Tax ID / CIF / VAT")
    parser.add_argument("--email", default="ciso@client.com", help="CISO contact email")
    parser.add_argument("--address", default="Corporate Headquarters", help="Fiscal Address")
    parser.add_argument("--tier", default="pilot", choices=["pilot", "enterprise"])
    parser.add_argument(
        "--serve", action="store_true",
        help="Start authenticated loopback HTTP service; requires BABYLON_ONBOARDING_SESSION_TOKEN (64 hex chars)",
    )
    parser.add_argument("--port", type=int, default=8060, help="Port for HTTP daemon")
    args = parser.parse_args()

    if args.serve:
        try:
            key = _session_key(os.environ.get("BABYLON_ONBOARDING_SESSION_TOKEN", ""))
        except ValueError as exc:
            parser.error(str(exc))
        httpd = OnboardingHTTPServer(args.port, key)
        print(f"🚀 BABYLON-60 Zero-Touch Daemon corriendo en http://127.0.0.1:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Daemon detenido por el operador.")
        finally:
            httpd.server_close()
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
