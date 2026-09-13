"""
CORTEX ANTIGRAVITY MCP SERVER FOR CODEX
=======================================
Sovereign Model Context Protocol (MCP) server providing Codex Desktop
(GPT-6 Astra Ultra) with direct, bidirectional tools to communicate with
Antigravity (Gemini), inspect artifacts, check state, and dispatch tasks.

Transport: stdio (JSON-RPC 2.0)
Invariants:
- INV_C5_17: Sovereign, local, zero-cloud intermediary.
- INV_BFT_02: SQLite WAL mode persistence via TunnelBus.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, TextIO, TypedDict

from .tunnel_bus import TunnelBus

logger = logging.getLogger("codex_tunnel.mcp")

WORKSPACE_ROOT = Path("/Users/borjafernandezangulo/BABYLON-60")
ANTIGRAVITY_BRAIN = Path.home() / ".gemini" / "antigravity" / "brain"


class TextContent(TypedDict):
    type: str
    text: str


class ToolResult(TypedDict, total=False):
    content: list[TextContent]
    isError: bool


class ToolInputSchema(TypedDict, total=False):
    type: str
    properties: dict[str, object]
    required: list[str]


class ToolDefinition(TypedDict):
    name: str
    description: str
    inputSchema: ToolInputSchema


class AntigravityMcpServer:
    """MCP Server exposing Antigravity bidirectional tools to Codex."""

    def __init__(
        self,
        stdin: TextIO = sys.stdin,
        stdout: TextIO = sys.stdout,
        bus: TunnelBus | None = None,
    ):
        self._stdin = stdin
        self._stdout = stdout
        self._bus = bus or TunnelBus()
        self._running = False
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "initialize": self._handle_initialize,
            "notifications/initialized": self._handle_initialized,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
        }

    def run(self) -> None:
        """Main JSON-RPC stdio event loop."""
        self._running = True
        while self._running:
            try:
                line = self._stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue

                req = json.loads(line)
                response = self._process_request(req)
                if response is not None:
                    self._send_response(response)
            except json.JSONDecodeError:
                self._send_response(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }
                )
            except Exception as e:
                logger.exception("Error in MCP loop: %s", e)
                self._send_response(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": f"Internal error: {e}"},
                    }
                )

    def _process_request(self, req: dict[str, Any]) -> dict[str, Any] | None:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if not method:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32600, "message": "Invalid Request: missing method"},
            }

        # Notifications don't require responses
        if req_id is None:
            handler = self._handlers.get(method)
            if handler:
                try:
                    handler(params)
                except Exception as e:
                    logger.error("Notification handler error: %s", e)
            return None

        handler = self._handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        try:
            result = handler(params)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }

    def _send_response(self, resp: dict[str, Any]) -> None:
        payload = json.dumps(resp, ensure_ascii=False)
        self._stdout.write(payload + "\n")
        self._stdout.flush()

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False,
                }
            },
            "serverInfo": {
                "name": "antigravity-codex-tunnel",
                "version": "1.0.0",
            },
        }

    def _handle_initialized(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def _handle_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        tools: list[ToolDefinition] = [
            {
                "name": "antigravity_send_message",
                "description": "Send a message, task, question, or finding to Antigravity (Gemini agent) through the sovereign duplex tunnel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message, instructions, or payload to send to Antigravity.",
                        },
                        "msg_type": {
                            "type": "string",
                            "description": "Type of message: 'task', 'question', 'finding', 'diff', or 'status'.",
                            "default": "task",
                        },
                        "context": {
                            "type": "object",
                            "description": "Optional dictionary of context, file paths, or diffs.",
                        },
                        "wait_for_reply": {
                            "type": "boolean",
                            "description": "If true, blocks until Antigravity processes the message and responds (up to timeout_seconds).",
                            "default": False,
                        },
                        "timeout_seconds": {
                            "type": "number",
                            "description": "Maximum seconds to wait for reply if wait_for_reply is true (default: 30).",
                            "default": 30,
                        },
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "antigravity_receive_messages",
                "description": "Read pending messages, tasks, or answers sent from Antigravity to Codex.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum messages to pull (default: 5).",
                            "default": 5,
                        },
                        "mark_delivered": {
                            "type": "boolean",
                            "description": "Whether to mark messages as delivered (default: true).",
                            "default": True,
                        },
                    },
                },
            },
            {
                "name": "antigravity_status",
                "description": "Get Antigravity's current workspace status, git HEAD, active brain directory, and message bus statistics.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "antigravity_read_artifact",
                "description": "Read an Antigravity artifact (such as implementation_plan.md or walkthrough.md) from the active brain directory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "artifact_name": {
                            "type": "string",
                            "description": "Name of artifact (e.g., 'implementation_plan.md', 'walkthrough.md').",
                        }
                    },
                    "required": ["artifact_name"],
                },
            },
        ]
        return {"tools": tools}

    def _tool_send_message(self, args: dict[str, Any]) -> ToolResult:
        msg_text = args.get("message", "")
        msg_type = args.get("msg_type", "task")
        context = args.get("context", {})
        wait_reply = args.get("wait_for_reply", False)
        timeout_sec = float(args.get("timeout_seconds", 30))

        payload = {
            "message": msg_text,
            "context": context,
        }
        msg = self._bus.push_message(
            source="codex",
            destination="antigravity",
            payload=payload,
            msg_type=msg_type,
        )

        result_text = f"Message queued onto tunnel bus [ID: {msg.id}]"
        if wait_reply:
            reply = self._bus.wait_for_reply(msg.id, timeout_sec=timeout_sec)
            if reply:
                result_text += f"\n\nAntigravity responded:\n{json.dumps(reply.response_payload or reply.payload, indent=2, ensure_ascii=False)}"
            else:
                result_text += f"\n\nWait timed out after {timeout_sec}s without reply (message remains pending)."

        return {"content": [{"type": "text", "text": result_text}]}

    def _tool_receive_messages(self, args: dict[str, Any]) -> ToolResult:
        limit = int(args.get("limit", 5))
        mark_del = bool(args.get("mark_delivered", True))
        messages = self._bus.pull_messages(
            destination="codex",
            status="pending",
            limit=limit,
            mark_delivered=mark_del,
        )
        data = [m.to_dict() for m in messages]
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(data, indent=2, ensure_ascii=False)
                    if data
                    else "No pending messages from Antigravity.",
                }
            ]
        }

    def _tool_status(self, _args: dict[str, Any]) -> ToolResult:
        git_branch = "unknown"
        git_head = "unknown"
        try:
            p_b = subprocess.run(
                ["git", "branch", "--show-current"], cwd=WORKSPACE_ROOT, capture_output=True, text=True
            )
            git_branch = p_b.stdout.strip()
            p_h = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=WORKSPACE_ROOT, capture_output=True, text=True
            )
            git_head = p_h.stdout.strip()
        except Exception:
            pass

        bus_stats = self._bus.get_status()
        status_data = {
            "workspace": str(WORKSPACE_ROOT),
            "git_branch": git_branch,
            "git_head": git_head,
            "bus_telemetry": bus_stats,
            "brain_directory": str(ANTIGRAVITY_BRAIN),
        }
        return {"content": [{"type": "text", "text": json.dumps(status_data, indent=2)}]}

    def _find_artifact(self, art_name: str) -> Path | None:
        if not ANTIGRAVITY_BRAIN.is_dir():
            return None
        for conv_dir in sorted(ANTIGRAVITY_BRAIN.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if conv_dir.is_dir():
                cand = conv_dir / art_name
                if cand.is_file():
                    return cand
        return None

    def _tool_read_artifact(self, args: dict[str, Any]) -> ToolResult:
        art_name = args.get("artifact_name", "")
        found_path = self._find_artifact(art_name)
        if not found_path or not found_path.is_file():
            return {
                "content": [{"type": "text", "text": f"Artifact '{art_name}' not found in {ANTIGRAVITY_BRAIN}"}],
                "isError": True,
            }
        try:
            content = found_path.read_text(encoding="utf-8")
            return {"content": [{"type": "text", "text": f"--- Artifact: {art_name} ({found_path}) ---\n\n{content}"}]}
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error reading artifact {art_name}: {e}"}],
                "isError": True,
            }

    def _handle_tools_call(self, params: dict[str, Any]) -> ToolResult:
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "antigravity_send_message":
            return self._tool_send_message(args)
        if tool_name == "antigravity_receive_messages":
            return self._tool_receive_messages(args)
        if tool_name == "antigravity_status":
            return self._tool_status(args)
        if tool_name == "antigravity_read_artifact":
            return self._tool_read_artifact(args)

        return {
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True,
        }
