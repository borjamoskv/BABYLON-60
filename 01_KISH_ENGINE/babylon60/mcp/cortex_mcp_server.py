# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""
CORTEX MCP SERVER — Sovereign BFT Memory Server (MCP Protocol)
===============================================================
Servidor MCP soberano que expone el ledger inmutable CortexPersistLedger,
las firmas de atestación Merkle Root SHA3-256 a clientes externos
(Claude Desktop, Cursor, agents remotos) mediante
el protocolo estándar Model Context Protocol (JSON-RPC 2.0 over stdio).

Herramientas expuestas:
  - bft_append_event:       Registrar eventos causales inmutables con Lamport.
  - bft_query_ledger:       Consultar la cadena de bloques y filtros causales.
  - bft_verify_merkle_root: Calcular y atestar la Raíz de Merkle SHA3-256.

Recursos expuestos:
  - bft://ledger/status:        Diagnóstico de salud y número de nodes.
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
import re
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TextIO, TypedDict, cast


if TYPE_CHECKING:
    from babylon60.mcp.mail_integration import BabylonMailIntegration


class TextContent(TypedDict):
    type: str
    text: str


class ToolResult(TypedDict, total=False):
    content: list[TextContent]
    isError: bool


class JsonRpcError(TypedDict):
    code: int
    message: str


class JsonRpcResponse(TypedDict, total=False):
    jsonrpc: str
    id: object
    result: object
    error: JsonRpcError


class ResourceContent(TypedDict, total=False):
    uri: str
    mimeType: str
    text: str


class ResourceReadResult(TypedDict):
    contents: list[ResourceContent]


class ToolInputSchema(TypedDict, total=False):
    type: str
    properties: dict[str, object]
    required: list[str]


class ToolDefinition(TypedDict):
    name: str
    description: str
    inputSchema: ToolInputSchema


class ResourceDefinition(TypedDict):
    uri: str
    name: str
    description: str
    mimeType: str


# Ensure project root on path for standalone execution
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger  # noqa: E402
from babylon60.mcp.signature_ui import (  # noqa: E402
    read_signature_resource,
    render_signature_result,
    signature_resources,
    signature_tool_descriptor,
    supports_signature_ui,
)
from babylon60.verification.verification_gate import VerificationGate  # noqa: E402

logger = logging.getLogger("babylon60.mcp.server")

# ---------------------------------------------------------------------------
# Default ledger path
# ---------------------------------------------------------------------------
BABYLON_BASE_PATH = Path(os.getenv("BABYLON_HOME", str(Path.home() / ".babylon60")))
DEFAULT_LEDGER_PATH = BABYLON_BASE_PATH / "mcp_ledger.db"
DEFAULT_MAIL_LEDGER_PATH = BABYLON_BASE_PATH / "data" / "mail_ledger.db"
_DEFAULT_CAUSAL_GATE_FALLBACK = (
    str(BABYLON_BASE_PATH / "causal_gate.db")
    if "BABYLON_HOME" in os.environ
    else str(Path(__file__).resolve().parents[3] / ".cortex" / "causal_gate.db")
)
DEFAULT_CAUSAL_GATE_PATH = Path(
    os.getenv(
        "BABYLON_CAUSAL_GATE_DB",
        _DEFAULT_CAUSAL_GATE_FALLBACK,
    )
)

# ---------------------------------------------------------------------------
# MCP Protocol Constants (JSON-RPC 2.0)
# ---------------------------------------------------------------------------
JSONRPC_VERSION = "2.0"
MCP_SERVER_NAME = "cortex-persist-bft"
MCP_SERVER_VERSION = "5.0.0"

# MCP Protocol version
MCP_PROTOCOL_VERSION = "4.3.0"

# ---------------------------------------------------------------------------
# Tool & Resource Definitions (B1: NAME != IDENTITY — Canonical + Functional Aliases)
# ---------------------------------------------------------------------------
CANONICAL_TOOL_ALIASES: dict[str, str] = {
    "cortex_event_append": "bft_append_event",
    "cortex_ledger_query": "bft_query_ledger",
    "cortex_merkle_verify": "bft_verify_merkle_root",
    "cortex_risk_evaluate": "causal_evaluate_task_risk",
    "cortex_ledger_verify": "causal_verify_ledger",
    "cortex_agent_dispatch": "royal_rumble_dispatch",
    "cortex_blackboard_dispatch": "blackboard_dispatch",
    "cortex_mail_send": "bft_send_sovereign_mail",
    "cortex_mcp_bomb_detonate": "detonate_ephemeral_mcp",
    "cortex_skill_route": "bft_route_skill",
}

CANONICAL_RESOURCE_ALIASES: dict[str, str] = {
    "cortex://ledger/status": "bft://ledger/status",
    "cortex://merkle/attestation": "bft://merkle/attestation",
    "cortex://causal/ledger": "bft://causal/ledger",
    "cortex://skills/catalog": "bft://skills/catalog",
}

