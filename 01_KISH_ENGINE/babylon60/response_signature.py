"""Portable response signatures from explicit observations, without telemetry.

Source labels come from the caller. Rendering does not attest to their truth.
"""

from datetime import datetime
from html import escape
from importlib.resources import files
import json
import re
from string import Template
import unicodedata


FIELD_NAMES = (
    "LLM",
    "MODO COGNITIVO",
    "TOPOLOGÍA ACTIVA",
    "RÉGIMEN TÉRMICO",
    "EXERGÍA INFORMATIVA",
    "MUTACIÓN CAUSAL",
)
OPTIONAL_FIELD_NAMES = ("VERIFICACIÓN", "CAMBIOS", "LÍMITES")
_ALL_FIELDS = FIELD_NAMES + OPTIONAL_FIELD_NAMES
_DEFAULTS = dict(zip(FIELD_NAMES, ("No expuesto", "No expuesto", "MOSKV-1", "No medido", "No medida", "Ninguna")))
_ABSENT_SOURCE = "No expuesta"
_MISSING_SOURCES = ("No expuesta", "No expuesto", "No disponible", "Desconocida", "Desconocido")
_ISO_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$"
_MUTATION_PATTERN = r"^(?:[a-fA-F0-9]{7,64}|Ninguna(?: \([^()|]+\))?)$"
_PLACEHOLDER_PATTERN = r"\{\{|\}\}|\$\{|\b(?:TODO|TBD|FIXME)\b|<(?:MODEL|MODELO|EFFORT|ESFUERZO|HASH|FUENTE|VALOR)>"
_PLACEHOLDERS = re.compile(_PLACEHOLDER_PATTERN, re.IGNORECASE)
_TEXT_SCHEMA: dict[str, object] = {
    "type": "string",
    "minLength": 1,
    "maxLength": 4096,
    "pattern": r"^[^\u0000-\u001f\u007f-\u009f]+$",
    "not": {"pattern": _PLACEHOLDER_PATTERN},
}

SIGNATURE_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "MOSKV-1 response signature observation",
    "description": "Current observations only; source declarations are not attestation. Unknown data stays unknown.",
    "type": "object",
    "additionalProperties": False,
    "required": ["observed_at"],
    "properties": {
        "schema_version": {"type": "integer", "const": 1, "default": 1},
        "observed_at": {"type": "string", "format": "date-time", "pattern": _ISO_PATTERN},
        "fields": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                field: (
                    {"type": "string", "const": "MOSKV-1"}
                    if field == "TOPOLOGÍA ACTIVA"
                    else {**_TEXT_SCHEMA, "allOf": [{"pattern": _MUTATION_PATTERN}]}
                    if field == "MUTACIÓN CAUSAL"
                    else _TEXT_SCHEMA.copy()
                )
                for field in _ALL_FIELDS
            },
        },
        "sources": {
            "type": "object",
            "additionalProperties": False,
            "properties": {field: _TEXT_SCHEMA.copy() for field in _ALL_FIELDS},
        },
    },
    "allOf": [
        {
            "if": {
                "required": ["fields"],
                "properties": {"fields": {"required": [field], "properties": {field: {"not": {"const": default}}}}},
            },
            "then": {
                "required": ["sources"],
                "properties": {
                    "sources": {"required": [field], "properties": {field: {"not": {"enum": list(_MISSING_SOURCES)}}}},
                },
            },
        }
        for field, default in (_DEFAULTS | dict.fromkeys(OPTIONAL_FIELD_NAMES, "")).items()
        if field != "TOPOLOGÍA ACTIVA"
    ],
}


def _clean_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ValueError(f"{label} must be a nonempty string of at most 4096 characters")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for character in value):
        raise ValueError(f"{label} contains control or unsupported Unicode characters")
    if _PLACEHOLDERS.search(value) or value.strip() in {"...", "…", "???"}:
        raise ValueError(f"{label} contains an unresolved placeholder")
    return value


