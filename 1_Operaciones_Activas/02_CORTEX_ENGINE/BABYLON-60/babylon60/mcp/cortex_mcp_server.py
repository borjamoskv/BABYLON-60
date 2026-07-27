# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
CORTEX MCP SERVER — Sovereign BFT Memory Server (MCP Protocol)
===============================================================
Servidor MCP soberano que expone el ledger inmutable CortexPersistLedger,
las firmas de atestación Merkle Root SHA3-256 y la mensajería BabylonMail
a clientes externos (Claude Desktop, Cursor, agentes remotos) mediante
el protocolo estándar Model Context Protocol (JSON-RPC 2.0 over stdio).

Herramientas expuestas:
  - bft_append_event:       Registrar eventos causales inmutables con Lamport.
  - bft_query_ledger:       Consultar la cadena de bloques y filtros causales.
  - bft_verify_merkle_root: Calcular y atestar la Raíz de Merkle SHA3-256.
  - bft_send_sovereign_mail: Enviar correos autenticados @babylon60.com.

Recursos expuestos:
  - bft://ledger/status:        Diagnóstico de salud y número de nodos.
  - bft://merkle/attestation:   Firma de inmutabilidad del estado.

Transporte: stdio (JSON-RPC 2.0) con fallback WebSocket planificado.

Invariantes:
  - INV_BFT_02: WAL mode + busy_timeout=5000ms.
  - INV_BFT_03: Causal taint obligatorio.
  - INV_BFT_04: Claves de idempotencia UUID v5.
  - INV_C5_17: 100% Soberano, Gratis y Auto-hospedado.

Authorship: Telmo Dinámico de Moskv (borjamoskv)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root on path for standalone execution
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger

logger = logging.getLogger("babylon60.mcp.server")

# ---------------------------------------------------------------------------
# Default ledger path
# ---------------------------------------------------------------------------
DEFAULT_LEDGER_PATH = Path.home() / ".babylon60" / "mcp_ledger.db"
DEFAULT_MAIL_LEDGER_PATH = Path.home() / ".babylon60" / "babylonmail" / "mail_ledger.db"

# ---------------------------------------------------------------------------
# MCP Protocol Constants (JSON-RPC 2.0)
# ---------------------------------------------------------------------------
JSONRPC_VERSION = "2.0"
MCP_SERVER_NAME = "cortex-persist-bft"
MCP_SERVER_VERSION = "1.1.0"

# MCP Protocol version
MCP_PROTOCOL_VERSION = "2025-03-26"

