# [C5-REAL] Exergy-Maximized
"""
BABYLONMAIL CLI & SUBAGENT INTERFACE
====================================
Interfaz CLI de alta exergía para enviar, recibir y auditar correos
soberanos bajo el dominio @babylon60.com.

Integrado con CortexPersistLedger y firma Ed25519.

Authorship: Borja Moskv (borjamoskv)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

MAIL_DIR = Path.home() / ".babylon60" / "babylonmail"
MAIL_DB_PATH = MAIL_DIR / "mail_ledger.db"

def get_ledger() -> CortexPersistLedger:
    return CortexPersistLedger(MAIL_DB_PATH)

def cmd_status():
    account_file = MAIL_DIR / "account.json"
    if not account_file.exists():
        user = os.environ.get("USER", "borja")
        profile = {
            "email": f"{user}@babylon60.com",
            "username": user,
            "domain": "babylon60.com",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "key_fingerprint": "ed25519:7536b90af4baa146ac60d719982be602081bd18d",
            "is_active": True
        }
        MAIL_DIR.mkdir(parents=True, exist_ok=True)
        with open(account_file, "w") as f:
            json.dump(profile, f, indent=2)
    else:
        with open(account_file, "r") as f:
            profile = json.load(f)

    ledger = get_ledger()
    attestation = ledger.get_state_attestation()

    print("\n" + "="*50)
    print("📧 BABYLONMAIL SOBERANO (@babylon60.com)")
    print("="*50)
    print(f"Cuenta Actual  : {profile.get('email')}")
    print(f"Estado DB      : 🟢 {MAIL_DB_PATH}")
    print(f"Total Correos  : {attestation['total_entries']}")
    print(f"Merkle Root    : {attestation['merkle_root'][:16]}...")
    print(f"Firma Keypair  : {profile.get('key_fingerprint')}")
    print("="*50 + "\n")

def cmd_send(to: str, subject: str, body: str):
    ledger = get_ledger()
    account_file = MAIL_DIR / "account.json"
    user = os.environ.get("USER", "borja")
    from_email = f"{user}@babylon60.com"

    payload = {
        "from": from_email,
        "to": to,
        "subject": subject,
        "body": body,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    event = CortexEvent(
        event_type="BABYLON_MAIL_SENT",
        payload=payload,
        cortex_taint=f"{user}:babylon_mail_cli:send"
    )

    ack = ledger.append_event(event)
    print(f"🟢 [SENT] Correo enviado a {to} | BFT Seq: {ack['seq']} | Hash: {ack['entry_hash'][:12]}...")

def cmd_list():
    ledger = get_ledger()
    with ledger._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT seq, payload_json, timestamp FROM cortex_ledger WHERE event_type = 'BABYLON_MAIL_SENT' ORDER BY seq DESC")
        rows = cursor.fetchall()

    print(f"\n📥 BANDEJA DE CORREO (@babylon60.com) — {len(rows)} mensajes\n" + "-"*60)
    for seq, payload_json, ts in rows:
        data = json.loads(payload_json)
        print(f"[{seq:04d}] {ts[:19]} | DE: {data.get('from')} -> PARA: {data.get('to')}")
        print(f"       Asunto: {data.get('subject')}")
        print("-" * 60)

def main():
    parser = argparse.ArgumentParser(description="BabylonMail Sovereign CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Ver estado de cuenta e inmutabilidad")
    subparsers.add_parser("list", help="Listar correos soberanos")

    send_p = subparsers.add_parser("send", help="Enviar correo soberano")
    send_p.add_argument("--to", required=True, help="Destinatario @babylon60.com")
    send_p.add_argument("--subject", required=True, help="Asunto")
    send_p.add_argument("--body", required=True, help="Cuerpo del correo")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "send":
        cmd_send(args.to, args.subject, args.body)
    elif args.command == "list":
        cmd_list()
    else:
        cmd_status()

if __name__ == "__main__":
    main()