def _string_map(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or key not in _ALL_FIELDS:
            raise ValueError(f"{label} contains an unknown field")
        result[key] = _clean_text(item, f"{label}.{key}")
    return result


def _validated_parts(payload: dict[str, object]) -> tuple[dict[str, str], dict[str, str], str]:
    allowed = {"schema_version", "observed_at", "fields", "sources"}
    if not isinstance(payload, dict) or any(key not in allowed for key in payload):
        raise ValueError(
            "Signature payload must be an object with only schema_version, observed_at, fields and sources"
        )
    version = payload.get("schema_version", 1)
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported signature schema_version; expected integer 1")
    observed_at = _clean_text(payload.get("observed_at"), "observed_at")
    if not re.fullmatch(_ISO_PATTERN, observed_at):
        raise ValueError("observed_at must be an ISO8601 timestamp with seconds and an explicit timezone")
    if not observed_at.endswith("Z") and (int(observed_at[-5:-3]) > 23 or int(observed_at[-2:]) > 59):
        raise ValueError("observed_at has an invalid timezone offset")
    try:
        stamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("observed_at is not a valid date and timezone") from error
    if stamp.utcoffset() is None:
        raise ValueError("observed_at requires an explicit timezone")
    fields = _DEFAULTS | _string_map(payload.get("fields", {}), "fields")
    sources = dict.fromkeys(FIELD_NAMES, _ABSENT_SOURCE) | _string_map(payload.get("sources", {}), "sources")
    if fields["TOPOLOGÍA ACTIVA"] != "MOSKV-1":
        raise ValueError("TOPOLOGÍA ACTIVA must be MOSKV-1")
    mutation = fields["MUTACIÓN CAUSAL"]
    if not re.fullmatch(_MUTATION_PATTERN, mutation) or (
        mutation.startswith("Ninguna (") and not mutation[9:-1].strip()
    ):
        raise ValueError("MUTACIÓN CAUSAL must be a Git commit hash, Ninguna or Ninguna (object)")
    for field, value in fields.items():
        if value != _DEFAULTS.get(field) and sources.get(field, _ABSENT_SOURCE).strip().casefold() in {
            source.casefold() for source in _MISSING_SOURCES
        }:
            raise ValueError(f"An exposed or measured {field} requires a source")
    return fields, sources, observed_at


def normalize_signature(payload: dict[str, object]) -> dict[str, object]:
    """Return six base fields and supplied optional context, without altering input."""
    fields, sources, observed_at = _validated_parts(payload)
    return {"schema_version": 1, "observed_at": observed_at, "fields": fields, "sources": sources}


def _markdown(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()#+.!|~-])", r"\\\1", escape(value, quote=False))


def _render_html(fields: dict[str, str], sources: dict[str, str], observed_at: str) -> str:
    tokens: dict[str, str] = {"OBSERVED_AT": escape(observed_at, quote=True)}
    for field, token in zip(FIELD_NAMES, ("MODEL", "EFFORT", "TOPOLOGY", "THERMAL", "LEXICAL", "MUTATION")):
        tokens[token] = escape(fields[field], quote=True)
        tokens[f"{token}_SOURCE"] = escape(sources[field], quote=True)
    tokens["HERO_CLASS"] = ""
    tokens["EFFORT_SECTION"] = ""
    if fields["MODO COGNITIVO"] != _DEFAULTS["MODO COGNITIVO"]:
        tokens["HERO_CLASS"] = "s-has-effort"
        tokens["EFFORT_SECTION"] = (
            '<div class="s-effort"><div class="s-label">Modo cognitivo</div>'
            f'<div class="s-effort-value" data-signature-field="MODO COGNITIVO">{tokens["EFFORT"]}</div>'
            f'<div class="s-meta">Fuente: <span data-signature-source="MODO COGNITIVO">{tokens["EFFORT_SOURCE"]}</span></div></div>'
        )
    metrics: list[str] = []
    for field, token, label, icon, note in (
        ("RÉGIMEN TÉRMICO", "THERMAL", "Régimen térmico", "◉", "Estado térmico y temperatura son medidas distintas."),
        ("EXERGÍA INFORMATIVA", "LEXICAL", "Índice léxico", "≋", "No mide energía física ni calidad."),
    ):
        if fields[field] != _DEFAULTS[field]:
            metrics.append(
                f'<div class="s-metric"><span class="s-icon" aria-hidden="true">{icon}</span>'
                f'<div class="s-label">{label}</div><div class="s-value" data-signature-field="{field}">{tokens[token]}</div>'
                f'<div class="s-note">{note}</div><div class="s-note">Fuente: '
                f'<span data-signature-source="{field}">{tokens[token + "_SOURCE"]}</span></div></div>'
            )
    tokens["METRICS_SECTION"] = '<div class="s-grid">' + "".join(metrics) + "</div>" if metrics else ""
    tokens["CHANGE_SECTION"] = ""
    if fields["MUTACIÓN CAUSAL"] != _DEFAULTS["MUTACIÓN CAUSAL"]:
        tokens["CHANGE_SECTION"] = (
            '<div class="s-change"><div class="s-label">Mutación causal</div>'
            f'<div class="s-value" data-signature-field="MUTACIÓN CAUSAL">{tokens["MUTATION"]}</div>'
            f'<div class="s-note">Fuente: <span data-signature-source="MUTACIÓN CAUSAL">{tokens["MUTATION_SOURCE"]}</span></div>'
            "</div>"
        )
    context: list[str] = []
    for field in OPTIONAL_FIELD_NAMES:
        if field in fields:
            context.append(
                f'<div class="s-source"><dt>{field.capitalize()}</dt><dd>'
                f'<span class="s-context-value" data-signature-field="{field}">{escape(fields[field], quote=True)}</span>'
                f'<div class="s-note">Fuente: <span data-signature-source="{field}">{escape(sources[field], quote=True)}</span>'
                "</div></dd></div>"
            )
    tokens["CONTEXT_SECTION"] = '<dl class="s-context">' + "".join(context) + "</dl>" if context else ""
    template = files("babylon60").joinpath("signature_panel.html").read_text(encoding="utf-8")
    return Template(template).substitute(tokens)


def render_signature(payload: dict[str, object], format: str) -> str:
    """Render html, markdown, text or json; never infer or measure missing data.

    HTML is a self-contained fragment, also usable as a standalone .html file.
    No writes, network access, clock reads or kernel calls are performed.
    """
    if not isinstance(format, str) or format not in {"html", "markdown", "text", "json"}:
        raise ValueError("Unsupported signature format; expected html, markdown, text or json")
    fields, sources, observed_at = _validated_parts(payload)
    if format == "json":
        return json.dumps(
            {"schema_version": 1, "observed_at": observed_at, "fields": fields, "sources": sources},
            ensure_ascii=False,
            indent=2,
        )
    if format == "text":
        rows = [f"Observación: {observed_at}", "Fuentes:"]
        rows.extend(f"  {field}: {sources[field]}" for field in FIELD_NAMES)
        rows.extend(
            f"{field}: {fields[field]}\n  Fuente: {sources[field]}" for field in OPTIONAL_FIELD_NAMES if field in fields
        )
        rows.extend(["Sin atestación criptográfica.", ""])
        rows.extend(f"[ {field} ]: {fields[field]}" for field in FIELD_NAMES)
        return "\n".join(rows)
    if format == "markdown":
        rows = ["| Indicador | Dato | Fuente |", "| :--- | :--- | :--- |"]
        rows.extend(
            f"| {_markdown(field)} | {_markdown(fields[field])} | {_markdown(sources[field])} |"
            for field in _ALL_FIELDS
            if field in fields
        )
        return "\n".join(rows) + f"\n\nObservación: {_markdown(observed_at)} · Sin atestación criptográfica."
    return _render_html(fields, sources, observed_at)
