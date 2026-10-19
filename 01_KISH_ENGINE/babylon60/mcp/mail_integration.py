"""Opt-in BabylonMail MCP recording; no SMTP transport or sender authentication.

Importing the base MCP server does not load this module or create a mail ledger.
The existing tool name/event schema are retained for callers that opt in.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger


MAIL_TOOL: dict[str, object] = {
    "name": "bft_send_sovereign_mail",
    "description": (
        "Record a local BabylonMail message under a @babylon60.com label. "
        "This records a BFT ledger event only; it does not deliver email or authenticate the sender."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address (e.g. hypervisor@babylon60.com).",
            },
            "subject": {
                "type": "string",
                "description": "Email subject line.",
            },
            "body": {
                "type": "string",
                "description": "Email body text.",
            },
        },
        "required": ["to", "subject", "body"],
    },
}


class BabylonMailIntegration:
    """Local mail event recording, enabled only by an explicit ledger path."""

    tool_definition = MAIL_TOOL

    def __init__(self, ledger_path: Path | str) -> None:
        self.ledger = CortexPersistLedger(ledger_path)

    def send(self, args: dict[str, object]) -> dict[str, object]:
        raw_user = os.environ.get("USER", "operator")
        user = re.sub(r"[^a-zA-Z0-9._-]", "", raw_user) or "operator"
        from_email = f"{user}@babylon60.com"

        payload: dict[str, object] = {
            "from": from_email,
            "to": str(args["to"]),
            "subject": str(args["subject"]),
            "body": str(args["body"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        event = CortexEvent(
            event_type="BABYLON_MAIL_SENT",
            payload=payload,
            cortex_taint=f"{user}:mcp_server:send_mail",
        )

        ack = self.ledger.append_event(event)
        text = (
            f"📧 BabylonMail Recorded via MCP (local ledger only)\n"
            f"  From:    {from_email}\n"
            f"  To:      {args['to']}\n"
            f"  Subject: {args['subject']}\n"
            f"  BFT Seq: {ack['seq']}\n"
            f"  Hash:    {ack['entry_hash'][:16]}...\n"
            f"  Status:  {ack['status']}"
        )
        return {"content": [{"type": "text", "text": text}], "isError": False}