# ---------------------------------------------------------------------------
# Tool & Resource Definitions
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "name": "bft_append_event",
        "description": (
            "Append an immutable causal event to the BFT ledger. "
            "Each event is hash-chained (SHA3-256), Lamport-ordered, "
            "and UUID v5 deduplicated. Returns seq, entry_hash, lamport_t."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Event type identifier (e.g. 'CODE_MUTATION', 'DECISION').",
                },
                "payload": {
                    "type": "object",
                    "description": "Arbitrary JSON payload to persist immutably.",
                },
                "cortex_taint": {
                    "type": "string",
                    "description": "Causal provenance string: who/when/why (INV_BFT_03).",
                },
                "agent_id": {
                    "type": "string",
                    "description": "Agent identity (default: MCP-CLIENT).",
                    "default": "MCP-CLIENT",
                },
            },
            "required": ["event_type", "payload", "cortex_taint"],
        },
    },
    {
        "name": "bft_query_ledger",
        "description": (
            "Query the BFT ledger entries. Optionally filter by event_type. "
            "Returns the last N entries (default 10) in reverse chronological order."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Optional filter by event type.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max entries to return (default 10).",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
    {
        "name": "bft_verify_merkle_root",
        "description": (
            "Compute and return the Merkle Root SHA3-256 attestation of the "
            "entire ledger state. Also runs full hash-chain integrity verification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "bft_send_sovereign_mail",
        "description": (
            "Send a sovereign BabylonMail message via @babylon60.com. "
            "The message is persisted immutably in the BFT mail ledger."
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
    },
]

RESOURCES: list[dict[str, Any]] = [
    {
        "uri": "bft://ledger/status",
        "name": "BFT Ledger Status",
        "description": "Real-time health diagnostics of the CortexPersistLedger including node count, max Lamport, and integrity status.",
        "mimeType": "application/json",
    },
    {
        "uri": "bft://merkle/attestation",
        "name": "Merkle Root Attestation",
        "description": "Cryptographic SHA3-256 Merkle Root attestation of the full ledger state for tamper-evidence verification.",
        "mimeType": "application/json",
    },
]


# ===========================================================================
# MCP Server Core
# ===========================================================================

class CortexMCPServer:
    """
    Servidor MCP Soberano BFT (JSON-RPC 2.0 over stdio).

    Expone herramientas de persistencia criptográfica y recursos de diagnóstico
    del ledger inmutable CortexPersistLedger a clientes MCP externos.
    """

    def __init__(
        self,
        ledger_path: Path | str = DEFAULT_LEDGER_PATH,
        mail_ledger_path: Path | str = DEFAULT_MAIL_LEDGER_PATH,
    ) -> None:
        self.ledger = CortexPersistLedger(ledger_path)
        self.mail_ledger = CortexPersistLedger(mail_ledger_path)
        self._running = False
        self._request_handlers: dict[str, Any] = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "ping": self._handle_ping,
        }

    # -----------------------------------------------------------------------
    # JSON-RPC I/O (stdio transport)
    # -----------------------------------------------------------------------

    def _read_message(self, input_stream: Any = None) -> dict[str, Any] | None:
        """Read a single JSON-RPC message from stdin."""
        stream = input_stream or sys.stdin
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            return None
        return json.loads(line)

    def _write_message(self, message: dict[str, Any], output_stream: Any = None) -> None:
        """Write a single JSON-RPC message to stdout."""
        stream = output_stream or sys.stdout
        stream.write(json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n")
        stream.flush()

    def _make_response(self, request_id: Any, result: Any) -> dict[str, Any]:
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}

    def _make_error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    # -----------------------------------------------------------------------
    # MCP Protocol Handlers
    # -----------------------------------------------------------------------

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            },
            "serverInfo": {
                "name": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
            },
        }

    def _handle_initialized(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def _handle_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"tools": TOOLS}

    def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        dispatch: dict[str, Any] = {
            "bft_append_event": self._tool_append_event,
            "bft_query_ledger": self._tool_query_ledger,
            "bft_verify_merkle_root": self._tool_verify_merkle_root,
            "bft_send_sovereign_mail": self._tool_send_sovereign_mail,
        }

        handler = dispatch.get(tool_name)
        if not handler:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            }

        return handler(arguments)

    def _handle_resources_list(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"resources": RESOURCES}

    def _handle_resources_read(self, params: dict[str, Any]) -> dict[str, Any]:
        uri = params.get("uri", "")

        if uri == "bft://ledger/status":
            attestation = self.ledger.get_state_attestation()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(attestation, indent=2),
                    }
                ]
            }
        elif uri == "bft://merkle/attestation":
            merkle_root = self.ledger.get_merkle_root()
            integrity = self.ledger.verify_integrity()
            result = {
                "merkle_root": merkle_root,
                "integrity_verified": integrity,
                "attested_at": datetime.now(timezone.utc).isoformat(),
                "server": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
            }
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result, indent=2),
                    }
                ]
            }
        else:
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": f"Unknown resource: {uri}",
                    }
                ]
            }

    # -----------------------------------------------------------------------
    # Tool Implementations
    # -----------------------------------------------------------------------

    def _tool_append_event(self, args: dict[str, Any]) -> dict[str, Any]:
        event = CortexEvent(
            event_type=args["event_type"],
            payload=args["payload"],
            cortex_taint=args["cortex_taint"],
            agent_id=args.get("agent_id", "MCP-CLIENT"),
        )
        ack = self.ledger.append_event(event)
        text = (
            f"🟢 Event appended to BFT Ledger\n"
            f"  Seq:        {ack['seq']}\n"
            f"  Event ID:   {ack['event_id']}\n"
            f"  Entry Hash: {ack['entry_hash'][:24]}...\n"
            f"  Lamport:    {ack['lamport_t']}\n"
            f"  Status:     {ack['status']}"
        )
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def _tool_query_ledger(self, args: dict[str, Any]) -> dict[str, Any]:
        event_type = args.get("event_type")
        limit = args.get("limit", 10)

        with self.ledger._get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute(
                    "SELECT seq, event_type, payload_json, cortex_taint, lamport_t, entry_hash, timestamp "
                    "FROM cortex_ledger WHERE event_type = ? ORDER BY seq DESC LIMIT ?",
                    (event_type, limit),
                )
            else:
                cursor.execute(
                    "SELECT seq, event_type, payload_json, cortex_taint, lamport_t, entry_hash, timestamp "
                    "FROM cortex_ledger ORDER BY seq DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()

        entries = []
        for row in rows:
            entries.append({
                "seq": row[0],
                "event_type": row[1],
                "payload": json.loads(row[2]),
                "cortex_taint": row[3],
                "lamport_t": row[4],
                "entry_hash": row[5][:24] + "...",
                "timestamp": row[6],
            })

        text = json.dumps({"total_returned": len(entries), "entries": entries}, indent=2)
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def _tool_verify_merkle_root(self, args: dict[str, Any]) -> dict[str, Any]:
        merkle_root = self.ledger.get_merkle_root()
        integrity = self.ledger.verify_integrity()
        attestation = self.ledger.get_state_attestation()

        text = (
            f"🔐 Merkle Root Attestation (SHA3-256)\n"
            f"  Merkle Root:  {merkle_root[:32]}...\n"
            f"  Integrity:    {'🟢 VERIFIED' if integrity else '🔴 BROKEN'}\n"
            f"  Total Entries: {attestation['total_entries']}\n"
            f"  Max Lamport:  {attestation['max_lamport']}\n"
            f"  Attested At:  {attestation['attested_at']}"
        )
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def _tool_send_sovereign_mail(self, args: dict[str, Any]) -> dict[str, Any]:
        user = os.environ.get("USER", "operator")
        from_email = f"{user}@babylon60.com"

        payload = {
            "from": from_email,
            "to": args["to"],
            "subject": args["subject"],
            "body": args["body"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        event = CortexEvent(
            event_type="BABYLON_MAIL_SENT",
            payload=payload,
            cortex_taint=f"{user}:mcp_server:send_mail",
        )

        ack = self.mail_ledger.append_event(event)
        text = (
            f"📧 BabylonMail Sent via MCP\n"
            f"  From:    {from_email}\n"
            f"  To:      {args['to']}\n"
            f"  Subject: {args['subject']}\n"
            f"  BFT Seq: {ack['seq']}\n"
            f"  Hash:    {ack['entry_hash'][:16]}...\n"
            f"  Status:  {ack['status']}"
        )
        return {"content": [{"type": "text", "text": text}], "isError": False}

    # -----------------------------------------------------------------------
    # Process a single JSON-RPC request (used for testing and stdio loop)
    # -----------------------------------------------------------------------

    def process_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single JSON-RPC request and return the response."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        handler = self._request_handlers.get(method)
        if not handler:
            if request_id is not None:
                return self._make_error(request_id, -32601, f"Method not found: {method}")
            return None  # Notification with unknown method — ignore

        result = handler(params)

        # Notifications (no id) don't get responses
        if request_id is None:
            return None

        return self._make_response(request_id, result)

    # -----------------------------------------------------------------------
    # Main stdio event loop
    # -----------------------------------------------------------------------

    def run_stdio(self) -> None:
        """Run the MCP server on stdio (blocking)."""
        self._running = True
        logger.info(f"🟢 CortexMCPServer v{MCP_SERVER_VERSION} started on stdio")

        while self._running:
            msg = self._read_message()
            if msg is None:
                break  # EOF

            response = self.process_request(msg)
            if response is not None:
                self._write_message(response)

        logger.info("🔴 CortexMCPServer stdio loop ended")

    def stop(self) -> None:
        self._running = False


# ===========================================================================
# CLI entrypoint
# ===========================================================================

def main() -> None:
    """Entry point for `python -m babylon60.mcp.cortex_mcp_server`."""
    import argparse

    parser = argparse.ArgumentParser(description="CORTEX MCP Server — Sovereign BFT Memory")
    parser.add_argument("--ledger", type=str, default=str(DEFAULT_LEDGER_PATH), help="Path to BFT ledger DB")
    parser.add_argument("--mail-ledger", type=str, default=str(DEFAULT_MAIL_LEDGER_PATH), help="Path to BabylonMail ledger DB")
    args = parser.parse_args()

    server = CortexMCPServer(
        ledger_path=Path(args.ledger),
        mail_ledger_path=Path(args.mail_ledger),
    )
    server.run_stdio()


if __name__ == "__main__":
    main()