TOOLS: list[dict[str, object]] = [
    {
        "name": "bft_append_event",
        "canonical_alias": "cortex_event_append",
        "description": (
            "[Alias: cortex_event_append] Append an immutable causal event to the BFT ledger. "
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
        "canonical_alias": "cortex_ledger_query",
        "description": (
            "[Alias: cortex_ledger_query] Query the BFT ledger entries. Optionally filter by event_type. "
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
        "canonical_alias": "cortex_merkle_verify",
        "description": (
            "[Alias: cortex_merkle_verify] Compute and return the Merkle Root SHA3-256 attestation of the "
            "entire ledger state. Also runs full hash-chain integrity verification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "causal_evaluate_task_risk",
        "canonical_alias": "cortex_risk_evaluate",
        "description": (
            "[Alias: cortex_risk_evaluate] Evaluate the risk level (LOW, MEDIUM, HIGH, CRITICAL) of a proposed "
            "swarm task payload under Causal Gate governance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_payload": {
                    "type": "object",
                    "description": "Task specification containing action, command, or mutability flag.",
                },
            },
            "required": ["task_payload"],
        },
    },
    {
        "name": "causal_verify_ledger",
        "canonical_alias": "cortex_ledger_verify",
        "description": (
            "[Alias: cortex_ledger_verify] Verify the cryptographic SHA-256 Merkle chain integrity of the Causal Verification Gate audit ledger."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "royal_rumble_dispatch",
        "canonical_alias": "cortex_agent_dispatch",
        "description": (
            "[Alias: cortex_agent_dispatch] Dispatch an agentic query or embedding through BABYLON-60's multi-provider router "
            "with AX-0 SensitivePathGuard and automatic local M3 Pro failover (LM Studio :1234 / Ollama :11434)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt or code snippet to process.",
                },
                "role": {
                    "type": "string",
                    "description": "Role tier: planner, coder_act, structured_review, subagent_fast, or local_direct.",
                    "default": "coder_act",
                },
                "context_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of file paths referenced by the prompt (evaluated by SensitivePathGuard).",
                },
                "prefer_local": {
                    "type": "boolean",
                    "description": "If true, bypass WAN and execute directly on local Apple Silicon (:1234 / :11434).",
                    "default": False,
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "blackboard_dispatch",
        "canonical_alias": "cortex_blackboard_dispatch",
        "description": (
            "[Alias: cortex_blackboard_dispatch] Deterministic inter-agent Blackboard broker "
            "(publish, resolve, poll, curate) backed by SQLite WAL with Two-Man Rule verification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation: publish, resolve, poll, or curate.",
                },
                "task_id": {
                    "type": "string",
                    "description": "Task identifier.",
                },
                "logical_tick": {
                    "type": "integer",
                    "description": "Monotonic causal tick (INV_C5_CANONICAL_LOGICAL_TICK).",
                    "default": 1,
                },
                "topic": {
                    "type": "string",
                    "description": "Topic: HYPOTHESIS, PATCH_PROPOSAL, VERIFICATION_FAILURE, INVARIANT_ALERT.",
                    "default": "HYPOTHESIS",
                },
                "author_agent_id": {
                    "type": "string",
                    "description": "Producer agent identifier.",
                },
                "verifier_agent_id": {
                    "type": "string",
                    "description": "Verifier agent identifier (must differ from author_agent_id).",
                },
                "target_path": {
                    "type": "string",
                    "description": "Target file path.",
                },
                "claim": {
                    "type": "string",
                    "description": "Concise claim (<= 280 chars).",
                },
                "tuple_id": {
                    "type": "string",
                    "description": "Tuple SHA-256 ID for resolve operation.",
                },
                "new_status": {
                    "type": "string",
                    "description": "Resolution status: VERIFIED or FALSIFIED.",
                },
                "evidence_hash": {
                    "type": "string",
                    "description": "64-hex SHA-256 digest of empirical test/execution evidence.",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional SQLite WAL database path.",
                },
            },
            "required": ["operation", "task_id"],
        },
    },
    {
        "name": "detonate_ephemeral_mcp",
        "canonical_alias": "cortex_mcp_bomb_detonate",
        "description": (
            "[Alias: cortex_mcp_bomb_detonate] Synthesize, validate (Z3 + AST Gate), execute over isolated "
            "stdio JSON-RPC 2.0, and immediately self-destruct (unlink + DB purge) a single-use 'MCP Bomba'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain_name": {
                    "type": "string",
                    "description": "Identifier of the ephemeral domain (e.g. 'MatrixEigen', 'LogParser').",
                },
                "implementation_body": {
                    "type": "string",
                    "description": (
                        "Python function body implementing the tool logic (must return a JSON-serializable value; "
                        "sandboxed via AST Gate against OS/network/subprocess escapes)."
                    ),
                },
                "call_arguments": {
                    "type": "object",
                    "description": "Arguments dictionary passed to both schema deduction and the single-use tools/call invocation.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for the synthesized MCP tool.",
                },
                "cortex_taint": {
                    "type": "string",
                    "description": "Causal provenance string for the BFT attestation receipt.",
                    "default": "MCP-BOMB-AUTO",
                },
            },
            "required": ["domain_name", "implementation_body", "call_arguments"],
        },
    },
    {
        "name": "bft_route_skill",
        "canonical_alias": "cortex_skill_route",
        "description": (
            "[Alias: cortex_skill_route] Deterministically route an agentic intent or functional alias to the optimal "
            "CORTEX Declarative Skill (out of 130 registered skills) and return its role triad, tier, and functorial DAG chain."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language intent, trigger phrase, or canonical_alias (e.g. 'epistemic-simplifier', 'kernel-thermo-audit').",
                },
                "scope": {
                    "type": "string",
                    "description": "Scope filter: all, workspace, global, or kernel (default: all).",
                    "default": "all",
                },
            },
            "required": ["query"],
        },
    },
]

