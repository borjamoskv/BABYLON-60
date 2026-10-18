"""Shared, read-only signature transport for MCP Apps and text-only clients.

UI support comes from the client's negotiated capabilities, never its brand.
The renderer validates declared data; it does not attest the model or hardware.
"""

from __future__ import annotations

from copy import deepcopy
from importlib.resources import files
import json

from babylon60.response_signature import SIGNATURE_SCHEMA, normalize_signature, render_signature


SIGNATURE_TOOL_NAME = "babylon_signature_render"
SIGNATURE_UI_URI = "ui://babylon60/signature"
SIGNATURE_UI_MIME = "text/html;profile=mcp-app"
SIGNATURE_SCHEMA_URI = "babylon://signature/schema"
_FORMATS = ("auto", "ui", "html", "markdown", "text", "json")


def supports_signature_ui(capabilities: object) -> bool:
    """Check the standard MCP Apps MIME capability without guessing host support."""
    if not isinstance(capabilities, dict):
        return False
    extensions = capabilities.get("extensions")
    if not isinstance(extensions, dict):
        return False
    ui = extensions.get("io.modelcontextprotocol/ui")
    if not isinstance(ui, dict):
        return False
    mime_types = ui.get("mimeTypes")
    return isinstance(mime_types, list) and SIGNATURE_UI_MIME in mime_types


def signature_tool_descriptor(ui_supported: bool = False) -> dict[str, object]:
    """Describe the same signature tool for clients with and without an app view."""
    descriptor: dict[str, object] = {
        "name": SIGNATURE_TOOL_NAME,
        "title": "Firma MOSKV-1",
        "description": (
            "Render a response signature from current, sourced observations. "
            "Supply observed_at and sources; never infer model, effort or measurements. "
            "auto selects the negotiated MCP App or Markdown fallback. "
            "Present one final signature only; do not duplicate the panel as a text footer."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "payload": deepcopy(SIGNATURE_SCHEMA),
                "format": {"type": "string", "enum": list(_FORMATS), "default": "auto"},
            },
            "required": ["payload"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    }
    if ui_supported:
        descriptor["_meta"] = {"ui": {"resourceUri": SIGNATURE_UI_URI}}
    return descriptor


def signature_resources(ui_supported: bool = False) -> list[dict[str, object]]:
    """Advertise the schema everywhere and the app only when negotiated."""
    resources: list[dict[str, object]] = [
        {
            "uri": SIGNATURE_SCHEMA_URI,
            "name": "response-signature-schema",
            "description": "Portable signature data schema with observation time and sources.",
            "mimeType": "application/json",
        }
    ]
    if ui_supported:
        resources.append(
            {
                "uri": SIGNATURE_UI_URI,
                "name": "response-signature-panel",
                "description": "Read-only MOSKV-1 panel; data arrives with each tool result.",
                "mimeType": SIGNATURE_UI_MIME,
            }
        )
    return resources


def read_signature_resource(uri: str) -> dict[str, object]:
    """Read a fixed packaged resource, never a client-provided filesystem path."""
    if uri == SIGNATURE_SCHEMA_URI:
        resource: dict[str, object] = {
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(SIGNATURE_SCHEMA, ensure_ascii=False, indent=2),
        }
    elif uri == SIGNATURE_UI_URI:
        resource = {
            "uri": uri,
            "mimeType": SIGNATURE_UI_MIME,
            "text": files("babylon60.mcp").joinpath("signature_app.html").read_text(encoding="utf-8"),
            "_meta": {
                "ui": {
                    "csp": {"connectDomains": [], "resourceDomains": []},
                    "prefersBorder": False,
                }
            },
        }
    else:
        raise ValueError(f"Unknown signature resource: {uri}")
    return {"contents": [resource]}


def render_signature_result(
    payload: dict[str, object],
    format: str = "auto",
    ui_supported: bool = False,
) -> dict[str, object]:
    """Return portable data and meaningful fallback content in a CallToolResult."""
    try:
        if format not in _FORMATS:
            raise ValueError(f"Unsupported signature format: {format}")
        signature = normalize_signature(payload)
        selected_format = format
        if format in ("auto", "ui"):
            selected_format = "ui" if ui_supported else "markdown"
        content_format = "markdown" if selected_format == "ui" else selected_format
        rendered = render_signature(signature, content_format)
    except (TypeError, ValueError) as error:
        return {
            "content": [{"type": "text", "text": f"Firma no generada: {error}"}],
            "isError": True,
        }
    return {
        "content": [{"type": "text", "text": rendered}],
        "structuredContent": {"signature": signature, "selected_format": selected_format},
        "isError": False,
    }