RESOURCES: list[dict[str, object]] = [
    {
        "uri": "babylon://presentation/guide",
        "name": "Babylon presentation guide",
        "description": "Shared reading and presentation contract for human-facing Babylon responses.",
        "mimeType": "text/markdown",
    },
    {
        "uri": "bft://ledger/status",
        "canonical_alias": "cortex://ledger/status",
        "name": "BFT Ledger Status",
        "description": "Real-time health diagnostics of the CortexPersistLedger including node count, max Lamport, and integrity status.",
        "mimeType": "application/json",
    },
    {
        "uri": "bft://merkle/attestation",
        "canonical_alias": "cortex://merkle/attestation",
        "name": "Merkle Root Attestation",
        "description": "Cryptographic SHA3-256 Merkle Root attestation of the full ledger state for tamper-evidence verification.",
        "mimeType": "application/json",
    },
    {
        "uri": "bft://causal/ledger",
        "canonical_alias": "cortex://causal/ledger",
        "name": "Causal Gate Audit Ledger Status",
        "description": "Health and SCITT Merkle chain verification status of the Causal Verification Gate.",
        "mimeType": "application/json",
    },
    {
        "uri": "bft://skills/catalog",
        "canonical_alias": "cortex://skills/catalog",
        "name": "CORTEX Declarative Skills Catalog (130 Skills)",
        "description": "Compiled ontology of 130 CORTEX declarative skills with canonical_alias mappings, 3-Evaluator Exergy tiers, and 26 functorial DAG edges.",
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
        mail_ledger_path: Path | str | None = None,
        causal_gate_path: Path | str = DEFAULT_CAUSAL_GATE_PATH,
        use_canonical_names: bool | None = None,
    ) -> None:
        self.ledger = CortexPersistLedger(ledger_path)
        self._mail_integration: BabylonMailIntegration | None = None
        self.mail_ledger: CortexPersistLedger | None = None
        if mail_ledger_path is not None:
            from babylon60.mcp.mail_integration import BabylonMailIntegration

            self._mail_integration = BabylonMailIntegration(mail_ledger_path)
            self.mail_ledger = self._mail_integration.ledger
        Path(causal_gate_path).parent.mkdir(parents=True, exist_ok=True)
        self.verification_gate = VerificationGate(db_path=str(causal_gate_path))
        if use_canonical_names is None:
            env_flag = os.getenv("BABYLON60_MCP_CANONICAL_NAMES", "").strip().lower()
            self.use_canonical_names = env_flag in {"1", "true", "yes"}
        else:
            self.use_canonical_names = bool(use_canonical_names)
        self._running = False
        self._signature_ui_supported = False
        self._request_handlers: dict[str, Callable[[dict[str, object]], dict[str, object]]] = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
            "ping": self._handle_ping,
        }

    # -----------------------------------------------------------------------
    # JSON-RPC I/O (stdio transport)
    # -----------------------------------------------------------------------

    def _read_message(self, input_stream: TextIO | None = None) -> dict[str, object] | None:
        """Read a single JSON-RPC message from stdin."""
        stream = input_stream or sys.stdin
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            return None
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            return cast(dict[str, object], parsed)
        return None

    def _write_message(self, message: Mapping[str, object], output_stream: TextIO | None = None) -> None:
        """Write a single JSON-RPC message to stdout."""
        stream = output_stream or sys.stdout
        stream.write(json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n")
        stream.flush()

    def _make_response(self, request_id: object, result: object) -> JsonRpcResponse:
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}

    def _make_error(self, request_id: object, code: int, message: str) -> JsonRpcResponse:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    # -----------------------------------------------------------------------
    # MCP Protocol Handlers
    # -----------------------------------------------------------------------

    def _handle_initialize(self, params: dict[str, object]) -> dict[str, object]:
        self._signature_ui_supported = supports_signature_ui(params.get("capabilities"))
        capabilities: dict[str, object] = {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
        }
        if self._signature_ui_supported:
            capabilities["extensions"] = {"io.modelcontextprotocol/ui": {"mimeTypes": ["text/html;profile=mcp-app"]}}
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "instructions": (Path(__file__).absolute().parents[1] / "presentation.md").read_text(encoding="utf-8"),
            "capabilities": capabilities,
            "serverInfo": {
                "name": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
            },
        }

    def _handle_initialized(self, params: dict[str, object]) -> dict[str, object]:
        return {}

    def _handle_ping(self, params: dict[str, object]) -> dict[str, object]:
        return {}

    def _handle_tools_list(self, params: dict[str, object]) -> dict[str, object]:
        raw_tools: list[dict[str, object]] = [dict(t) for t in TOOLS]
        raw_tools.append(signature_tool_descriptor(self._signature_ui_supported))
        if self._mail_integration is not None:
            mail_def: dict[str, object] = dict(self._mail_integration.tool_definition)
            mail_def.setdefault("canonical_alias", "cortex_mail_send")
            raw_tools.append(mail_def)
        if not self.use_canonical_names:
            return {"tools": raw_tools}
        canonical_tools: list[dict[str, object]] = []
        for t_copy in raw_tools:
            alias = t_copy.get("canonical_alias")
            if isinstance(alias, str) and alias:
                t_copy["legacy_name"] = t_copy["name"]
                t_copy["name"] = alias
            canonical_tools.append(t_copy)
        return {"tools": canonical_tools}

    def _handle_tools_call(self, params: dict[str, object]) -> dict[str, object]:
        tool_name = str(params.get("name", ""))
        resolved_name = CANONICAL_TOOL_ALIASES.get(tool_name, tool_name)
        arguments_raw = params.get("arguments", {})
        arguments: dict[str, object] = arguments_raw if isinstance(arguments_raw, dict) else {}

        if resolved_name == "babylon_signature_render":
            payload = arguments.get("payload")
            signature_format = arguments.get("format", "auto")
            if (
                not isinstance(payload, dict)
                or not isinstance(signature_format, str)
                or set(arguments) - {"payload", "format"}
            ):
                return {
                    "content": [
                        {"type": "text", "text": "Firma no generada: se requiere payload y un formato válido."}
                    ],
                    "isError": True,
                }
            return render_signature_result(
                payload,
                format=signature_format,
                ui_supported=self._signature_ui_supported,
            )

        dispatch: dict[str, Callable[[dict[str, object]], dict[str, object]]] = {
            "bft_append_event": self._tool_append_event,
            "bft_query_ledger": self._tool_query_ledger,
            "bft_verify_merkle_root": self._tool_verify_merkle_root,
            "causal_evaluate_task_risk": self._tool_causal_evaluate_task_risk,
            "causal_register_sign_off": self._tool_causal_register_sign_off,
            "causal_verify_ledger": self._tool_causal_verify_ledger,
            "royal_rumble_dispatch": self._tool_royal_rumble_dispatch,
            "blackboard_dispatch": self._tool_blackboard_dispatch,
            "detonate_ephemeral_mcp": self._tool_detonate_ephemeral_mcp,
            "bft_route_skill": self._tool_route_skill,
        }

        if self._mail_integration is not None:
            dispatch["bft_send_sovereign_mail"] = self._mail_integration.send

        handler = dispatch.get(resolved_name)
        if not handler:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            }

        return handler(arguments)

    def _handle_resources_list(self, params: dict[str, object]) -> dict[str, object]:
        resources = [dict(resource) for resource in RESOURCES]
        resources.extend(signature_resources(self._signature_ui_supported))
        if not self.use_canonical_names:
            return {"resources": resources}
        canonical_resources: list[dict[str, object]] = []
        for r in resources:
            r_copy = dict(r)
            alias = r_copy.get("canonical_alias")
            if isinstance(alias, str) and alias:
                r_copy["legacy_uri"] = r_copy["uri"]
                r_copy["uri"] = alias
            canonical_resources.append(r_copy)
        return {"resources": canonical_resources}

    def _handle_resources_read(self, params: dict[str, object]) -> dict[str, object]:
        uri_raw = str(params.get("uri", ""))
        uri = CANONICAL_RESOURCE_ALIASES.get(uri_raw, uri_raw)

        if uri in {"ui://babylon60/signature", "babylon://signature/schema"}:
            return read_signature_resource(uri)

        if uri == "babylon://presentation/guide":
            return {
                "contents": [
                    {
                        "uri": uri_raw,
                        "mimeType": "text/markdown",
                        "text": (Path(__file__).absolute().parents[1] / "presentation.md").read_text(encoding="utf-8"),
                    }
                ]
            }

        if uri == "bft://ledger/status":
            attestation = self.ledger.get_state_attestation()
            return {
                "contents": [
                    {
                        "uri": uri_raw,
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
        elif uri == "bft://causal/ledger":
            integrity = self.verification_gate.verify_ledger_integrity()
            result = {
                "causal_gate_status": "ACTIVE",
                "scitt_integrity_verified": integrity,
                "db_path": str(self.verification_gate.db_path),
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
        elif uri == "bft://skills/catalog":
            catalog_data = self._load_skills_catalog()
            summary = {
                "version": catalog_data.get("version", "26.400"),
                "total_skills": catalog_data.get("total_skills", 0),
                "average_exergy_density": catalog_data.get("average_exergy_density", 0),
                "adjacency_edges": len(cast(list[object], catalog_data.get("adjacency", []))),
                "skills": [
                    {
                        "name": e.get("name"),
                        "canonical_alias": e.get("canonical_alias", e.get("name")),
                        "tier": e.get("tier"),
                        "category": e.get("category"),
                        "role": e.get("role", "ejecutor"),
                        "scope": e.get("scope", "global"),
                    }
                    for e in cast(list[dict[str, object]], catalog_data.get("entries", []))
                ],
            }
            return {
                "contents": [
                    {
                        "uri": uri_raw,
                        "mimeType": "application/json",
                        "text": json.dumps(summary, indent=2, ensure_ascii=False),
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

    def _load_skills_catalog(self) -> dict[str, object]:
        skills_json = REPO_ROOT.parent / "docs" / "skills.json"
        if skills_json.exists():
            try:
                loaded = json.loads(skills_json.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    return loaded
            except Exception:
                pass
        return {"entries": [], "adjacency": [], "total_skills": 0}

    def _handle_prompts_list(self, params: dict[str, object]) -> dict[str, object]:
        """Expose workspace declarative skills (.agents/skills/*/SKILL.md) as native MCP prompts."""
        import yaml

        ws_dir = REPO_ROOT.parent / ".agents" / "skills"
        prompts: list[dict[str, object]] = []
        if ws_dir.exists():
            for skill_dir in sorted(ws_dir.iterdir()):
                md_path = skill_dir / "SKILL.md"
                if not (skill_dir.is_dir() and md_path.exists()):
                    continue
                text = md_path.read_text(encoding="utf-8", errors="ignore")
                fm: dict[str, object] = {}
                parts = text.split("---", 2)
                if text.startswith("---") and len(parts) >= 3:
                    parsed = yaml.safe_load(parts[1])
                    if isinstance(parsed, dict):
                        fm = parsed
                legacy_name = str(fm.get("name", skill_dir.name))
                alias = str(fm.get("canonical_alias", legacy_name)).strip() or legacy_name
                primary_name = alias if self.use_canonical_names else legacy_name
                prompts.append(
                    {
                        "name": primary_name,
                        "canonical_alias": alias,
                        "legacy_name": legacy_name,
                        "description": f"[{alias}] {fm.get('description', '')}",
                        "arguments": [
                            {
                                "name": "task",
                                "description": "Optional task or target context to execute with this CORTEX skill.",
                                "required": False,
                            }
                        ],
                    }
                )
        return {"prompts": prompts}

    def _handle_prompts_get(self, params: dict[str, object]) -> dict[str, object]:
        """Resolve a CORTEX declarative skill by name or canonical_alias and return its prompt messages."""
        import yaml

        target = str(params.get("name", "")).strip()
        args_raw = params.get("arguments", {})
        args_dict = args_raw if isinstance(args_raw, dict) else {}
        task_arg = str(args_dict.get("task", "")).strip()

        ws_dir = REPO_ROOT.parent / ".agents" / "skills"
        if ws_dir.exists():
            for skill_dir in sorted(ws_dir.iterdir()):
                md_path = skill_dir / "SKILL.md"
                if not (skill_dir.is_dir() and md_path.exists()):
                    continue
                text = md_path.read_text(encoding="utf-8", errors="ignore")
                fm: dict[str, object] = {}
                parts = text.split("---", 2)
                if text.startswith("---") and len(parts) >= 3:
                    parsed = yaml.safe_load(parts[1])
                    if isinstance(parsed, dict):
                        fm = parsed
                sname = str(fm.get("name", skill_dir.name))
                salias = str(fm.get("canonical_alias", "")).strip()
                if target in {sname, salias}:
                    prompt_text = text
                    if task_arg:
                        prompt_text += f"\n\n## Active Operator Task\n{task_arg}\n"
                    return {
                        "description": str(fm.get("description", sname)),
                        "messages": [
                            {
                                "role": "user",
                                "content": {"type": "text", "text": prompt_text},
                            }
                        ],
                    }

        catalog = self._load_skills_catalog()
        for entry in cast(list[dict[str, object]], catalog.get("entries", [])):
            ename = str(entry.get("name", ""))
            ealias = str(entry.get("canonical_alias", ""))
            if target in {ename, ealias}:
                summary_prompt = (
                    f"# CORTEX Skill: {entry.get('display_name', ename)}\n"
                    f"- Canonical Alias: `{ealias}` (ID: `{ename}`)\n"
                    f"- Role Triad: `{entry.get('role', 'ejecutor')}` | Tier: `{entry.get('tier', 18000)}` | Scope: `{entry.get('scope', 'global')}`\n"
                    f"- Description: {entry.get('description', '')}\n"
                )
                if task_arg:
                    summary_prompt += f"\n## Active Operator Task\n{task_arg}\n"
                return {
                    "description": str(entry.get("description", ename)),
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": summary_prompt},
                        }
                    ],
                }

        return {
            "description": f"Unknown skill prompt: {target}",
            "messages": [],
            "isError": True,
        }

    # -----------------------------------------------------------------------
    # Tool Implementations
    # -----------------------------------------------------------------------

    def _tool_append_event(self, args: dict[str, object]) -> dict[str, object]:
        raw_payload = args.get("payload", {})
        payload = raw_payload if isinstance(raw_payload, dict) else {}
        event = CortexEvent(
            event_type=str(args["event_type"]),
            payload=payload,
            cortex_taint=str(args["cortex_taint"]),
            agent_id=str(args.get("agent_id", "MCP-CLIENT")),
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

    def _tool_query_ledger(self, args: dict[str, object]) -> dict[str, object]:
        event_type = args.get("event_type")
        event_type_str = str(event_type) if event_type is not None else None
        raw_limit = args.get("limit", 10)
        limit = int(raw_limit) if isinstance(raw_limit, (int, str)) else 10

        with self.ledger._get_connection() as conn:
            cursor = conn.cursor()
            if event_type_str:
                cursor.execute(
                    "SELECT seq, event_type, payload_json, cortex_taint, lamport_t, entry_hash, timestamp "
                    "FROM cortex_ledger WHERE event_type = ? ORDER BY seq DESC LIMIT ?",
                    (event_type_str, limit),
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
            entries.append(
                {
                    "seq": row[0],
                    "event_type": row[1],
                    "payload": json.loads(row[2]),
                    "cortex_taint": row[3],
                    "lamport_t": row[4],
                    "entry_hash": row[5][:24] + "...",
                    "timestamp": row[6],
                }
            )

        text = json.dumps({"total_returned": len(entries), "entries": entries}, indent=2)
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def _tool_verify_merkle_root(self, args: dict[str, object]) -> dict[str, object]:
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

    def _tool_causal_evaluate_task_risk(self, args: dict[str, object]) -> dict[str, object]:
        task_payload_raw = args.get("task_payload", {})
        task_payload = task_payload_raw if isinstance(task_payload_raw, dict) else {}
        risk = self.verification_gate.evaluate_task(task_payload)
        is_allowed = self.verification_gate.is_allowed(task_payload)
        action_name = task_payload.get("action", "N/A") if isinstance(task_payload, dict) else "N/A"
        text = (
            f"⚖️ Causal Task Risk Evaluation\n"
            f"  Evaluated Risk: {risk.name}\n"
            f"  Execution Allowed: {'🟢 YES' if is_allowed else '🔴 PAUSED (Requires Human Sign-off)'}\n"
            f"  Action: {action_name}"
        )
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def _tool_causal_register_sign_off(self, args: dict[str, object]) -> dict[str, object]:
        # AX-0: A stochastic component MUST NOT authorize an irreversible effect it proposes.
        # Proposer (MCP client/LLM) != Authorizer (Human operator / Secure Enclave hardware).
        text = (
            "🔴 [AX-0 VIOLATION BLOCKED] Stochastic MCP clients cannot self-authorize tasks.\n"
            "  Rule AX-0: proposer(action) != authorizer(action).\n"
            "  Human or hardware authorization must occur out-of-band via 'babylon60 approve <execution_id> --task-file <task.json>'."
        )
        return {"content": [{"type": "text", "text": text}], "isError": True}

    def _tool_causal_verify_ledger(self, args: dict[str, object]) -> dict[str, object]:
        integrity = self.verification_gate.verify_ledger_integrity()
        text = (
            f"🔐 Causal Audit Ledger Merkle Integrity Verification\n"
            f"  Status: {'🟢 VERIFIED OK (SHA-256 Chain Intact)' if integrity else '🔴 CORRUPTED'}\n"
            f"  Engine: VerificationGate (SCITT Profile)"
        )
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def _tool_royal_rumble_dispatch(self, args: dict[str, object]) -> dict[str, object]:
        swarms_root = REPO_ROOT.parent / "02_EDIN_SWARMS"
        if str(swarms_root) not in sys.path:
            sys.path.insert(0, str(swarms_root))
        from agents_archi.clients.openrouter import OpenRouterClient, OpenRouterRoleTier

        prompt = str(args.get("prompt", ""))
        role_str = str(args.get("role", "coder_act")).lower()
        prefer_local = bool(args.get("prefer_local", False))
        raw_paths = args.get("context_paths")
        context_paths = [str(p) for p in raw_paths] if isinstance(raw_paths, list) else None

        client = OpenRouterClient(enable_local_failover=True)
        if prefer_local or role_str == "local_direct":
            res = client.query_local(prompt=prompt, fallback_reason="prefer_local_requested")
        else:
            role_map = {
                "planner": OpenRouterRoleTier.PLANNER,
                "coder_act": OpenRouterRoleTier.CODER_ACT,
                "structured_review": OpenRouterRoleTier.STRUCTURED_REVIEW,
                "subagent_fast": OpenRouterRoleTier.SUBAGENT_FAST,
                "sensitive_sovereign": OpenRouterRoleTier.SENSITIVE_SOVEREIGN,
            }
            role_tier = role_map.get(role_str, OpenRouterRoleTier.CODER_ACT)
            res = client.query(
                prompt=prompt,
                role=role_tier,
                context_paths=context_paths,
                allow_local_failover=True,
            )

        is_err = not bool(res.get("success"))
        return {
            "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}],
            "isError": is_err,
        }

    def _tool_blackboard_dispatch(self, args: dict[str, object]) -> dict[str, object]:
        from dataclasses import asdict

        swarms_root = REPO_ROOT.parent / "02_EDIN_SWARMS"
        if str(swarms_root) not in sys.path:
            sys.path.insert(0, str(swarms_root))
        from agents_archi.orchestrator import (
            BlackboardArbiter,
            BlackboardStatus,
            BlackboardTopic,
            ColdPathCurator,
            CortexWalStore,
        )

        op = str(args.get("operation", "")).strip().lower()
        task_id = str(args.get("task_id", "default_task")).strip()
        tick_raw = args.get("logical_tick", 1)
        logical_tick = int(tick_raw) if isinstance(tick_raw, (int, str)) else 1
        db_raw = args.get("db_path")
        db_path = Path(str(db_raw)) if db_raw else (REPO_ROOT.parent / ".babylon60" / "blackboard_wal.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)

        wal = CortexWalStore(db_path)
        try:
            arbiter = BlackboardArbiter(wal)
            if op == "publish":
                adm = arbiter.publish(
                    task_id=task_id,
                    logical_tick=logical_tick,
                    topic=str(args.get("topic", BlackboardTopic.HYPOTHESIS.value)),
                    author_agent_id=str(args.get("author_agent_id", "mcp_agent")),
                    target_path=str(args.get("target_path", "")),
                    claim=str(args.get("claim", "")),
                )
                payload_out: dict[str, object] = {
                    "admitted": adm.admitted,
                    "reason": adm.reason,
                    "tuple_id": adm.tuple_id,
                    "tuple": asdict(adm.tuple_record) if adm.tuple_record else None,
                }
                return {
                    "content": [{"type": "text", "text": json.dumps(payload_out, ensure_ascii=False)}],
                    "isError": not adm.admitted,
                }
            if op == "resolve":
                resolved = arbiter.resolve(
                    tuple_id=str(args.get("tuple_id", "")),
                    verifier_agent_id=str(args.get("verifier_agent_id", "")),
                    new_status=str(args.get("new_status", BlackboardStatus.VERIFIED.value)),
                    evidence_hash=str(args.get("evidence_hash", "")),
                    logical_tick=logical_tick,
                )
                return {
                    "content": [{"type": "text", "text": json.dumps(asdict(resolved), ensure_ascii=False)}],
                    "isError": False,
                }
            if op == "curate":
                curator = ColdPathCurator(arbiter)
                digest = curator.compact_resolved_tuples(task_id, logical_tick=logical_tick)
                return {
                    "content": [{"type": "text", "text": json.dumps(asdict(digest), ensure_ascii=False)}],
                    "isError": False,
                }
            if op == "poll":
                status_filter = str(args.get("new_status", BlackboardStatus.OPEN.value))
                tuples = arbiter.poll_subscription(task_id, status=status_filter)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps([asdict(t) for t in tuples], ensure_ascii=False),
                        }
                    ],
                    "isError": False,
                }
            return {
                "content": [{"type": "text", "text": f"Unsupported blackboard operation: {op}"}],
                "isError": True,
            }
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": f"Blackboard error: {exc}"}],
                "isError": True,
            }
        finally:
            wal.close()

    def _tool_detonate_ephemeral_mcp(self, args: dict[str, object]) -> dict[str, object]:
        from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager

        domain_name = str(args.get("domain_name", "")).strip()
        implementation_body = str(args.get("implementation_body", ""))
        raw_call_args = args.get("call_arguments", {})
        call_arguments: dict[str, object] = raw_call_args if isinstance(raw_call_args, dict) else {}
        desc_raw = args.get("description")
        description = str(desc_raw) if desc_raw is not None else None
        cortex_taint = str(args.get("cortex_taint", "MCP-BOMB-AUTO"))

        if not domain_name:
            return {
                "content": [{"type": "text", "text": "Missing required parameter: domain_name"}],
                "isError": True,
            }

        try:
            lifecycle = McpLifecycleManager(db_path=str(self.verification_gate.db_path))
            bomb_receipt = lifecycle.synthesize_and_detonate_bomb(
                domain_name=domain_name,
                implementation_body=implementation_body,
                call_arguments=call_arguments,
                description=description,
            )
            is_err = bomb_receipt.get("status") != "SUCCESS" or not bomb_receipt.get("self_destruct_verified", False)

            event = CortexEvent(
                event_type="MCP_BOMB_DETONATED",
                payload={
                    "server_name": bomb_receipt.get("server_name"),
                    "tool_name": bomb_receipt.get("tool_name"),
                    "code_hash": bomb_receipt.get("code_hash"),
                    "self_destruct_verified": bomb_receipt.get("self_destruct_verified"),
                    "status": bomb_receipt.get("status"),
                },
                cortex_taint=cortex_taint,
                agent_id="CORTEX-MCP-BOMB",
            )
            ack = self.ledger.append_event(event)
            bomb_receipt["bft_attestation"] = {
                "seq": ack["seq"],
                "entry_hash": ack["entry_hash"],
                "lamport_t": ack["lamport_t"],
            }
            return {
                "content": [{"type": "text", "text": json.dumps(bomb_receipt, ensure_ascii=False, indent=2)}],
                "isError": is_err,
            }
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": f"MCP Bomb synthesis/detonation blocked: {exc}"}],
                "isError": True,
            }

    def _tool_route_skill(self, args: dict[str, object]) -> dict[str, object]:
        """Deterministically route an agentic query/intent to the optimal CORTEX declarative skill."""
        query = str(args.get("query", "")).strip()
        scope_filter = str(args.get("scope", "all")).strip().lower()

        if not query:
            return {
                "content": [{"type": "text", "text": "Error: 'bft_route_skill' requires 'query' argument."}],
                "isError": True,
            }

        catalog = self._load_skills_catalog()
        entries = cast(list[dict[str, object]], catalog.get("entries", []))
        adjacency = cast(list[object], catalog.get("adjacency", []))

        q_norm = query.lower().strip()
        q_words = set(re.findall(r"\b[a-záéíóúñ0-9_-]{3,}\b", q_norm))

        best_skill: dict[str, object] | None = None
        best_score = 0.0

        for s in entries:
            s_scope = str(s.get("scope", "global")).lower()
            if scope_filter != "all" and s_scope != scope_filter:
                continue

            score = 0.0
            name = str(s.get("name", ""))
            alias = str(s.get("canonical_alias") or name)

            if q_norm in {name.lower(), alias.lower()}:
                score += 50.0

            raw_triggers = s.get("triggers", [])
            triggers: list[str] = raw_triggers if isinstance(raw_triggers, list) else []
            for trig in triggers:
                trig_str = str(trig).lower().strip()
                if not trig_str:
                    continue
                if trig_str in q_norm:
                    score += 15.0
                else:
                    common = set(trig_str.split()).intersection(q_words)
                    score += len(common) * 3.0

            name_words = set(name.replace("-", " ").lower().split()) | set(alias.replace("-", " ").lower().split())
            score += len(name_words.intersection(q_words)) * 2.5

            desc = str(s.get("description", "")).lower()
            desc_words = set(re.findall(r"\b[a-záéíóúñ0-9_-]{3,}\b", desc))
            score += len(desc_words.intersection(q_words)) * 0.5

            if score > best_score:
                best_score = score
                best_skill = s

        if not best_skill or best_score <= 0.0:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "query": query,
                                "scope": scope_filter,
                                "elected": None,
                                "match": False,
                                "message": f"No skill matched query '{query}' in scope '{scope_filter}'",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "isError": True,
            }

        role = str(best_skill.get("role", "ejecutor"))
        if role in ("arquitecto", "planificador"):
            upstream, downstream = "operador", "ejecutor"
        elif role in ("auditor", "verificador", "supervisor"):
            upstream, downstream = "ejecutor", "operador"
        else:
            upstream, downstream = "planificador", "auditor"

        connected_edges: list[object] = []
        target_name = best_skill.get("name")
        for edge in adjacency:
            if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                if edge[0] == target_name or edge[1] == target_name:
                    connected_edges.append(edge)
            elif isinstance(edge, dict):
                if edge.get("source") == target_name or edge.get("target") == target_name:
                    connected_edges.append(edge)

        payload = {
            "query": query,
            "scope": scope_filter,
            "score": round(best_score, 2),
            "match": True,
            "elected": {
                "name": best_skill.get("name"),
                "canonical_alias": best_skill.get("canonical_alias") or best_skill.get("name"),
                "display_name": best_skill.get("display_name", best_skill.get("name")),
                "role": role,
                "scope": best_skill.get("scope", "global"),
                "tier": best_skill.get("tier", 20000),
                "category": best_skill.get("category", "General"),
                "description": best_skill.get("description", ""),
                "triggers": best_skill.get("triggers", []),
                "handoff_chain": {
                    "upstream": upstream,
                    "current": role,
                    "downstream": downstream,
                },
                "dag_edges": connected_edges,
            },
        }

        return {
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
            "isError": False,
        }

    # -----------------------------------------------------------------------
    # Process a single JSON-RPC request (used for testing and stdio loop)
    # -----------------------------------------------------------------------

    def process_request(self, request: dict[str, object]) -> JsonRpcResponse | None:
        """Process a single JSON-RPC request and return the response."""
        method = str(request.get("method", ""))
        params_raw = request.get("params", {})
        params: dict[str, object] = params_raw if isinstance(params_raw, dict) else {}
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
    parser.add_argument(
        "--mail-ledger",
        type=str,
        default=None,
        help=f"Enable optional BabylonMail recording at this DB path (conventional path: {DEFAULT_MAIL_LEDGER_PATH})",
    )
    parser.add_argument(
        "--use-canonical-names",
        action="store_true",
        default=None,
        help="Expose canonical functional names (cortex_*) as primary in tools/list and resources/list",
    )
    args = parser.parse_args()

    server = CortexMCPServer(
        ledger_path=Path(args.ledger),
        mail_ledger_path=Path(args.mail_ledger) if args.mail_ledger is not None else None,
        use_canonical_names=True if args.use_canonical_names else None,
    )
    server.run_stdio()


if __name__ == "__main__":
    main()
